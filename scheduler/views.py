from django.shortcuts import render, redirect, get_object_or_404 # We can use get_object_or_404 for tutor error handeling
from django.contrib import messages
from django.utils import timezone # Timezone to make scheduling accurate for user
from django.db.models import Q
from datetime import datetime, timedelta, date # Used for date handeling
from django.contrib.auth import login, authenticate

from .models import User, Student, Tutor, Course, Location, Booking, TutorAvailability
from .decorators import login_required, role_required

from .email import send_booking_request_email, send_booking_confirmed_email


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

                # Log the user in for Django Admin compatibility
                if user.role == 'admin':
                    django_user = authenticate(request, username=nuid, password=password)
                    if django_user:
                        login(request, django_user)
                    return redirect('/admin/')

                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid NUID or password')

        except User.DoesNotExist:
            messages.error(request, 'Invalid NUID or password')

    # GET request or failed POST falls through to here
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
        messages.error(request, 'Student profile not found.')
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
def cancel_reschedule(request):
    try:
        student = Student.objects.get(user_id=request.session['user_id'])
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')

    bookings = Booking.objects.filter(
        students=student,
        status='confirmed',
        start_ts__gt=timezone.now()
    ).order_by('start_ts')

    if request.method == 'POST':
        action = request.POST.get('action')
        booking_id = request.POST.get('booking_id')

        booking = get_object_or_404(Booking, id=booking_id, students=student)

        if action == 'cancel':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Your appointment has been cancelled.')
            return redirect('cancel_reschedule')

        elif action == 'reschedule':
            new_date = request.POST.get('new_date')
            new_time = request.POST.get('new_time')

            if not new_date or not new_time:
                messages.error(request, 'Please select a new date and time.')
                return redirect('cancel_reschedule')

            try:
                new_start = datetime.strptime(
                    f"{new_date} {new_time}", "%Y-%m-%d %H:%M"
                )
                new_start = timezone.make_aware(new_start)

                duration = booking.end_ts - booking.start_ts
                new_end = new_start + duration

                if new_start <= timezone.now():
                    messages.error(request, 'You cannot reschedule into the past.')
                    return redirect('cancel_reschedule')

                conflict = Booking.objects.filter(
                    tutor=booking.tutor,
                    status='confirmed'
                ).filter(
                    Q(start_ts__lt=new_end) & Q(end_ts__gt=new_start)
                )

                if conflict.exists():
                    messages.error(request, 'That tutor is already booked at that time.')
                    return redirect('cancel_reschedule')

                booking.start_ts = new_start
                booking.end_ts = new_end
                booking.save()

                messages.success(request, 'Your session has been successfully rescheduled.')
                return redirect('cancel_reschedule')

            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                return redirect('cancel_reschedule')

    return render(request, 'cancel_reschedule.html', {
        'bookings': bookings
    })

@login_required
@role_required('tutor')
def tutor_dashboard(request):
    return render(request, 'tutor_dashboard.html')


