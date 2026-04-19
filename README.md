# 🎓 PlaceIQ — Real-Time Campus Placement Analytics System
> **AAT Project · Big Data Analytics · Apache Kafka Integration** A fully containerized, real-time campus placement analytics platform built with **Apache Kafka**, **Python**, **Flask**, **Socket.IO**, and a modern dark-theme dashboard. ---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                              │
│                                                                     │
│  ┌──────────┐     ┌──────────────┐     ┌────────────────────────┐  │
│  │Zookeeper │────▶│    Kafka     │◀────│  Producer (Python)     │  │
│  │  :2181   │     │    :9092     │     │  Simulates placement   │  │
│  └──────────┘     └──────┬───────┘     │  events in real-time   │  │
│                          │             └────────────────────────┘  │
│                          │ placement-events topic                   │
│                          ▼                                          │
│                   ┌──────────────┐                                  │
│                   │  Consumer    │  Flask + Socket.IO               │
│                   │   :5001      │  Aggregates analytics            │
│                   └──────┬───────┘  Emits WebSocket updates        │
│                          │                                          │
│              ┌───────────┤                                          │
│              ▼           ▼                                          │
│        ┌──────────┐  ┌───────────┐                                 │
│        │ Frontend │  │ Kafka UI  │                                  │
│        │  :3000   │  │  :8080    │                                  │
│        │ (nginx)  │  │(Monitor)  │                                  │
│        └──────────┘  └───────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Producer** → Generates synthetic placement events (applied, shortlisted, interviewed, offered, accepted, rejected) and publishes to Kafka topic `placement-events`
2. **Kafka** → Streams events with fault tolerance and guaranteed delivery
3. **Consumer** → Flask app consuming Kafka events, computing analytics in real-time, broadcasting via Socket.IO
4. **Frontend** → Live dashboard updating charts/metrics via WebSocket without any page refresh

---

## 📁 Project Structure

```
campus-placement-analytics/
├── docker-compose.yml          # Orchestrates all services
├── README.md
├── producer/
│   ├── producer.py             # Kafka producer: simulates placement events
│   ├── requirements.txt
│   └── Dockerfile
├── consumer/
│   ├── consumer.py             # Kafka consumer + Flask REST + Socket.IO
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── index.html              # Full dashboard (Chart.js + Socket.IO)
    └── Dockerfile              # nginx serving static files
```

---

## 🚀 How to Run

### Prerequisites
| Tool | Min Version | Install |
|------|------------|---------|
| Docker | 24.x | https://docs.docker.com/get-docker/ |
| Docker Compose | v2.x | Included with Docker Desktop |

> **Note:** No Python, Node.js, or Kafka installation required on your machine. Everything runs in Docker.

---

### Step 1 — Clone / Unzip the project
```bash
cd campus-placement-analytics
```

### Step 2 — Build and Start All Services
```bash
docker compose up --build
```

This will:
- Pull Kafka + Zookeeper images (~500 MB first time)
- Build the producer, consumer, and frontend Docker images
- Start all 5 containers

> ⏱ **First run takes ~2–3 minutes** for Kafka to initialize and containers to connect.

---

### Step 3 — Open the Dashboard

| Service | URL | Description |
|---------|-----|-------------|
| **📊 Dashboard** | http://localhost:3000 | Live analytics frontend |
| **🔌 Consumer API** | http://localhost:5001/analytics | REST endpoint (JSON) |
| **🗂 Kafka UI** | http://localhost:8080 | Monitor Kafka topics/messages |
| **❤️ Health Check** | http://localhost:5001/health | Consumer health |

---

### Step 4 — Watch It Work
- The **Producer** starts sending events within ~10 seconds
- The **Dashboard** updates in real-time via WebSocket (no refresh needed)
- Check **Kafka UI** at `:8080` to see messages flowing through the `placement-events` topic

---

## 🛑 Stopping the Project

```bash
# Stop all containers
docker compose down

# Stop AND remove volumes (fresh start)
docker compose down -v
```

---

## 🔧 Useful Commands

```bash
# View logs from all services
docker compose logs -f

# View logs from a specific service
docker compose logs -f producer
docker compose logs -f consumer

# Check running containers
docker ps

# Restart a single service
docker compose restart producer

# Scale the producer (run 2 producers)
docker compose up --scale producer=2
```

---

## 📊 Analytics Features

### Kafka Topic
- **Topic:** `placement-events`
- **Event types:** `applied`, `shortlisted`, `interviewed`, `offered`, `accepted`, `rejected`
- **Partition:** 1 (configurable)

### Dashboard Panels
| Panel | Description |
|-------|-------------|
| KPI Strip | Live counters for all event types + salary stats |
| Event Stream | Time-series line chart of events per minute |
| Event Distribution | Doughnut chart of event type breakdown |
| Sector-wise Offers | Bar chart by company sector |
| CGPA vs Package | Scatter plot showing correlation |
| Offers by Branch | Horizontal bar chart per branch |
| Live Event Feed | Real-time scrolling event log |
| Top Recruiters | Top 10 companies by offer count |
| Skill Demand Index | Bar chart of most in-demand skills |
| Branch Placement Rate | Conversion rate table |
| Gender Distribution | Pie chart |

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| Message Broker | Apache Kafka 7.5 (Confluent) |
| Coordination | Apache Zookeeper |
| Producer | Python 3.11 + kafka-python |
| Consumer / API | Python 3.11 + Flask + Flask-SocketIO |
| Real-time Push | Socket.IO (WebSocket) |
| Frontend | Vanilla HTML/CSS/JS + Chart.js 4 |
| Web Server | nginx (Alpine) |
| Containerization | Docker + Docker Compose |
| Monitoring | Kafka UI (provectuslabs) |

---

## ⚙️ Configuration

Edit `docker-compose.yml` to change:
- `KAFKA_BROKER` — Kafka connection string
- Exposed ports for any service
- Producer event frequency (edit `producer.py` — `time.sleep(...)`)

---

## 🎓 AAT Information

- **Subject:** Big Data Analytics
- **Topic:** Real-Time Campus Placement Analytics System
- **Integration:** Apache Kafka ↔ Flask Analytics Engine
- **Key Concept:** Event streaming architecture with real-time aggregation

---

*Built with ❤️ for Big Data Analytics AAT*
