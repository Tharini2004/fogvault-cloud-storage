#  FogVault: Securing Cloud Storage with Fog Computing

> A secure, fault-tolerant cloud storage system integrating fog computing for reduced latency, end-to-end AES-256 encryption, and reliable data recovery.

##  Overview

Traditional cloud storage systems suffer from:
-  High latency due to distant data centers
-  Security vulnerabilities in centralized storage
- Slow and expensive fault recovery

**FogVault** solves these by deploying **fog nodes at the network edge**, enabling:
- Local data processing, caching & encryption
-  End-to-end AES-256 encryption + RSA key exchange
-  Fast fault-tolerant recovery
-  Role-based access control & audit logging

---

##  Key Results

| Parameter | Traditional Cloud | FogVault | Improvement |
|---|---|---|---|
| Upload Latency | 1100–1200 ms | 700–750 ms | **~35%** |
| Download Latency | 1200–1300 ms | 720–780 ms | **~40%** |
| Bandwidth Usage | High | Reduced | **30% savings** |
| Throughput | Moderate | Improved | **~25% increase** |
| Data Security | Centralized | End-to-end encrypted | **High** |
| Fault Tolerance | Slow recovery | Fog-assisted | **Reliable** |

---

##  System Architecture

```
CLIENT LAYER
    │
    ▼
FOG NODES LAYER  ←→  Authentication & Access Control
    │  (Encrypt, Cache, Log, Fault Tolerance)
    ▼
CLOUD LAYER (AWS S3 / Google Cloud Storage)
    │  (Encrypted storage, Backup, Redundancy)
    ▼
Audit & Logging Module
Communication Module (HTTPS / MQTT)
```

**3 Layers:**
1. **Client Layer** — Web UI for upload/download/authentication
2. **Fog Layer** — Local encryption, caching, fault tolerance, audit logs
3. **Cloud Layer** — AWS S3 / GCS for long-term encrypted storage

---

##  Tech Stack

| Component | Technology |
|---|---|
| Backend | Python (Flask) |
| Frontend | HTML, CSS, JavaScript |
| Database | MongoDB (metadata & logs) |
| Cloud Storage | AWS S3 |
| Encryption | AES-256 (data), RSA (key exchange) |
| Communication | HTTPS, MQTT |
| Fog Devices | Raspberry Pi / Local Edge Servers |

---

##  Project Structure

```
fogvault/
│
├── app.py                  # Flask main application
├── fogvault_logic.py       # Business logic & fog node operations
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
│
├── templates/
│   ├── index.html          # Landing page
│   ├── login.html          # Login page
│   ├── dashboard.html      # File management dashboard
│   ├── upload.html         # File upload page
│   └── history.html        # Transaction history
│
├── static/
│   ├── style.css           # Styling
│   └── script.js           # Frontend logic
│
└── README.md
```

---

##  How to Run

### 1. Clone the repo
```bash
git clone https://github.com/Tharini2004/fogvault-cloud-storage.git
cd fogvault-cloud-storage
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and AWS credentials
```

### 4. Run the app
```bash
python app.py
```

### 5. Open browser
```
http://127.0.0.1:5000
```

---

## Security Features

- **AES-256** symmetric encryption for all file data
- **RSA** asymmetric key exchange between clients and fog nodes
- **Role-Based Access Control (RBAC)** — only authorized users access files
- **Audit Logging** — all operations tracked and logged
- **Hash Verification** — MD5/SHA integrity checks prevent tampering
- **XOR Redundancy** — files split into blocks for fault tolerance

---

## Workflow

**Upload:**
1. User selects file → sent to fog node
2. Fog node encrypts (AES-256) + caches
3. Encrypted file stored in AWS S3

**Download:**
1. User requests file
2. Fog node checks cache first → serves locally if cached
3. If not cached → fetches from S3, decrypts, delivers

**Fault Recovery:**
1. Cloud node fails → fog node serves cached files
2. Once restored → fog node auto-syncs with cloud

---

## License

Academic Major Project — Nagarjuna College of Engineering & Technology, 2025–26.
