from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from flask_cors import CORS
from datetime import datetime
import base64
import json
import os
import queue
import random
import secrets
import threading
import time
import math

# ─── ML / sklearn (graceful fallback if not installed) ────────────────────────
try:
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

DATA_DIR   = os.path.dirname(os.path.abspath(__file__))
ACCESS_FILE = os.path.join(DATA_DIR, "access_passes.json")
REQUEST_FILE = os.path.join(DATA_DIR, "visitor_request.json")
LOG_FILE    = os.path.join(DATA_DIR, "visit_log.json")
BLOCK_FILE  = os.path.join(DATA_DIR, "blocked.json")
SNAP_FILE   = os.path.join(DATA_DIR, "visitor_snapshot.jpg")
VISITORS_FILE = os.path.join(DATA_DIR, "visitors_db.json")
COUNCIL_LOG_FILE = os.path.join(DATA_DIR, "council_log.json")

PASS_TTL        = 180
COURIER_TTL     = 600
MAX_FAILS       = 3
LOCKOUT_SECONDS = 300
RING_WINDOW     = 60
MAX_RINGS       = 5

# ─── Agent weights (Sentinel-X council) ──────────────────────────────────────
AGENT_WEIGHTS = {
    "threat":   0.40,
    "identity": 0.30,
    "trust":    0.20,
    "behavior": 0.10,
}

clients      = []
clients_lock = threading.Lock()

# ─── Train a simple RandomForest threat model on startup ─────────────────────
_rf_model = None

def _train_model():
    global _rf_model
    if not ML_AVAILABLE:
        return
    # Synthetic training data: [trust_score, face_match, failed_attempts, behavior_risk, visitor_type_enc]
    # label: 0=SAFE, 1=RISKY
    X = [
        [90, 95, 0,  5, 1],   # family, trusted
        [85, 90, 0,  8, 1],
        [80, 88, 0, 10, 2],   # guest, okay
        [70, 75, 1, 15, 2],
        [60, 65, 2, 30, 3],   # service, medium risk
        [40, 50, 4, 70, 4],   # unknown, risky
        [30, 40, 5, 80, 4],
        [20, 30, 5, 90, 4],
        [55, 60, 2, 40, 3],
        [75, 80, 1, 20, 2],
        [88, 91, 0, 12, 1],
        [35, 45, 3, 65, 4],
        [65, 70, 1, 25, 3],
        [92, 97, 0,  3, 1],
        [10, 20, 5, 95, 4],
    ]
    y = [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1]
    _rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
    _rf_model.fit(X, y)

_train_model()

VISITOR_TYPE_ENC = {"family": 1, "guest": 2, "service": 3, "courier": 3, "unknown": 4}

# ─── Utility helpers ──────────────────────────────────────────────────────────
def now_label():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")

def read_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def append_log(event, detail=None):
    log = read_json(LOG_FILE, [])
    row = {"event": event, "time": now_label(), "detail": detail or {}}
    log.insert(0, row)
    write_json(LOG_FILE, log[:200])
    push_event("log_updated", row)

def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()

def generate_code():
    return str(random.randint(100000, 999999))

def generate_token():
    return secrets.token_urlsafe(18)

# ─── Visitor history DB ───────────────────────────────────────────────────────
def get_visitor_history(name, phone):
    db = read_json(VISITORS_FILE, {})
    key = f"{name.lower().strip()}:{phone.strip()}"
    return db.get(key, {"approved": 0, "denied": 0, "failed_attempts": 0, "visits": 0})

def update_visitor_history(name, phone, outcome):
    db = read_json(VISITORS_FILE, {})
    key = f"{name.lower().strip()}:{phone.strip()}"
    rec = db.get(key, {"approved": 0, "denied": 0, "failed_attempts": 0, "visits": 0})
    rec["visits"] += 1
    if outcome == "approved":
        rec["approved"] += 1
    elif outcome == "denied":
        rec["denied"] += 1
    elif outcome == "failed":
        rec["failed_attempts"] += 1
    db[key] = rec
    write_json(VISITORS_FILE, db)

