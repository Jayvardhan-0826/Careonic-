from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),  # Default to login
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bp_tracking/', views.bp_tracking, name='bp_tracking'),
    path('report/', views.generate_report, name='report'),
    path('download_report/', views.download_report, name='download_report'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('get_entry_details/<str:date>/', views.get_entry_details, name='get_entry_details'),
    path('schedule_appointment/', views.schedule_appointment, name='schedule_appointment'),
    path('vitals/', views.vitals_prediction, name='vitals_prediction'),
    path('vitals/predict/', views.get_vitals_predictions, name='get_vitals_predictions'),
    # ── Integrated Vitals Dashboard (MongoDB History + Predictions) ──
    path('vitals-dashboard/', views.vitals_dashboard, name='vitals_dashboard'),
    path('api/vitals/history/', views.api_vitals_history, name='api_vitals_history'),
    path('api/vitals/predict/', views.api_vitals_predict, name='api_vitals_predict'),
]