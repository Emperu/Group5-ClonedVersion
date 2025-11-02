from django.urls import path
from . import views

from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('booked-sessions/', views.booked_sessions, name='booked_sessions'),
    path('tutor-list/', views.tutor_list, name='tutor_list'),
    path('upcoming-appointments/', views.upcoming_appointments, name='upcoming_appointments'),
    path('cancel-reschedule/', views.cancel_reschedule, name='cancel_reschedule'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root':
settings.MEDIA_ROOT}), #serve media files when deployed
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root':
settings.STATIC_ROOT}), #serve static files when deployed
]