# ─── SSE push ────────────────────────────────────────────────────────────────
def push_event(event, payload):
    message = f"event: {event}\ndata: {json.dumps(payload)}\n\n"
    with clients_lock:
        for q in list(clients):
            try:
                q.put_nowait(message)
            except queue.Full:
                clients.remove(q)

# ─── Rate-limit helpers ───────────────────────────────────────────────────────
def is_limited(ip, mode):
    data = read_json(BLOCK_FILE, {})
    row = data.get(ip, {"rings": [], "fails": 0, "locked_until": 0})
    current = time.time()
    if row.get("locked_until", 0) > current:
        return True, int(row["locked_until"] - current)
    if mode == "ring":
        row["rings"] = [t for t in row.get("rings", []) if current - t < RING_WINDOW]
        if len(row["rings"]) >= MAX_RINGS:
            data[ip] = row
            write_json(BLOCK_FILE, data)
            return True, RING_WINDOW
    return False, 0

def record_ring(ip):
    data = read_json(BLOCK_FILE, {})
    row = data.get(ip, {"rings": [], "fails": 0, "locked_until": 0})
    current = time.time()
    row["rings"] = [t for t in row.get("rings", []) if current - t < RING_WINDOW]
    row["rings"].append(current)
    data[ip] = row
    write_json(BLOCK_FILE, data)

def record_fail(ip):
    data = read_json(BLOCK_FILE, {})
    row = data.get(ip, {"rings": [], "fails": 0, "locked_until": 0})
    row["fails"] = row.get("fails", 0) + 1
    if row["fails"] >= MAX_FAILS:
        row["fails"] = 0
        row["locked_until"] = time.time() + LOCKOUT_SECONDS
    data[ip] = row
    write_json(BLOCK_FILE, data)
    return max(0, MAX_FAILS - row.get("fails", 0))

def clear_fail(ip):
    data = read_json(BLOCK_FILE, {})
    if ip in data:
        data[ip]["fails"] = 0
        data[ip]["locked_until"] = 0
        write_json(BLOCK_FILE, data)

# ─── Pass helpers ─────────────────────────────────────────────────────────────
def load_passes():
    passes = read_json(ACCESS_FILE, [])
    current = time.time()
    changed = False
    for p in passes:
        if p.get("status") == "active" and current > p.get("expires_at", 0):
            p["status"] = "expired"
            changed = True
    if changed:
        write_json(ACCESS_FILE, passes)
    return passes

def save_passes(passes):
    write_json(ACCESS_FILE, passes)

def active_passes():
    return [p for p in load_passes() if p.get("status") == "active"]

def public_pass(p):
    remaining = max(0, int(p.get("expires_at", 0) - time.time()))
    data = dict(p)
    data["remaining"] = remaining
    data["share_url"] = request.host_url.rstrip("/") + "/pass/" + p["token"]
    return data

# ═════════════════════════════════════════════════════════════════════════════
#  MULTI-AGENT AI SECURITY COUNCIL
# ═════════════════════════════════════════════════════════════════════════════

def _vote_from_score(score, thresholds=(80, 50)):
    """Convert a numeric score (0-100) to APPROVE / REVIEW / DENY."""
    if score >= thresholds[0]:
        return "APPROVE"
    elif score >= thresholds[1]:
        return "REVIEW"
    return "DENY"


def agent_identity(face_match: float) -> dict:
    """
    Agent 1 – Identity Agent
    Verifies whether the visitor is known based on face-match score.
    In a real deployment this would come from a face-recognition model;
    here the visitor supplies it (or we estimate from visitor_type).
    """
    if face_match >= 90:
        confidence = "HIGH"
    elif face_match >= 70:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    vote = _vote_from_score(face_match, (90, 70))
    return {
        "agent": "Identity Agent",
        "icon": "🪪",
        "description": "Verifies visitor identity via face-match score",
        "face_match": round(face_match, 1),
        "confidence": confidence,
        "score": round(face_match, 1),   # identity score = face_match
        "vote": vote,
        "reasoning": f"Face-match {face_match:.0f}% → confidence {confidence}",
    }


