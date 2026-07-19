"""Rule-based fallback responses for all three agents.
Activated automatically when Gemini is unavailable or returns invalid JSON.
"""

from __future__ import annotations

from app.models import ColorState

# ─── Crowd Agent fallback ─────────────────────────────────────────────────────

_CROWD_CAUSES = {
    ColorState.critical: "Severe overcrowding — multiple ingress points converging. Capacity exceeded.",
    ColorState.red: "High fan density due to post-match egress or concurrent event start.",
    ColorState.yellow: "Moderate congestion — concession peak times or section transition.",
    ColorState.green: "Zone is operating within normal capacity parameters.",
}

_CROWD_ACTIONS = {
    ColorState.critical: "Immediately deploy 4+ volunteers to redirect flow. Activate PA broadcast. Open overflow gate.",
    ColorState.red: "Deploy 2 volunteers for crowd control. Update digital signage. Monitor every 60s.",
    ColorState.yellow: "Send 1 volunteer to monitor. Consider opening adjacent concourse pathway.",
    ColorState.green: "No immediate action required. Maintain standard monitoring.",
}

_CROWD_CONFIDENCE = {
    ColorState.critical: 0.91,
    ColorState.red: 0.85,
    ColorState.yellow: 0.72,
    ColorState.green: 0.95,
}


def crowd_fallback(zone_id: str, zone_name: str, density_pct: float, color_state: ColorState) -> dict:
    state = color_state
    return {
        "zone_id": zone_id,
        "cause": _CROWD_CAUSES[state],
        "recommendation": _CROWD_ACTIONS[state],
        "confidence": _CROWD_CONFIDENCE[state],
        "used_ai": False,
    }


# ─── Fan Assistant fallback ───────────────────────────────────────────────────

_FAN_RESPONSES_EN = {
    "directions": "Please follow the green floor markings to your section. Volunteers in orange vests are stationed at every major junction.",
    "food": "Food and beverage kiosks are located on both the North and South Concourses. Halal and vegetarian options are available.",
    "medical": "Medical stations are located near Section 101 (North) and Section 110 (South). For emergencies, alert any volunteer immediately.",
    "toilets": "Restrooms are available at all concourse levels. Accessible facilities are clearly marked with the blue wheelchair symbol.",
    "default": "For assistance, please approach any volunteer in an orange vest or visit the information desk at Gate A or Gate B.",
}

_FAN_RESPONSES_ES = {
    "directions": "Siga las marcas verdes en el suelo hacia su sección. Los voluntarios con chalecos naranjas están en cada intersección principal.",
    "food": "Los puestos de comida y bebida están en los Concursos Norte y Sur. Hay opciones halal y vegetarianas disponibles.",
    "medical": "Las estaciones médicas están cerca de la Sección 101 (Norte) y la Sección 110 (Sur). En caso de emergencia, avise a un voluntario.",
    "toilets": "Los baños están disponibles en todos los niveles del concurso. Las instalaciones accesibles están marcadas con el símbolo azul de silla de ruedas.",
    "default": "Para obtener ayuda, acérquese a cualquier voluntario con chaleco naranja o visite el mostrador de información en la Puerta A o B.",
}

_FAN_RESPONSES_AR = {
    "directions": "يرجى اتباع العلامات الخضراء على الأرضية للوصول إلى مقعدك. يتواجد المتطوعون بالسترات البرتقالية عند كل تقاطع رئيسي.",
    "food": "تتوفر أكشاك الطعام والمشروبات في الممرات الشمالية والجنوبية. تتوفر خيارات حلال ونباتية.",
    "medical": "تقع محطات الطوارئ الطبية بالقرب من القسم 101 (شمال) والقسم 110 (جنوب). في حالات الطوارئ، أبلغ أي متطوع فوراً.",
    "toilets": "دورات المياه متاحة في جميع مستويات الممر. المرافق المخصصة لذوي الإعاقة مميزة بعلامة الكرسي المتحرك الزرقاء.",
    "default": "للحصول على المساعدة، تفضل بالتوجه إلى أي متطوع يرتدي سترة برتقالية أو قم بزيارة مكتب المعلومات عند البوابة A أو B.",
}


