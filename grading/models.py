from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP

# Create your models here.

class CustomUser(AbstractUser):

    POSITION_CHOICES = [
        ("student", "Student"),
        ("lecturer", "Lecturer"),
        ("hod", "Head of Department"),
        ("admin", "Lecturer")
    ]
    email = models.EmailField(unique=True, null=True)
    username =  models.CharField(max_length=30, blank=True, null=True)


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
            'B': 3.25,
            'BC': 3.00,
            'C': 2.75,
            'CD': 2.5,
            'D': 2.25,
            'E': 2.0,
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
                self.grade = 'CD'
            elif score >= 45:
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
    tgp = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    gpa = models.DecimalField(max_digits=5, decimal_places=4, null=True)
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
        self.save(from_calculate_gpa=True)

    def save(self, *args, **kwargs):
        """Override save to create cumulative results automatically"""
        # Avoid infinite recursion from calculate_gpa
        if kwargs.pop('from_calculate_gpa', False):
            return super().save(*args, **kwargs)

        # Normal save
        result = super().save(*args, **kwargs)

        # Create or update cumulative result after saving
        if self.pk:  # Only if the result has been saved (has primary key)
            # Import here to avoid circular import
            from .models import Cummulative_Result
            Cummulative_Result.create_cumulative_result(self)

        return result