def agent_trust(history: dict, visitor_type: str) -> dict:
    """
    Agent 2 – Trust Agent
    Evaluates trustworthiness from visit history.
    Formula: approved*5 - denied*10 - failed_attempts*15  (capped 0-100)
    """
    approved  = history.get("approved", 0)
    denied    = history.get("denied", 0)
    failed    = history.get("failed_attempts", 0)
    total_visits = history.get("visits", 0)

    base = 60  # first-time visitors start at neutral
    if total_visits == 0:
        trust_score = base
        reasoning = "First-time visitor – neutral baseline 60"
    else:
        trust_score = base + approved * 5 - denied * 10 - failed * 15
        reasoning = (
            f"{approved} approvals (+{approved*5}), "
            f"{denied} denials (-{denied*10}), "
            f"{failed} failed attempts (-{failed*15})"
        )

    # Bonus for trusted categories
    if visitor_type == "family":
        trust_score += 15
        reasoning += " | +15 trusted-family bonus"
    elif visitor_type == "guest":
        trust_score += 5

    trust_score = max(0, min(100, trust_score))
    vote = _vote_from_score(trust_score)
    return {
        "agent": "Trust Agent",
        "icon": "🤝",
        "description": "Evaluates historical trustworthiness",
        "approved_visits":  approved,
        "denied_visits":    denied,
        "failed_attempts":  failed,
        "total_visits":     total_visits,
        "score":  trust_score,
        "vote":   vote,
        "reasoning": reasoning,
    }


def agent_behavior(visitor_type: str, purpose: str, hour: int, device_info: str) -> dict:
    """
    Agent 3 – Behavior Agent
    Detects unusual patterns: visit time, visitor category, unclear purpose.
    Lower risk = higher behavior_score for weighted voting.
    """
    risk = 0
    notes = []

    # Time of day
    if 8 <= hour <= 20:
        notes.append("Normal business hours")
    elif 20 < hour <= 23:
        risk += 15
        notes.append("+15 Evening visit")
    else:
        risk += 30
        notes.append("+30 Late-night / early-morning visit")

    # Visitor category risk
    type_risk = {"family": 0, "guest": 10, "courier": 8, "service": 18, "unknown": 35}
    r = type_risk.get(visitor_type, 25)
    risk += r
    notes.append(f"+{r} visitor type '{visitor_type}'")

    # Purpose clarity
    if len(purpose.strip()) < 5:
        risk += 20
        notes.append("+20 Unclear purpose")
    elif len(purpose.strip()) > 10:
        notes.append("Purpose is clear")

    risk = max(0, min(100, risk))
    behavior_score = 100 - risk   # invert: low risk → high score
    vote = _vote_from_score(behavior_score, (65, 40))

    return {
        "agent": "Behavior Agent",
        "icon": "🔍",
        "description": "Detects behavioral anomalies and risk patterns",
        "visit_hour":      hour,
        "visitor_type":    visitor_type,
        "purpose_length":  len(purpose.strip()),
        "risk":            risk,
        "score":           behavior_score,
        "vote":            vote,
        "reasoning":       " | ".join(notes),
    }


def agent_threat(trust_score: float, face_match: float, failed_attempts: int,
                 behavior_risk: int, visitor_type: str) -> dict:
    """
    Agent 4 – Threat Prediction Agent
    Uses RandomForest (sklearn) when available; falls back to rule-based heuristic.
    """
    type_enc = VISITOR_TYPE_ENC.get(visitor_type, 4)
    features = [trust_score, face_match, failed_attempts, behavior_risk, type_enc]

    if ML_AVAILABLE and _rf_model is not None:
        arr = np.array([features])
        proba = _rf_model.predict_proba(arr)[0]
        threat_probability = round(float(proba[1]) * 100, 1)  # class 1 = RISKY
        method = "RandomForest ML model"
    else:
        # Rule-based fallback
        threat_probability = max(0.0, min(100.0,
            (100 - trust_score) * 0.35
            + (100 - face_match) * 0.25
            + failed_attempts * 10
            + behavior_risk * 0.2
        ))
        method = "Rule-based heuristic"

    # Threat probability → vote (lower threat = better)
    threat_score = 100 - threat_probability
    vote = _vote_from_score(threat_score, (70, 40))

    return {
        "agent": "Threat Prediction Agent",
        "icon": "🤖",
        "description": f"ML-based threat predictor ({method})",
        "threat_probability": round(threat_probability, 1),
        "score": round(threat_score, 1),
        "vote": vote,
        "method": method,
        "features": {
            "trust_score":    trust_score,
            "face_match":     face_match,
            "failed_attempts": failed_attempts,
            "behavior_risk":  behavior_risk,
            "visitor_type":   visitor_type,
        },
        "reasoning": (
            f"Threat probability {threat_probability:.1f}% → "
            f"threat score {threat_score:.1f} → {vote}"
        ),
    }


