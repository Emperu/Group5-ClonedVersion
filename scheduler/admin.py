from django.contrib import admin
from django import forms
from .models import User, Student, Tutor, Course, Location, Booking


class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Enter a password (will be hashed automatically)"
    )

    class Meta:
        model = User
        fields = '__all__'

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash the password before saving
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ['nuid', 'first_name', 'last_name', 'email', 'role']
    list_filter = ['role']
    search_fields = ['nuid', 'first_name', 'last_name', 'email']


# Register models
admin.site.register(User, UserAdmin)
admin.site.register(Student)
admin.site.register(Tutor)
admin.site.register(Course)
admin.site.register(Location)
admin.site.register(Booking)