@login_required
@role_required('tutor')
def tutor_schedule(request):
    # View for tutors to manage  availability
    try:
        tutor = Tutor.objects.get(user_id=request.session['user_id'])
    except Tutor.DoesNotExist:
        messages.error(request, 'Tutor not found.')
        return redirect('home')

    # Add or delete availability
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            day_of_week = request.POST.get('day_of_week')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            if not all([day_of_week, start_time, end_time]):
                messages.error(request, 'Please fill in all fields.')
            else:
                try:
                    # Validate that end time is after start time
                    from datetime import datetime
                    start_dt = datetime.strptime(start_time, '%H:%M').time()
                    end_dt = datetime.strptime(end_time, '%H:%M').time()

                    if end_dt <= start_dt:
                        messages.error(request, 'End time must be after start time.')
                    else:
                        # Check for overlapping availability
                        existing = TutorAvailability.objects.filter(
                            tutor=tutor,
                            day_of_week=int(day_of_week),
                            is_active=True
                        ).filter(
                            Q(start_time__lt=end_dt) & Q(end_time__gt=start_dt)
                        )

                        if existing.exists():
                            messages.error(request, 'This time slot overlaps with existing availability.')
                        else:
                            TutorAvailability.objects.create(
                                tutor=tutor,
                                day_of_week=int(day_of_week),
                                start_time=start_dt,
                                end_time=end_dt,
                                is_active=True
                            )
                            messages.success(request, 'Availability slot added successfully!')
                except ValueError:
                    messages.error(request, 'Invalid time format.')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')

        elif action == 'delete':
            availability_id = request.POST.get('availability_id')
            try:
                availability = TutorAvailability.objects.get(id=availability_id, tutor=tutor)
                availability.delete()
                messages.success(request, 'Availability slot removed.')
            except TutorAvailability.DoesNotExist:
                messages.error(request, 'Availability slot not found.')

        elif action == 'toggle':
            availability_id = request.POST.get('availability_id')
            try:
                availability = TutorAvailability.objects.get(id=availability_id, tutor=tutor)
                availability.is_active = not availability.is_active
                availability.save()
                status = 'activated' if availability.is_active else 'deactivated'
                messages.success(request, f'Availability slot {status}.')
            except TutorAvailability.DoesNotExist:
                messages.error(request, 'Availability slot not found.')

        return redirect('tutor_schedule')

    # Display current availability
    availability_slots = TutorAvailability.objects.filter(tutor=tutor).order_by('day_of_week', 'start_time')

    # Group by day of week for display
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    grouped_availability = {}
    for slot in availability_slots:
        day_name = days[slot.day_of_week]
        if day_name not in grouped_availability:
            grouped_availability[day_name] = []
        grouped_availability[day_name].append(slot)

    context = {
        'availability_slots': availability_slots,
        'grouped_availability': grouped_availability,
        'days': days,
    }
    return render(request, 'tutor_schedule.html', context)


@login_required
@role_required('tutor')
def tutor_appointments(request):
    # View for tutors to see their booked sessions
    try:
        tutor = Tutor.objects.get(user_id=request.session['user_id'])

        # All bookings for specific tutor, sort by start time by default, we can probably modify this later for implementing different ways to sort
        bookings = Booking.objects.filter(tutor=tutor).select_related('location', 'course').prefetch_related('students__user').order_by('start_ts')

        context = {'bookings': bookings,}
    except Tutor.DoesNotExist:
        messages.error(request, 'Tutor not found.')
        context = {'bookings': []}
    return render(request, 'tutor_appointments.html', context)

@login_required
@role_required('tutor')
def accept_booking(request, booking_id):
    # View for tutors to accept booking requests
    try:
        tutor = Tutor.objects.get(user_id=request.session['user_id'])
        booking = Booking.objects.get(id=booking_id, tutor=tutor) # Only this booking, and only this tutor

        if booking.status != 'pending':
            messages.error(request, 'Booking already accepted/rejected')
            return redirect('tutor_appointments')

        # Check for confirmed bookings with same time
        conflicting_bookings = Booking.objects.filter(tutor=tutor, status='confirmed',).filter(Q(start_ts__lt=booking.end_ts) & Q(end_ts__gt=booking.start_ts))

        if conflicting_bookings.exists():
            messages.error(request, 'Time conflict with other bookings')
            return redirect('tutor_appointments')


        booking.status = 'confirmed'
        booking.save()

        send_booking_confirmed_email(booking)

        messages.success(request, 'Booking accepted')

    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
    except Tutor.DoesNotExist:
        messages.error(request, 'Tutor not found')

    return redirect('tutor_appointments')


