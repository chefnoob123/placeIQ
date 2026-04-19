import json
import time
import random
import os
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC = "placement-events"

COMPANIES = [
    {"name": "Google", "sector": "Tech", "package": (18, 45)},
    {"name": "Microsoft", "sector": "Tech", "package": (16, 40)},
    {"name": "Amazon", "sector": "Tech", "package": (14, 38)},
    {"name": "Infosys", "sector": "IT Services", "package": (3.5, 6)},
    {"name": "TCS", "sector": "IT Services", "package": (3.5, 7)},
    {"name": "Wipro", "sector": "IT Services", "package": (3.5, 6.5)},
    {"name": "Goldman Sachs", "sector": "Finance", "package": (12, 30)},
    {"name": "JP Morgan", "sector": "Finance", "package": (10, 28)},
    {"name": "Deloitte", "sector": "Consulting", "package": (7, 14)},
    {"name": "McKinsey", "sector": "Consulting", "package": (15, 35)},
    {"name": "Flipkart", "sector": "E-Commerce", "package": (12, 25)},
    {"name": "Razorpay", "sector": "Fintech", "package": (10, 22)},
    {"name": "Swiggy", "sector": "Startup", "package": (8, 20)},
    {"name": "NVIDIA", "sector": "Tech", "package": (20, 50)},
    {"name": "Adobe", "sector": "Tech", "package": (14, 32)},
]

BRANCHES = ["CSE", "ECE", "EEE", "ME", "CE", "IT", "AIDS", "AIML"]
GENDERS = ["Male", "Female", "Other"]
SKILLS = ["Python", "Java", "ML", "Data Science", "React", "Node.js", "Cloud", "DevOps", "SQL", "C++"]
EVENTS = ["applied", "shortlisted", "interviewed", "offered", "accepted", "rejected"]

student_pool = []
for i in range(1, 201):
    student_pool.append({
        "student_id": f"STU{i:04d}",
        "name": f"Student_{i}",
        "branch": random.choice(BRANCHES),
        "gender": random.choice(GENDERS),
        "cgpa": round(random.uniform(5.5, 9.9), 2),
        "backlogs": random.choices([0, 1, 2], weights=[0.75, 0.18, 0.07])[0],
        "skills": random.sample(SKILLS, k=random.randint(2, 5)),
        "internships": random.randint(0, 3),
    })


def get_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            print(f"[Producer] Connected to Kafka at {KAFKA_BROKER}")
            return producer
        except NoBrokersAvailable:
            print("[Producer] Waiting for Kafka broker...")
            time.sleep(5)


def generate_event():
    student = random.choice(student_pool)
    company = random.choice(COMPANIES)
    event_type = random.choice(EVENTS)

    # Salary logic based on event
    salary = None
    if event_type in ["offered", "accepted"]:
        lo, hi = company["package"]
        base = random.uniform(lo, hi)
        # Boost for high CGPA
        if student["cgpa"] > 8.5:
            base *= 1.1
        salary = round(base, 2)

    event = {
        "event_id": f"EVT{random.randint(100000, 999999)}",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "student": student,
        "company": {
            "name": company["name"],
            "sector": company["sector"],
        },
        "salary_lpa": salary,
        "round": random.choice(["Aptitude", "Technical", "HR", "Managerial"]) if event_type == "interviewed" else None,
    }
    return event


def main():
    print("[Producer] Starting Campus Placement Event Producer...")
    time.sleep(10)  # Wait for Kafka to be ready
    producer = get_producer()

    count = 0
    try:
        while True:
            event = generate_event()
            producer.send(TOPIC, value=event)
            count += 1
            print(f"[Producer] Sent event #{count}: {event['event_type']} | {event['student']['student_id']} -> {event['company']['name']}")
            # Vary speed to simulate bursts
            time.sleep(random.uniform(0.3, 1.5))
    except KeyboardInterrupt:
        print("[Producer] Shutting down...")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
