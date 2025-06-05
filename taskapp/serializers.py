from rest_framework import serializers
from .models import Task, CustomUser
from django.contrib.auth import get_user_model

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        
    def validate(self, data):
        # Get status being set (if updating, fall back to instance status)
        status = data.get('status') or getattr(self.instance, 'status', None)
        completion_report = data.get('completion_report') or getattr(self.instance, 'completion_report', None)
        worked_hours = data.get('worked_hours') or getattr(self.instance, 'worked_hours', None)

        # Require completion_report and worked_hours if status is completed
        if status == 'completed':
            if not completion_report:
                raise serializers.ValidationError({
                    'completion_report': 'Completion report is required when marking a task as completed.'
                })
            if worked_hours is None:
                raise serializers.ValidationError({
                    'worked_hours': 'Worked hours are required when marking as completed.'
                })
            
            # Additional validation for worked_hours
            try:
                if float(worked_hours) <= 0:
                    raise serializers.ValidationError({
                        'worked_hours': 'Worked hours must be greater than 0.'
                    })
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'worked_hours': 'Worked hours must be a valid number.'
                })
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'role']
