from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import base64
import os
from django.conf import settings

cipher_suite = Fernet(settings.FERNET_KEY.encode())

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    pin = models.CharField(max_length=6)
    initial_weight = models.DecimalField(max_digits=5, decimal_places=2)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True)
    chronic_disease = models.CharField(max_length=50, default='Hypertension')
    encrypted_pin = models.BinaryField(null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)  # New email field
    patient_id = models.CharField(max_length=12, unique=True, null=True, blank=True, help_text='Patient ID e.g. HUPA0001P')

    def set_encrypted_pin(self, pin):
        if pin:
            self.encrypted_pin = cipher_suite.encrypt(pin.encode())

    def get_decrypted_pin(self):
        return cipher_suite.decrypt(self.encrypted_pin).decode() if self.encrypted_pin else None

    def __str__(self):
        return f"{self.user.username}'s Profile"
    

class BPMeasurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    measurement_date = models.DateField()
    systolic_bp = models.IntegerField()
    diastolic_bp = models.IntegerField()
    heart_rate = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

class DietLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    sodium_intake = models.IntegerField()  # mg/day
    potassium_intake = models.IntegerField()  # mg/day
    carb_intake = models.IntegerField()  # grams/day

class SymptomLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    symptom_description = models.TextField()
    severity = models.CharField(max_length=10, choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe')])

class Appointment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='appointments')
    date_time = models.DateTimeField()
    doctor = models.CharField(max_length=100)  # e.g., "Cardiologist", "Endocrinologist"
    reason = models.TextField()
    contact_info = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='Scheduled')  # e.g., "Scheduled", "Confirmed"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.date_time}"


class GlucoseLog(models.Model):
    """User-logged glucose and heart rate readings used to drive vitals prediction."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    logged_at = models.DateTimeField(auto_now_add=True)
    glucose = models.FloatField(help_text='Blood glucose in mg/dL')
    heart_rate = models.FloatField(help_text='Heart rate in bpm')

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.user.username} | {self.glucose} mg/dL | {self.heart_rate} bpm @ {self.logged_at.strftime('%Y-%m-%d %H:%M')}"