from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class CustomUser(AbstractUser):

    POSITION_CHOICES = [
        ("student", "Student"),
        ("lecturer", "Lecturer"),
        ("hod", "Head of Department"),
        ("admin", "Lecturer")
    ]
    email = models.EmailField(unique=True, null=True)
    username =  models.CharField(max_length=15, blank=True, null=True)


    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        default="student",
        help_text=_("User's position in the institution"),
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']





class Department(models.Model):
    name = models.CharField(max_length=100, null = True)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
    




class LecturerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    phone = models.CharField(max_length=255, null=True)
    bio = models.TextField(null=True)
    image = models.ImageField(upload_to='profile-images', null=True)
    gender =  models.CharField(max_length=10, blank=True, null=True)



    def __str__(self):
        return f" Username: {self.user.username} - Department: {self.department}"



class HodProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    phone = models.CharField(max_length=255, null=True)
    bio = models.TextField(null=True)
    image = models.ImageField(upload_to='profile-images', null=True)
    gender =  models.CharField(max_length=10, blank=True, null=True)



    def __str__(self):
        return f" Username: {self.user.username} - Department: {self.department}"




class Level(models.Model):
    name = models.CharField(max_length=100, null = True)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
    


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255, null=True)
    matric_number = models.CharField(max_length=255, unique=True, blank = True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    phone = models.CharField(max_length=255,null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='profile-images', null=True)
    gender =  models.CharField(max_length=10, blank=True, null=True)


    def __str__(self):
        return f"{self.user.username}  - {self.matric_number}"



class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100, null = True)
    code = models.CharField(max_length=100, null = True)
    credit_unit = models.CharField(max_length=100, null= True)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title
    


class Semester(models.Model):
    name = models.CharField(max_length=100, null = True)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
    




class Grade(models.Model):
    GRADE_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted to Department'),
        ('approved', 'Approved by Admin'),
]
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.CASCADE, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    score = models.IntegerField(null=True)
    grade_point = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=GRADE_STATUS, default='draft')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'semester', 'level', 'department')  # Ensure uniqueness

    def __str__(self):
        return f"{self.student} - {self.course} - {self.semester} - {self.grade}"

    def calculate_grade_point(self):
        """Calculate grade point based on letter grade and credit unit"""
        # Grade point mapping
        grade_points = {
            'A': 4.0,
            'AB': 3.5,
            'B': 3.0,
            'BC': 2.5,
            'C': 2.0,
            'D': 1.5,
            'E': 1.0,
            'F': 0.0
        }

        if not self.grade or not self.course or not self.course.credit_unit:
            return 0

        # Get grade point for the letter grade
        letter_grade = self.grade.upper().strip()
        base_grade_point = grade_points.get(letter_grade, 0.0)

        # Get credit unit
        try:
            credit_unit = int(self.course.credit_unit)
        except (ValueError, TypeError):
            credit_unit = 0

        # Calculate total grade point (grade point × credit unit)
        total_grade_point = base_grade_point * credit_unit

        return total_grade_point

    def save(self, *args, **kwargs):
        """Auto-calculate grade and grade point when saving"""
        # Assign grade based on score
        if self.score is not None:
            score = self.score
            if score >= 75:
                self.grade = 'A'
            elif score >= 70:
                self.grade = 'AB'
            elif score >= 65:
                self.grade = 'B'
            elif score >= 60:
                self.grade = 'BC'
            elif score >= 55:
                self.grade = 'C'
            elif score >= 50:
                self.grade = 'D'
            elif score >= 40:
                self.grade = 'E'
            else:
                self.grade = 'F'
        # Calculate and set grade point
        self.grade_point = self.calculate_grade_point()
        super().save(*args, **kwargs)
    




class Result(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    matric_number = models.CharField(max_length=255)
    grade_score = models.ManyToManyField(Grade, blank=True)  # Restored for template rendering
    tgp = models.FloatField(null=True)
    gpa = models.FloatField(null=True)
    tcu = models.IntegerField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], default='draft', null=True)

    
    hod_status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('publish', 'Publish'),
    ], default='draft', null=True)


    remark = models.CharField(max_length=20, choices=[
        ('co', 'co'),
        ('withdrawn', 'withdrawn'),
        ('passed', 'passed'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], null=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.first_name} {self.student.user.last_name} - {self.matric_number} - GPA: {self.gpa}"

    def get_grades(self):
        """Return all grades for this result's context."""
        return Grade.objects.filter(
            student=self.student,
            department=self.department,
            level=self.level,
            semester=self.semester,
            status='approved'
        )

    def calculate_gpa(self):
        grades = self.get_grades()
        total_points = 0
        total_units = 0
        for grade in grades:
            try:
                credit_unit = int(grade.course.credit_unit)
            except (ValueError, TypeError):
                credit_unit = 0
            total_points += grade.calculate_grade_point()
            total_units += credit_unit
        if total_units > 0:
            self.gpa = total_points / total_units
            self.tgp = total_points
            self.tcu = total_units
        else:
            self.gpa = 0
            self.tgp = 0
            self.tcu = 0
        self.save()




class Cummulative_Result(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, null = True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    result = models.ManyToManyField('Result', blank= True)

    gpa = models.FloatField(null=True)
    tcu = models.IntegerField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], default='draft', null=True)

    
    hod_status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('publish', 'Publish'),
    ], default='draft', null=True)


    remark = models.CharField(max_length=20, choices=[
        ('co', 'co'),
        ('withdrawn', 'withdrawn'),
        ('passed', 'passed'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], null=True)

    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.student.full_name}====={self.gpa}'