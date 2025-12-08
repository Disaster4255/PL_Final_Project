from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('team-stats/<int:event_id>/', views.team_stats_view, name='team_stats'),
    path('match-analytics/<int:match_id>/', views.match_analytics_view, name='match_analytics'),
    path('export/<int:event_id>/', views.export_data_view, name='export_data'),
    path('fetch-statbotics/<int:event_id>/', views.fetch_statbotics_data, name='fetch_statbotics'),
    path('pick-list/<int:event_id>/', views.pick_list_view, name='pick_list'),
]
