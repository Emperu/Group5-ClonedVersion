from django.contrib import admin
from .models import User, Student, Tutor, Course, Location, Booking
# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Tutor)
admin.site.register(Course)
admin.site.register(Location)
admin.site.register(Booking)