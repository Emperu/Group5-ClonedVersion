import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MavTutoring.settings')
django.setup()

from django.contrib.auth import get_user_model
from scheduler.models import User as SchedulerUser

def create_admin():
    nuid = "00000000"
    password = "password123"
    email = "admin@mavtutoring.com"
    first_name = "Admin"
    last_name = "User"

    print(f"Setting up admin with NUID: {nuid}...")

    # 1. Create or Update Scheduler User (Your Custom App User)
    try:
        s_user = SchedulerUser.objects.get(nuid=nuid)
        s_user.set_password(password)
        s_user.role = 'admin'
        s_user.first_name = first_name
        s_user.last_name = last_name
        s_user.save()
        print(f" - Updated existing Scheduler User.")
    except SchedulerUser.DoesNotExist:
        s_user = SchedulerUser(
            nuid=nuid,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='admin'
        )
        s_user.set_password(password)
        s_user.save()
        print(f" - Created new Scheduler User.")

    # 2. Create or Update Django Auth User (For Django Admin Panel)
    # We use the NUID as the username for the Django admin user
    User = get_user_model()
    try:
        d_user = User.objects.get(username=nuid)
        d_user.set_password(password)
        d_user.email = email
        d_user.is_staff = True
        d_user.is_superuser = True
        d_user.save()
        print(f" - Updated existing Django Superuser.")
    except User.DoesNotExist:
        User.objects.create_superuser(username=nuid, email=email, password=password)
        print(f" - Created new Django Superuser.")

    print("Done! You can now log in with these credentials.")

if __name__ == '__main__':
    create_admin()