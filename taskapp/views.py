from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer
from .permissions import IsSuperAdminOrTaskOwner

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ---------------- User Management Views ----------------
@login_required
@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        if not all([username, email, password, role]):
            messages.error(request, 'All fields are required')
            return redirect('superadmin_dashboard')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('superadmin_dashboard')
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.role = role
        user.save()
        
        messages.success(request, 'User created successfully')
        return redirect('superadmin_dashboard')
    
    return redirect('superadmin_dashboard')

@login_required
def change_user_role(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        new_role = request.POST.get('role')
        user.role = new_role
        user.save()
        messages.success(request, f'Role changed for {user.username}')
        return redirect('superadmin_dashboard')
    return redirect('superadmin_dashboard')

@login_required
def edit_user(request, user_id):
    """Handle user editing for superadmins"""
    if request.user.role != 'superadmin':
        return render(request, '403.html')

    User = get_user_model()
    user_to_edit = User.objects.filter(id=user_id).first()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if all([username, email, role]):
            user_to_edit.username = username
            user_to_edit.email = email
            user_to_edit.role = role
            user_to_edit.save()
            messages.success(request, 'User updated successfully!')
        else:
            messages.error(request, 'All fields are required')
            
    return redirect('superadmin_dashboard')

# ---------------- TaskViewSet (API) ----------------
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTaskOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin' or user.role == 'admin':
            # Admins can see tasks of users assigned to them
            return Task.objects.all() if user.role == 'superadmin' else Task.objects.filter(assigned_to__assigned_admin=user)
        return Task.objects.filter(assigned_to=user)

    def perform_create(self, serializer):
        # Only admins and superadmins can create tasks
        if self.request.user.role not in ['admin', 'superadmin']:
            raise PermissionDenied("Only admins can create tasks.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        
        # If the task is being marked as completed
        if 'status' in request.data and request.data['status'] == 'completed':
            # Only the assigned user can mark a task as completed
            if task.assigned_to != request.user:
                return Response(
                    {'error': 'Only the assigned user can mark a task as completed.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='report')
    def report(self, request, pk=None):
        """
        Get the completion report for a task
        Only available for completed tasks and to admins/superadmins
        """
        task = self.get_object()
        
        if task.status != 'completed':
            return Response(
                {'error': 'Task is not completed yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if request.user.role not in ['admin', 'superadmin'] and request.user != task.assigned_to:
            return Response(
                {'error': 'You do not have permission to view this report.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return Response({
            'completion_report': task.completion_report,
            'worked_hours': task.worked_hours,
            'completed_by': task.assigned_to.username,
            'completed_on': str(task.due_date)
        })

    @action(detail=True, methods=['get'], url_path='report')
    def report(self, request, pk=None):
        """
        Admins/SuperAdmins: View completion report & worked hours for a completed task
        """
        task = self.get_object()
        user = request.user

        # Only admins/superadmins can access this endpoint
        if user.role not in ['admin', 'superadmin']:
            return Response({'error': 'You do not have permission to view this report.'},
                            status=status.HTTP_403_FORBIDDEN)

        # Task must be completed
        if task.status != 'completed':
            return Response({'error': 'Report is only available for completed tasks.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Show only the relevant fields
        report_data = {
            'task_id': task.id,
            'title': task.title,
            'assigned_to': task.assigned_to.username,
            'completion_report': task.completion_report,
            'worked_hours': task.worked_hours,
            'completed_on': str(task.due_date),  # You can change this if you have a real "completed_on" field
        }
        return Response(report_data)

# ---------------- Custom Admin Panel Views ----------------

@login_required
def superadmin_dashboard(request):
    if request.user.role != 'superadmin':
        return render(request, '403.html')
    User = get_user_model()
    all_users = User.objects.all()
    all_admins = User.objects.filter(role='admin')
    all_tasks = Task.objects.all()
    context = {
        'all_users': all_users,
        'all_admins': all_admins,
        'all_tasks': all_tasks,
    }
    return render(request, 'superadmin_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view for managing assigned users' tasks"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin role required.')
        return redirect('login')
    
    try:
        # Get all users assigned to this admin
        assigned_users = request.user.assigned_users.all()
        tasks = Task.objects.filter(assigned_to__in=assigned_users)
        
        context = {
            'tasks': tasks,
            'assigned_users': assigned_users,
            'admin_user': request.user,
            'messages': messages.get_messages(request)
        }
        
        response = render(request, 'admin_dashboard.html', context)
        response.status_code = 200
        return response
        
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return render(request, 'admin_dashboard.html', {
            'messages': messages.get_messages(request),
            'tasks': [],
            'assigned_users': []
        })

@login_required
def user_dashboard(request):
    """Dashboard view for regular users"""
    if request.user.role != 'user':
        return render(request, '403.html')
    tasks = Task.objects.filter(assigned_to=request.user)
    context = {
        'tasks': tasks,
        'messages': messages.get_messages(request)
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def delete_user(request, user_id):
    if request.user.role != 'superadmin':
        return render(request, '403.html')
    User = get_user_model()
    user_to_delete = User.objects.filter(id=user_id).first()
    if request.method == 'POST' and user_to_delete:
        if user_to_delete != request.user:  # Don't allow self-delete
            user_to_delete.delete()
    return redirect('superadmin_dashboard')

@login_required
def create_task(request):
    if request.user.role != 'superadmin':
        return render(request, '403.html')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        
        if not all([title, description, assigned_to_id, due_date]):
            messages.error(request, 'All fields are required.')
            return redirect('superadmin_dashboard')
            
        try:
            User = get_user_model()
            assigned_user = User.objects.get(id=assigned_to_id)
            Task.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_user,
                due_date=due_date,
                status='pending'
            )
            messages.success(request, 'Task created successfully!')
            return redirect('superadmin_dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('superadmin_dashboard')
            
    return redirect('superadmin_dashboard')

@login_required
def delete_task(request, task_id):
    if request.user.role != 'superadmin':
        return render(request, '403.html')
    delete_task_message = None
    task_to_delete = Task.objects.filter(id=task_id).first()
    if request.method == 'POST' and task_to_delete:
        task_to_delete.delete()
        delete_task_message = "Task deleted successfully!"
    # Re-render dashboard with message
    User = get_user_model()
    all_users = User.objects.all()
    all_admins = User.objects.filter(role='admin')
    all_tasks = Task.objects.all()
    context = {
        'all_users': all_users,
        'all_admins': all_admins,
        'all_tasks': all_tasks,
        'delete_task_message': delete_task_message,
    }
    return render(request, 'superadmin_dashboard.html', context)

@login_required
def edit_task(request, task_id):
    if request.user.role != 'superadmin':
        return render(request, '403.html')
    User = get_user_model()
    task = Task.objects.filter(id=task_id).first()
    edit_task_message = None

    if not task:
        return redirect('superadmin_dashboard')

    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        task.status = request.POST.get('status')
        try:
            task.assigned_to = User.objects.get(id=assigned_to_id)
            task.due_date = due_date
            task.save()
            edit_task_message = "Task updated successfully!"
            return redirect('superadmin_dashboard')
        except Exception as e:
            edit_task_message = f"Error: {str(e)}"

    all_users = User.objects.all()
    context = {
        'task': task,
        'all_users': all_users,
        'edit_task_message': edit_task_message,
    }
    return render(request, 'edit_task.html', context)

@login_required
def complete_task(request, task_id):
    """Handle task completion with report and worked hours"""
    if request.method != 'POST':
        return redirect('user_dashboard')

    task = Task.objects.filter(id=task_id, assigned_to=request.user).first()
    if not task:
        messages.error(request, 'Task not found or you do not have permission.')
        return redirect('user_dashboard')

    if task.status == 'completed':
        messages.error(request, 'Task is already completed.')
        return redirect('user_dashboard')

    completion_report = request.POST.get('completion_report')
    try:
        worked_hours = float(request.POST.get('worked_hours', 0))
    except ValueError:
        messages.error(request, 'Invalid worked hours value.')
        return redirect('user_dashboard')

    if not completion_report or worked_hours <= 0:
        messages.error(request, 'Please provide both completion report and valid worked hours.')
        return redirect('user_dashboard')

    task.status = 'completed'
    task.completion_report = completion_report
    task.worked_hours = worked_hours
    task.save()

    messages.success(request, 'Task marked as completed successfully!')
    return redirect('user_dashboard')

@login_required
def index(request):
    """Root view that redirects users to their appropriate dashboard based on role"""
    if request.user.role == 'superadmin':
        return redirect('superadmin_dashboard')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        return redirect('user_dashboard')