class Cummulative_Result(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    result = models.ManyToManyField('Result', blank=True)

    # Current semester/level GPA
    current_gpa = models.DecimalField(max_digits=5, decimal_places=4, null=True, help_text="GPA for current semester")

    # Cumulative GPA calculations
    cumulative_gpa = models.DecimalField(max_digits=5, decimal_places=4, null=True, help_text="Cumulative GPA up to this point")
    yearly_cumulative_gpa = models.DecimalField(max_digits=5, decimal_places=4, null=True, help_text="Cumulative GPA for the academic year")
    overall_cumulative_gpa = models.DecimalField(max_digits=5, decimal_places=4, null=True, help_text="Overall cumulative GPA across all years")

    # Credit units
    tcu = models.IntegerField(null=True, help_text="Total Credit Units")
    cumulative_tcu = models.IntegerField(null=True, help_text="Cumulative Total Credit Units")

    # Academic year tracking
    academic_year = models.CharField(max_length=10, null=True, help_text="e.g., Year 1, Year 2")

    # Admin approval status (same as regular results)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], default='draft', help_text="Admin approval status")

    # HOD approval status (same as regular results)
    hod_status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('published', 'Published'),
    ], default='draft', help_text="HOD approval status")

    remark = models.CharField(max_length=20, choices=[
        ('distinction', 'Distinction'),
        ('upper_credit', 'Upper Credit'),
        ('lower_credit', 'Lower Credit'),
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('co', 'Carry Over'),
        ('withdrawn', 'Withdrawn'),
    ], null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'department', 'level', 'semester']
        ordering = ['-created']

    def __str__(self):
        return f'{self.student.full_name} - {self.level.name} {self.semester.name} - CGPA: {self.cumulative_gpa}'

    def calculate_cumulative_gpa(self):
        """Calculate cumulative GPA based on academic progression - Only for second semester"""
        try:
            # Only calculate cumulative for second semester
            if 'second' not in self.semester.name.lower() and '2' not in self.semester.name:
                print(f"Skipping cumulative calculation for {self.semester.name} - not second semester")
                return False

            # Determine academic year and program based on level
            level_name = self.level.name.upper()

            if 'ND1' in level_name:
                self.academic_year = 'ND1'
                program_type = 'ND'
                year_number = 1
            elif 'ND2' in level_name:
                self.academic_year = 'ND2'
                program_type = 'ND'
                year_number = 2
            elif 'HND1' in level_name:
                self.academic_year = 'HND1'
                program_type = 'HND'
                year_number = 1
            elif 'HND2' in level_name:
                self.academic_year = 'HND2'
                program_type = 'HND'
                year_number = 2
            else:
                # For degree programs (100, 200, 300, 400 levels)
                if '100' in level_name:
                    self.academic_year = 'Year 1'
                    program_type = 'DEGREE'
                    year_number = 1
                elif '200' in level_name:
                    self.academic_year = 'Year 2'
                    program_type = 'DEGREE'
                    year_number = 2
                elif '300' in level_name:
                    self.academic_year = 'Year 3'
                    program_type = 'DEGREE'
                    year_number = 3
                elif '400' in level_name:
                    self.academic_year = 'Year 4'
                    program_type = 'DEGREE'
                    year_number = 4
                else:
                    self.academic_year = 'Year 1'
                    program_type = 'DEGREE'
                    year_number = 1

            # Get current semester GPA
            if hasattr(self, 'current_gpa') and self.current_gpa:
                current_semester_gpa = self.current_gpa
            else:
                # Get GPA from related Result if not set
                related_result = Result.objects.filter(
                    student=self.student,
                    department=self.department,
                    level=self.level,
                    semester=self.semester
                ).first()
                current_semester_gpa = related_result.gpa if related_result else 0.0
                self.current_gpa = current_semester_gpa

            # Get first semester result for the SAME LEVEL (same academic year)
            # Try multiple patterns to find first semester
            first_semester_result = None

            # Pattern 1: Contains 'first'
            first_semester_result = Result.objects.filter(
                student=self.student,
                department=self.department,
                level=self.level,  # Same level (ND1, ND2, HND1, HND2)
                semester__name__icontains='first'
            ).first()

            # Pattern 2: Contains '1st' or 'IST'
            if not first_semester_result:
                first_semester_result = Result.objects.filter(
                    student=self.student,
                    department=self.department,
                    level=self.level,
                ).filter(
                    Q(semester__name__icontains='1st') |
                    Q(semester__name__icontains='IST')
                ).exclude(semester=self.semester).first()

            # Pattern 3: Just contains '1' (but not current semester)
            if not first_semester_result:
                first_semester_result = Result.objects.filter(
                    student=self.student,
                    department=self.department,
                    level=self.level,
                    semester__name__icontains='1'
                ).exclude(semester=self.semester).first()

            # Get the GPAs for calculation (using Decimal for exact arithmetic)
            first_semester_gpa = Decimal(str(first_semester_result.gpa)) if first_semester_result else Decimal('0.0')
            second_semester_gpa = Decimal(str(current_semester_gpa))  # This is the second semester

            # Debug: Print what we found
            print(f"\n🔍 DEBUG: Cumulative GPA Calculation for {self.student.full_name} - {self.level.name}")
            print(f"   Looking for first semester result...")
            if first_semester_result:
                print(f"   ✅ Found first semester: {first_semester_result.semester.name} - GPA: {first_semester_gpa:.2f}")
            else:
                print(f"   ❌ No first semester result found for level: {self.level.name}")
                # Let's see what semesters exist for this student and level
                all_semesters = Result.objects.filter(
                    student=self.student,
                    department=self.department,
                    level=self.level
                ).values_list('semester__name', flat=True)
                print(f"   Available semesters for {self.level.name}: {list(all_semesters)}")

            print(f"   Second semester: {self.semester.name} - GPA: {second_semester_gpa:.2f}")

            # Calculate yearly cumulative GPA for THIS SPECIFIC YEAR (using exact Decimal arithmetic)
            # Example: For ND1 - take ND1 First + ND1 Second, divide by 2
            # Example: For HND2 - take HND2 First + HND2 Second, divide by 2
            if first_semester_result and first_semester_gpa > 0:
                self.yearly_cumulative_gpa = (first_semester_gpa + second_semester_gpa) / Decimal('2')
                print(f"   🧮 Calculation: ({first_semester_gpa:.2f} + {second_semester_gpa:.2f}) ÷ 2 = {self.yearly_cumulative_gpa:.2f}")
                print(f"   ✅ Yearly CGPA for {self.academic_year}: {self.yearly_cumulative_gpa:.2f}")
            else:
                # If no first semester found, use only second semester
                self.yearly_cumulative_gpa = second_semester_gpa
                print(f"   ⚠️  Warning: No first semester found for {self.academic_year}")
                print(f"   Using second semester only: {second_semester_gpa:.2f}")
                print(f"   This means the cumulative calculation is incomplete!")

            # Calculate overall cumulative GPA based on academic progression
            if year_number == 1:
                # First year (ND1, HND1) - overall cumulative is same as yearly
                self.overall_cumulative_gpa = self.yearly_cumulative_gpa
                print(f"First year - Overall CGPA = Yearly CGPA = {self.overall_cumulative_gpa:.2f}")
            else:
                # Second year or higher - get previous year's cumulative
                if program_type == 'ND':
                    # For ND2, get ND1 cumulative result
                    previous_level_name = 'ND1'
                elif program_type == 'HND':
                    # For HND2, get HND1 cumulative result
                    previous_level_name = 'HND1'
                else:
                    # For degree programs (200, 300, 400 levels)
                    previous_year = year_number - 1
                    previous_level_name = f'{previous_year}00'

                # Get previous year's cumulative result (second semester)
                previous_cumulative = Cummulative_Result.objects.filter(
                    student=self.student,
                    department=self.department,
                    level__name__icontains=previous_level_name,
                    semester__name__icontains='second'
                ).first()

                if previous_cumulative and previous_cumulative.yearly_cumulative_gpa:
                    # Calculate overall: (Previous Year CGPA + Current Year CGPA) ÷ 2 (using exact Decimal arithmetic)
                    previous_year_cgpa = Decimal(str(previous_cumulative.yearly_cumulative_gpa))
                    current_year_cgpa = Decimal(str(self.yearly_cumulative_gpa))
                    self.overall_cumulative_gpa = (previous_year_cgpa + current_year_cgpa) / Decimal('2')

                    print(f"Overall CGPA calculation:")
                    print(f"  Previous Year ({previous_level_name}) CGPA: {previous_year_cgpa:.2f}")
                    print(f"  Current Year ({self.academic_year}) CGPA: {current_year_cgpa:.2f}")
                    print(f"  Overall CGPA: ({previous_year_cgpa:.2f} + {current_year_cgpa:.2f}) ÷ 2 = {self.overall_cumulative_gpa:.2f}")
                else:
                    # If no previous cumulative found, use current year only
                    self.overall_cumulative_gpa = self.yearly_cumulative_gpa
                    print(f"No previous year found - Overall CGPA = Current Year CGPA = {self.overall_cumulative_gpa:.2f}")

            # Set the main cumulative_gpa field to the overall cumulative
            self.cumulative_gpa = self.overall_cumulative_gpa

            # Calculate cumulative TCU
            all_results = Result.objects.filter(
                student=self.student,
                department=self.department,
                status='approved'
            )
            total_tcu = sum([result.tcu for result in all_results if result.tcu]) or 0
            self.cumulative_tcu = total_tcu

            # Calculate remark based on cumulative GPA
            self.calculate_remark()

            print(f"Cumulative GPA calculated for {self.student.full_name} - {self.level.name} {self.semester.name}")
            print(f"First Semester GPA: {first_semester_gpa:.2f}")
            print(f"Second Semester GPA: {current_semester_gpa:.2f}")
            print(f"Yearly Cumulative: {self.yearly_cumulative_gpa:.2f}")
            print(f"Overall Cumulative: {self.overall_cumulative_gpa:.2f}")

            return True

        except Exception as e:
            print(f"Error calculating cumulative GPA: {str(e)}")
            return False

    def calculate_remark(self):
        """Calculate remark based on cumulative GPA"""
        if not self.cumulative_gpa:
            self.remark = 'fail'
            return

        gpa = float(self.cumulative_gpa)

        if gpa >= 3.50:
            self.remark = 'distinction'
        elif gpa >= 3.00:
            self.remark = 'upper_credit'
        elif gpa >= 2.50:
            self.remark = 'lower_credit'
        elif gpa >= 2.00:
            self.remark = 'pass'
        else:
            self.remark = 'fail'

    def get_remark_display_with_range(self):
        """Get remark display with GPA range"""
        remark_ranges = {
            'distinction': 'Distinction (3.50 - 4.00)',
            'upper_credit': 'Upper Credit (3.00 - 3.49)',
            'lower_credit': 'Lower Credit (2.50 - 2.99)',
            'pass': 'Pass (2.00 - 2.49)',
            'fail': 'Fail (Below 2.00)',
            'co': 'Carry Over',
            'withdrawn': 'Withdrawn',
        }
        return remark_ranges.get(self.remark, self.remark or 'Unknown')

    def get_calculation_details(self):
        """Get details of how the cumulative GPA was calculated for the SAME ACADEMIC YEAR"""
        results = self.result.all().order_by('semester__name')

        if results.count() == 2:
            # Find first and second semester results
            first_sem = None
            second_sem = None

            for result in results:
                if 'first' in result.semester.name.lower() or '1' in result.semester.name:
                    first_sem = result
                elif 'second' in result.semester.name.lower() or '2' in result.semester.name:
                    second_sem = result

            if first_sem and second_sem:
                return {
                    'academic_year': self.academic_year,
                    'first_semester': {
                        'name': first_sem.semester.name,
                        'gpa': first_sem.gpa
                    },
                    'second_semester': {
                        'name': second_sem.semester.name,
                        'gpa': second_sem.gpa
                    },
                    'yearly_cgpa': self.yearly_cumulative_gpa,
                    'calculation': f"({first_sem.gpa:.2f} + {second_sem.gpa:.2f}) ÷ 2 = {self.yearly_cumulative_gpa:.2f}",
                    'calculation_formula': f"{self.academic_year} CGPA = ({self.academic_year} First Sem + {self.academic_year} Second Sem) ÷ 2",
                    'has_both_semesters': True
                }
            else:
                # Fallback if we can't identify first/second
                first_result = results.first()
                second_result = results.last()
                return {
                    'academic_year': self.academic_year,
                    'first_semester': {
                        'name': first_result.semester.name,
                        'gpa': first_result.gpa
                    },
                    'second_semester': {
                        'name': second_result.semester.name,
                        'gpa': second_result.gpa
                    },
                    'yearly_cgpa': self.yearly_cumulative_gpa,
                    'calculation': f"({first_result.gpa:.2f} + {second_result.gpa:.2f}) ÷ 2 = {self.yearly_cumulative_gpa:.2f}",
                    'has_both_semesters': True
                }
        elif results.count() == 1:
            result = results.first()
            return {
                'academic_year': self.academic_year,
                'semester': result.semester.name,
                'gpa': result.gpa,
                'yearly_cgpa': self.yearly_cumulative_gpa or result.gpa,
                'calculation': f"Only {result.semester.name} available: {result.gpa:.2f}",
                'has_both_semesters': False
            }
        else:
            return {
                'academic_year': self.academic_year,
                'calculation': 'No semester results linked',
                'yearly_cgpa': self.yearly_cumulative_gpa or 0.0,
                'has_both_semesters': False
            }

    def save(self, *args, **kwargs):
        """Override save to automatically calculate cumulative GPA"""
        super().save(*args, **kwargs)

        # Calculate cumulative GPA after saving
        if self.calculate_cumulative_gpa():
            # Save again with updated cumulative values
            super().save(update_fields=['cumulative_gpa', 'yearly_cumulative_gpa', 'overall_cumulative_gpa', 'academic_year', 'cumulative_tcu', 'remark'])

    @classmethod
    def create_cumulative_result(cls, result_instance):
        """Create or update cumulative result when a regular result is created/updated - Only for second semester"""
        try:
            # Only create cumulative results for second semester
            semester_name = result_instance.semester.name.lower()
            if 'second' not in semester_name and '2' not in semester_name:
                print(f"Skipping cumulative result creation for {result_instance.semester.name} - not second semester")
                return None

            # Get first semester result for the SAME ACADEMIC YEAR (same level)
            # This ensures we're combining results from the same year
            # Example: ND1 First + ND1 Second, HND2 First + HND2 Second
            first_semester_result = None

            # Pattern 1: Contains 'first'
            first_semester_result = Result.objects.filter(
                student=result_instance.student,
                department=result_instance.department,
                level=result_instance.level,  # SAME LEVEL = SAME ACADEMIC YEAR
                semester__name__icontains='first'
            ).first()

            # Pattern 2: Contains '1st' or 'IST'
            if not first_semester_result:
                first_semester_result = Result.objects.filter(
                    student=result_instance.student,
                    department=result_instance.department,
                    level=result_instance.level,
                ).filter(
                    Q(semester__name__icontains='1st') |
                    Q(semester__name__icontains='IST')
                ).exclude(semester=result_instance.semester).first()

            # Pattern 3: Just contains '1' (but not current semester)
            if not first_semester_result:
                first_semester_result = Result.objects.filter(
                    student=result_instance.student,
                    department=result_instance.department,
                    level=result_instance.level,
                    semester__name__icontains='1'
                ).exclude(semester=result_instance.semester).first()

            if not first_semester_result:
                print(f"⚠️  First semester result not found for {result_instance.student.full_name} - {result_instance.level.name}")
                print(f"   Looking for: {result_instance.level.name} First Semester")
                print(f"   Found: {result_instance.level.name} {result_instance.semester.name} only")

                # Debug: Show what semesters exist for this student and level
                all_semesters = Result.objects.filter(
                    student=result_instance.student,
                    department=result_instance.department,
                    level=result_instance.level
                ).values_list('semester__name', flat=True)
                print(f"   Available semesters for {result_instance.level.name}: {list(all_semesters)}")
                print("   Cumulative result will be created but may not be accurate")

            # Get or create cumulative result
            cumulative_result, created = cls.objects.get_or_create(
                student=result_instance.student,
                department=result_instance.department,
                level=result_instance.level,
                semester=result_instance.semester,
                defaults={
                    'current_gpa': result_instance.gpa,
                    'tcu': result_instance.tcu,
                    'status': 'approved',  # Auto-approved by admin (can be changed later)
                    'hod_status': 'draft',  # Requires HOD approval to publish
                }
            )

            if not created:
                # Update existing cumulative result
                cumulative_result.current_gpa = result_instance.gpa
                cumulative_result.tcu = result_instance.tcu
                # Keep existing approval status (don't override)

            # Clear existing results and add both semester results from the SAME ACADEMIC YEAR
            cumulative_result.result.clear()

            # Add the second semester result (current result being processed)
            cumulative_result.result.add(result_instance)

            # Add the first semester result from the SAME LEVEL if it exists
            if first_semester_result:
                cumulative_result.result.add(first_semester_result)

                # Calculate and display the cumulative calculation
                first_gpa = first_semester_result.gpa
                second_gpa = result_instance.gpa
                calculated_cgpa = (first_gpa + second_gpa) / 2

                print(f"✅ Successfully linked both semester results for {result_instance.student.full_name} - {result_instance.level.name}")
                print(f"   📊 {first_semester_result.semester.name}: {first_gpa:.2f} GPA")
                print(f"   📊 {result_instance.semester.name}: {second_gpa:.2f} GPA")
                print(f"   🧮 Calculation: ({first_gpa:.2f} + {second_gpa:.2f}) ÷ 2 = {calculated_cgpa:.2f} CGPA")
            else:
                print(f"⚠️  Only second semester result added for {result_instance.student.full_name} - {result_instance.level.name}")
                print(f"   Missing first semester result for complete calculation")

            # Save to trigger cumulative calculations
            cumulative_result.save()

            return cumulative_result

        except Exception as e:
            print(f"Error creating cumulative result: {str(e)}")
            return None








from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser


@receiver(pre_save, sender=CustomUser)
def track_old_is_active(sender, instance, **kwargs):
    """Track the previous is_active value before saving."""
    if instance.pk:  # Only for existing users
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_is_active = old_instance.is_active
        except sender.DoesNotExist:
            instance._old_is_active = None


@receiver(post_save, sender=CustomUser)
def send_activation_email(sender, instance, created, **kwargs):
    """Send email when a user account is approved (is_active changes from False -> True)."""
    if not created:  # Only for updates
        old_is_active = getattr(instance, "_old_is_active", None)

        if old_is_active is False and instance.is_active is True:
            subject = "Your Student Account Has Been Approved"
            message = f"""
Dear {instance.get_full_name() or instance.username},

Good news! 🎉  

Your account has been reviewed and approved by the administrator.  
✅ You can now log in using your registered username and password.  

Go to our platform and log in.  

Best regards,  
PTI Grading System
"""
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [instance.email],
                fail_silently=True,  # <-- better to set to False so you see errors
            )
