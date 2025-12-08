from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list_view, name='event_list'),
    path('create/', views.create_event_view, name='create_event'),
    path('<int:event_id>/', views.event_detail_view, name='event_detail'),
    path('<int:event_id>/sync-statbotics/', views.sync_statbotics_view, name='sync_statbotics'),
    path('<int:event_id>/reimport/', views.reimport_event_view, name='reimport_event'),
    path('<int:event_id>/reset-matches/', views.reset_matches_view, name='reset_matches'),
    path('<int:event_id>/delete/', views.delete_event_view, name='delete_event'),
    path('match/<int:match_id>/', views.match_detail_view, name='match_detail'),
]
