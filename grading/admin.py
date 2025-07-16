from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from django.http import HttpResponse
import csv
try:
    import tablib
    HAS_TABLIB = True
except ImportError:
    HAS_TABLIB = False



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
    list_display = (
        'student', 'matric_number', 'department', 'level', 'semester',
        'courses_and_grades', 'tcp', 'cgpa', 'gpa', 'remark', 'status', 'hod_status'
    )
    search_fields = ('student__full_name', 'matric_number')
    list_filter = ('department', 'level', 'semester', 'status', 'remark')

    actions = [
        'mark_as_approved', 'mark_as_draft', 'mark_as_published', 'mark_as_unpublished',
        'export_as_csv', 
    ]

    def courses_and_grades(self, obj):
        return ", ".join([
            f"{g.course.code} ({g.score}={g.grade})" for g in obj.grade_score.all()
        ])
    courses_and_grades.short_description = "Courses, Scores & Grades"

    def tcp(self, obj):
        return getattr(obj, 'tgp', '')
    tcp.short_description = "TCP"

    def cgpa(self, obj):
        return getattr(obj, 'cgpa', '')
    cgpa.short_description = "CGPA"

    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} result(s) marked as approved.")
    mark_as_approved.short_description = "Mark selected results as Approved"

    def mark_as_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} result(s) marked as draft.")
    mark_as_draft.short_description = "Mark selected results as Draft"

    def mark_as_published(self, request, queryset):
        updated = queryset.update(hod_status='publish')
        self.message_user(request, f"{updated} result(s) marked as Published.")
    mark_as_published.short_description = "Mark selected results as Published (HOD)"

    def mark_as_unpublished(self, request, queryset):
        updated = queryset.update(hod_status='draft')
        self.message_user(request, f"{updated} result(s) marked as Unpublished.")
    mark_as_unpublished.short_description = "Mark selected results as Unpublished (HOD)"


    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [
            'student', 'matric_number', 'department', 'level', 'semester',
            'courses_and_grades', 'tcp',  'gpa', 'remark'
        ]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=results.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([
                str(obj.student), obj.matric_number, str(obj.department), str(obj.level), str(obj.semester),
                self.courses_and_grades(obj), self.tcp(obj),  obj.gpa, obj.remark
            ])
        return response
    export_as_csv.short_description = "Export Selected as CSV"







class SemesterAdmin(ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)

class HodProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'department', 'phone')
    search_fields = ('full_name', 'department__name')
    list_filter = ('department',)


class Cum_ResultAdmin(ModelAdmin):
    list_display = ('student',  'department', 'level', 'semester',  'cumulative_tcu', 'cumulative_gpa', 'remark' )
    search_fields = ('student__full_name', 'student__matric_number')
    list_filter = ('department', 'level', 'semester', 'status', 'hod_status')
    actions = ['export_cumulative_as_csv', 'mark_as_approved', 'mark_as_published']

    def export_cumulative_as_csv(self, request, queryset):
        """Export selected cumulative results to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cumulative_results.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Matric Number', 'Department', 'Level', 'Semester',
            'Academic Year', 'Current GPA', 'Yearly CGPA', 'Overall CGPA',
            'TCU', 'Cumulative TCU', 'Remark', 'Admin Status', 'HOD Status', 'Created Date'
        ])

        for obj in queryset:
            writer.writerow([
                str(obj.student.full_name),
                obj.student.matric_number,
                str(obj.department.name),
                str(obj.level.name),
                str(obj.semester.name),
                obj.academic_year or 'N/A',
                f"{obj.current_gpa:.3f}" if obj.current_gpa else '0.000',
                f"{obj.yearly_cumulative_gpa:.3f}" if obj.yearly_cumulative_gpa else '0.000',
                f"{obj.overall_cumulative_gpa:.3f}" if obj.overall_cumulative_gpa else '0.000',
                obj.tcu or 0,
                obj.cumulative_tcu or 0,
                obj.get_remark_display() if obj.remark else 'N/A',
                obj.status.title(),
                obj.hod_status.title(),
                obj.created.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_cumulative_as_csv.short_description = "Export Selected Cumulative Results as CSV"

    def mark_as_approved(self, request, queryset):
        """Mark selected cumulative results as approved (Admin)"""
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} cumulative result(s) marked as approved.")
    mark_as_approved.short_description = "Mark selected as Approved (Admin)"

    def mark_as_published(self, request, queryset):
        """Mark selected cumulative results as published (HOD)"""
        updated = queryset.update(hod_status='published')
        self.message_user(request, f"{updated} cumulative result(s) marked as published.")
    mark_as_published.short_description = "Mark selected as Published (HOD)"

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
admin.site.register(Cummulative_Result, Cum_ResultAdmin)




site_title = "PTI Grading Admin"
site_header = "Manage PTI Grading Admin"
index_title = "PTI Admin Dashboard"