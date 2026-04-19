import json
import os
import threading
import time
from collections import defaultdict
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC = "placement-events"

app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── In-memory analytics state ──────────────────────────────────────────────────
analytics = {
    "total_events": 0,
    "total_offers": 0,
    "total_accepted": 0,
    "total_rejected": 0,
    "total_applied": 0,
    "total_shortlisted": 0,
    "total_interviewed": 0,
    "avg_salary": 0.0,
    "max_salary": 0.0,
    "min_salary": float("inf"),
    "salaries": [],
    "offers_by_company": defaultdict(int),
    "offers_by_sector": defaultdict(int),
    "offers_by_branch": defaultdict(int),
    "events_by_type": defaultdict(int),
    "placements_over_time": [],          # [{time, count}]
    "salary_by_branch": defaultdict(list),
    "cgpa_vs_salary": [],                # [{cgpa, salary, company}]
    "gender_distribution": defaultdict(int),
    "skill_demand": defaultdict(int),
    "recent_events": [],                 # last 20
    "top_companies": [],
    "branch_placement_rate": defaultdict(lambda: {"applied": 0, "offered": 0}),
    "sector_breakdown": defaultdict(int),
    "hourly_trend": defaultdict(int),
}

salary_sum = 0.0
salary_count = 0
lock = threading.Lock()


def process_event(event):
    global salary_sum, salary_count

    with lock:
        analytics["total_events"] += 1
        etype = event.get("event_type", "unknown")
        analytics["events_by_type"][etype] += 1

        student = event.get("student", {})
        company = event.get("company", {})
        salary = event.get("salary_lpa")
        branch = student.get("branch", "Unknown")
        gender = student.get("gender", "Unknown")
        skills = student.get("skills", [])

        # Event type counters
        counter_map = {
            "applied": "total_applied",
            "shortlisted": "total_shortlisted",
            "interviewed": "total_interviewed",
            "offered": "total_offers",
            "accepted": "total_accepted",
            "rejected": "total_rejected",
        }
        if etype in counter_map:
            analytics[counter_map[etype]] += 1

        # Branch tracking
        if etype == "applied":
            analytics["branch_placement_rate"][branch]["applied"] += 1
        if etype in ("offered", "accepted"):
            analytics["branch_placement_rate"][branch]["offered"] += 1

        # Salary analytics
        if salary is not None:
            analytics["salaries"].append(salary)
            salary_sum += salary
            salary_count += 1
            analytics["avg_salary"] = round(salary_sum / salary_count, 2)
            analytics["max_salary"] = round(
                max(analytics["max_salary"], salary), 2)
            if salary < analytics["min_salary"]:
                analytics["min_salary"] = round(salary, 2)
            analytics["salary_by_branch"][branch].append(salary)
            if student.get("cgpa"):
                analytics["cgpa_vs_salary"].append({
                    "cgpa": student["cgpa"],
                    "salary": salary,
                    "company": company.get("name", ""),
                    "branch": branch,
                })

        # Company / sector
        if etype in ("offered", "accepted"):
            cname = company.get("name", "Unknown")
            analytics["offers_by_company"][cname] += 1
            analytics["offers_by_branch"][branch] += 1
            sector = company.get("sector", "Other")
            analytics["offers_by_sector"][sector] += 1
            analytics["sector_breakdown"][sector] += 1

        # Gender
        analytics["gender_distribution"][gender] += 1

        # Skills
        for skill in skills:
            analytics["skill_demand"][skill] += 1

        # Time trend (bucket by minute)
        now = datetime.utcnow()
        minute_key = now.strftime("%H:%M")
        analytics["hourly_trend"][minute_key] += 1
        analytics["placements_over_time"] = [
            {"time": k, "count": v}
            for k, v in sorted(analytics["hourly_trend"].items())
        ][-30:]  # last 30 minutes

        # Recent events (keep 20)
        analytics["recent_events"].insert(0, {
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
            "type": etype,
            "student_id": student.get("student_id"),
            "student_branch": branch,
            "company": company.get("name"),
            "salary": salary,
            "cgpa": student.get("cgpa"),
        })
        analytics["recent_events"] = analytics["recent_events"][:20]

        # Top companies
        analytics["top_companies"] = sorted(
            [{"name": k, "offers": v}
                for k, v in analytics["offers_by_company"].items()],
            key=lambda x: x["offers"],
            reverse=True,
        )[:10]

        return build_snapshot()


def build_snapshot():
    """Build a serializable snapshot for the frontend."""
    min_sal = analytics["min_salary"] if analytics["min_salary"] != float(
        "inf") else 0.0
    branch_rates = {}
    for br, data in analytics["branch_placement_rate"].items():
        applied = data["applied"]
        offered = data["offered"]
        rate = round((offered / applied * 100) if applied > 0 else 0, 1)
        branch_rates[br] = {"applied": applied,
                            "offered": offered, "rate": rate}

    branch_avg_salary = {}
    for br, sals in analytics["salary_by_branch"].items():
        branch_avg_salary[br] = round(sum(sals) / len(sals), 2) if sals else 0

    return {
        "total_events": analytics["total_events"],
        "total_offers": analytics["total_offers"],
        "total_accepted": analytics["total_accepted"],
        "total_rejected": analytics["total_rejected"],
        "total_applied": analytics["total_applied"],
        "total_shortlisted": analytics["total_shortlisted"],
        "total_interviewed": analytics["total_interviewed"],
        "avg_salary": analytics["avg_salary"],
        "max_salary": analytics["max_salary"],
        "min_salary": round(min_sal, 2),
        "offers_by_company": dict(analytics["offers_by_company"]),
        "offers_by_sector": dict(analytics["offers_by_sector"]),
        "offers_by_branch": dict(analytics["offers_by_branch"]),
        "events_by_type": dict(analytics["events_by_type"]),
        "placements_over_time": analytics["placements_over_time"],
        "cgpa_vs_salary": analytics["cgpa_vs_salary"][-100:],
        "gender_distribution": dict(analytics["gender_distribution"]),
        "skill_demand": dict(analytics["skill_demand"]),
        "recent_events": analytics["recent_events"],
        "top_companies": analytics["top_companies"],
        "branch_placement_rate": branch_rates,
        "branch_avg_salary": branch_avg_salary,
        "sector_breakdown": dict(analytics["sector_breakdown"]),
    }


def kafka_consumer_thread():
    print("[Consumer] Waiting for Kafka broker...")
    time.sleep(12)

    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset="earliest",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                group_id="placement-analytics-group",
            )
            print(
                f"[Consumer] Connected to Kafka. Listening on topic: {TOPIC}")
            break
        except NoBrokersAvailable:
            print("[Consumer] Broker not available, retrying...")
            time.sleep(5)

    for message in consumer:
        event = message.value
        snapshot = process_event(event)
        socketio.emit("analytics_update", snapshot)


# ── REST endpoints ─────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/analytics")
def get_analytics():
    with lock:
        return jsonify(build_snapshot())


# ── SocketIO events ────────────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print("[SocketIO] Client connected")
    with lock:
        snapshot = build_snapshot()
    socketio.emit("analytics_update", snapshot)


if __name__ == "__main__":
    t = threading.Thread(target=kafka_consumer_thread, daemon=True)
    t.start()
    socketio.run(app, host="0.0.0.0", port=5001,
                 allow_unsafe_werkzeug=True, log_output=False)
