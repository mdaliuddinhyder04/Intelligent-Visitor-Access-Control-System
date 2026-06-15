# Sentinel-X: Multi-Agent AI Security Council

**M.Tech Research Project — Intelligent Physical Access Control & Threat Prediction**

---

## What's New vs. Smart-Door-Fixed

| Feature | smart-door-fixed | Sentinel-X |
|---|---|---|
| Risk assessment | Single heuristic score | 4 independent AI agents |
| Threat model | Rule-based only | RandomForest ML (sklearn) |
| Visitor history | Not tracked | Full trust-score DB |
| Owner dashboard | Basic approval | Full council analytics |
| Agent voting | ❌ | Weighted ensemble (40/30/20/10%) |
| Visitor reputation | ❌ | Built-in reputation engine |
| Threat analytics | ❌ | Risk breakdown dashboard |

---

## Project Structure

```
sentinel-x/
├── backend/
│   ├── app.py              ← Flask API + 4 AI agents + council engine
│   ├── requirements.txt    ← Flask, scikit-learn, numpy
│   ├── access_passes.json  ← Active passes (auto-managed)
│   ├── blocked.json        ← Rate-limit / lockout state
│   ├── visitors_db.json    ← Visitor trust history (auto-created)
│   ├── council_log.json    ← Per-session council decisions (auto-created)
│   ├── visit_log.json      ← Activity log (auto-created)
│   └── visitor_request.json ← Current pending requests (auto-created)
├── frontend/
│   ├── index.html          ← Visitor portal (shows council result)
│   └── owner.html          ← Owner Command Center (full council UI)
├── start.sh                ← One-click launcher (Linux/macOS)
└── README.md
```

---

## Quick Start

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Windows
```cmd
python -m venv venv
venv\Scripts\pip install -r backend\requirements.txt
venv\Scripts\python backend\app.py
```

Then open:
- **Visitor portal**: http://127.0.0.1:5000/
- **Owner dashboard**: http://127.0.0.1:5000/owner

---

## AI Security Council — How It Works

```
          Visitor Request
                ↓
     ┌──────────┬──────────┬──────────┐
     ↓          ↓          ↓          ↓
Identity    Trust      Behavior   Threat
Agent       Agent       Agent     Agent
(30%)       (20%)       (10%)     (40%)
     └──────────┴──────────┴──────────┘
                ↓
     Weighted Score + Majority Vote
                ↓
        APPROVE / REVIEW / DENY
                ↓
        Owner Command Center
```

### Agent Details

| Agent | Weight | Input | Output |
|---|---|---|---|
| Identity Agent | 30% | Face-match score, visitor type | Score 0-100, APPROVE/REVIEW/DENY |
| Trust Agent | 20% | Visit history, approvals, denials | Trust score 0-100 |
| Behavior Agent | 10% | Time of day, purpose clarity, category | Risk score → vote |
| Threat Prediction Agent | 40% | All above features → RandomForest | Threat probability % |

### Voting Algorithm
```
final_score = threat*0.40 + identity*0.30 + trust*0.20 + behavior*0.10

if score >= 72 → APPROVE
elif score >= 48 → REVIEW  
else → DENY
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/visitor_request | Submit visitor request → runs council |
| GET  | /api/check_requests  | Get pending request (with council data) |
| POST | /api/create_pass     | Owner approves → generates OTP pass |
| POST | /api/verify_code     | Visitor enters OTP to unlock door |
| GET  | /api/threat_analytics | Risk breakdown stats |
| GET  | /api/visitor_reputation | Trust scores per visitor |
| GET  | /api/council_log     | All past council decisions |
| GET  | /api/security_status | Live system stats + ML status |

---

## Research Title (M.Tech)

**"Sentinel-X: Multi-Agent AI Security Council for Intelligent Physical Access Control and Threat Prediction"**

### Research Contributions
1. Multi-agent ensemble voting for physical security decisions
2. Behavioral anomaly detection at door entry points
3. ML-based (RandomForest) threat probability scoring
4. Dynamic trust scoring from visit history
5. Weighted agent consensus (Threat:40%, Identity:30%, Trust:20%, Behavior:10%)