def run_security_council(visitor_data: dict, history: dict) -> dict:
    """
    AI Security Council Engine
    Runs all 4 agents, applies weighted voting, returns final verdict.
    """
    visitor_type = visitor_data.get("visitor_type", "unknown")
    name         = visitor_data.get("name", "")
    purpose      = visitor_data.get("purpose", "")
    hour         = datetime.now().hour
    device_info  = visitor_data.get("device_info", "")

    # Estimate face_match from visitor type (proxy; real deployment = face-recog API)
    type_face_base = {"family": 88, "guest": 65, "courier": 60, "service": 55, "unknown": 40}
    face_match = float(visitor_data.get("face_match",
        type_face_base.get(visitor_type, 50) + random.uniform(-8, 8)))
    face_match = max(0, min(100, face_match))

    # Run all 4 agents
    id_agent   = agent_identity(face_match)
    trust_ag   = agent_trust(history, visitor_type)
    behav_ag   = agent_behavior(visitor_type, purpose, hour, device_info)
    threat_ag  = agent_threat(
        trust_ag["score"], face_match,
        history.get("failed_attempts", 0),
        100 - behav_ag["score"],   # behavior_risk
        visitor_type
    )

    agents = [id_agent, trust_ag, behav_ag, threat_ag]

    # ── Weighted scoring ──────────────────────────────────────────────────
    final_score = (
        id_agent["score"]  * AGENT_WEIGHTS["identity"]
        + trust_ag["score"]  * AGENT_WEIGHTS["trust"]
        + behav_ag["score"]  * AGENT_WEIGHTS["behavior"]
        + threat_ag["score"] * AGENT_WEIGHTS["threat"]
    )
    final_score = round(final_score, 1)

    # ── Simple majority vote count ────────────────────────────────────────
    vote_counts = {"APPROVE": 0, "REVIEW": 0, "DENY": 0}
    for a in agents:
        vote_counts[a["vote"]] = vote_counts.get(a["vote"], 0) + 1

    weighted_decision = _vote_from_score(final_score, (72, 48))

    # ── Override: if threat agent says DENY, elevate ──────────────────────
    if threat_ag["vote"] == "DENY" and vote_counts["DENY"] >= 2:
        weighted_decision = "DENY"
    elif threat_ag["vote"] == "DENY" and weighted_decision == "APPROVE":
        weighted_decision = "REVIEW"   # at least escalate

    council_result = {
        "agents":           agents,
        "vote_counts":      vote_counts,
        "weighted_score":   final_score,
        "final_decision":   weighted_decision,
        "weights":          AGENT_WEIGHTS,
        "timestamp":        now_label(),
        "visitor_name":     name,
        "visitor_type":     visitor_type,
        "risk_profile": {
            "level": "LOW" if final_score >= 72 else "MEDIUM" if final_score >= 48 else "HIGH",
            "score": final_score,
        },
        "recommendation": _recommendation(weighted_decision, agents),
    }
    return council_result


def _recommendation(decision: str, agents: list) -> str:
    if decision == "APPROVE":
        return "All major security indicators are within acceptable range. Safe to grant access."
    elif decision == "REVIEW":
        flags = [a["agent"] for a in agents if a["vote"] in ("REVIEW", "DENY")]
        return f"Caution: {', '.join(flags)} raised concerns. Manual owner review recommended."
    else:
        flags = [a["agent"] for a in agents if a["vote"] == "DENY"]
        return f"Access denied. {', '.join(flags)} flagged this visitor as high risk."


