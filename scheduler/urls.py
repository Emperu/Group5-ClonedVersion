from django.urls import path
from . import views

from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Student-only routes
    path('booked-sessions/', views.booked_sessions, name='booked_sessions'),
    path('tutor-list/', views.tutor_list, name='tutor_list'),
    path('book-session/<int:tutor_id>/', views.book_session, name='book_session'),
    path('upcoming-appointments/', views.upcoming_appointments, name='upcoming_appointments'),
    path('cancel-reschedule/', views.cancel_reschedule, name='cancel_reschedule'),

    # Tutor-only routes
    path('tutor/dashboard/', views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/schedule/', views.tutor_schedule, name='tutor_schedule'),
    path('tutor/appointments/', views.tutor_appointments, name='tutor_appointments'),

    # Admin-only routes
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root':
                                                 settings.MEDIA_ROOT}),  # serve media files when deployed
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root':
                                                  settings.STATIC_ROOT}),  # serve static files when deployed
]

