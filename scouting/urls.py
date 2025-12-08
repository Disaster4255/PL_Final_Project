from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.scouter_dashboard_view, name='scouter_dashboard'),
    path('assign/<int:match_id>/', views.assign_scouters_view, name='assign_scouters'),
    path('auto-assign/<int:event_id>/', views.auto_assign_scouters_view, name='auto_assign_scouters'),
    path('submit/<int:assignment_id>/', views.submit_scouting_report_view, name='submit_report'),
    path('predict/<int:match_id>/', views.submit_prediction_view, name='submit_prediction'),
    path('generate-qr/<int:report_id>/', views.generate_qr_code_view, name='generate_qr_code'),
    path('scan-qr/', views.scan_qr_code_view, name='scan_qr_code'),
    path('confirm/<int:report_id>/', views.confirm_report_view, name='confirm_report'),
    path('reports/<int:match_id>/', views.view_match_reports_view, name='view_match_reports'),
    path('complete/<int:match_id>/', views.complete_match_view, name='complete_match'),
    path('leaderboard/', views.prediction_leaderboard_view, name='leaderboard'),
]
