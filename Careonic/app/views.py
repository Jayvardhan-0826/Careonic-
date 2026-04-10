from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UserProfile, BPMeasurement, WeightLog, DietLog, SymptomLog, Appointment, GlucoseLog
import requests as http_requests
from django.utils import timezone
from django.db.models import Avg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import timedelta, date
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import BPForm, WeightForm, DietForm, SymptomForm, UserProfileForm
from datetime import datetime
from decouple import config
import json
from django.db.models import Avg, Count
import matplotlib.pyplot as plt
import io
import base64
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib
from django.urls import reverse
from urllib.parse import urlencode
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from cryptography.fernet import Fernet
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
import os

logger = logging.getLogger(__name__)

key = Fernet.generate_key()
cipher_suite = Fernet(key)

def signup(request):
    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            pin = request.POST.get('pin', '1234')
            profile.set_encrypted_pin(pin)
            profile.email = profile_form.cleaned_data['email']  # Save email
            profile.save()
            login(request, user)
            return redirect('dashboard')
    else:
        user_form = UserCreationForm()
        profile_form = UserProfileForm()

    return render(request, 'app/signup.html', {
        'form': user_form,
        'profile_form': profile_form
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        pin = request.POST.get('pin', '').strip()
        
        if form.is_valid():
            user = form.get_user()
            try:
                profile = UserProfile.objects.get(user=user)
                stored_pin = profile.get_decrypted_pin()

                if stored_pin and pin == stored_pin:
                    login(request, user)
                    return redirect('dashboard')
                else:
                    form.add_error(None, "Invalid Security PIN. Please try again.")
            except UserProfile.DoesNotExist:
                form.add_error(None, "No Security PIN set for this account. Contact support.")
        else:
            form.add_error(None, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'app/login.html', {'form': form})

@login_required
def dashboard(request):
    # Get dates with entries for calendar highlighting
    entries = BPMeasurement.objects.filter(user=request.user).values_list('measurement_date', flat=True).distinct()
    event_dates = [d.strftime('%Y-%m-%d') for d in entries]
    return render(request, 'app/dashboard.html', {'event_dates': json.dumps(event_dates)})


@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
        profile.save()

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'app/profile.html', {'form': form})

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

@login_required
def bp_tracking(request):
    today = date.today().strftime('%Y-%m-%d')
    selected_date = request.GET.get('date', today)

    if request.method == 'POST':
        logger.info("Received POST request with data: %s", request.POST)
        saved_forms = []

        try:
            bp_form = BPForm(request.POST)
            weight_form = WeightForm(request.POST)
            diet_form = DietForm(request.POST)
            symptom_form = SymptomForm(request.POST)

            if bp_form.is_valid():
                bp = bp_form.save(commit=False)
                bp.user = request.user
                bp.save()
                saved_forms.append('Blood Pressure')
                # Threshold check for BP
                if bp.systolic_bp > 140 or bp.diastolic_bp > 90 or (hasattr(bp, 'sugar_level') and bp.sugar_level > 200):
                    send_danger_email(request, request.user, bp)

            if weight_form.is_valid():
                w = weight_form.save(commit=False)
                w.user = request.user
                w.save()
                saved_forms.append('Weight')
                profile = request.user.userprofile
                if profile.initial_weight and w.weight > profile.initial_weight * 1.05:
                    send_danger_email(request, request.user, w)

            if diet_form.is_valid():
                d = diet_form.save(commit=False)
                d.user = request.user
                d.save()
                saved_forms.append('Diet')
                if d.sodium_intake > 2300 or d.carb_intake > 300:
                    send_danger_email(request, request.user, d)

            if symptom_form.is_valid():
                s = symptom_form.save(commit=False)
                s.user = request.user
                s.save()
                saved_forms.append('Symptom')
                if s.severity == 'severe':
                    send_danger_email(request, request.user, s)

            if request.POST.get('submit_all'):
                if saved_forms:
                    messages.success(request, f"Successfully logged: {', '.join(saved_forms)}.")
                else:
                    messages.warning(request, "No valid data to log.")
            else:
                if saved_forms:
                    messages.success(request, f"Successfully logged {saved_forms[0]}.")
                else:
                    messages.warning(request, "Invalid data.")

            redirect_url = reverse('bp_tracking')
            if selected_date != today:
                redirect_url += f'?{urlencode({"date": selected_date})}'

            return redirect(redirect_url)

        except Exception as e:
            logger.error("Error processing POST request: %s", str(e))
            messages.error(request, "An error occurred while saving data.")
            return render(request, 'app/bp_tracking.html', {
                'bp_form': bp_form, 'weight_form': weight_form, 'diet_form': diet_form, 'symptom_form': symptom_form,
                'measurements': BPMeasurement.objects.filter(user=request.user, measurement_date=selected_date),
                'weight_logs': WeightLog.objects.filter(user=request.user, log_date=selected_date),
                'diet_logs': DietLog.objects.filter(user=request.user, log_date=selected_date),
                'symptom_logs': SymptomLog.objects.filter(user=request.user, log_date=selected_date),
            })

    # GET request handling
    bp_form = BPForm(initial={'measurement_date': selected_date})
    weight_form = WeightForm(initial={'log_date': selected_date})
    diet_form = DietForm(initial={'log_date': selected_date})
    symptom_form = SymptomForm(initial={'log_date': selected_date})

    context = {
        'bp_form': bp_form, 'weight_form': weight_form, 'diet_form': diet_form, 'symptom_form': symptom_form,
        'measurements': BPMeasurement.objects.filter(user=request.user, measurement_date=selected_date),
        'weight_logs': WeightLog.objects.filter(user=request.user, log_date=selected_date),
        'diet_logs': DietLog.objects.filter(user=request.user, log_date=selected_date),
        'symptom_logs': SymptomLog.objects.filter(user=request.user, log_date=selected_date),
    }
    return render(request, 'app/bp_tracking.html', context)

def send_danger_email(request, user, measurement):
    profile = user.userprofile
    subject = 'Health Alert: Exceeded Danger Levels'
    date_measured = getattr(measurement, 'measurement_date', getattr(measurement, 'log_date', timezone.now()))
    danger_levels = []
    if isinstance(measurement, BPMeasurement):
        if measurement.systolic_bp > 140:
            danger_levels.append(f"Systolic BP: {measurement.systolic_bp} mmHg (Threshold: >140)")
        if measurement.diastolic_bp > 90:
            danger_levels.append(f"Diastolic BP: {measurement.diastolic_bp} mmHg (Threshold: >90)")
        if hasattr(measurement, 'sugar_level') and measurement.sugar_level > 200:
            danger_levels.append(f"Sugar Level: {measurement.sugar_level} mg/dL (Threshold: >200)")
    elif isinstance(measurement, WeightLog):
        if profile.initial_weight and measurement.weight > profile.initial_weight * 1.05:
            danger_levels.append(f"Weight: {measurement.weight} kg (Threshold: >5% of {profile.initial_weight} kg)")
    elif isinstance(measurement, DietLog):
        if measurement.sodium_intake > 2300:
            danger_levels.append(f"Sodium: {measurement.sodium_intake} mg (Threshold: >2300)")
        if measurement.carb_intake > 300:
            danger_levels.append(f"Carbs: {measurement.carb_intake} g (Threshold: >300)")
    elif isinstance(measurement, SymptomLog):
        if measurement.severity == 'severe':
            danger_levels.append(f"Symptom Severity: {measurement.severity} - {measurement.symptom_description}")

    if danger_levels:
        doctor = "Cardiologist" if isinstance(measurement, BPMeasurement) else "General Physician"
        message = render_to_string('app/danger_email.html', {
            'user_name': user.username,
            'date_measured': date_measured,
            'danger_levels': danger_levels,
            'appointment_url': request.build_absolute_uri(reverse('schedule_appointment')) + f'?doctor={doctor}&pre_fill=1',
        })

        # DEBUG: Print email instead of sending
        if config('DEBUG_EMAIL', default=False, cast=bool):
            logger.info(f"[DEBUG EMAIL] To: {profile.email}\nSubject: {subject}\n{message}")
            return  # Skip sending

        # PRODUCTION: Send email (will crash on Render)
        try:
            send_mail(
                subject,
                "Please enable HTML in your email client.",
                config('EMAIL_HOST_USER'),
                [profile.email],
                html_message=message,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Email failed: {e}")

@login_required
@require_GET
def get_entry_details(request, date):
    try:
        logger.info(f"Fetching details for date: {date}")
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        bp_entries = BPMeasurement.objects.filter(user=request.user, measurement_date=date_obj).count()
        weight_entries = WeightLog.objects.filter(user=request.user, log_date=date_obj).count()
        diet_entries = DietLog.objects.filter(user=request.user, log_date=date_obj).count()
        symptom_entries = SymptomLog.objects.filter(user=request.user, log_date=date_obj).count()

        details_list = []
        if bp_entries > 0:
            details_list.append(f"<li>{bp_entries} BP measurement(s)</li>")
        if weight_entries > 0:
            details_list.append(f"<li>{weight_entries} weight log(s)</li>")
        if diet_entries > 0:
            details_list.append(f"<li>{diet_entries} diet log(s)</li>")
        if symptom_entries > 0:
            details_list.append(f"<li>{symptom_entries} symptom log(s)</li>")

        if details_list:
            details = "<ul>" + "".join(details_list) + "</ul>"
        else:
            details = "<p>No entries for this date.</p>"

        return JsonResponse({'details': details})
    except ValueError as e:
        logger.error(f"Invalid date format: {date}, error: {e}")
        return JsonResponse({'details': '<p>Invalid date format.</p>'}, status=400)
    except Exception as e:
        logger.error(f"Error fetching details for {date}: {e}")
        return JsonResponse({'details': '<p>Failed to load details. Try again later.</p>'}, status=500)
    



@login_required
def generate_report(request):
    user = request.user
    today = date.today()
    start_date = today - relativedelta(days=30)

    # --- Query Data (last 30 days) ---
    bp_data = BPMeasurement.objects.filter(user=user, measurement_date__gte=start_date).order_by('measurement_date')
    weight_data = WeightLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')
    diet_data = DietLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')
    symptom_data = SymptomLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')

    # --- Summaries ---
    bp_summary = bp_data.aggregate(
        avg_systolic=Avg('systolic_bp'),
        avg_diastolic=Avg('diastolic_bp'),
        avg_heart_rate=Avg('heart_rate')
    )
    weight_summary = weight_data.aggregate(avg_weight=Avg('weight'))
    diet_summary = diet_data.aggregate(
        avg_sodium=Avg('sodium_intake'),
        avg_potassium=Avg('potassium_intake'),
        avg_carb=Avg('carb_intake')
    )
    symptom_summary = symptom_data.values('severity').annotate(count=Count('id'))

    # --- Generate Graphs ---
    bp_graph = generate_line_graph(bp_data, 'measurement_date', ['systolic_bp', 'diastolic_bp'], 'BP Trends', 'Date', 'BP (mmHg)')
    weight_graph = generate_line_graph(weight_data, 'log_date', ['weight'], 'Weight Trends', 'Date', 'Weight (kg)')
    diet_graph = generate_line_graph(diet_data, 'log_date', ['sodium_intake', 'potassium_intake', 'carb_intake'], 'Diet Trends', 'Date', 'Intake')
    symptom_graph = generate_bar_graph(symptom_data, 'severity', 'Symptom Severity Count', 'Severity', 'Count')
    # --- User Profile Info ---
    try:
        profile = user.userprofile
        dob = profile.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)) if dob else "N/A"
        gender = profile.gender or "N/A"
    except UserProfile.DoesNotExist:
        age, gender = "N/A", "N/A"

    current_weight = weight_data.last().weight if weight_data.exists() else profile.initial_weight if 'profile' in locals() else "N/A"

    context = {
        "name": user.first_name or user.username,
        "age": age,
        "gender": gender,
        "current_weight": current_weight,

        "bp_data": bp_data,
        "weight_data": weight_data,
        "diet_data": diet_data,
        "symptom_data": symptom_data,

        "bp_summary": bp_summary,
        "weight_summary": weight_summary,
        "diet_summary": diet_summary,
        "symptom_summary": symptom_summary,

        "bp_graph": bp_graph,
        "weight_graph": weight_graph,
        "diet_graph": diet_graph,
        "symptom_graph": symptom_graph,
    }
    return render(request, "app/report.html", context)

