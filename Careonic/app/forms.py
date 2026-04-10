from django import forms
from .models import BPMeasurement, WeightLog, DietLog, SymptomLog, UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['height', 'initial_weight', 'chronic_disease', 'date_of_birth', 'gender', 'email']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'initial_weight': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'chronic_disease': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        }
        
class BPForm(forms.ModelForm):
    class Meta:
        model = BPMeasurement
        fields = ['measurement_date', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'notes']
        widgets = {
            'measurement_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'systolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'min': 0, 'max': 300}),
            'diastolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'min': 0, 'max': 200}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 200}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class WeightForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['log_date', 'weight']
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'step': '0.01', 'min': 0, 'max': 500}),
        }

class DietForm(forms.ModelForm):
    class Meta:
        model = DietLog
        fields = ['log_date', 'sodium_intake', 'potassium_intake', 'carb_intake']
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'sodium_intake': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'min': 0, 'max': 10000}),
            'potassium_intake': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'min': 0, 'max': 10000}),
            'carb_intake': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'min': 0, 'max': 1000}),
        }

class SymptomForm(forms.ModelForm):
    class Meta:
        model = SymptomLog
        fields = ['log_date', 'symptom_description', 'severity']
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'symptom_description': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'severity': forms.Select(choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe')], attrs={'class': 'form-select', 'required': True}),
        }