# 🛡️ Sentinel-X Intelligent Visitor Access Control System

<p align="center">
  <b>AI-Powered Smart Visitor Verification & Access Management Platform</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-Flask-blue">
  <img src="https://img.shields.io/badge/OpenCV-Webcam-green">
  <img src="https://img.shields.io/badge/REST-API-orange">
  <img src="https://img.shields.io/badge/AI-Multi--Agent-red">
  <img src="https://img.shields.io/badge/ML-RandomForest-purple">
</p>

---

## 📖 Overview

Sentinel-X is an AI-powered visitor access control system that allows homeowners, apartments, offices, and gated communities to securely manage visitor entry through real-time identity verification, intelligent risk assessment, and owner approval workflows.

The system captures visitor snapshots, analyzes visitor trust and behavior using a Multi-Agent AI Security Council, generates secure time-bound access passes, and maintains complete visitor audit logs.

Unlike traditional visitor management systems, Sentinel-X combines security automation, machine learning, visitor reputation tracking, and intelligent threat prediction into a single platform.

---

## ✨ Key Features

### 👤 Visitor Portal
- Visitor access request submission
- Webcam snapshot capture
- Purpose-based entry requests
- Secure access code verification
- Real-time approval workflow

### 🏠 Owner Command Center
- Live visitor monitoring
- Snapshot review dashboard
- Approve or reject visitors
- Access pass generation
- Visitor reputation tracking
- Security analytics dashboard

### 🔒 Smart Security Controls
- 6-digit secure access codes
- Time-bound access passes
- Automatic pass expiration
- Visitor lockout protection
- Rate limiting against spam requests
- Failed-attempt monitoring

### 📊 Analytics & Monitoring
- Visitor activity logs
- Threat analytics
- Visitor reputation scores
- Security event tracking
- Historical access records
- Council decision logs

---

# 🧠 AI Multi-Agent Security Council

One of the most unique features of Sentinel-X is its AI Security Council.

The system uses multiple intelligent agents to evaluate every visitor before access is granted.

### 1️⃣ Identity Agent
Analyzes visitor identity confidence using face-match scoring.

**Evaluates:**
- Identity confidence
- Face-match score
- Verification reliability

---

### 2️⃣ Trust Agent
Calculates visitor trustworthiness using historical visit records.

**Factors:**
- Approved visits
- Rejected visits
- Failed attempts
- Visitor category

---

### 3️⃣ Behavior Agent
Detects suspicious behavioral patterns.

**Analyzes:**
- Visit timing
- Visitor type
- Purpose clarity
- Activity anomalies

---

### 4️⃣ Threat Prediction Agent
Uses a Random Forest Machine Learning model to predict visitor risk.

**Machine Learning Inputs**
- Trust score
- Face-match score
- Failed attempts
- Behavioral risk
- Visitor category

---

### 🎯 Final Decision Engine

The council combines weighted votes from all agents:

| Agent | Weight |
|---------|---------|
| Threat Agent | 40% |
| Identity Agent | 30% |
| Trust Agent | 20% |
| Behavior Agent | 10% |

Final outcomes:

- ✅ APPROVE
- ⚠️ REVIEW
- ❌ DENY

---

# 🏗️ System Architecture

```text
Visitor
   │
   ▼
Visitor Portal
   │
   ▼
Flask REST API Backend
   │
   ├── Snapshot Capture
   ├── Visitor Request Engine
   ├── Security Council
   ├── Threat Prediction Model
   ├── Access Pass Manager
   ├── Reputation Engine
   └── Audit Logging
   │
   ▼
Owner Command Center
   │
   ▼
Approve / Review / Deny
```

---

# ⚙️ Tech Stack

## Backend
- Python
- Flask
- Flask-CORS

## Machine Learning
- Scikit-Learn
- Random Forest Classifier
- NumPy

## Frontend
- HTML5
- CSS3
- JavaScript

## Communication
- REST APIs
- Server-Sent Events (SSE)

## Data Storage
- JSON-based persistence

---

# 📂 Project Structure

```text
Intelligent Visitor Access Control System
│
├── backend
│   ├── app.py
│   ├── requirements.txt
│   ├── visitor_request.json
│   ├── visit_log.json
│   ├── blocked.json
│   ├── council_log.json
│   └── visitor_snapshot.jpg
│
├── frontend
│   ├── index.html
│   └── owner.html
│
└── start.sh
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/mdaliuddinhyder04/Intelligent-Visitor-Access-Control-System.git

cd Intelligent-Visitor-Access-Control-System
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

### Activate

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r backend/requirements.txt
```

---

## Run Application

```bash
cd backend

python app.py
```

---

## Open Browser

```text
http://localhost:5000
```

Visitor Portal:

```text
http://localhost:5000/
```

Owner Dashboard:

```text
http://localhost:5000/owner
```

---

# 🔌 Core REST APIs

| Method | Endpoint | Description |
|----------|------------|-------------|
| POST | /api/visitor_request | Create visitor request |
| POST | /api/visitor_snapshot | Upload visitor image |
| GET | /api/get_snapshot | Retrieve snapshot |
| POST | /api/create_pass | Generate access pass |
| POST | /api/verify_code | Verify visitor code |
| GET | /api/passes | Active passes |
| GET | /api/log | Security logs |
| GET | /api/security_status | Security status |
| GET | /api/threat_analytics | Threat analytics |
| GET | /api/visitor_reputation | Visitor reputation |
| GET | /api/council_log | AI council decisions |

---

# 🛡️ Security Features

- Access pass expiration
- Visitor lockout protection
- Spam prevention
- Rate limiting
- Failed-attempt tracking
- Threat prediction
- Visitor reputation management
- Audit trail logging
- Snapshot verification

---

# 📈 Future Enhancements

- Face Recognition using OpenCV
- YOLO-based Intruder Detection
- SMS Notifications
- Email Alerts
- QR-Code Entry System
- Mobile Application
- IoT Smart Door Lock Integration
- Cloud Deployment (AWS/Azure)
- Real-Time Push Notifications
- Database Integration (MySQL/PostgreSQL)

---

# 🎓 Learning Outcomes

This project demonstrates:

- Full-Stack Web Development
- REST API Design
- Machine Learning Integration
- Multi-Agent AI Systems
- Visitor Authentication Systems
- Security Analytics
- Event-Driven Architecture
- Real-Time Communication
- Intelligent Access Control

---

# 👨‍💻 Author

**Mohammed Aliuddin Hyder**

📧 mohammedaliuddinhyder04@gmail.com

🌐 GitHub: https://github.com/mdaliuddinhyder04

💼 LinkedIn: https://www.linkedin.com/in/mdaliuddinhyder04

---

# ⭐ Support

If you found this project useful, please consider giving it a ⭐ on GitHub.

Your support helps improve future AI, Security, and Full-Stack Development projects.