@login_required
@role_required('tutor')
def reject_booking(request, booking_id):
    # View for tutors to reject booking requests
    try:
        tutor = Tutor.objects.get(user_id=request.session['user_id'])
        booking = Booking.objects.get(id=booking_id, tutor=tutor) # Only this booking, and only this tutor

        if booking.status != 'pending':
            messages.error(request, 'Booking already accepted/rejected')
            return redirect('tutor_appointments')

        booking.status = 'rejected'
        booking.save()
        messages.success(request, 'Booking rejected')


    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
    except Tutor.DoesNotExist:
        messages.error(request, 'Tutor not found')

    return redirect('tutor_appointments')


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
    # Students can select an available tutor and book
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Get the current student
    try:
        student = Student.objects.get(user_id=request.session['user_id'])
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('tutor_list')
    
    # All courses this tutor teaches
    tutor_courses = Course.objects.filter(tutors=tutor)
    # All available locations
    locations = Location.objects.all()
    # Tutor availability
    availability_slots = TutorAvailability.objects.filter(tutor=tutor, is_active=True).order_by('day_of_week', 'start_time')

    # Display by day of week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    grouped_availability = {}
    for slot in availability_slots:
        day_name = days[slot.day_of_week]
        if day_name not in grouped_availability:
            grouped_availability[day_name] = []
        grouped_availability[day_name].append(slot)


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
                'grouped_availability': grouped_availability,
            }
            return render(request, 'book_session.html', context)
        
        try:
            datetime_str = f"{start_date} {start_time}"
            start_ts = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            start_ts = timezone.make_aware(start_ts)

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
                    'grouped_availability': grouped_availability,
                }
                return render(request, 'book_session.html', context)
            
            # Check for time conflicts other bookings with tutor
            conflicting_bookings = Booking.objects.filter(
                tutor=tutor,
                status='confirmed',  # Only check confirmed appointments
            ).filter(
                Q(start_ts__lt=end_ts) & Q(end_ts__gt=start_ts)
            )

            # Validate with tutor availability
            day_of_week = start_ts.weekday()
            start_time_only = start_ts.time()
            end_time_only = end_ts.time()

            # Check availability for the specific date and time
            available_slots = TutorAvailability.objects.filter(tutor=tutor, day_of_week=day_of_week, is_active=True).filter(Q(start_time__lte=start_time_only) & Q(end_time__gte=end_time_only))

            if not available_slots.exists():
                messages.error(request,
                               'This tutor is not available at the selected time. Please choose a different time.')
                context = {
                    'tutor': tutor,
                    'tutor_courses': tutor_courses,
                    'locations': locations,
                    'today': date.today(),
                    'grouped_availability': grouped_availability,
                }
                return render(request, 'book_session.html', context)

            # Check if there is already a booking at the selected date and time
            if conflicting_bookings.exists():
                messages.error(request, 'This tutor is already booked during this time. Please choose a different time.')
                context = {
                    'tutor': tutor,
                    'tutor_courses': tutor_courses,
                    'locations': locations,
                    'today': date.today(),
                    'grouped_availability': grouped_availability,
                }
                return render(request, 'book_session.html', context)
            
            # Get course and location objects
            course = Course.objects.get(id=course_id) if course_id else None
            location = Location.objects.get(id=location_id)
            
            # Create booking
            booking = Booking.objects.create(
                tutor=tutor,
                location=location,
                course=course,
                start_ts=start_ts,
                end_ts=end_ts,
                status='pending' # Pending must be the default before a tutor approves booking
            )
            
            # Add student to the booking
            booking.students.add(student)

            # Send confirmation email
            send_booking_request_email(booking, student)
            
            messages.success(request, f'Request for session with {tutor.user.first_name} {tutor.user.last_name} sent for review') # Sprint 3: I reworded this to reflect the default status being pending instead of confirmed
            return redirect('booked_sessions')
            
        except ValueError as e:
            messages.error(request, 'Invalid date or time format.')
        except Course.DoesNotExist:
            messages.error(request, 'Selected course not found.')
        except Location.DoesNotExist:
            messages.error(request, 'Selected location not found.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    # Display tutor booking form
    context = {
        'tutor': tutor,
        'tutor_courses': tutor_courses,
        'locations': locations,
        'today': date.today(),
        'grouped_availability': grouped_availability,
        'has_availability': availability_slots.exists()
    }

    return render(request, 'book_session.html', context)