def _classify_query(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["direction", "how do i get", "where is", "find", "locate", "seat", "section", "gate"]):
        return "directions"
    if any(w in q for w in ["food", "drink", "eat", "beverage", "kiosk", "halal", "vegetarian", "snack"]):
        return "food"
    if any(w in q for w in ["medical", "doctor", "hurt", "emergency", "first aid", "sick", "injury"]):
        return "medical"
    if any(w in q for w in ["toilet", "restroom", "bathroom", "wc", "lavatory"]):
        return "toilets"
    return "default"


def fan_fallback(query: str, language: str = "en") -> dict:
    key = _classify_query(query)
    return {
        "answer_en": _FAN_RESPONSES_EN[key],
        "answer_es": _FAN_RESPONSES_ES[key],
        "answer_ar": _FAN_RESPONSES_AR[key],
        "confidence": 0.78,
        "used_ai": False,
    }


# ─── Incident Agent fallback ──────────────────────────────────────────────────

_SEVERITY_PLAYBOOKS = {
    "critical": {
        "severity": "critical",
        "score": 0.95,
        "playbook": "1. Alert stadium security commander immediately. 2. Dispatch medical team if injury involved. 3. Initiate PA announcement to clear area. 4. Preserve scene for investigation. 5. Notify local authorities if required.",
    },
    "high": {
        "severity": "high",
        "score": 0.78,
        "playbook": "1. Assign senior volunteer or security officer to scene. 2. Deploy crowd control barriers if needed. 3. Broadcast advisory message. 4. Log incident with timestamps. 5. Review CCTV footage.",
    },
    "medium": {
        "severity": "medium",
        "score": 0.55,
        "playbook": "1. Send nearest volunteer to assess. 2. Record incident details in system. 3. Monitor situation for escalation. 4. Notify supervisor if not resolved in 15 minutes.",
    },
    "low": {
        "severity": "low",
        "score": 0.25,
        "playbook": "1. Log for record. 2. Nearest volunteer to handle if available. 3. No immediate PA required. 4. Review at end of shift.",
    },
}


def _classify_incident_severity(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    if any(w in text for w in ["critical", "medical", "emergency", "fire", "weapon", "injury", "collapse"]):
        return "critical"
    if any(w in text for w in ["crowd", "overcrowd", "fight", "lost child", "security", "evacuation"]):
        return "high"
    if any(w in text for w in ["spill", "delay", "queue", "complaint", "blocked"]):
        return "medium"
    return "low"


def incident_fallback(title: str, description: str, zone_id: str | None) -> dict:
    severity_key = _classify_incident_severity(title, description)
    pb = _SEVERITY_PLAYBOOKS[severity_key]
    return {
        "zone_id": zone_id,
        "severity": pb["severity"],
        "confidence": pb["score"],
        "cause": f"Rule-based classification: {severity_key} severity indicators detected.",
        "recommendation": pb["playbook"],
        "used_ai": False,
    }


# ─── Broadcast fallback templates ─────────────────────────────────────────────

BROADCAST_TEMPLATES = {
    "en": "Attention stadium guests: {message} Please follow instructions from staff and volunteers. Thank you for your cooperation.",
    "es": "Atención visitantes del estadio: {message} Por favor, siga las instrucciones del personal y los voluntarios. Gracias por su cooperación.",
    "ar": "انتباه زوار الملعب: {message} يرجى اتباع تعليمات الموظفين والمتطوعين. شكراً لتعاونكم.",
}


def broadcast_fallback(incident_title: str, incident_description: str) -> dict:
    short = incident_description[:120] + ("..." if len(incident_description) > 120 else "")
    return {
        "message_en": BROADCAST_TEMPLATES["en"].format(message=short),
        "message_es": BROADCAST_TEMPLATES["es"].format(message=short),
        "message_ar": BROADCAST_TEMPLATES["ar"].format(message=short),
        "used_ai": False,
    }
