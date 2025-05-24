from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.models import School, UserProfile, Invitation, RegistrationCode

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up demo data for testing the secure registration system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-schools',
            action='store_true',
            help='Create demo schools',
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create demo admin user',
        )
        parser.add_argument(
            '--create-codes',
            action='store_true',
            help='Create demo registration codes',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create all demo data',
        )

    def handle(self, *args, **options):
        if options['all']:
            options['create_schools'] = True
            options['create_admin'] = True
            options['create_codes'] = True

        schools = []
        admin_user = None

        if options['create_schools']:
            schools = self.create_schools()

        if options['create_admin']:
            admin_user = self.create_admin_user()

        if options['create_codes'] and schools and admin_user:
            self.create_registration_codes(schools, admin_user)

        self.stdout.write(
            self.style.SUCCESS('Demo data setup completed successfully!')
        )

    def create_schools(self):
        """Create demo schools."""
        self.stdout.write('Creating demo schools...')
        
        schools_data = [
            {
                'name': 'Greenwood High School',
                'code': 'GHS001',
                'address': '123 Education Street',
                'city': 'Learning City',
                'state': 'Knowledge State',
                'country': 'Education Country',
                'postal_code': '12345',
                'phone': '+1-555-0001',
                'email': 'admin@greenwood.edu',
                'school_type': 'public',
                'academic_year_start': timezone.now().date().replace(month=8, day=1),
                'academic_year_end': timezone.now().date().replace(month=6, day=30),
            },
            {
                'name': 'Tech Valley Academy',
                'code': 'TVA002',
                'address': '456 Innovation Avenue',
                'city': 'Tech City',
                'state': 'Silicon State',
                'country': 'Innovation Country',
                'postal_code': '54321',
                'phone': '+1-555-0002',
                'email': 'admin@techvalley.edu',
                'school_type': 'private',
                'academic_year_start': timezone.now().date().replace(month=9, day=1),
                'academic_year_end': timezone.now().date().replace(month=6, day=15),
            },
            {
                'name': 'International Learning Center',
                'code': 'ILC003',
                'address': '789 Global Plaza',
                'city': 'World City',
                'state': 'International State',
                'country': 'Global Country',
                'postal_code': '98765',
                'phone': '+1-555-0003',
                'email': 'admin@ilc.edu',
                'school_type': 'international',
                'academic_year_start': timezone.now().date().replace(month=9, day=15),
                'academic_year_end': timezone.now().date().replace(month=7, day=1),
            }
        ]

        schools = []
        for school_data in schools_data:
            school, created = School.objects.get_or_create(
                code=school_data['code'],
                defaults=school_data
            )
            if created:
                self.stdout.write(f'  ✓ Created school: {school.name}')
            else:
                self.stdout.write(f'  - School already exists: {school.name}')
            schools.append(school)

        return schools

    def create_admin_user(self):
        """Create demo admin user."""
        self.stdout.write('Creating demo admin user...')
        
        admin_data = {
            'email': 'admin@convade.com',
            'first_name': 'System',
            'last_name': 'Administrator',
            'role': User.ADMIN,
            'is_staff': True,
            'is_superuser': True,
            'is_email_verified': True,
        }

        admin_user, created = User.objects.get_or_create(
            email=admin_data['email'],
            defaults=admin_data
        )

        if created:
            admin_user.set_password('admin123456')
            admin_user.save()
            self.stdout.write(f'  ✓ Created admin user: {admin_user.email}')
            self.stdout.write(f'    Password: admin123456')
        else:
            self.stdout.write(f'  - Admin user already exists: {admin_user.email}')

        return admin_user

    def create_registration_codes(self, schools, admin_user):
        """Create demo registration codes."""
        self.stdout.write('Creating demo registration codes...')
        
        codes_data = [
            {
                'school': schools[0],  # Greenwood High School
                'role': User.STUDENT,
                'max_uses': 50,
                'grade_level': '9th Grade',
                'expires_at': timezone.now() + timedelta(days=30),
            },
            {
                'school': schools[0],  # Greenwood High School
                'role': User.TEACHER,
                'max_uses': 10,
                'department': 'Mathematics',
                'expires_at': timezone.now() + timedelta(days=60),
            },
            {
                'school': schools[1],  # Tech Valley Academy
                'role': User.STUDENT,
                'max_uses': 30,
                'grade_level': '11th Grade',
                'expires_at': timezone.now() + timedelta(days=45),
            },
            {
                'school': schools[2],  # International Learning Center
                'role': User.STUDENT,
                'max_uses': 0,  # Unlimited
                'expires_at': timezone.now() + timedelta(days=90),
            }
        ]

        for code_data in codes_data:
            reg_code = RegistrationCode.generate_code(
                created_by=admin_user,
                **code_data
            )
            self.stdout.write(
                f'  ✓ Created registration code: {reg_code.code} '
                f'({reg_code.school.name} - {reg_code.get_role_display()})'
            )

    def create_demo_invitations(self, schools, admin_user):
        """Create demo invitations (optional)."""
        self.stdout.write('Creating demo invitations...')
        
        invitations_data = [
            {
                'email': 'teacher1@example.com',
                'role': User.TEACHER,
                'school': schools[0],
            },
            {
                'email': 'student1@example.com',
                'role': User.STUDENT,
                'school': schools[0],
            },
            {
                'email': 'teacher2@example.com',
                'role': User.TEACHER,
                'school': schools[1],
            }
        ]

        for inv_data in invitations_data:
            invitation = Invitation.create_invitation(
                invited_by=admin_user,
                expires_in_days=14,
                **inv_data
            )
            self.stdout.write(
                f'  ✓ Created invitation: {invitation.email} '
                f'({invitation.school.name} - {invitation.get_role_display()})'
            )
            self.stdout.write(f'    Token: {invitation.token}') 