def save_council_log(council_result: dict, visitor_id: str):
    log = read_json(COUNCIL_LOG_FILE, [])
    log.insert(0, {"visitor_id": visitor_id, **council_result})
    write_json(COUNCIL_LOG_FILE, log[:100])

# ═════════════════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/events")
def events():
    q = queue.Queue(maxsize=50)
    with clients_lock:
        clients.append(q)

    def stream():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    yield q.get(timeout=25)
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with clients_lock:
                if q in clients:
                    clients.remove(q)

    return Response(stream_with_context(stream()), mimetype="text/event-stream")


@app.route("/api/visitor_snapshot", methods=["POST"])
def visitor_snapshot():
    with open(SNAP_FILE, "wb") as f:
        f.write(request.data)
    return jsonify({"saved": True})


@app.route("/api/get_snapshot")
def get_snapshot():
    if not os.path.exists(SNAP_FILE):
        return jsonify({"img": None})
    with open(SNAP_FILE, "rb") as f:
        image = base64.b64encode(f.read()).decode("utf-8")
    return jsonify({"img": "data:image/jpeg;base64," + image})


@app.route("/api/clear_snapshot", methods=["POST"])
def clear_snapshot():
    if os.path.exists(SNAP_FILE):
        os.remove(SNAP_FILE)
    return jsonify({"cleared": True})


@app.route("/api/visitor_request", methods=["POST"])
def visitor_request():
    ip = client_ip()
    limited, wait = is_limited(ip, "ring")
    if limited:
        return jsonify({"error": f"Too many requests. Try again in {wait} seconds."}), 429
    record_ring(ip)

    body = request.get_json(silent=True) or {}
    visitor_type = body.get("visitor_type", "guest")
    name         = body.get("name", "").strip()
    purpose      = body.get("purpose", "").strip()
    phone        = body.get("phone", "").strip()
    package_id   = body.get("package_id", "").strip()

    if not name or not purpose or not phone:
        return jsonify({"error": "Name, phone and purpose are required."}), 400
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"error": "Phone number must be exactly 10 digits."}), 400

    # ── Run AI Security Council ───────────────────────────────────────────
    history = get_visitor_history(name, phone)
    visitor_data = {
        "visitor_type": visitor_type,
        "name":    name,
        "purpose": purpose,
        "phone":   phone,
    }
    council = run_security_council(visitor_data, history)
    save_council_log(council, name)

    data = {
        "id":           generate_token(),
        "pending":      True,
        "time":         now_label(),
        "visitor_type": visitor_type,
        "name":         name,
        "purpose":      purpose,
        "phone":        phone,
        "package_id":   package_id,
        "ip":           ip,
        "council":      council,   # ← AI Security Council result
        # legacy risk field (from original app) kept for backward compat
        "risk": {
            "score": round(100 - council["weighted_score"]),
            "level": council["risk_profile"]["level"].lower(),
            "reasons": [a["reasoning"] for a in council["agents"]],
        },
    }

    existing = read_json(REQUEST_FILE, [])
    if not isinstance(existing, list):
        existing = [existing] if existing.get("pending") else []
    existing.insert(0, data)
    write_json(REQUEST_FILE, existing[:10])
    append_log("visitor_requested", {"name": name, "council_decision": council["final_decision"]})
    push_event("visitor_arrived", data)
    return jsonify({"message": "Owner alerted", "council": council})


@app.route("/api/check_requests")
def check_requests():
    raw = read_json(REQUEST_FILE, [])
    if not isinstance(raw, list):
        raw = [raw] if raw.get("pending") else []
    pending = [r for r in raw if r.get("pending")]
    return jsonify(pending[0] if pending else {"pending": False})


@app.route("/api/all_requests")
def all_requests():
    raw = read_json(REQUEST_FILE, [])
    if not isinstance(raw, list):
        raw = [raw] if raw.get("pending") else []
    return jsonify(raw)


