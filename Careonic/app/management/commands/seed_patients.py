"""
Management command: seed_patients
Creates 25 patient users (HUPA0001P – HUPA0025P) in the Django SQLite database.
Run: python manage.py seed_patients
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from cryptography.fernet import Fernet
from app.models import UserProfile
from datetime import date

DEFAULT_PASSWORD = "Careonic@2024"
DEFAULT_PIN = "1234"
DEFAULT_DOB = date(1990, 1, 1)

PATIENT_PROFILES = [
    {"first_name": "Ananya",    "last_name": "Sharma",    "gender": "F", "height": 162.0, "weight": 58.0,  "disease": "Hypertension"},
    {"first_name": "Rohan",     "last_name": "Mehta",     "gender": "M", "height": 175.0, "weight": 72.0,  "disease": "Diabetes"},
    {"first_name": "Priya",     "last_name": "Nair",      "gender": "F", "height": 158.0, "weight": 55.0,  "disease": "Hypertension"},
    {"first_name": "Karan",     "last_name": "Gupta",     "gender": "M", "height": 180.0, "weight": 80.0,  "disease": "Obesity"},
    {"first_name": "Sneha",     "last_name": "Patel",     "gender": "F", "height": 164.0, "weight": 60.0,  "disease": "Asthma"},
    {"first_name": "Vikram",    "last_name": "Singh",     "gender": "M", "height": 178.0, "weight": 78.0,  "disease": "Hypertension"},
    {"first_name": "Meera",     "last_name": "Iyer",      "gender": "F", "height": 155.0, "weight": 52.0,  "disease": "Diabetes"},
    {"first_name": "Arjun",     "last_name": "Reddy",     "gender": "M", "height": 182.0, "weight": 85.0,  "disease": "Hypertension"},
    {"first_name": "Divya",     "last_name": "Krishnan",  "gender": "F", "height": 160.0, "weight": 57.0,  "disease": "Anemia"},
    {"first_name": "Rahul",     "last_name": "Joshi",     "gender": "M", "height": 170.0, "weight": 68.0,  "disease": "Hypertension"},
    {"first_name": "Lakshmi",   "last_name": "Menon",     "gender": "F", "height": 153.0, "weight": 50.0,  "disease": "Hypothyroidism"},
    {"first_name": "Siddharth", "last_name": "Rao",       "gender": "M", "height": 176.0, "weight": 74.0,  "disease": "Diabetes"},
    {"first_name": "Kavya",     "last_name": "Pillai",    "gender": "F", "height": 166.0, "weight": 62.0,  "disease": "Hypertension"},
    {"first_name": "Nikhil",    "last_name": "Verma",     "gender": "M", "height": 179.0, "weight": 82.0,  "disease": "Obesity"},
    {"first_name": "Deepa",     "last_name": "Nambiar",   "gender": "F", "height": 157.0, "weight": 54.0,  "disease": "Asthma"},
    {"first_name": "Aditya",    "last_name": "Kumar",     "gender": "M", "height": 183.0, "weight": 88.0,  "disease": "Hypertension"},
    {"first_name": "Swathi",    "last_name": "Bhat",      "gender": "F", "height": 161.0, "weight": 56.0,  "disease": "Diabetes"},
    {"first_name": "Praveen",   "last_name": "Chandra",   "gender": "M", "height": 174.0, "weight": 71.0,  "disease": "Hypertension"},
    {"first_name": "Nandini",   "last_name": "Kaur",      "gender": "F", "height": 159.0, "weight": 53.0,  "disease": "PCOS"},
    {"first_name": "Suresh",    "last_name": "Hegde",     "gender": "M", "height": 168.0, "weight": 66.0,  "disease": "Hypertension"},
    {"first_name": "Revathi",   "last_name": "Iyengar",   "gender": "F", "height": 154.0, "weight": 51.0,  "disease": "Anemia"},
    {"first_name": "Varun",     "last_name": "Malhotra",  "gender": "M", "height": 177.0, "weight": 76.0,  "disease": "Diabetes"},
    {"first_name": "Pooja",     "last_name": "Agarwal",   "gender": "F", "height": 163.0, "weight": 59.0,  "disease": "Hypertension"},
    {"first_name": "Harish",    "last_name": "Babu",      "gender": "M", "height": 181.0, "weight": 83.0,  "disease": "Obesity"},
    {"first_name": "Geetha",    "last_name": "Sundar",    "gender": "F", "height": 156.0, "weight": 53.0,  "disease": "Hypothyroidism"},
]


class Command(BaseCommand):
    help = "Seed 25 patient users (HUPA0001P – HUPA0025P) into the database"

    def handle(self, *args, **options):
        cipher = Fernet(settings.FERNET_KEY.encode())
        created = 0
        skipped = 0

        for i, profile_data in enumerate(PATIENT_PROFILES, start=1):
            username = f"patient{i:02d}"
            patient_id = f"HUPA{i:04d}P"

            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f"  SKIP  {username} ({patient_id}) — already exists"))
                skipped += 1
                continue

            # Create Django user
            user = User.objects.create_user(
                username=username,
                password=DEFAULT_PASSWORD,
                first_name=profile_data["first_name"],
                last_name=profile_data["last_name"],
            )

            # Create profile
            encrypted_pin = cipher.encrypt(DEFAULT_PIN.encode())
            UserProfile.objects.create(
                user=user,
                patient_id=patient_id,
                height=profile_data["height"],
                initial_weight=profile_data["weight"],
                pin=DEFAULT_PIN,
                encrypted_pin=encrypted_pin,
                date_of_birth=DEFAULT_DOB,
                gender=profile_data["gender"],
                chronic_disease=profile_data["disease"],
                email=f"{username}@careonic.demo",
            )

            self.stdout.write(self.style.SUCCESS(
                f"  CREATE {username} ({patient_id}) – {profile_data['first_name']} {profile_data['last_name']}"
            ))
            created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done! Created: {created}  |  Skipped: {skipped}"))
        self.stdout.write(f"Login with password: {DEFAULT_PASSWORD}  |  PIN: {DEFAULT_PIN}")
