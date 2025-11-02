from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')
def booked_sessions(request):
    return render(request, 'booked_sessions.html')

def tutor_list(request):
    return render(request, 'tutor_list.html')

def upcoming_appointments(request):
    return render(request, 'upcoming_appointments.html')

def cancel_reschedule(request):
    return render(request, 'cancel_reschedule.html')