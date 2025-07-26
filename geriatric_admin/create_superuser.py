#!/usr/bin/env python
"""
Script to create a superuser for testing purposes.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.core.models import User
from apps.core.utils import generate_employee_id

def create_superuser():
    """Create a superuser for testing."""
    
    # Check if superuser already exists
    if User.objects.filter(username='admin').exists():
        print("Superuser 'admin' already exists.")
        return
    
    # Generate employee ID
    employee_id = generate_employee_id('ADM')
    
    # Create superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        employee_id=employee_id,
        first_name='System',
        last_name='Administrator'
    )
    
    print(f"Superuser created successfully!")
    print(f"Username: {user.username}")
    print(f"Employee ID: {user.employee_id}")
    print(f"Email: {user.email}")
    print(f"Password: admin123")

if __name__ == '__main__':
    create_superuser()