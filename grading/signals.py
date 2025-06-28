from django.db.models.signals import post_save
from django.dispatch import receiver

# Print to confirm signals.py is being loaded
print("🔄 Loading grading signals...")

# Import models
from .models import CustomUser, StudentProfile, LecturerProfile, HodProfile, Grade, Result

print(f"✅ Models imported: Grade={Grade}, Result={Result}")

@receiver(post_save, sender=CustomUser)
def create_position_instance(sender, instance, created, **kwargs):
    if created:  # Ensure this runs only when a new user is created
        position = instance.position.lower()
        
        if position == "student":
            StudentProfile.objects.create(user=instance)
        elif position == "lecturer":
            LecturerProfile.objects.create(user=instance)
        elif position == "hod":
            HodProfile.objects.create(user=instance)


# Do NOT connect signals explicitly here; the @receiver decorator is sufficient and avoids duplicate calls.
# Make sure this file is imported in grading/apps.py in the ready() method for Django to register the signals.

def create_result_if_all_grades_approved(student, department, level, semester):
    """Create, update, or remove result based on grade approval status"""
    grades = Grade.objects.filter(student=student, department=department, level=level, semester=semester)

    print(f"Checking grades for {student.full_name}: {grades.count()} total grades")  # Debug log

    if grades.exists():
        approved_grades = grades.filter(status='approved')
        total_grades = grades.count()
        approved_count = approved_grades.count()

        print(f"Approved: {approved_count}/{total_grades} grades")  # Debug log

        # Check if ALL grades are approved
        if approved_count == total_grades and approved_count > 0:
            print(f"All grades approved! Creating/updating result for {student.full_name}")  # Debug log

            # Calculate values first
            total_credit_units = 0
            total_grade_points = 0

            print(f"📊 Calculating totals from {approved_count} approved grades:")

            for grade in approved_grades:
                try:
                    credit_unit = int(grade.course.credit_unit) if grade.course.credit_unit else 0
                    grade_point = float(grade.grade_point) if grade.grade_point else 0.0

                    total_credit_units += credit_unit
                    total_grade_points += grade_point

                    print(f"  📝 {grade.course.code}: {grade.grade} ({grade.score}%) = {credit_unit} units × {grade_point/credit_unit if credit_unit > 0 else 0:.1f} = {grade_point} points")

                except (ValueError, TypeError) as e:
                    print(f"  ❌ Error processing {grade.course.code}: {e}")
                    continue

            # Calculate GPA
            gpa = total_grade_points / total_credit_units if total_credit_units > 0 else 0.0
            remark = 'passed' if gpa >= 1.0 else 'failed'

            print(f"📈 Final Calculation: TCU={total_credit_units}, TGP={total_grade_points:.2f}, GPA={gpa:.2f}, Remark={remark}")

            # Create or update result with calculated values
            result, created = Result.objects.get_or_create(
                student=student,
                department=department,
                level=level,
                semester=semester,
                defaults={
                    'matric_number': student.matric_number,
                    'tcu': total_credit_units,
                    'tgp': total_grade_points,
                    'gpa': gpa,
                    'remark': remark,
                    'status': 'draft'
                }
            )

            # If result already existed, update it with new calculations
            if not created:
                result.tcu = total_credit_units
                result.tgp = total_grade_points
                result.gpa = gpa
                result.remark = remark
                result.save()

            # Add all approved grades to the grade_score field for template rendering
            result.grade_score.clear() 
            result.grade_score.add(*approved_grades) 
            print(f"📋 Added {approved_grades.count()} grades to result.grade_score")

            if created:
                print(f"✅ New result created for {student.full_name}: GPA={result.gpa:.2f}")
            else:
                print(f"✅ Result updated for {student.full_name}: GPA={result.gpa:.2f}")
        else:
            print(f"❌ Not all grades approved yet ({approved_count}/{total_grades})")

            # Check if a result exists and update its status to draft or remove it
            existing_result = Result.objects.filter(
                student=student,
                department=department,
                level=level,
                semester=semester
            ).first()

            if existing_result:
                if approved_count == 0:
                    print(f"🗑️ Removing result for {student.full_name} (no approved grades)")
                    existing_result.delete()
                else:
                    print(f"📝 Updating result to draft status for {student.full_name}")
                    existing_result.status = 'draft'

                    # Recalculate with only approved grades
                    total_credit_units = 0
                    total_grade_points = 0

                    for grade in approved_grades:
                        try:
                            credit_unit = int(grade.course.credit_unit) if grade.course.credit_unit else 0
                            grade_point = float(grade.grade_point) if grade.grade_point else 0.0
                            total_credit_units += credit_unit
                            total_grade_points += grade_point
                        except (ValueError, TypeError):
                            continue

                    existing_result.tcu = total_credit_units
                    existing_result.tgp = total_grade_points
                    existing_result.gpa = total_grade_points / total_credit_units if total_credit_units > 0 else 0.0
                    existing_result.remark = 'passed' if existing_result.gpa >= 1.0 else 'failed'
                    existing_result.save()

                    # Update grade_score with current approved grades
                    existing_result.grade_score.clear()
                    existing_result.grade_score.add(*approved_grades)

                    print(f"📊 Partial result updated: {approved_count}/{total_grades} grades, GPA={existing_result.gpa:.2f}")
    else:
        print(f"❌ No grades found for {student.full_name}")






@receiver(post_save, sender=Grade)
def handle_grade_approval(sender, instance, created, **kwargs):
    """Signal handler to create/update result when grades are approved/disapproved"""
    print(f"🚨 SIGNAL ENTRY: Grade signal fired!")
    try:
        # Always check when a grade is saved, regardless of status
        # This ensures we catch both new approvals and status changes
        action = "created" if created else "updated"
        print(f"🔔 SIGNAL TRIGGERED: Grade {action} for {instance.student.full_name} - {instance.course.code} - Status: {instance.status}")
        print(f"📍 Student: {instance.student}, Department: {instance.department}, Level: {instance.level}, Semester: {instance.semester}")

        # Always check and update result based on current grade statuses
        create_result_if_all_grades_approved(
            instance.student,
            instance.department,
            instance.level,
            instance.semester
        )
        print(f"✅ Signal processing completed for {instance.student.full_name}")

    except Exception as e:
        print(f"❌ ERROR in signal: {str(e)}")
        import traceback
        traceback.print_exc()


print(f"🔗 Grade signal connected: {handle_grade_approval} -> {Grade}")
print("✅ All signals loaded successfully!")
