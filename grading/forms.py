from django import forms
from django.db.models import Q
from .models import Grade, StudentProfile, Course, Department, Level, Semester, LecturerProfile, HodProfile, CustomUser

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        exclude = ['lecturer', 'created', 'grade', 'status']

    def __init__(self, *args, **kwargs):
        # Get additional filtering values passed from the view
        selected_student = kwargs.pop('selected_student', None)
        selected_department = kwargs.pop('selected_department', None)
        selected_level = kwargs.pop('selected_level', None)
        selected_semester = kwargs.pop('selected_semester', None)

        super(GradeForm, self).__init__(*args, **kwargs)

        # Apply consistent styling
        small_class = 'form-control form-control-sm'
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': small_class})

        # Filter students
        if selected_student:
            self.fields['student'].queryset = StudentProfile.objects.filter(id=selected_student)
        else:
            self.fields['student'].queryset = StudentProfile.objects.none()

        # Filter courses
        if selected_department and selected_level and selected_semester:
            try:
                general_dept = Department.objects.get(name__iexact='general')
            except Department.DoesNotExist:
                general_dept = None

            course_filter = Q(level=selected_level, semester=selected_semester) & (
                Q(department=selected_department) |
                Q(department=general_dept) if general_dept else Q(department=selected_department)
            )

            self.fields['course'].queryset = Course.objects.filter(course_filter)
        else:
            self.fields['course'].queryset = Course.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)

        score = instance.score
        if score >= 75:
            instance.grade = 'A'
        elif score >= 65:
            instance.grade = 'B'
        elif score >= 60:
            instance.grade = 'BC'
        elif score >= 55:
            instance.grade = 'C'
        elif score >= 50:
            instance.grade = 'D'
        elif score >= 40:
            instance.grade = 'E'
        else:
            instance.grade = 'F'

        if commit:
            instance.save()
        return instance


# Profile Update Forms
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'matric_number', 'phone', 'gender', 'image']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'matric_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your matriculation number'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Select Gender'),
                ('male', 'Male'),
                ('female', 'Female'),
                ('other', 'Other')
            ]),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for updates
        for field in self.fields.values():
            field.required = False


class LecturerProfileForm(forms.ModelForm):
    class Meta:
        model = LecturerProfile
        fields = ['full_name', 'phone', 'bio', 'gender', 'image']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your bio',
                'rows': 4
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Select Gender'),
                ('male', 'Male'),
                ('female', 'Female'),
                ('other', 'Other')
            ]),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for updates
        for field in self.fields.values():
            field.required = False


class HodProfileForm(forms.ModelForm):
    class Meta:
        model = HodProfile
        fields = ['full_name', 'phone', 'bio', 'gender', 'image']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your bio',
                'rows': 4
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Select Gender'),
                ('male', 'Male'),
                ('female', 'Female'),
                ('other', 'Other')
            ]),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for updates
        for field in self.fields.values():
            field.required = False


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'readonly': 'readonly'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email readonly and not required for updates
        self.fields['email'].required = False
        self.fields['email'].widget.attrs['readonly'] = True
