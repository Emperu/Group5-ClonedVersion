from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta, date
from .models import User, Student, Tutor, Course, Location, Booking
from .decorators import login_required, role_required


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        nuid = request.POST.get('NUID')
        password = request.POST.get('password')
        role = request.POST.get('role')

        # Validate role selection
        if not role or role not in ['student', 'tutor', 'admin']:
            messages.error(request, 'Please select a valid role')
            return render(request, 'login.html')

        # Validate NUID is 8 digits
        if not nuid or len(nuid) != 8 or not nuid.isdigit():
            messages.error(request, 'NUID must be exactly 8 digits')
            return render(request, 'login.html')

        try:
            user = User.objects.get(nuid=nuid)

            # Check if the user's role matches the selected role
            if user.role != role:
                messages.error(request, f'This account is not registered as a {role}')
                return render(request, 'login.html')

            if user.check_password(password):
                # Store user info in session
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_nuid'] = user.nuid
                request.session['user_role'] = user.role
                request.session['user_name'] = f"{user.first_name} {user.last_name}"
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid NUID or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid NUID or password')

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()  # Clear all session data
    messages.success(request, 'You have been logged out')
    return redirect('login')


@login_required
@role_required('student')
def booked_sessions(request):
    try:
        student = Student.objects.get(user_id=request.session['user_id'])
        bookings = Booking.objects.filter(students=student).select_related('tutor__user', 'location', 'course').order_by('start_ts')
        context = {
            'bookings': bookings,
        }
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        context = {'bookings': []}
    return render(request, 'booked_sessions.html', context)


@login_required
@role_required('student')
def tutor_list(request):
    tutors = Tutor.objects.all().select_related('user').prefetch_related('taught_courses')
    context = {
        'tutors': tutors,
    }
    return render(request, 'tutor_list.html', context)


@login_required
@role_required('student')
def upcoming_appointments(request):
    return render(request, 'upcoming_appointments.html')


@login_required
@role_required('student')
def cancel_reschedule(request):
    return render(request, 'cancel_reschedule.html')


@login_required
@role_required('tutor')
def tutor_dashboard(request):
    return render(request, 'tutor_dashboard.html')


@login_required
@role_required('tutor')
def tutor_schedule(request):
    return render(request, 'tutor_schedule.html')


@login_required
@role_required('tutor')
def tutor_appointments(request):
    return render(request, 'tutor_appointments.html')


@login_required
@role_required('admin')
def admin_dashboard(request):
    students = Student.objects.all()
    tutors = Tutor.objects.all()
    context = {
        'students': students,
        'tutors': tutors,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@role_required('student')
def book_session(request, tutor_id):
    """View for booking a tutoring session with a specific tutor"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Get the current student
    try:
        student = Student.objects.get(user_id=request.session['user_id'])
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('tutor_list')
    
    # Get courses this tutor teaches
    tutor_courses = Course.objects.filter(tutors=tutor)
    # Get all available locations
    locations = Location.objects.all()
    
    if request.method == 'POST':
        # Get form data
        course_id = request.POST.get('course')
        location_id = request.POST.get('location')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        duration = request.POST.get('duration', '60')  # Default 60 minutes
        
        # Validate required fields
        if not all([course_id, location_id, start_date, start_time]):
            messages.error(request, 'Please fill in all required fields.')
            context = {
                'tutor': tutor,
                'tutor_courses': tutor_courses,
                'locations': locations,
                'today': date.today(),
            }
            return render(request, 'book_session.html', context)
        
        try:
            # Parse date and time
            datetime_str = f"{start_date} {start_time}"
            start_ts = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            start_ts = timezone.make_aware(start_ts)
            
            # Calculate end time
            duration_minutes = int(duration)
            end_ts = start_ts + timedelta(minutes=duration_minutes)
            
            # Validate that start time is in the future
            if start_ts <= timezone.now():
                messages.error(request, 'Booking time must be in the future.')
                context = {
                    'tutor': tutor,
                    'tutor_courses': tutor_courses,
                    'locations': locations,
                    'today': date.today(),
                }
                return render(request, 'book_session.html', context)
            
            # Check for time conflicts with existing bookings for this tutor
            conflicting_bookings = Booking.objects.filter(
                tutor=tutor,
                status__in=['confirmed', 'pending'],  # Only check active bookings
            ).filter(
                Q(start_ts__lt=end_ts) & Q(end_ts__gt=start_ts)
            )
            
            if conflicting_bookings.exists():
                messages.error(request, 'This tutor is already booked during this time. Please choose a different time.')
                context = {
                    'tutor': tutor,
                    'tutor_courses': tutor_courses,
                    'locations': locations,
                    'today': date.today(),
                }
                return render(request, 'book_session.html', context)
            
            # Get course and location objects
            course = Course.objects.get(id=course_id) if course_id else None
            location = Location.objects.get(id=location_id)
            
            # Create the booking
            booking = Booking.objects.create(
                tutor=tutor,
                location=location,
                course=course,
                start_ts=start_ts,
                end_ts=end_ts,
                status='confirmed'
            )
            
            # Add student to the booking
            booking.students.add(student)
            
            messages.success(request, f'Successfully booked a session with {tutor.user.first_name} {tutor.user.last_name}!')
            return redirect('booked_sessions')
            
        except ValueError as e:
            messages.error(request, 'Invalid date or time format.')
        except Course.DoesNotExist:
            messages.error(request, 'Selected course not found.')
        except Location.DoesNotExist:
            messages.error(request, 'Selected location not found.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    # GET request - show booking form
    context = {
        'tutor': tutor,
        'tutor_courses': tutor_courses,
        'locations': locations,
        'today': date.today(),
    }
    return render(request, 'book_session.html', context)