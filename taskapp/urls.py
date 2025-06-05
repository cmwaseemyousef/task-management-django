from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, 
    superadmin_dashboard,
    admin_dashboard,
    user_dashboard,
    delete_user,
    create_user,
    change_user_role,
    create_task,
    delete_task,
    edit_task,
    edit_user,
    complete_task,
    index  # Add the new view
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# API Router
router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')

urlpatterns = [
    # Root URL
    path('', index, name='index'),
    
    # Authentication
    path('', include('taskapp.auth_urls')),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Dashboard views
    path('superadmin/dashboard/', superadmin_dashboard, name='superadmin_dashboard'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('user/dashboard/', user_dashboard, name='user_dashboard'),

    # User management (SuperAdmin)
    path('superadmin/create-user/', create_user, name='create_user'),
    path('superadmin/delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('superadmin/change-role/<int:user_id>/', change_user_role, name='change_user_role'),
    path('superadmin/edit-user/<int:user_id>/', edit_user, name='edit_user'),  # Add this line

    # Task management (SuperAdmin)
    path('superadmin/create-task/', create_task, name='create_task'),
    path('superadmin/delete-task/<int:task_id>/', delete_task, name='delete_task'),
    path('superadmin/edit-task/<int:task_id>/', edit_task, name='edit_task'),
    path('task/<int:task_id>/complete/', complete_task, name='complete_task'),
]
