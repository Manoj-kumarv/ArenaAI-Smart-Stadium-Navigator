"""Seed script — run once to initialise the DB and populate demo data.
Usage:
    cd apps/backend
    python -m scripts.seed
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.auth import get_password_hash
from app.database import SessionLocal, engine
from app.models import Base, Incident, IncidentSeverity, User, UserRole, Zone, ZoneType

# ─── Create tables ────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ─── Users ────────────────────────────────────────────────────────────────────
USERS = [
    {"username": "ops_admin", "email": "ops@arenaiq.local", "password": "OpsPass123!", "role": UserRole.ops_staff},
    {"username": "fan_user",  "email": "fan@arenaiq.local", "password": "FanPass123!",  "role": UserRole.fan},
]

for u in USERS:
    if not db.query(User).filter_by(username=u["username"]).first():
        db.add(User(
            username=u["username"],
            email=u["email"],
            hashed_password=get_password_hash(u["password"]),
            role=u["role"],
        ))

# ─── Zones (25 zones) ─────────────────────────────────────────────────────────
ZONES = [
    # Gates (4)
    {"id":"gate_a","name":"Gate A","zone_type":ZoneType.gate,"capacity":800,"x":200,"y":10,"w":80,"h":50,"is_step_free":True,"is_low_noise":False},
    {"id":"gate_b","name":"Gate B","zone_type":ZoneType.gate,"capacity":800,"x":520,"y":10,"w":80,"h":50,"is_step_free":True,"is_low_noise":False},
    {"id":"gate_c","name":"Gate C","zone_type":ZoneType.gate,"capacity":800,"x":200,"y":480,"w":80,"h":50,"is_step_free":False,"is_low_noise":False},
    {"id":"gate_d","name":"Gate D","zone_type":ZoneType.gate,"capacity":800,"x":520,"y":480,"w":80,"h":50,"is_step_free":False,"is_low_noise":False},
    # Sections (12)
    {"id":"section_101","name":"Section 101","zone_type":ZoneType.section,"capacity":600,"x":80,"y":100,"w":80,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_102","name":"Section 102","zone_type":ZoneType.section,"capacity":600,"x":80,"y":175,"w":80,"h":60,"is_step_free":True,"is_low_noise":True},
    {"id":"section_103","name":"Section 103","zone_type":ZoneType.section,"capacity":600,"x":80,"y":250,"w":80,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_104","name":"Section 104","zone_type":ZoneType.section,"capacity":600,"x":80,"y":325,"w":80,"h":60,"is_step_free":True,"is_low_noise":False},
    {"id":"section_110","name":"Section 110","zone_type":ZoneType.section,"capacity":600,"x":640,"y":100,"w":80,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_111","name":"Section 111","zone_type":ZoneType.section,"capacity":600,"x":640,"y":175,"w":80,"h":60,"is_step_free":True,"is_low_noise":True},
    {"id":"section_112","name":"Section 112","zone_type":ZoneType.section,"capacity":600,"x":640,"y":250,"w":80,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_113","name":"Section 113","zone_type":ZoneType.section,"capacity":600,"x":640,"y":325,"w":80,"h":60,"is_step_free":True,"is_low_noise":False},
    {"id":"section_120","name":"Section 120","zone_type":ZoneType.section,"capacity":600,"x":240,"y":80,"w":100,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_121","name":"Section 121","zone_type":ZoneType.section,"capacity":600,"x":360,"y":80,"w":100,"h":60,"is_step_free":True,"is_low_noise":False},
    {"id":"section_122","name":"Section 122","zone_type":ZoneType.section,"capacity":600,"x":240,"y":400,"w":100,"h":60,"is_step_free":False,"is_low_noise":False},
    {"id":"section_123","name":"Section 123","zone_type":ZoneType.section,"capacity":600,"x":360,"y":400,"w":100,"h":60,"is_step_free":True,"is_low_noise":True},
    # Concourses (2)
    {"id":"concourse_north","name":"North Concourse","zone_type":ZoneType.concourse,"capacity":1200,"x":190,"y":150,"w":420,"h":70,"is_step_free":True,"is_low_noise":False},
    {"id":"concourse_south","name":"South Concourse","zone_type":ZoneType.concourse,"capacity":1200,"x":190,"y":320,"w":420,"h":70,"is_step_free":True,"is_low_noise":False},
    # Parking (2)
    {"id":"parking_p1","name":"Parking P1","zone_type":ZoneType.parking,"capacity":2000,"x":10,"y":10,"w":120,"h":80,"is_step_free":True,"is_low_noise":False},
    {"id":"parking_p2","name":"Parking P2","zone_type":ZoneType.parking,"capacity":2000,"x":670,"y":10,"w":120,"h":80,"is_step_free":True,"is_low_noise":False},
    # Medical (2)
    {"id":"medical_1","name":"Medical Station 1","zone_type":ZoneType.medical,"capacity":50,"x":175,"y":230,"w":60,"h":40,"is_step_free":True,"is_low_noise":True},
    {"id":"medical_2","name":"Medical Station 2","zone_type":ZoneType.medical,"capacity":50,"x":565,"y":230,"w":60,"h":40,"is_step_free":True,"is_low_noise":True},
    # Volunteer Posts (5)
    {"id":"vol_post_1","name":"Volunteer Post 1","zone_type":ZoneType.volunteer_post,"capacity":20,"x":290,"y":155,"w":50,"h":30,"is_step_free":True,"is_low_noise":False},
    {"id":"vol_post_2","name":"Volunteer Post 2","zone_type":ZoneType.volunteer_post,"capacity":20,"x":460,"y":155,"w":50,"h":30,"is_step_free":True,"is_low_noise":False},
    {"id":"vol_post_3","name":"Volunteer Post 3","zone_type":ZoneType.volunteer_post,"capacity":20,"x":375,"y":250,"w":50,"h":30,"is_step_free":True,"is_low_noise":True},
]

for z in ZONES:
    if not db.query(Zone).filter_by(id=z["id"]).first():
        db.add(Zone(**z))

# ─── Sample Incidents (5) ─────────────────────────────────────────────────────
INCIDENTS = [
    {"zone_id":"gate_a","title":"Gate A overcrowding","description":"Large queue forming at Gate A entry checkpoint — estimated 400 fans in queue.","severity":IncidentSeverity.high,"ai_severity_score":0.82},
    {"zone_id":"concourse_north","title":"Food vendor spill","description":"Slip hazard near kiosk 3 on North Concourse. Area cordoned but crowd building.","severity":IncidentSeverity.medium,"ai_severity_score":0.55},
    {"zone_id":"section_102","title":"Medical assistance required","description":"Fan reported dizziness in Section 102, row 14. Medical team en route.","severity":IncidentSeverity.critical,"ai_severity_score":0.95},
    {"zone_id":"parking_p1","title":"Unauthorised vehicle P1","description":"Vehicle blocking emergency lane in P1. Security alerted.","severity":IncidentSeverity.medium,"ai_severity_score":0.60},
    {"zone_id":"section_120","title":"Lost child reported","description":"Child separated from guardian near Section 120. Volunteer and security notified.","severity":IncidentSeverity.high,"ai_severity_score":0.88},
]

for inc in INCIDENTS:
    if not db.query(Incident).filter_by(title=inc["title"]).first():
        db.add(Incident(**inc))

db.commit()
db.close()
print("SUCCESS: Database seeded successfully.")
print("   ops_admin / OpsPass123!")
print("   fan_user  / FanPass123!")
