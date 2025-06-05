curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"superadmin\",\"password\":\"admin123\"}"import requests
import json
from datetime import datetime, timedelta

# API Base URL
BASE_URL = 'http://127.0.0.1:8000'

def print_response(response, description=""):
    """Print API response in a formatted way"""
    print(f"\n=== {description} ===")
    print(f"Status Code: {response.status_code}")
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("=" * 50)

def get_token(username, password):
    """Get JWT token for authentication"""
    print(f"\nGetting token for user: {username}")
    response = requests.post(
        f'{BASE_URL}/api/token/',
        json={'username': username, 'password': password}
    )
    print_response(response, "Token Response")
    if response.status_code == 200:
        return response.json()
    return None

def get_tasks(token):
    """Get list of tasks"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/api/tasks/', headers=headers)
    print_response(response, "Get Tasks")
    return response.json() if response.status_code == 200 else None

def create_task(token, task_data):
    """Create a new task"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f'{BASE_URL}/api/tasks/',
        headers=headers,
        json=task_data
    )
    print_response(response, "Create Task")
    return response.json() if response.status_code in [200, 201] else None

def update_task(token, task_id, task_data):
    """Update an existing task"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.patch(
        f'{BASE_URL}/api/tasks/{task_id}/',
        headers=headers,
        json=task_data
    )
    print_response(response, "Update Task")
    return response.json() if response.status_code == 200 else None

def get_task_report(token, task_id):
    """Get task completion report"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{BASE_URL}/api/tasks/{task_id}/report/',
        headers=headers
    )
    print_response(response, "Task Report")
    return response.json() if response.status_code == 200 else None

# Test the API with different user roles
def test_api():
    # Test with superadmin
    print("\n=== Testing with Superadmin ===")
    token_data = get_token('superadmin', 'admin123')
    if not token_data:
        print("Failed to get superadmin token")
        return
    
    superadmin_token = token_data['access']
    
    # Get all tasks as superadmin
    tasks = get_tasks(superadmin_token)
    
    # Create a new task
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    new_task = {
        'title': 'API Test Task',
        'description': 'Task created via API',
        'assigned_to': 4,  # Make sure this ID exists in your database
        'due_date': tomorrow,
        'status': 'pending'
    }
    created_task = create_task(superadmin_token, new_task)
    
    # Test with regular user
    print("\n=== Testing with Regular User ===")
    token_data = get_token('user', 'user123')
    if not token_data:
        print("Failed to get user token")
        return
        
    user_token = token_data['access']
    
    # Get user's tasks
    user_tasks = get_tasks(user_token)
    
    # Try to complete a task
    if user_tasks:
        task_id = user_tasks[0]['id']
        completion_data = {
            'status': 'completed',
            'completion_report': 'Task completed via API',
            'worked_hours': 2.5
        }
        completed_task = update_task(user_token, task_id, completion_data)
        
        if completed_task:
            # Get task report
            report = get_task_report(superadmin_token, task_id)
            print(json.dumps(report, indent=2))

def main():
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Make sure it's running at", BASE_URL)
    except Exception as e:
        print("\nError occurred:", str(e))

if __name__ == '__main__':
    main()