@login_required
def download_report(request):
    # Fetch user profile
    profile = UserProfile.objects.get(user=request.user)
    name = request.user.get_full_name() or request.user.username
    age = (date.today() - profile.date_of_birth).days // 365 if hasattr(profile, 'date_of_birth') else 'N/A'
    gender = profile.gender if hasattr(profile, 'gender') else 'N/A'
    current_weight = profile.initial_weight
    latest_weight = WeightLog.objects.filter(user=request.user).order_by('-log_date').first()
    if latest_weight:
        current_weight = latest_weight.weight

    # Fetch data for last 30 days
    start_date = date.today() - relativedelta(months=1)
    bp_data = BPMeasurement.objects.filter(user=request.user, measurement_date__gte=start_date).order_by('measurement_date')
    weight_data = WeightLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')
    diet_data = DietLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')
    symptom_data = SymptomLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')

    # Summaries
    bp_summary = bp_data.aggregate(avg_systolic=Avg('systolic_bp'), avg_diastolic=Avg('diastolic_bp'), avg_heart_rate=Avg('heart_rate'))
    weight_summary = weight_data.aggregate(avg_weight=Avg('weight'))
    diet_summary = diet_data.aggregate(avg_sodium=Avg('sodium_intake'), avg_potassium=Avg('potassium_intake'), avg_carb=Avg('carb_intake'))
    symptom_summary = symptom_data.values('severity').annotate(count=Count('severity'))

    # Generate graphs
    bp_graph = generate_line_graph(bp_data, 'measurement_date', ['systolic_bp', 'diastolic_bp'], 'BP Trends', 'Date', 'BP (mmHg)')
    weight_graph = generate_line_graph(weight_data, 'log_date', ['weight'], 'Weight Trends', 'Date', 'Weight (kg)')
    diet_graph = generate_line_graph(diet_data, 'log_date', ['sodium_intake', 'potassium_intake', 'carb_intake'], 'Diet Trends', 'Date', 'Intake (mg/g)')
    symptom_graph = generate_bar_graph(symptom_data, 'severity', 'Symptoms Severity Count', 'Severity', 'Count')

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{name}_Health_Report_{date.today().strftime("%Y%m%d")}.pdf"'

    # PDF document setup
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='Title', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue)
    header_style = ParagraphStyle(name='Header', parent=styles['Heading2'], fontSize=14, textColor=colors.black)
    normal_style = styles['Normal']

    # Patient Information
    elements.append(Paragraph(f"Health Report for {name}", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Age: {age} | Gender: {gender} | Current Weight: {current_weight} kg", normal_style))
    elements.append(Spacer(1, 24))

    # BP Section
    elements.append(Paragraph("BP Measurements", header_style))
    if bp_data.exists():
        data = [['Date', 'Systolic BP', 'Diastolic BP', 'Heart Rate', 'Notes']]
        for entry in bp_data:
            data.append([
                entry.measurement_date.strftime('%Y-%m-%d'),
                str(entry.systolic_bp),
                str(entry.diastolic_bp),
                str(entry.heart_rate or ''),
                entry.notes or ''
            ])
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average: {bp_summary['avg_systolic'] or 'N/A'} / {bp_summary['avg_diastolic'] or 'N/A'} mmHg, Avg HR: {bp_summary['avg_heart_rate'] or 'N/A'} bpm", normal_style))
    else:
        elements.append(Paragraph("No BP data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Weight Section
    elements.append(Paragraph("Weight Logs", header_style))
    if weight_data.exists():
        data = [['Date', 'Weight (kg)']]
        for entry in weight_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), str(entry.weight)])
        table = Table(data, colWidths=[1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average Weight: {weight_summary['avg_weight'] or 'N/A'} kg", normal_style))
    else:
        elements.append(Paragraph("No weight data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Diet Section
    elements.append(Paragraph("Diet Logs", header_style))
    if diet_data.exists():
        data = [['Date', 'Sodium (mg)', 'Potassium (mg)', 'Carbs (g)']]
        for entry in diet_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), str(entry.sodium_intake), str(entry.potassium_intake), str(entry.carb_intake)])
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average Sodium: {diet_summary['avg_sodium'] or 'N/A'} mg, Potassium: {diet_summary['avg_potassium'] or 'N/A'} mg, Carbs: {diet_summary['avg_carb'] or 'N/A'} g", normal_style))
    else:
        elements.append(Paragraph("No diet data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Symptom Section
    elements.append(Paragraph("Symptoms", header_style))
    if symptom_data.exists():
        data = [['Date', 'Description', 'Severity']]
        for entry in symptom_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), entry.symptom_description, entry.severity])
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph("Symptom Summary:", normal_style))
        for item in symptom_summary:
            elements.append(Paragraph(f"{item['severity']}: {item['count']}", normal_style))
    else:
        elements.append(Paragraph("No symptom data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Add Graphs
    if bp_graph:
        elements.append(Paragraph("BP Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(bp_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if weight_graph:
        elements.append(Paragraph("Weight Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(weight_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if diet_graph:
        elements.append(Paragraph("Diet Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(diet_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if symptom_graph:
        elements.append(Paragraph("Symptoms Severity Count", header_style))
        img = Image(io.BytesIO(base64.b64decode(symptom_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    return response


def generate_line_graph(data, date_field, value_fields, title, xlabel, ylabel):
    if not data.exists():
        return None
    dates = [getattr(entry, date_field) for entry in data]
    values = {field: [getattr(entry, field) for entry in data] for field in value_fields}

    fig, ax = plt.subplots()
    for field in value_fields:
        ax.plot(dates, values[field], label=field.replace('_', ' ').title(), marker='o')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return img_base64

def generate_bar_graph(data, category_field, title, xlabel, ylabel):
    if not data.exists():
        return None
    categories = list(set([getattr(entry, category_field) for entry in data]))
    counts = [data.filter(**{category_field: cat}).count() for cat in categories]

    fig, ax = plt.subplots()
    ax.bar(categories, counts, color='skyblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return img_base64


@login_required
def schedule_appointment(request):
    if request.method == 'POST':
        user = request.user
        profile = user.userprofile
        doctor = request.POST.get('doctor')
        date_time = request.POST.get('date_time')
        reason = request.POST.get('reason')
        contact_info = request.POST.get('contact_info')

        if request.GET.get('pre_fill'):
            # Pre-filled from email
            danger_data = request.GET.get('danger_data', '')
            reason = f"Emergency: {danger_data}" if danger_data else reason
            doctor = request.GET.get('doctor', doctor)

        appointment = Appointment.objects.create(
            user=profile,
            date_time=date_time,
            doctor=doctor,
            reason=reason,
            contact_info=contact_info,
        )
        send_confirmation_email(user, appointment)
        messages.success(request, "Appointment scheduled successfully!")
        return redirect('dashboard')

    # Pre-fill logic from email
    initial_data = {}
    if request.GET.get('pre_fill'):
        doctor = request.GET.get('doctor', 'General Physician')
        initial_data = {
            'doctor': doctor,
            'reason': request.GET.get('danger_data', 'Health concern'),
            'contact_info': profile.contact_info or '',
        }

    return render(request, 'app/schedule_appointment.html', {
        'form': {'initial': initial_data},
        'doctors': ['Cardiologist', 'Endocrinologist', 'General Physician'],
    })

def send_confirmation_email(user, appointment):
    subject = 'Appointment Confirmation'
    message = render_to_string('app/confirmation_email.html', {
        'user_name': user.username,
        'appointment': appointment,
    })
    send_mail(
        subject,
        message,
        os.getenv('EMAIL_HOST_USER'),
        [user.userprofile.email],
        html_message=message,
        fail_silently=False,
    )


# ─── Vitals Prediction Feature ──────────────────────────────────────────────

from django.conf import settings as django_settings
from pymongo import MongoClient

PREDICT_API_BASE = getattr(django_settings, 'PREDICT_API_BASE', "http://127.0.0.1:8000/predict")
MONGO_URI = getattr(django_settings, 'MONGO_URI', '')
MONGO_DB_NAME = getattr(django_settings, 'MONGO_DB_NAME', 'users_vital_data')


def _get_patient_id(request):
    """Return the patient_id for the logged-in user, or None."""
    try:
        return request.user.userprofile.patient_id
    except UserProfile.DoesNotExist:
        return None


@login_required
def vitals_prediction(request):
    """
    GET  – Render the Vitals Forecast page.
    POST – Save a GlucoseLog entry and return the FastAPI predictions as JSON.
    """
    patient_id = _get_patient_id(request)
    recent_logs = GlucoseLog.objects.filter(user=request.user)[:5]

    if request.method == "POST":
        try:
            glucose = float(request.POST.get("glucose", 0))
            heart_rate = float(request.POST.get("heart_rate", 0))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid glucose or heart rate value."}, status=400)

        # Save the log entry
        GlucoseLog.objects.create(user=request.user, glucose=glucose, heart_rate=heart_rate)

        # Fetch predictions from FastAPI
        prediction_data = None
        api_error = None
        if patient_id:
            try:
                resp = http_requests.get(f"{PREDICT_API_BASE}/{patient_id}", timeout=10)
                resp.raise_for_status()
                prediction_data = resp.json()
            except http_requests.exceptions.ConnectionError:
                api_error = "Prediction server is offline. Please ensure the FastAPI server is running on port 8000."
            except http_requests.exceptions.Timeout:
                api_error = "Prediction server timed out. Please try again."
            except Exception as exc:
                api_error = f"Prediction error: {str(exc)}"
        else:
            api_error = "Your account is not linked to a patient ID. Please contact an administrator."

        return JsonResponse({
            "success": True,
            "glucose": glucose,
            "heart_rate": heart_rate,
            "predictions": prediction_data.get("predictions", []) if prediction_data else [],
            "error": api_error,
        })

    return render(request, "app/vitals_prediction.html", {
        "patient_id": patient_id,
        "recent_logs": recent_logs,
    })


@login_required
@require_GET
def get_vitals_predictions(request):
    """AJAX endpoint – fetch predictions for the logged-in user's patient ID."""
    patient_id = _get_patient_id(request)
    if not patient_id:
        return JsonResponse({"error": "No patient ID linked to your account."}, status=400)

    try:
        resp = http_requests.get(f"{PREDICT_API_BASE}/{patient_id}", timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json())
    except http_requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Prediction server is offline."}, status=503)
    except http_requests.exceptions.Timeout:
        return JsonResponse({"error": "Prediction server timed out."}, status=504)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


# ─── Vitals Dashboard (MongoDB History + Predictions) ────────────────────────

@login_required
def vitals_dashboard(request):
    """Integrated vitals dashboard with MongoDB history + prediction charts."""
    patient_id = _get_patient_id(request)
    return render(request, "app/vitals_dashboard.html", {
        "patient_id": patient_id,
    })


@login_required
@require_GET
def api_vitals_history(request):
    """
    AJAX endpoint — return the full vitals history for the logged-in patient
    read directly from MongoDB.
    Optional query: ?limit=50 (default: all records)
    """
    patient_id = _get_patient_id(request)
    if not patient_id:
        return JsonResponse({"error": "No patient ID linked."}, status=400)

    limit = int(request.GET.get("limit", 0))

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB_NAME]
        col = db[patient_id]

        query = col.find(
            {},
            {"_id": 0, "glucose": 1, "heart_rate": 1, "time_stamp": 1}
        ).sort("time_stamp", 1)  # oldest first for charting

        if limit > 0:
            query = query.limit(limit)

        records = []
        for doc in query:
            ts = doc.get("time_stamp")
            if ts is not None:
                # pymongo returns datetime objects for ISODate fields
                if hasattr(ts, 'isoformat'):
                    ts_str = ts.isoformat()
                else:
                    ts_str = str(ts)
            else:
                ts_str = ""
            records.append({
                "time_stamp": ts_str,
                "glucose": doc.get("glucose"),
                "heart_rate": doc.get("heart_rate"),
            })
        client.close()

        return JsonResponse({
            "patient_id": patient_id,
            "total": len(records),
            "records": records,
        })
    except Exception as exc:
        return JsonResponse({"error": f"MongoDB error: {str(exc)}"}, status=503)


@login_required
@require_GET
def api_vitals_predict(request):
    """
    AJAX endpoint — proxy to FastAPI /predict/{patient_id}.
    Returns 12 × 5-min predictions for glucose & heart rate.
    """
    patient_id = _get_patient_id(request)
    if not patient_id:
        return JsonResponse({"error": "No patient ID linked."}, status=400)

    try:
        resp = http_requests.get(f"{PREDICT_API_BASE}/{patient_id}", timeout=15)
        resp.raise_for_status()
        return JsonResponse(resp.json())
    except http_requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Prediction server is offline. Start the FastAPI server on port 8000."}, status=503)
    except http_requests.exceptions.Timeout:
        return JsonResponse({"error": "Prediction server timed out."}, status=504)
    except http_requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        return JsonResponse({"error": detail}, status=exc.response.status_code)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)