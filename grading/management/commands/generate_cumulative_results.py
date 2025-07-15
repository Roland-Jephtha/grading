from django.core.management.base import BaseCommand
from grading.models import Result, Cummulative_Result
from django.db import transaction, models

class Command(BaseCommand):
    help = 'Generate cumulative results for existing regular results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing cumulative results',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting cumulative results generation...'))

        # First, let's see what semesters exist in the database
        all_semesters = Result.objects.values_list('semester__name', flat=True).distinct()
        self.stdout.write(f'Available semesters in database: {list(all_semesters)}')

        # Get all approved results for second semester only (flexible patterns)
        second_semester_results = Result.objects.filter(
            status='approved'
        ).filter(
            models.Q(semester__name__icontains='second') |
            models.Q(semester__name__icontains='2nd') |
            models.Q(semester__name__icontains='2ND') |
            models.Q(semester__name__regex=r'.*2.*')
        ).order_by('student', 'created')

        self.stdout.write(f'Second semester results found: {second_semester_results.count()}')

        # If no second semester results found, let's try a broader search
        if second_semester_results.count() == 0:
            self.stdout.write(self.style.WARNING('No second semester results found with current patterns.'))
            self.stdout.write('Trying broader search...')

            # Try to find any results that might be second semester
            possible_second = Result.objects.filter(status='approved').filter(
                models.Q(semester__name__icontains='2') |
                models.Q(semester__name__iregex=r'.*second.*') |
                models.Q(semester__name__iregex=r'.*2nd.*')
            )
            self.stdout.write(f'Possible second semester results: {possible_second.count()}')
            for result in possible_second[:5]:  # Show first 5
                self.stdout.write(f'  - {result.student.full_name}: {result.level.name} {result.semester.name}')

        results = second_semester_results
        
        total_results = results.count()
        processed = 0
        created = 0
        updated = 0
        errors = 0
        
        self.stdout.write(f'Found {total_results} results to process...')
        
        with transaction.atomic():
            for result in results:
                try:
                    # Check if cumulative result already exists
                    existing = Cummulative_Result.objects.filter(
                        student=result.student,
                        department=result.department,
                        level=result.level,
                        semester=result.semester
                    ).first()
                    
                    if existing and not force:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping existing cumulative result for {result.student.full_name} '
                                f'({result.level.name} {result.semester.name}). Use --force to regenerate.'
                            )
                        )
                        processed += 1
                        continue
                    
                    # Create or update cumulative result
                    cumulative_result = Cummulative_Result.create_cumulative_result(result)
                    
                    if cumulative_result:
                        if existing:
                            updated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Updated cumulative result for {result.student.full_name} '
                                    f'({result.level.name} {result.semester.name}) - '
                                    f'CGPA: {cumulative_result.cumulative_gpa:.2f}'
                                )
                            )
                        else:
                            created += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created cumulative result for {result.student.full_name} '
                                    f'({result.level.name} {result.semester.name}) - '
                                    f'CGPA: {cumulative_result.cumulative_gpa:.2f}'
                                )
                            )
                    else:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to create cumulative result for {result.student.full_name} '
                                f'({result.level.name} {result.semester.name})'
                            )
                        )
                    
                    processed += 1
                    
                    # Progress indicator
                    if processed % 10 == 0:
                        self.stdout.write(f'Processed {processed}/{total_results} results...')
                        
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing result for {result.student.full_name}: {str(e)}'
                        )
                    )
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('CUMULATIVE RESULTS GENERATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Total Results Processed: {processed}')
        self.stdout.write(f'Cumulative Results Created: {created}')
        self.stdout.write(f'Cumulative Results Updated: {updated}')
        self.stdout.write(f'Errors: {errors}')
        
        if errors == 0:
            self.stdout.write(self.style.SUCCESS('\nAll cumulative results generated successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'\nCompleted with {errors} errors. Check the output above for details.'))
