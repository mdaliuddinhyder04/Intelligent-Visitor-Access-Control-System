# 🛡️ Sentinel Smart Door

### Intelligent Visitor Access Control System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" />
  <img src="https://img.shields.io/badge/Flask-Web%20Framework-green" />
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-red" />
  <img src="https://img.shields.io/badge/REST%20API-Enabled-orange" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

A secure and intelligent visitor access management system that enables homeowners and organizations to remotely monitor, verify, and grant visitor access through a web-based dashboard. The system combines real-time webcam image capture, owner approval workflows, secure time-bound access codes, and activity logging to provide a modern smart access control solution.

---

## 🚀 Features

### Visitor Portal
- Submit visitor access requests through a web interface
- Capture visitor photographs using a webcam
- Receive owner-generated access codes
- Verify identity using a secure authentication process
- Get instant approval or rejection notifications

### Owner Dashboard
- View visitor requests in real time
- Inspect captured visitor photographs
- Generate unique 6-digit access codes
- Approve or reject visitor entry requests
- Monitor visitor access history

### Security Features
- Time-bound access code validation
- Unique code generation for each request
- Snapshot-based visitor verification
- Access expiration mechanism
- REST API-based communication
- Complete visitor audit trail

### Activity Monitoring
- Timestamped visitor logs
- Access approval and rejection records
- Snapshot storage and review
- Historical access tracking

---

## 🏗️ System Architecture

```text
Visitor
   │
   ▼
Web Interface
   │
   ▼
Flask Backend
   │
   ├── Visitor Request Management
   ├── Webcam Snapshot Capture
   ├── Secure Code Generation
   ├── Access Verification
   ├── REST APIs
   └── Activity Logging
   │
   ▼
Owner Dashboard
   │
   ▼
Access Approval / Rejection
```

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- REST APIs

### Frontend
- HTML5
- CSS3
- JavaScript

### Computer Vision
- OpenCV
- Webcam Integration

### Data Storage
- SQLite
- JSON-based Data Handling

### Tools & Libraries
- Jinja2
- Bootstrap / Custom UI
- AJAX
- Fetch API

---

## 📂 Project Structure

```text
Intelligent-Visitor-Access-Control-System/
│
├── static/
│   ├── css/
│   ├── js/
│   ├── uploads/
│   └── snapshots/
│
├── templates/
│   ├── index.html
│   ├── owner.html
│   └── history.html
│
├── app.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/mdaliuddinhyder04/Intelligent-Visitor-Access-Control-System.git
cd Intelligent-Visitor-Access-Control-System
```

### Create a Virtual Environment

```bash
python -m venv venv
```

### Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python app.py
```

---

## 🌐 Access the Application

Open your browser and navigate to:

```text
http://127.0.0.1:5000
```

---

## 📸 Application Workflow

1. Visitor opens the access portal.
2. Visitor submits an access request.
3. Webcam captures a visitor snapshot.
4. Snapshot is uploaded to the server.
5. Owner receives the request on the dashboard.
6. Owner reviews visitor details.
7. Secure access code is generated.
8. Visitor enters the code.
9. System validates the request.
10. Access is granted or denied.
11. Activity is recorded in history logs.

---

## 🔒 Security Mechanisms

- Secure 6-digit access code generation
- Time-limited verification process
- Snapshot-based identity confirmation
- Request validation using REST APIs
- Visitor activity logging
- Session management and verification

---

## 📈 Future Enhancements

- Face Recognition Authentication
- QR Code-Based Entry
- Email Notifications
- SMS Alerts
- Mobile Application
- IoT Smart Lock Integration
- Cloud Deployment
- Multi-Owner Access Management
- Real-Time Notifications

---

## 🎯 Learning Outcomes

- Full-Stack Web Development
- REST API Development
- Computer Vision Integration
- Authentication and Authorization Systems
- Secure Access Management
- Flask Application Development
- Real-Time Dashboard Design

---

## 👨‍💻 Author

**Mohammed Aliuddin Hyder**

📧 mohammedaliuddinhyder04@gmail.com

🔗 LinkedIn: www.linkedin.com/in/mdaliuddinhyder04

🔗 GitHub: https://github.com/mdaliuddinhyder04

---

## ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub and sharing feedback for future improvements.
