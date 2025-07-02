from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('grading', grading, name='grading'),
    path('fetch-students/', fetch_students, name='fetch_students'),
    path('login', login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('fetch-courses/', fetch_courses, name='fetch_courses'),
    path('submit-grades/', submit_grades, name='submit_grades'),
    path('hod/submitted-grades/', department_grades_view, name='submitted_grades'),
    path('department/approve/<int:course_id>/', approve_course_grades, name='approve_course_grades'),
    path('department/disapprove/<int:course_id>/', disapprove_course_grades, name='disapprove_course_grades'),

    # Result URLs
    path('department/results/', student_results_view, name='student_results_view'),
    path('department/view-result/<int:result_id>/', view_student_result, name='view_student_result'),
    path('department/publish-result/<int:result_id>/', publish_student_result, name='publish_student_result'),
    path('department/fetch-student-results/', fetch_student_results_data, name='fetch_student_results_data'),
    path('department/view-all-results/', view_all_results, name='view_all_results'),

    # Lecturer Results URLs
    path('lecturer/results/', lecturer_results_view, name='lecturer_results_view'),

    # Student Results URLs
    path('student/my-results/', student_results_view, name='student_my_results'),
    path('student/performance/', student_performance_view, name='student_performance'),

    # Profile Update URL
    path('update-profile/', update_profile, name='update_profile'),

    # Grade Management URLs
    path('delete-grade/<int:grade_id>/', delete_grade, name='delete_grade'),

    # HOD Status Toggle URL
    path('toggle-hod-status/<int:result_id>/', toggle_hod_status, name='toggle_hod_status'),

    # Bulk Publish Results URL
    path('publish-all-results/', publish_all_results, name='publish_all_results'),




    # path('submit/', views.submit, name='submit'),
]



