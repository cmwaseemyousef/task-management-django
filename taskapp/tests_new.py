from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task
from datetime import date

class TaskManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        User = get_user_model()
        
        # Create test users
        self.superadmin = User.objects.create_user(
            username='superadmin',
            password='test123',
            email='superadmin@test.com',
            role='superadmin'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='test123',
            email='admin@test.com',
            role='admin'
        )
        
        self.user = User.objects.create_user(
            username='user',
            password='test123',
            email='user@test.com',
            role='user'
        )
        
        # Create a test task
        self.test_task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            assigned_to=self.user,
            due_date=date.today(),
            status='pending'
        )

    def test_user_roles(self):
        """Test that user roles are correctly assigned"""
        self.assertEqual(self.superadmin.role, 'superadmin')
        self.assertEqual(self.admin.role, 'admin')
        self.assertEqual(self.user.role, 'user')

    def test_user_login(self):
        """Test user login functionality"""
        response = self.client.post(reverse('login'), {
            'username': 'user',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_task_creation(self):
        """Test task creation by superadmin"""
        self.client.force_login(self.superadmin)
        response = self.client.post(reverse('create_task'), {
            'title': 'New Task',
            'description': 'New Description',
            'assigned_to': self.user.id,
            'due_date': date.today()
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Task.objects.filter(title='New Task').exists())

    def test_task_completion(self):
        """Test task completion with report"""
        self.client.force_login(self.user)
        
        # First check task is not completed
        task = Task.objects.get(id=self.test_task.id)
        self.assertEqual(task.status, 'pending')
        
        response = self.client.post(reverse('complete_task', args=[self.test_task.id]), {
            'completion_report': 'Task completed successfully',
            'worked_hours': 4.5
        })
        self.assertEqual(response.status_code, 302)  # Redirect after completion
        
        # Verify task is marked as completed
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.completion_report, 'Task completed successfully')
        self.assertEqual(task.worked_hours, 4.5)

    def test_api_authentication(self):
        """Test API authentication"""
        # Try accessing without token
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Login and get token
        response = self.client.post('/api/token/', {
            'username': 'user',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['access']
        
        # Try accessing with token
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_task_list(self):
        """Test API task listing"""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User should only see their assigned tasks
        tasks = response.json()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Test Task')

    def test_api_task_completion(self):
        """Test task completion through API"""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.patch(f'/api/tasks/{self.test_task.id}/', {
            'status': 'completed',
            'completion_report': 'Completed via API',
            'worked_hours': 3.5
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task is updated
        task = Task.objects.get(id=self.test_task.id)
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.completion_report, 'Completed via API')
        self.assertEqual(task.worked_hours, 3.5)

    def test_superadmin_access(self):
        """Test superadmin access to all tasks"""
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse('superadmin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')

    def test_admin_access(self):
        """Test admin access to tasks"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_task_completion(self):
        """Test invalid task completion attempts"""
        self.client.force_login(self.user)
        
        # Try completing without report
        response = self.client.post(reverse('complete_task', args=[self.test_task.id]), {
            'worked_hours': 4.5
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(id=self.test_task.id)
        self.assertEqual(task.status, 'pending')  # Should remain pending
        
        # Try completing with invalid hours
        response = self.client.post(reverse('complete_task', args=[self.test_task.id]), {
            'completion_report': 'Test report',
            'worked_hours': -1
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(id=self.test_task.id)
        self.assertEqual(task.status, 'pending')  # Should remain pending
