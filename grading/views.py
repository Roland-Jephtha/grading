from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as log, logout
from django.contrib import messages
from django.http import JsonResponse
from .forms import GradeForm, StudentProfileForm, LecturerProfileForm, HodProfileForm, UserUpdateForm
from django.db import models



from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json







def login(request):
    if request.user.is_anonymous:
        if request.method == "POST":
            email = request.POST["email"].lower()
            password = request.POST["password"]
            user = authenticate(email=email, password=password)
            if user is not None:
                log(request, user)
                messages.success(request, "Login successful!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid email or password")
                return redirect('login')
    else:
        return redirect("dashboard")
    return render(request, 'login.html')







# def index(request):
#     return render(request, 'dashboard/dashboard.html')







@login_required(login_url="login")
def dashboard(request):
    if request.user.position == "student":
        try:
            profile = StudentProfile.objects.get(user=request.user)

            # Get student performance data
            all_grades = Grade.objects.filter(
                student=profile,
                status='approved'
            ).select_related('course', 'semester')

            all_results = Result.objects.filter(
                student=profile,
                department=profile.department
            ).select_related('level', 'semester')

            # Calculate student statistics
            total_courses = all_grades.count()
            current_gpa = all_results.aggregate(avg_gpa=models.Avg('gpa'))['avg_gpa'] or 0
            completed_semesters = all_results.count()
            total_credit_units = sum([int(grade.course.credit_unit) for grade in all_grades if grade.course.credit_unit])

            student_stats = {
                'total_courses': total_courses,
                'current_gpa': round(current_gpa, 2),
                'completed_semesters': completed_semesters,
                'credit_units': total_credit_units,
            }

            context = {
                'profile': profile,
                'student_stats': student_stats,
            }

        except StudentProfile.DoesNotExist:
            context = {
                'profile': None,
                'student_stats': {
                    'total_courses': 0,
                    'current_gpa': 0.00,
                    'completed_semesters': 0,
                    'credit_units': 0,
                }
            }

        return render(request, 'dashboard/dashboard.html', context)

    elif request.user.position == "lecturer":
        try:
            profile = LecturerProfile.objects.get(user=request.user)

            # Get lecturer's grades and courses through grades
            lecturer_grades = Grade.objects.filter(lecturer=profile)

            # Get unique courses the lecturer has taught (through grades)
            lecturer_courses = Course.objects.filter(
                id__in=lecturer_grades.values_list('course_id', flat=True)
            ).distinct()

            # Get unique students the lecturer has taught (through grades)
            lecturer_students = StudentProfile.objects.filter(
                id__in=lecturer_grades.values_list('student_id', flat=True)
            ).distinct()

            # Calculate lecturer statistics
            total_courses = lecturer_courses.count()
            total_students = lecturer_students.count()
            pending_grades = lecturer_grades.filter(status='draft').count()
            submitted_grades = lecturer_grades.filter(status='submitted').count()

            lecturer_stats = {
                'total_courses': total_courses,
                'total_students': total_students,
                'pending_grades': pending_grades,
                'submitted_grades': submitted_grades,
                'department': profile.department.name if profile.department else 'Not Set',
            }

            context = {
                'profile': profile,
                'lecturer_stats': lecturer_stats,
                'lecturers': LecturerProfile.objects.count(),
                'students': StudentProfile.objects.count(),
            }

        except LecturerProfile.DoesNotExist:
            context = {
                'profile': None,
                'lecturer_stats': {
                    'total_courses': 0,
                    'total_students': 0,
                    'pending_grades': 0,
                    'submitted_grades': 0,
                    'department': 'Not Set',
                },
                'lecturers': LecturerProfile.objects.count(),
                'students': StudentProfile.objects.count(),
            }

        return render(request, 'dashboard/dashboard.html', context)

    elif request.user.position == "hod":
        try:
            profile = HodProfile.objects.get(user=request.user)

            # Get department-specific data
            department_students = StudentProfile.objects.filter(department=profile.department)
            department_lecturers = LecturerProfile.objects.filter(department=profile.department)
            department_courses = Course.objects.filter(department=profile.department)

            # Get pending approvals (submitted grades)
            pending_approvals = Grade.objects.filter(
                department=profile.department,
                status='submitted'
            ).values('course').distinct().count()

            # Calculate HOD statistics
            hod_stats = {
                'total_students': department_students.count(),
                'total_lecturers': department_lecturers.count(),
                'total_courses': department_courses.count(),
                'pending_approvals': pending_approvals,
                'department': profile.department.name if profile.department else 'Not Set',
            }

            context = {
                'profile': profile,
                'hod_stats': hod_stats,
                'lecturers': LecturerProfile.objects.count(),
                'students': StudentProfile.objects.count(),
            }

        except HodProfile.DoesNotExist:
            context = {
                'profile': None,
                'hod_stats': {
                    'total_students': 0,
                    'total_lecturers': 0,
                    'total_courses': 0,
                    'pending_approvals': 0,
                    'department': 'Not Set',
                },
                'lecturers': LecturerProfile.objects.count(),
                'students': StudentProfile.objects.count(),
            }

        return render(request, 'dashboard/dashboard.html', context)

    # Default fallback
    lecturers = LecturerProfile.objects.count()
    students = StudentProfile.objects.count()

    context = {
        'lecturers': lecturers,
        'students': students,
    }

    return render(request, 'dashboard/dashboard.html', context)

