@app.route("/api/clear_requests", methods=["POST"])
def clear_requests():
    raw = read_json(REQUEST_FILE, [])
    if not isinstance(raw, list):
        raw = [raw] if raw.get("pending") else []
    dismissed = False
    for r in raw:
        if r.get("pending") and not dismissed:
            r["pending"] = False
            dismissed = True
    write_json(REQUEST_FILE, raw)
    if os.path.exists(SNAP_FILE):
        os.remove(SNAP_FILE)
    push_event("request_cleared", {})
    return jsonify({"cleared": True})


@app.route("/api/pending_count")
def pending_count():
    raw = read_json(REQUEST_FILE, [])
    if not isinstance(raw, list):
        raw = [raw] if raw.get("pending") else []
    count = sum(1 for r in raw if r.get("pending"))
    return jsonify({"count": count})


@app.route("/api/create_pass", methods=["POST"])
def create_pass():
    body    = request.get_json(silent=True) or {}
    visitor = body.get("visitor", {})
    mode    = body.get("mode", visitor.get("visitor_type", "guest"))
    ttl     = COURIER_TTL if mode == "courier" else PASS_TTL
    if body.get("ttl"):
        ttl = max(30, min(int(body["ttl"]), 3600))

    code = generate_code()
    access_pass = {
        "id":           generate_token(),
        "token":        generate_token(),
        "code":         code,
        "mode":         mode,
        "visitor":      visitor,
        "created_at":   time.time(),
        "expires_at":   time.time() + ttl,
        "created_label": now_label(),
        "ttl":          ttl,
        "status":       "active",
        "used_at":      None,
        "max_uses":     1,
        "uses":         0,
        "instructions": body.get("instructions", ""),
    }
    passes = load_passes()
    passes.insert(0, access_pass)
    save_passes(passes[:50])
    append_log("pass_created", {"mode": mode, "visitor": visitor})
    push_event("pass_created", public_pass(access_pass))
    # Update visitor history when owner approves
    name  = visitor.get("name", "")
    phone = visitor.get("phone", "")
    if name and phone:
        update_visitor_history(name, phone, "approved")
    return jsonify(public_pass(access_pass))


@app.route("/api/passes")
def get_passes():
    return jsonify([public_pass(p) for p in active_passes()])


@app.route("/api/revoke_pass/<pass_id>", methods=["POST"])
def revoke_pass(pass_id):
    passes = load_passes()
    for p in passes:
        if p["id"] == pass_id:
            p["status"] = "revoked"
            visitor = p.get("visitor", {})
            append_log("pass_revoked", {"visitor": visitor, "mode": p.get("mode")})
            push_event("pass_revoked", {"id": pass_id})
            # Update visitor history
            name  = visitor.get("name", "")
            phone = visitor.get("phone", "")
            if name and phone:
                update_visitor_history(name, phone, "denied")
            break
    save_passes(passes)
    return jsonify({"revoked": True})


@app.route("/api/verify_code", methods=["POST"])
def verify_code():
    ip = client_ip()
    limited, wait = is_limited(ip, "verify")
    if limited:
        return jsonify({"result": "locked", "message": f"Locked for {wait} seconds."}), 429

    entered = (request.get_json(silent=True) or {}).get("code", "").strip()
    passes  = load_passes()
    for p in passes:
        if p.get("status") == "active" and p.get("code") == entered:
            if time.time() > p["expires_at"]:
                p["status"] = "expired"
                save_passes(passes)
                return jsonify({"result": "expired"})
            if p.get("uses", 0) >= p.get("max_uses", 1):
                p["status"] = "used"
                save_passes(passes)
                return jsonify({"result": "used"})
            p["uses"]   = p.get("uses", 0) + 1
            p["used_at"] = now_label()
            p["status"] = "used"
            save_passes(passes)
            clear_fail(ip)
            detail = {"mode": p.get("mode"), "visitor": p.get("visitor", {}), "ip": ip}
            append_log("access_granted", detail)
            push_event("door_unlocked", detail)
            return jsonify({"result": "success", "mode": p.get("mode")})

    attempts_left = record_fail(ip)
    append_log("access_denied", {"ip": ip, "attempts_left": attempts_left})
    push_event("access_denied", {"ip": ip, "attempts_left": attempts_left})
    return jsonify({"result": "fail", "attempts_left": attempts_left})


