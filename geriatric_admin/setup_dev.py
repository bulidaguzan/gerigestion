#!/usr/bin/env python
"""
Development setup script for Geriatric Administration System.
This script helps set up the development environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return None

def check_prerequisites():
    """Check if required software is installed."""
    print("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("✗ Python 3.9+ is required")
        return False
    print("✓ Python version is compatible")
    
    # Check if PostgreSQL is available
    pg_result = run_command("pg_config --version", "Checking PostgreSQL")
    if not pg_result:
        print("⚠ PostgreSQL not found. Please install PostgreSQL 12+")
        return False
    
    # Check if Redis is available
    redis_result = run_command("redis-cli --version", "Checking Redis")
    if not redis_result:
        print("⚠ Redis not found. Please install Redis 6+")
        return False
    
    return True

def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    result = run_command("python -m venv venv", "Creating virtual environment")
    return result is not None

def install_dependencies():
    """Install Python dependencies."""
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix-like
        pip_path = "venv/bin/pip"
    
    # Upgrade pip first
    run_command(f"{pip_path} install --upgrade pip", "Upgrading pip")
    
    # Install development dependencies
    result = run_command(
        f"{pip_path} install -r requirements/development.txt",
        "Installing development dependencies"
    )
    return result is not None

def setup_environment_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠ Please update .env file with your database and Redis configuration")
        return True
    else:
        print("✗ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "media/uploads",
        "staticfiles",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def run_initial_migrations():
    """Run initial database migrations."""
    # Determine the correct python path based on OS
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix-like
        python_path = "venv/bin/python"
    
    # Run migrations
    result = run_command(
        f"{python_path} manage.py migrate",
        "Running initial database migrations"
    )
    return result is not None

def main():
    """Main setup function."""
    print("=== Geriatric Administration System - Development Setup ===\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed. Please install required software.")
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("\n✗ Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Failed to install dependencies")
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        print("\n✗ Failed to setup environment file")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n=== Setup Complete ===")
    print("Next steps:")
    print("1. Update the .env file with your database and Redis configuration")
    print("2. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Run database migrations:")
    print("   python manage.py migrate")
    print("4. Create a superuser:")
    print("   python manage.py createsuperuser")
    print("5. Start the development server:")
    print("   python manage.py runserver")

if __name__ == "__main__":
    main()