def grading(request):
    selected_student_id = request.POST.get('student')
    selected_department = request.POST.get('department')
    selected_level = request.POST.get('level')
    selected_semester = request.POST.get('semester')

    if request.method == 'POST':
        form = GradeForm(
            request.POST,
            selected_student=selected_student_id,
            selected_department=selected_department,
            selected_level=selected_level,
            selected_semester=selected_semester
        )
        if form.is_valid():
            grade = form.save(commit=False)
            grade.lecturer = LecturerProfile.objects.get(user=request.user)
            grade.save()
            messages.success(request, 'Grade submitted successfully.')
            return redirect('grading')
        else:
            messages.error(request, form.errors)
            print("Form Errors:", form.errors)
    else:
        form = GradeForm()

    lecturer = LecturerProfile.objects.get(user=request.user)
    grades = Grade.objects.filter(lecturer=lecturer)
    level = Level.objects.all()
    department = Department.objects.all()
    semester = Semester.objects.all()


    context = {
        'form': form,
        'grades': grades,
        'levels': level,
        'departments': department,
        'semesters': semester    
    }

    return render(request, 'dashboard/grading.html', context)















def fetch_students(request):
    department_id = request.GET.get('department')
    level_id = request.GET.get('level')

    students = StudentProfile.objects.all()

    if department_id:
        students = students.filter(department_id=department_id)
    if level_id:
        students = students.filter(level_id=level_id)

    data = [{'id': s.id, 'name': str(s)} for s in students]
    return JsonResponse({'students': data})







def fetch_courses(request):
    department_id = request.GET.get('department')
    level_id = request.GET.get('level')
    semester_id = request.GET.get('semester')

    courses = Course.objects.none()  

    if department_id and level_id and semester_id:
        # Get 'General' department if it exists
        general_dept = Department.objects.filter(name__iexact='general').first()

        courses = Course.objects.filter(
            level_id=level_id,
            semester_id=semester_id
        ).filter(
            models.Q(department_id=department_id) |
            models.Q(department=general_dept)
        )

    data = [{'id': course.id, 'title': course.title} for course in courses]
    return JsonResponse({'courses': data})








def register(request):
    return render(request, 'auth/register.html')













def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')










