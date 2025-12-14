from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

# Confirmation emails for when a booking is REQUESTED
def send_booking_request_email(booking, student):
    # Student Email
    subject_student = f'Booking Request Sent - {booking.start_ts.strftime("%B %d, %y")}'

    context_student = {
        'booking': booking,
        'tutor': booking.tutor,
        'student': student,
        'recipient': 'student',
    }

    message_student = render_to_string('emails/booking_request.txt', context_student)
    html_message_student = render_to_string('emails/booking_request.html', context_student)

    send_mail(
        subject=subject_student,
        message=message_student,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[student.user.email],
        html_message=html_message_student,
        fail_silently=False,
    )

    # Tutor Email
    subject_tutor = f'New Appointment Request - {booking.start_ts.strftime("%B %d, %Y at %I:%M %p")}'

    context_tutor = {
        'booking': booking,
        'tutor': booking.tutor,
        'student': student,
        'recipient': 'tutor',
    }

    message_tutor = render_to_string('emails/booking_request.txt', context_tutor)
    html_message_tutor = render_to_string('emails/booking_request.html', context_tutor)

    send_mail(
        subject=subject_tutor,
        message=message_tutor,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[booking.tutor.user.email],
        html_message=html_message_tutor,
        fail_silently=False,
    )

# Confirmation emails for when a booking is APPROVED
def send_booking_confirmed_email(booking):
    # Tutor Email
    subject_tutor = f'Booking Confirmed - {booking.start_ts.strftime("%B %d, %Y")}'

    students_list = []
    student_emails = []
    for student in booking.students.all():
        students_list.append(f"{student.user.first_name} {student.user.last_name}")
        student_emails.append(student.user.email)

    context_tutor = {
        'booking': booking,
        'tutor': booking.tutor,
        'students_list': students_list,
        'recipient': 'tutor',
    }

    message_tutor = render_to_string('emails/booking_confirmed.txt', context_tutor)
    html_message_tutor = render_to_string('emails/booking_confirmed.html', context_tutor)

    send_mail(
        subject=subject_tutor,
        message=message_tutor,
        from_email=None,
        recipient_list=[booking.tutor.user.email],
        html_message=html_message_tutor,
        fail_silently=False,
    )

    # Student Email
    subject_student = f'Booking Confirmed - {booking.start_ts.strftime("%B %d, %Y")}'

    for student in booking.students.all():
        context_student = {
            'booking': booking,
            'tutor': booking.tutor,
            'student': student,
            'recipient': 'student',
        }

        message_student = render_to_string('emails/booking_confirmed.txt', context_student)
        html_message_student = render_to_string('emails/booking_confirmed.html', context_student)

        send_mail(
            subject=subject_student,
            message=message_student,
            from_email=None,
            recipient_list=[student.user.email],
            html_message=html_message_student,
            fail_silently=False,
        )