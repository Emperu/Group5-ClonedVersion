from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.hashers import make_password, check_password



# Base User Model

# ---------------------------------------------------------------------------------------------------------------------------
# Django automatically sets "id = models.AutoField(primary_key=True)", meaning there is no need for us to manually set a user ID
# ---------------------------------------------------------------------------------------------------------------------------

class User(models.Model):

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.CharField(max_length=100, unique=True)
    nuid = models.CharField(max_length=8, unique=True)  # Add NUID field
    password = models.CharField(max_length=128)  # Add password field
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('tutor', 'Tutor'), ('admin', 'Admin')]) # Case insensitive

    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if the provided password matches"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# Student Model

# ---------------------------------------------------------------------------------------------------------------------------
# I know in our data model plan from Sprint 0 we planned on having a Student ID as the PK for the student, I don't really remember the exact feedback we got but were we still planning on doing this?
# At the moment I have not included a StudentID in the data model since each user already has a User ID
# ---------------------------------------------------------------------------------------------------------------------------
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Student must be a user
    major = models.CharField(max_length=80)
    class_year = models.IntegerField()

    def __str__(self):
        return self.user.first_name


# Tutor Model

# ---------------------------------------------------------------------------------------------------------------------------
# Same question regarding our plans for a Tutor ID; is this still something we want to go forward with?
# ---------------------------------------------------------------------------------------------------------------------------

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Tutor must be a user
    bio = models.TextField()

    def __str__(self):
        return self.user.first_name



# Course Model

class Course(models.Model):
    course_number = models.CharField(max_length=10)
    title = models.CharField(max_length=50)
    description = models.TextField()
    semester = models.CharField(max_length=20)

    students = models.ManyToManyField(Student, related_name='enrolled_courses')
    tutors = models.ManyToManyField(Tutor, related_name='taught_courses')

    def __str__(self):
        return f"{self.course_number}: {self.title}"



# Location Model

class Location(models.Model):
    location_name = models.CharField(max_length=120)
    modality = models.CharField(max_length=10)
    join_link = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.location_name



# Booking Model

class Booking(models.Model):
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)
    start_ts = models.DateTimeField()
    end_ts = models.DateTimeField()

    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name='bookings')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id} with {self.tutor.user.first_name}"