@app.route("/api/log")
def get_log():
    return jsonify(read_json(LOG_FILE, []))

@app.route("/api/log", methods=["DELETE"])
def clear_log():
    write_json(LOG_FILE, [])
    return jsonify({"cleared": True})


@app.route("/api/security_status")
def security_status():
    block = read_json(BLOCK_FILE, {})
    return jsonify({
        "active_passes":   len(active_passes()),
        "locked_clients":  sum(1 for row in block.values() if row.get("locked_until", 0) > time.time()),
        "total_events":    len(read_json(LOG_FILE, [])),
        "ml_available":    ML_AVAILABLE,
    })


@app.route("/api/council_log")
def council_log():
    return jsonify(read_json(COUNCIL_LOG_FILE, []))


@app.route("/api/threat_analytics")
def threat_analytics():
    cl = read_json(COUNCIL_LOG_FILE, [])
    total  = len(cl)
    low    = sum(1 for r in cl if r.get("risk_profile", {}).get("level") == "LOW")
    medium = sum(1 for r in cl if r.get("risk_profile", {}).get("level") == "MEDIUM")
    high   = sum(1 for r in cl if r.get("risk_profile", {}).get("level") == "HIGH")
    approvals = sum(1 for r in cl if r.get("final_decision") == "APPROVE")
    reviews   = sum(1 for r in cl if r.get("final_decision") == "REVIEW")
    denials   = sum(1 for r in cl if r.get("final_decision") == "DENY")
    return jsonify({
        "total":     total,
        "low_risk":  low,
        "med_risk":  medium,
        "high_risk": high,
        "approvals": approvals,
        "reviews":   reviews,
        "denials":   denials,
        "ml_enabled": ML_AVAILABLE,
    })


@app.route("/api/visitor_reputation")
def visitor_reputation():
    db = read_json(VISITORS_FILE, {})
    records = []
    for key, data in db.items():
        name_phone = key.split(":", 1)
        records.append({
            "name":    name_phone[0].title() if name_phone else key,
            "phone":   name_phone[1] if len(name_phone) > 1 else "",
            "visits":  data.get("visits", 0),
            "approved": data.get("approved", 0),
            "denied":   data.get("denied", 0),
            "failed":   data.get("failed_attempts", 0),
            "trust_score": max(0, min(100,
                60 + data.get("approved", 0)*5
                   - data.get("denied", 0)*10
                   - data.get("failed_attempts", 0)*15
            )),
        })
    records.sort(key=lambda x: x["trust_score"], reverse=True)
    return jsonify(records)


# ─── Static routes ────────────────────────────────────────────────────────────
@app.route("/pass/<token>")
def pass_link(token):
    for p in active_passes():
        if p.get("token") == token:
            return app.send_static_file("index.html")
    return "<h2 style='font-family:Arial;color:#b91c1c'>Access link expired, used, or revoked.</h2>", 404

@app.route("/visitor")
def visitor_dashboard():
    return app.send_static_file("index.html")

@app.route("/")
def visitor_page():
    return app.send_static_file("index.html")

@app.route("/owner")
def owner_page():
    return app.send_static_file("owner.html")

@app.route("/<path:p>")
def static_files(p):
    return send_from_directory(app.static_folder, p)


if __name__ == "__main__":
    print("=" * 60)
    print("  Sentinel-X: AI Security Council")
    print(f"  ML (RandomForest): {'ENABLED' if ML_AVAILABLE else 'DISABLED (install scikit-learn)'}")
    print("  Visitor portal : http://127.0.0.1:5000/")
    print("  Owner dashboard: http://127.0.0.1:5000/owner")
    print("=" * 60)
    app.run(debug=True, threaded=True, use_reloader=False)
