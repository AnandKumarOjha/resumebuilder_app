import unittest
import io
import os
from app import create_app, db
from app.models import User, PersonalInfo, ResumeRole, Experience, Education, Skill
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test_secret_key'

class ResumeBuilderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_and_login(self, email='student@test.com', password='password123'):
        self.client.post('/register', data={
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ResumeBuilder', response.data)
        self.assertIn(b'One Profile, Multiple Tailored Resumes', response.data)

    def test_auth_workflow(self):
        # Register
        res = self.client.post('/register', data={
            'email': 'user1@example.com',
            'password': 'secretpassword',
            'confirm_password': 'secretpassword'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Account created', res.data)

        # Login
        res = self.client.post('/login', data={
            'email': 'user1@example.com',
            'password': 'secretpassword'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student &amp; Professional Dashboard', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Log In', res.data)

    def test_dashboard_and_resume_crud(self):
        self.register_and_login()

        # Update Personal Info
        res = self.client.post('/dashboard/personal-info', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone': '+1 555-0199',
            'address': 'San Francisco, CA',
            'linkedin': 'https://linkedin.com/in/janedoe',
            'portfolio': 'https://janedoe.dev'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Personal information updated successfully!', res.data)
        self.assertIn(b'Jane Doe', res.data)

        # Create Role
        res = self.client.post('/dashboard/role/new', data={
            'role_name': 'Full Stack Developer',
            'summary': 'Passionate engineer with experience in Python and React.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Full Stack Developer', res.data)

        role = ResumeRole.query.first()
        self.assertIsNotNone(role)
        self.assertEqual(role.role_name, 'Full Stack Developer')

        # Edit Role
        res = self.client.post(f'/dashboard/role/{role.id}/edit', data={
            'role_name': 'Senior Full Stack Developer',
            'summary': 'Senior engineer with experience leading teams.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Senior Full Stack Developer', res.data)

        # Add Experience
        res = self.client.post(f'/dashboard/role/{role.id}/experience/add', data={
            'company': 'Tech Corp',
            'job_title': 'Software Engineer',
            'start_date': 'Jan 2022',
            'end_date': 'Present',
            'description': 'Built microservices and scalable APIs.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Software Engineer', res.data)
        self.assertIn(b'Tech Corp', res.data)

        # Add Education
        res = self.client.post(f'/dashboard/role/{role.id}/education/add', data={
            'institution': 'State University',
            'degree': 'B.S. in Computer Science',
            'start_date': '2018',
            'end_date': '2022'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'State University', res.data)
        self.assertIn(b'B.S. in Computer Science', res.data)

        # Add Skill
        res = self.client.post(f'/dashboard/role/{role.id}/skill/add', data={
            'skill_name': 'Python & Flask'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Python &amp; Flask', res.data)

    def test_preview_and_pdf_generation_paywall(self):
        self.register_and_login()

        # Create Personal Info & Role
        user = User.query.first()
        self.assertFalse(user.is_premium)

        pinfo = PersonalInfo(
            user_id=user.id,
            first_name='Alex',
            last_name='Smith',
            phone='123-456-7890',
            address='New York, NY',
            linkedin='https://linkedin.com/in/alexsmith'
        )
        db.session.add(pinfo)
        role = ResumeRole(user_id=user.id, role_name='Data Scientist', summary='Machine learning specialist.')
        db.session.add(role)
        db.session.commit()

        exp = Experience(role_id=role.id, company='AI Labs', job_title='Data Analyst', start_date='2021', end_date='2023', description='Analyzed big data.')
        edu = Education(role_id=role.id, institution='MIT', degree='M.S. Data Science', start_date='2019', end_date='2021')
        skill = Skill(role_id=role.id, skill_name='Python, PyTorch')
        db.session.add_all([exp, edu, skill])
        db.session.commit()

        # 1. Preview should be accessible even for free users
        res = self.client.get(f'/preview/{role.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Data Scientist', res.data)
        self.assertIn(b'AI Labs', res.data)

        # Preview modern template
        res = self.client.get(f'/preview/{role.id}?template=modern')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Summary', res.data)

        # 2. PDF Download when NOT premium should be blocked and redirect to paywall
        res = self.client.get(f'/download/pdf/{role.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'PDF downloads require an active PRO', res.data)
        self.assertIn(b'Upgrade to ResumeBuilder PRO', res.data)

        # 3. Simulate upgrade via dev-activate
        res = self.client.post('/payment/dev-activate', data={'role_id': role.id}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'PRO membership has been activated', res.data)

        # Re-query user
        user = db.session.get(User, user.id)
        self.assertTrue(user.is_premium)

        # 4. PDF Download when premium should succeed and return PDF binary
        res = self.client.get(f'/download/pdf/{role.id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        self.assertTrue(res.data.startswith(b'%PDF-'))
        self.assertGreater(len(res.data), 1000)

        # Also test modern template PDF generation
        res_modern = self.client.get(f'/download/pdf/{role.id}?template=modern')
        self.assertEqual(res_modern.status_code, 200)
        self.assertEqual(res_modern.mimetype, 'application/pdf')
        self.assertTrue(res_modern.data.startswith(b'%PDF-'))
        self.assertGreater(len(res_modern.data), 1000)

    def test_stripe_webhook_processing(self):
        self.register_and_login(email='webhook_test@example.com')
        user = User.query.filter_by(email='webhook_test@example.com').first()
        self.assertFalse(user.is_premium)

        # Send mock stripe checkout.session.completed event
        mock_payload = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'client_reference_id': str(user.id),
                    'customer_email': user.email
                }
            }
        }
        res = self.client.post('/payment/webhook', json=mock_payload)
        self.assertEqual(res.status_code, 200)

        # User should now be upgraded
        db.session.refresh(user)
        self.assertTrue(user.is_premium)

if __name__ == '__main__':
    unittest.main()