@csrf_exempt
def submit_grades(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        department = data.get('department')
        level = data.get('level')
        semester = data.get('semester')

        lecturer = LecturerProfile.objects.get(user=request.user)

        # Update matching grade records
        updated = Grade.objects.filter(
            lecturer=lecturer,
            department__name=department,
            student__level__name=level,
            semester__name=semester,
            status='draft'
        ).update(status='submitted')

        messages.success(request, 'Grade Submitted Successfully')

        return JsonResponse({"message": f"{updated} grades submitted to department."})

    return JsonResponse({"message": "Invalid request"}, status=400)











# @login_required
# def submitted_grades_view(request):
#     # Optional: filter to HOD's department
#     user_department = request.user.department if hasattr(request.user, 'department') else None

#     if user_department:
#         grades = Grade.objects.filter(status='submitted', department=user_department).select_related('student', 'course', 'lecturer')
#     else:
#         grades = Grade.objects.filter(status='submitted').select_related('student', 'course', 'lecturer')

#     return render(request, 'grades/submitted_grades.html', {'grades': grades})













# views.py


@login_required
def department_grades_view(request):
    profile = HodProfile.objects.get(user=request.user)
    user_department = profile.department

    grades = Grade.objects.filter(
        status__in=['submitted', 'approved'],  # Show both submitted and approved grades
        department=user_department  # use FK instance, not name
    ).select_related('lecturer', 'course', 'student__level', 'semester', 'student')

    # Get all available levels, semesters, and courses for the department
    # This ensures dropdowns are populated even if no grades exist yet
    levels = Level.objects.all().order_by('name')
    semesters = Semester.objects.all().order_by('name')
    courses = Course.objects.filter(department=user_department).select_related('level', 'semester').order_by('title')

    # Also get courses that have submitted grades (in case some courses are from other departments but have grades)
    grade_course_ids = grades.values_list('course_id', flat=True).distinct()
    additional_courses = Course.objects.filter(id__in=grade_course_ids).exclude(id__in=courses.values_list('id', flat=True))

    # Combine department courses with courses that have grades
    all_course_ids = list(courses.values_list('id', flat=True)) + list(additional_courses.values_list('id', flat=True))
    courses = Course.objects.filter(id__in=all_course_ids).select_related('level', 'semester').order_by('title')

    context = {
        'profile': profile,
        'grades': grades,
        'courses': courses,
        'levels': levels,
        'semesters': semesters,
    }
    return render(request, 'dashboard/submitted_grades.html', context)











@login_required
def approve_course_grades(request, course_id):
    if request.method == 'POST':
        profile = HodProfile.objects.get(user=request.user)
        user_department = profile.department

        # Debug: Check what grades we're trying to update
        grades_to_update = Grade.objects.filter(
            course_id=course_id,
            department=user_department,
            status='submitted'
        )

        print(f"Attempting to approve {grades_to_update.count()} grades for course {course_id}")
        print(f"User department: {user_department}")

        # Update the grades individually to trigger signals
        updated_count = 0
        for grade in grades_to_update:
            print(f"Approving grade: {grade.student.full_name} - {grade.course.code}")
            grade.status = 'approved'
            grade.save()  # This will trigger the post_save signal
            updated_count += 1

        print(f"Actually updated {updated_count} grades (signals triggered)")

        if updated_count > 0:
            course = Course.objects.get(id=course_id)
            messages.success(request, f'Successfully approved {updated_count} grades for {course.title}')
        else:
            messages.warning(request, 'No grades were found to approve for this course')

        return redirect('submitted_grades')
    


@login_required
def disapprove_course_grades(request, course_id):
    if request.method == 'POST':
        profile = HodProfile.objects.get(user=request.user)
        user_department = profile.department

        # Debug: Check what grades we're trying to update
        grades_to_update = Grade.objects.filter(
            course_id=course_id,
            department=user_department,
            status='approved'
        )

        print(f"Attempting to disapprove {grades_to_update.count()} grades for course {course_id}")
        print(f"User department: {user_department}")

        # Update the grades individually to trigger signals
        updated_count = 0
        for grade in grades_to_update:
            print(f"Disapproving grade: {grade.student.full_name} - {grade.course.code}")
            grade.status = 'submitted'
            grade.save()  # This will trigger the post_save signal
            updated_count += 1

        print(f"Actually updated {updated_count} grades (signals triggered)")

        # Add success message
        if updated_count > 0:
            course = Course.objects.get(id=course_id)
            messages.success(request, f'Successfully disapproved {updated_count} grades for {course.title}')
        else:
            messages.warning(request, 'No approved grades were found to disapprove for this course')

        return redirect('submitted_grades')
















@login_required
def student_results_view(request):
    """View for managing student results"""
    profile = HodProfile.objects.get(user=request.user)
    user_department = profile.department

    # Get all students in the department
    students = StudentProfile.objects.filter(department=user_department).select_related('level')

    # Get all levels and semesters for filtering
    levels = Level.objects.all()
    semesters = Semester.objects.all()

    context = {
        'students': students,
        'levels': levels,
        'semesters': semesters,
        'department': user_department
    }

    return render(request, 'dashboard/student_results_new.html', context)






@login_required
def generate_student_result(request, student_id):
    """Generate result for a specific student"""
    if request.method == 'POST':
        try:
            profile = HodProfile.objects.get(user=request.user)
            user_department = profile.department

            student = StudentProfile.objects.get(id=student_id, department=user_department)
            semester_id = request.POST.get('semester')

            semester = Semester.objects.get(id=semester_id)

            # Get all approved grades for this student/semester/level
            grades = Grade.objects.filter(
                student=student,
                semester=semester,
                level=student.level,
                department=user_department,
                status='approved'
            )

            if not grades.exists():
                messages.error(request, f'No approved grades found for {student.full_name} in {semester.name}')
                return redirect('student_results_view')

            # Calculate totals
            total_credit_units = 0
            total_grade_points = 0

            for grade in grades:
                try:
                    credit_unit = int(grade.course.credit_unit) if grade.course.credit_unit else 0
                    grade_point = grade.grade_point

                    total_credit_units += credit_unit
                    total_grade_points += (grade_point * credit_unit)
                except (ValueError, TypeError):
                    continue

            # Calculate GPA
            gpa = total_grade_points / total_credit_units if total_credit_units > 0 else 0.00

            # Determine remark
            if gpa >= 1.0:
                remark = 'passed'
            else:
                remark = 'failed'

            # Create or update result for each grade (one result per course)
            results_created = 0
            for grade in grades:
                result, created = Result.objects.get_or_create(
                    student=student,
                    department=user_department,
                    level=student.level,
                    semester=semester,
                    matric_number=student.matric_number,
                    grade_score=grade,
                    defaults={
                        'tcu': int(grade.course.credit_unit) if grade.course.credit_unit else 0,
                        'tgp': grade.grade_point * (int(grade.course.credit_unit) if grade.course.credit_unit else 0),
                        'gpa': gpa,  # Overall GPA for the semester
                        'remark': remark,
                        'status': 'draft'
                    }
                )

                if not created:
                    # Update existing result
                    result.tcu = int(grade.course.credit_unit) if grade.course.credit_unit else 0
                    result.tgp = grade.grade_point * (int(grade.course.credit_unit) if grade.course.credit_unit else 0)
                    result.gpa = gpa
                    result.remark = remark
                    result.save()

                if created:
                    results_created += 1

            from django.contrib import messages
            if results_created > 0:
                messages.success(request, f'Generated {results_created} new results for {student.full_name}')
            else:
                messages.info(request, f'Updated existing results for {student.full_name}')

        except Exception as e:
            messages.error(request, f'Error generating result: {str(e)}')

    return redirect('student_results_view')






@login_required
def view_student_result(request, result_id):
    """View detailed result for a student"""
    profile = HodProfile.objects.get(user=request.user)
    user_department = profile.department

    result = Result.objects.get(
        id=result_id,
        department=user_department
    )

    # Get all results for this student in the same semester (all courses)
    semester_results = Result.objects.filter(
        student=result.student,
        semester=result.semester,
        level=result.level,
        department=user_department
    ).select_related('grade_score__course')

    context = {
        'result': result,
        'semester_results': semester_results,
        'student': result.student,
    }

    return render(request, 'dashboard/view_student_result.html', context)







@login_required
def publish_student_result(request, result_id):
    """Publish/unpublish a result"""
    if request.method == 'POST':
        try:
            profile = HodProfile.objects.get(user=request.user)
            user_department = profile.department

            result = Result.objects.get(
                id=result_id,
                department=user_department
            )

            # Toggle publish status for all results of this student in this semester
            semester_results = Result.objects.filter(
                student=result.student,
                semester=result.semester,
                level=result.level,
                department=user_department
            )

            new_status = 'published' if result.status == 'draft' else 'draft'
            semester_results.update(status=new_status)

            from django.contrib import messages
            status = "published" if new_status == 'published' else "unpublished"
            messages.success(request, f'Result {status} successfully for {result.student.full_name}')

        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')

    return redirect('student_results_view')






@login_required
def fetch_student_results_data(request):
    """AJAX endpoint to fetch results based on filters"""
    if request.method == 'GET':
        profile = HodProfile.objects.get(user=request.user)
        user_department = profile.department

        level_id = request.GET.get('level')
        semester_id = request.GET.get('semester')

        # Build filter conditions
        filters = {'department': user_department}
        if level_id:
            filters['level_id'] = level_id
        if semester_id:
            filters['semester_id'] = semester_id

        # Get unique students with results (group by student)
        results = Result.objects.filter(**filters).select_related(
            'student', 'level', 'semester', 'grade_score__course'
        ).order_by('student__matric_number', 'grade_score__course__code')

        # Group results by student
        student_results = {}
        for result in results:
            key = f"{result.student.id}_{result.semester.id}_{result.level.id}"
            if key not in student_results:
                student_results[key] = {
                    'student': result.student,
                    'semester': result.semester,
                    'level': result.level,
                    'results': [],
                    'total_tcu': 0,
                    'total_tgp': 0,
                    'gpa': result.gpa,  # Same for all courses in semester
                    'status': result.status,
                    'remark': result.remark,
                    'created': result.created
                }

            student_results[key]['results'].append(result)
            student_results[key]['total_tcu'] += result.tcu or 0
            student_results[key]['total_tgp'] += result.tgp or 0

        results_data = []
        for key, data in student_results.items():
            results_data.append({
                'id': data['results'][0].id,  # Use first result's ID for actions
                'student_name': data['student'].full_name,
                'matric_number': data['student'].matric_number,
                'level': data['level'].name,
                'semester': data['semester'].name,
                'total_credit_units': data['total_tcu'],
                'total_grade_points': float(data['total_tgp']),
                'gpa': float(data['gpa']) if data['gpa'] else 0.0,
                'status': data['status'],
                'remark': data['remark'],
                'course_count': len(data['results']),
                'created_at': data['created'].strftime('%Y-%m-%d %H:%M')
            })

        return JsonResponse({'results': results_data})


@login_required
def view_all_results(request):
    """View all results in a table format with filtering by level and semester"""
    profile = HodProfile.objects.get(user=request.user)
    user_department = profile.department

    # Get filter parameters
    level_id = request.GET.get('level')
    semester_id = request.GET.get('semester')

    # Get all levels and semesters for filtering
    levels = Level.objects.all()
    semesters = Semester.objects.all()

    # Get selected level and semester objects for display
    selected_level = Level.objects.get(id=level_id) if level_id else None
    selected_semester = Semester.objects.get(id=semester_id) if semester_id else None

    # Initialize variables
    student_results = {}
    passed_count = 0
    failed_count = 0
    published_count = 0
    show_results = False

    # Only show results if BOTH level and semester are selected
    if level_id and semester_id:
        show_results = True

        # Build filter conditions
        filters = {
            'department': user_department,
            'level_id': level_id,
            'semester_id': semester_id,
            'status': 'approved'
        }

        # Get filtered results
        results = Result.objects.filter(**filters).select_related(
            'student', 'level', 'semester'
        ).prefetch_related('grade_score__course').order_by(
            'student__matric_number'
        )

        # Group results by student to avoid duplicates
        for result in results:
            key = f"{result.student.id}_{result.semester.id}_{result.level.id}"
            if key not in student_results:
                student_results[key] = {
                    'result': result,
                    'grades': list(result.grade_score.all()),
                    'total_courses': result.grade_score.count()
                }

                # Count statistics
                if result.remark == 'passed':
                    passed_count += 1
                elif result.remark == 'failed':
                    failed_count += 1

                if result.status == 'published':
                    published_count += 1

    context = {
        'student_results': student_results,
        'levels': levels,
        'semesters': semesters,
        'selected_level': selected_level,
        'selected_semester': selected_semester,
        'department': user_department,
        'level_id': level_id,
        'semester_id': semester_id,
        'results_count': len(student_results),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'published_count': published_count,
        'show_results': show_results,
        'profile' : profile
    }

    return render(request, 'dashboard/view_all_results.html', context)


@login_required
def lecturer_results_view(request):
    """View for lecturers to see results of students they graded"""
    profile = LecturerProfile.objects.get(user=request.user)

    # Get filter parameters
    department_id = request.GET.get('department')
    level_id = request.GET.get('level')
    semester_id = request.GET.get('semester')

    # Get all departments, levels and semesters for filtering
    departments = Department.objects.all()
    levels = Level.objects.all()
    semesters = Semester.objects.all()

    # Get selected objects for display
    selected_department = Department.objects.get(id=department_id) if department_id else None
    selected_level = Level.objects.get(id=level_id) if level_id else None
    selected_semester = Semester.objects.get(id=semester_id) if semester_id else None

    # Initialize variables
    student_results = {}
    passed_count = 0
    failed_count = 0
    published_count = 0
    show_results = False

    # Only show results if department, level and semester are selected
    if department_id and level_id and semester_id:
        show_results = True

        # Get grades for courses taught by this lecturer with the selected filters
        lecturer_grades = Grade.objects.filter(
            lecturer=profile,
            department_id=department_id,
            level_id=level_id,
            semester_id=semester_id,
            status='approved'
        ).select_related('student', 'course')

        # Get unique students from these grades
        student_ids = lecturer_grades.values_list('student_id', flat=True).distinct()

        # Get results for these students (only published results)
        results = Result.objects.filter(
            student_id__in=student_ids,
            department_id=department_id,
            level_id=level_id,
            semester_id=semester_id,
            status='approved',
            hod_status = 'published'
        ).select_related('student', 'level', 'semester', 'department').prefetch_related('grade_score__course')

        # Group results by student
        for result in results:
            key = f"{result.student.id}_{result.semester.id}_{result.level.id}"
            if key not in student_results:
                # Get only the grades for courses taught by this lecturer
                # lecturer_taught_grades = result.grade_score.filter(lecturer=profile)
                lecturer_taught_grades = result.grade_score.all()

                student_results[key] = {
                    'result': result,
                    'grades': list(lecturer_taught_grades),
                    'total_courses': lecturer_taught_grades.count(),
                    'lecturer_courses_only': True
                }

                # Count statistics
                if result.remark == 'passed':
                    passed_count += 1
                elif result.remark == 'failed':
                    failed_count += 1

                if result.status == 'published':
                    published_count += 1

    context = {
        'student_results': student_results,
        'departments': departments,
        'levels': levels,
        'semesters': semesters,
        'selected_department': selected_department,
        'selected_level': selected_level,
        'selected_semester': selected_semester,
        'lecturer': profile,
        'department_id': department_id,
        'level_id': level_id,
        'semester_id': semester_id,
        'results_count': len(student_results),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'published_count': published_count,
        'show_results': show_results,
        'is_lecturer_view': True,
        'profile' : profile
    }

    return render(request, 'dashboard/lecturer_results.html', context)


@login_required
def student_results_view(request):
    """View for students to see their own results filtered by level and semester"""
    student_profile = StudentProfile.objects.get(user=request.user)

    # Get filter parameters
    level_id = request.GET.get('level')
    semester_id = request.GET.get('semester')

    # Get all levels and semesters for filtering
    levels = Level.objects.all()
    semesters = Semester.objects.all()

    # Get selected level and semester objects for display
    selected_level = Level.objects.get(id=level_id) if level_id else None
    selected_semester = Semester.objects.get(id=semester_id) if semester_id else None

    # Initialize variables
    student_result = None
    show_results = False

    # Only show results if BOTH level and semester are selected
    if level_id and semester_id:
        show_results = True

        # Get the student's result for the selected level and semester
        try:
            student_result = Result.objects.get(
                student=student_profile,
                level_id=level_id,
                semester_id=semester_id,
                department=student_profile.department,
                status='approved',
                hod_status='publish'
            )

            # Get all grades for this result
            grades = student_result.grade_score.all().select_related('course').order_by('course__code')

            student_result.grades_list = list(grades)
            student_result.total_courses = grades.count()

        except Result.DoesNotExist:
            student_result = None


    profile = StudentProfile.objects.get(user=request.user)

    context = {
        'student_result': student_result,
        'levels': levels,
        'semesters': semesters,
        'selected_level': selected_level,
        'selected_semester': selected_semester,
        'student': student_profile,
        'level_id': level_id,
        'semester_id': semester_id,
        'show_results': show_results,
        'is_student_view': True,
        'profile': profile
    }

    return render(request, 'dashboard/student_my_results.html', context)







@login_required
def student_performance_view(request):
    """View for student performance analytics with charts"""
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        # Handle case where student profile doesn't exist
        context = {
            'student': None,
            'performance_data': {'total_courses': 0, 'total_semesters': 0, 'current_level': 'Not Set', 'department': 'Not Set'},
            'gpa_trend': [],
            'semester_labels': [],
            'grade_distribution': {},
            'course_performance': [],
            'overall_stats': {'highest_gpa': 0, 'lowest_gpa': 0, 'average_gpa': 0, 'total_credit_units': 0, 'total_grade_points': 0},
            'passed_courses': 0,
            'failed_courses': 0,
            'pass_rate': 0,
            'all_results': [],
            'latest_result': None,
        }
        return render(request, 'dashboard/student_performance.html', context)

    # Get all student results (no filtering for simplicity)
    all_results = Result.objects.filter(
        student=student_profile,
        department=student_profile.department
    ).select_related('level', 'semester').order_by('created')

    # Get all grades for the student
    all_grades = Grade.objects.filter(
        student=student_profile,
        status='approved'
    ).select_related('course', 'semester', 'student__level').order_by('created')

    # GPA trend data (by semester)
    gpa_trend = []
    semester_labels = []
    for result in all_results:
        gpa_trend.append(float(result.gpa) if result.gpa else 0)
        semester_labels.append(f"{result.level.name} - {result.semester.name}")

    # Add sample data if no real data exists (for testing)
    if not gpa_trend:
        gpa_trend = [2.5, 3.0, 3.2, 3.5, 3.8]
        semester_labels = ["Level 100 - First", "Level 100 - Second", "Level 200 - First", "Level 200 - Second", "Level 300 - First"]

    # Grade distribution data
    grade_distribution = {}
    for grade in all_grades:
        grade_letter = grade.grade
        if grade_letter in grade_distribution:
            grade_distribution[grade_letter] += 1
        else:
            grade_distribution[grade_letter] = 1

    # Add sample grade distribution if no real data exists
    if not grade_distribution:
        grade_distribution = {'A': 5, 'B': 8, 'C': 3, 'D': 2, 'F': 1}

    # Performance data calculations (after grade_distribution is defined)
    total_courses_count = all_grades.count() or sum(grade_distribution.values()) if grade_distribution else 0
    performance_data = {
        'total_courses': total_courses_count,
        'total_semesters': all_results.count() or len(semester_labels),
        'current_level': student_profile.level.name if student_profile.level else 'Not Set',
        'department': student_profile.department.name if student_profile.department else 'Not Set',
    }

    # Course performance data (latest semester)
    latest_result = all_results.last()
    course_performance = []
    if latest_result:
        latest_grades = latest_result.grade_score.all().select_related('course')
        for grade in latest_grades:
            course_performance.append({
                'course': grade.course.code,
                'course_title': grade.course.title,
                'score': grade.score,
                'grade': grade.grade,
                'grade_point': float(grade.grade_point) if grade.grade_point else 0,
                'credit_unit': grade.course.credit_unit,
                'semester': grade.semester.name,
                'level': grade.student.level.name if grade.student.level else 'N/A'
            })

    # Add sample course performance if no real data exists
    if not course_performance:
        course_performance = [
            {'course': 'CSC101', 'course_title': 'Introduction to Computer Science', 'score': 85, 'grade': 'A', 'grade_point': 4.0, 'credit_unit': 3, 'semester': 'First', 'level': 'Level 100'},
            {'course': 'MTH101', 'course_title': 'General Mathematics I', 'score': 78, 'grade': 'B', 'grade_point': 3.0, 'credit_unit': 3, 'semester': 'First', 'level': 'Level 100'},
            {'course': 'PHY101', 'course_title': 'General Physics I', 'score': 92, 'grade': 'A', 'grade_point': 4.0, 'credit_unit': 3, 'semester': 'First', 'level': 'Level 100'},
            {'course': 'CHM101', 'course_title': 'General Chemistry I', 'score': 70, 'grade': 'B', 'grade_point': 3.0, 'credit_unit': 3, 'semester': 'First', 'level': 'Level 100'},
            {'course': 'ENG101', 'course_title': 'Use of English I', 'score': 88, 'grade': 'A', 'grade_point': 4.0, 'credit_unit': 2, 'semester': 'First', 'level': 'Level 100'},
        ]

    # Detailed student information
    student_details = {
        'full_name': f"{student_profile.user.first_name} {student_profile.user.last_name}".strip() or student_profile.user.username,
        'student_id': student_profile.student_id if hasattr(student_profile, 'student_id') else 'N/A',
        'email': student_profile.user.email,
        'department': student_profile.department.name if student_profile.department else 'Not Set',
        'level': student_profile.level.name if student_profile.level else 'Not Set',
        'date_joined': student_profile.user.date_joined,
        'is_active': student_profile.user.is_active,
    }

    # Semester-wise performance breakdown
    semester_performance = {}
    for result in all_results:
        semester_key = f"{result.level.name} - {result.semester.name}"
        semester_performance[semester_key] = {
            'gpa': float(result.gpa) if result.gpa else 0,
            'tcu': result.tcu or 0,
            'tgp': result.tgp or 0,
            'remark': result.remark or 'N/A',
            'status': result.status or 'N/A',
            'courses_count': result.grade_score.count() if hasattr(result, 'grade_score') else 0
        }

    # Academic progress metrics
    academic_metrics = {
        'cgpa': sum(gpa_trend) / len(gpa_trend) if gpa_trend else 0,
        'total_credit_attempted': sum([result.tcu for result in all_results if result.tcu]) or 45,  # Sample if no data
        'total_credit_earned': sum([result.tcu for result in all_results if result.tcu and result.gpa and result.gpa >= 1.0]) or 42,  # Sample if no data
        'academic_standing': 'Good Standing' if (sum(gpa_trend) / len(gpa_trend) if gpa_trend else 3.0) >= 2.0 else 'Academic Probation',
        'graduation_progress': min(((sum([result.tcu for result in all_results if result.tcu]) or 45) / 120) * 100, 100),  # Assuming 120 credits for graduation
    }

    # Performance by level
    level_performance = {}
    for result in all_results:
        level_name = result.level.name
        if level_name not in level_performance:
            level_performance[level_name] = {
                'gpa': [],
                'total_courses': 0,
                'passed_courses': 0
            }
        level_performance[level_name]['gpa'].append(float(result.gpa) if result.gpa else 0)

        # Count courses for this level
        level_grades = all_grades.filter(student__level=result.level)
        level_performance[level_name]['total_courses'] = level_grades.count()
        level_performance[level_name]['passed_courses'] = level_grades.exclude(grade='F').count()

    # Calculate average GPA per level
    for level_name in level_performance:
        gpas = level_performance[level_name]['gpa']
        level_performance[level_name]['avg_gpa'] = sum(gpas) / len(gpas) if gpas else 0

    # Overall statistics
    overall_stats = {
        'highest_gpa': max(gpa_trend) if gpa_trend else 0,
        'lowest_gpa': min(gpa_trend) if gpa_trend else 0,
        'average_gpa': sum(gpa_trend) / len(gpa_trend) if gpa_trend else 0,
        'total_credit_units': sum([result.tcu for result in all_results if result.tcu]),
        'total_grade_points': sum([result.tgp for result in all_results if result.tgp]),
    }

    # Pass/Fail statistics
    passed_courses = all_grades.exclude(grade='F').count()
    failed_courses = all_grades.filter(grade='F').count()

    # Add sample data if no real data exists
    if passed_courses == 0 and failed_courses == 0:
        passed_courses = sum([count for grade, count in grade_distribution.items() if grade != 'F'])
        failed_courses = grade_distribution.get('F', 0)

    total_courses = passed_courses + failed_courses
    pass_rate = (passed_courses / total_courses * 100) if total_courses > 0 else 0

    context = {
        'student': student_profile,
        'student_details': student_details,
        'performance_data': performance_data,
        'gpa_trend': gpa_trend,
        'semester_labels': semester_labels,
        'grade_distribution': grade_distribution,
        'course_performance': course_performance,
        'semester_performance': semester_performance,
        'academic_metrics': academic_metrics,
        'level_performance': level_performance,
        'overall_stats': overall_stats,
        'passed_courses': passed_courses,
        'failed_courses': failed_courses,
        'pass_rate': round(pass_rate, 1),
        'all_results': all_results,
        'latest_result': latest_result,
    }

    return render(request, 'dashboard/student_performance.html', context)








# Profile Update Views
@login_required
def update_profile(request):
    """Universal profile update view that handles all user types"""
    user = request.user

    if user.position == 'student':
        try:
            profile = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)

        if request.method == 'POST':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = StudentProfileForm(request.POST, request.FILES, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('update_profile')
        else:
            user_form = UserUpdateForm(instance=user)
            profile_form = StudentProfileForm(instance=profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'user_type': 'Student'
        }

    elif user.position == 'lecturer':
        try:
            profile = LecturerProfile.objects.get(user=user)
        except LecturerProfile.DoesNotExist:
            profile = LecturerProfile.objects.create(user=user)

        if request.method == 'POST':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = LecturerProfileForm(request.POST, request.FILES, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('update_profile')
        else:
            user_form = UserUpdateForm(instance=user)
            profile_form = LecturerProfileForm(instance=profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'user_type': 'Lecturer'
        }

    elif user.position == 'hod':
        try:
            profile = HodProfile.objects.get(user=user)
        except HodProfile.DoesNotExist:
            profile = HodProfile.objects.create(user=user)

        if request.method == 'POST':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = HodProfileForm(request.POST, request.FILES, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('update_profile')
        else:
            user_form = UserUpdateForm(instance=user)
            profile_form = HodProfileForm(instance=profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'user_type': 'HOD'
        }

    else:
        messages.error(request, 'Invalid user type.')
        return redirect('dashboard')

    return render(request, 'dashboard/update_profile.html', context)


@login_required
def delete_grade(request, grade_id):
    """Delete a grade with proper authorization"""
    try:
        grade = Grade.objects.get(id=grade_id)

        # Check if user is authorized to delete this grade
        if request.user.position == 'lecturer':
            lecturer_profile = LecturerProfile.objects.get(user=request.user)
            if grade.lecturer != lecturer_profile:
                messages.error(request, 'You are not authorized to delete this grade.')
                return redirect('grading')
        elif request.user.position == 'hod':
            hod_profile = HodProfile.objects.get(user=request.user)
            if grade.department != hod_profile.department:
                messages.error(request, 'You are not authorized to delete this grade.')
                return redirect('grading')
        else:
            messages.error(request, 'You are not authorized to delete grades.')
            return redirect('grading')

        # Check if grade can be deleted (only draft grades)
        if grade.status != 'draft':
            messages.error(request, f'Cannot delete {grade.status} grades. Only draft grades can be deleted.')
            return redirect('grading')

        # Store grade info for success message
        student_name = grade.student.full_name
        course_code = grade.course.code

        # Delete the grade
        grade.delete()

        messages.success(request, f'Grade for {student_name} in {course_code} has been deleted successfully.')
        return redirect('grading')

    except Grade.DoesNotExist:
        messages.error(request, 'Grade not found.')
        return redirect('grading')
    except (LecturerProfile.DoesNotExist, HodProfile.DoesNotExist):
        messages.error(request, 'Profile not found.')
        return redirect('grading')
    except Exception as e:
        messages.error(request, 'An error occurred while deleting the grade.')
        return redirect('grading')


@login_required
def toggle_hod_status(request, result_id):
    """Toggle HOD status between published and draft"""
    try:
        result = Result.objects.get(id=result_id)

        # Check if user is authorized (only HOD can toggle)
        if request.user.position != 'hod':
            messages.error(request, 'You are not authorized to perform this action.')
            return redirect('view_all_results')

        # Get HOD profile to check department
        hod_profile = HodProfile.objects.get(user=request.user)
        if result.department != hod_profile.department:
            messages.error(request, 'You can only manage results in your department.')
            return redirect('view_all_results')

        # Toggle the HOD status
        if result.hod_status == 'published':
            result.hod_status = 'draft'
            action = 'unpublished'
            messages.success(request, f'Result for {result.student.full_name} has been unpublished successfully.')
        else:
            result.hod_status = 'published'
            action = 'published'
            messages.success(request, f'Result for {result.student.full_name} has been published successfully.')

        result.save()

        return redirect('view_all_results')

    except Result.DoesNotExist:
        messages.error(request, 'Result not found.')
        return redirect('view_all_results')
    except HodProfile.DoesNotExist:
        messages.error(request, 'HOD profile not found.')
        return redirect('view_all_results')
    except Exception as e:
        messages.error(request, 'An error occurred while updating the result status.')
        return redirect('view_all_results')


@login_required
def publish_all_results(request):
    """Publish all results for a specific level and semester"""
    try:
        # Check if user is authorized (only HOD can publish)
        if request.user.position != 'hod':
            messages.error(request, 'You are not authorized to perform this action.')
            return redirect('view_all_results')

        # Get HOD profile
        hod_profile = HodProfile.objects.get(user=request.user)

        # Get level and semester from query parameters
        level_id = request.GET.get('level')
        semester_id = request.GET.get('semester')

        if not level_id or not semester_id:
            messages.error(request, 'Level and semester are required.')
            return redirect('view_all_results')

        # Get all results for the specified level, semester, and HOD's department
        results = Result.objects.filter(
            level_id=level_id,
            semester_id=semester_id,
            department=hod_profile.department,
            status='approved',
            hod_status='draft'  # Only publish draft results
        )

        if not results.exists():
            messages.info(request, 'No draft results found to publish for the selected level and semester.')
            return redirect('view_all_results')

        # Update all results to publish
        updated_count = results.update(hod_status='publish')

        # Get level and semester names for the message
        level = Level.objects.get(id=level_id)
        semester = Semester.objects.get(id=semester_id)

        messages.success(request, f'Successfully published {updated_count} result(s) for {level.name} - {semester.name}.')
        return redirect('view_all_results')

    except HodProfile.DoesNotExist:
        messages.error(request, 'HOD profile not found.')
        return redirect('view_all_results')
    except (Level.DoesNotExist, Semester.DoesNotExist):
        messages.error(request, 'Invalid level or semester.')
        return redirect('view_all_results')
    except Exception as e:
        messages.error(request, 'An error occurred while publishing results.')
        return redirect('view_all_results')

