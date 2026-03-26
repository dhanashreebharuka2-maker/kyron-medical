"""
Hard-coded providers and specialty metadata.
Appointment slots are generated programmatically in slot_generator.py.
"""
from __future__ import annotations


from typing import Any

PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "dr-chen",
        "full_name": "Dr. Elena Chen, MD",
        "specialty": "Cardiology",
        "body_part_focus": "Heart & cardiovascular system",
        "description": "Board-certified cardiologist focused on preventive care and chest-pain evaluation.",
    },
    {
        "id": "dr-okonkwo",
        "full_name": "Dr. Amara Okonkwo, MD",
        "specialty": "Dermatology",
        "body_part_focus": "Skin, hair, and nails",
        "description": "Dermatologist specializing in rashes, acne, and skin lesion evaluation.",
    },
    {
        "id": "dr-martinez",
        "full_name": "Dr. Luis Martinez, MD",
        "specialty": "Orthopedic Surgery",
        "body_part_focus": "Bones, joints, and musculoskeletal injuries",
        "description": "Orthopedic surgeon with emphasis on knee, shoulder, and sports-related injuries.",
    },
    {
        "id": "dr-patel",
        "full_name": "Dr. Priya Patel, MD",
        "specialty": "Gastroenterology",
        "body_part_focus": "Digestive system (stomach, intestines, liver)",
        "description": "Gastroenterologist focused on abdominal pain, reflux, and digestive health.",
    },
]

SPECIALTY_KEYWORDS: dict[str, list[str]] = {
    "dr-chen": [
        "heart",
        "chest",
        "cardio",
        "palpitation",
        "blood pressure",
        "hypertension",
        "cardiology",
        "cardiovascular",
    ],
    "dr-okonkwo": [
        "skin",
        "rash",
        "dermat",
        "mole",
        "acne",
        "eczema",
        "hair",
        "nail",
        "itch",
    ],
    "dr-martinez": [
        "knee",
        "shoulder",
        "joint",
        "bone",
        "ortho",
        "fracture",
        "sprain",
        "back pain",
        "muscle",
        "arthritis",
        "hip",
        "ankle",
    ],
    "dr-patel": [
        "stomach",
        "abdomen",
        "digest",
        "gastro",
        "nausea",
        "reflux",
        "heartburn",
        "bowel",
        "colon",
        "liver",
        "intestine",
    ],
}
