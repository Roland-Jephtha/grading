from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin


class CustomUserCreationForm(UserCreationForm, ModelAdmin):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'position', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm, ModelAdmin):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'position', 'password')


class CustomUserAdmin(UserAdmin, ModelAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ('username', 'email', 'position', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'position')
    ordering = ('username',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),  # Unfold picks this up
            'fields': ('username', 'email', 'position', 'password1', 'password2'),
        }),
    )
    fieldsets = (
        (None, {'fields': ('username', 'email', 'position', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )




class StudentProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'matric_number', 'department', 'level', 'semester')
    search_fields = ('full_name', 'matric_number')
    list_filter = ('department', 'level', 'semester')

class DepartmentAdmin(ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)

class LecturerProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'department', 'phone')
    search_fields = ('full_name', 'department__name')
    list_filter = ('department',)

class LevelAdmin(ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)

class CourseAdmin(ModelAdmin):
    list_display = ('title', 'code', 'department', 'level', 'semester', 'credit_unit')
    search_fields = ('title', 'code')
    list_filter = ('department', 'level', 'semester')

class GradeAdmin(ModelAdmin):
    list_display = ('student', 'course', 'score', 'grade', 'status')
    search_fields = ('student__full_name', 'course__title', 'course__code')
    list_filter = ('status', 'course', 'student')

class ResultAdmin(ModelAdmin):
    list_display = ('student', 'matric_number', 'department', 'level', 'semester', 'gpa', 'remark', 'status', 'hod_status')
    search_fields = ('student__full_name', 'matric_number')
    list_filter = ('department', 'level', 'semester', 'status', 'remark')

class SemesterAdmin(ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)

class HodProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'department', 'phone')
    search_fields = ('full_name', 'department__name')
    list_filter = ('department',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(LecturerProfile, LecturerProfileAdmin)
admin.site.register(Level, LevelAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(HodProfile, HodProfileAdmin)





site_title = "PTI Grading Admin"
site_header = "Manage PTI Grading Admin"
index_title = "PTI Admin Dashboard"