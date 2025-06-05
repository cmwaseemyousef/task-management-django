# Task Management API Guide

## Authentication

First, get your JWT token:
```bash
curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"superadmin\",\"password\":\"admin123\"}"
```

## Tasks API

### List Tasks
```bash
curl http://127.0.0.1:8000/api/tasks/ -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Create Task
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New API Task",
    "description": "Task created via API",
    "assigned_to": 3,
    "due_date": "2025-06-10",
    "status": "pending"
  }'
```

### Update Task
```bash
curl -X PATCH http://127.0.0.1:8000/api/tasks/1/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "completion_report": "Task completed via API",
    "worked_hours": 2.5
  }'
```

### Get Task Report
```bash
curl http://127.0.0.1:8000/api/tasks/1/report/ -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Token Refresh
```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

## Usage Notes:

1. Replace `YOUR_TOKEN_HERE` with the access token from authentication
2. Replace task IDs (e.g., `/tasks/1/`) with actual task IDs
3. Adjust user IDs in task creation (`assigned_to`) based on your users
4. Dates should be in YYYY-MM-DD format

## Permissions:

- Superadmin: Full access to all tasks and operations
- Admin: Can view/manage tasks of assigned users
- User: Can only view and update their own tasks
