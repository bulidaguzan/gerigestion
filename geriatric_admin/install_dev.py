#!/usr/bin/env python
"""
Simple development installation script for Geriatric Administration System.
This script sets up a basic development environment without external dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description, check=True):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return result.stdout
        else:
            print(f"⚠ {description} completed with warnings: {result.stderr}")
            return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return None

def setup_virtual_environment():
    """Create virtual environment."""
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
        python_path = "venv\\Scripts\\python"
    else:  # Unix-like
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
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
        
        # Update .env for development without external dependencies
        with open(env_file, 'a') as f:
            f.write("\n# Development settings (SQLite fallback)\n")
            f.write("DEBUG=True\n")
            f.write("USE_SQLITE=True\n")
        
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
        "backups",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def run_django_setup():
    """Run Django setup commands."""
    # Determine the correct python path based on OS
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix-like
        python_path = "venv/bin/python"
    
    # Set Django settings module for development
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
    
    # Run migrations
    result = run_command(
        f"{python_path} manage.py migrate",
        "Running initial database migrations"
    )
    
    if result is not None:
        # Collect static files
        run_command(
            f"{python_path} manage.py collectstatic --noinput",
            "Collecting static files"
        )
        
        # Check configuration
        run_command(
            f"{python_path} manage.py check_config --database-only",
            "Checking database configuration",
            check=False
        )
    
    return result is not None

def main():
    """Main setup function."""
    print("=== Geriatric Administration System - Simple Development Setup ===\n")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("✗ Python 3.9+ is required")
        sys.exit(1)
    print("✓ Python version is compatible")
    
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
    
    # Run Django setup
    if not run_django_setup():
        print("\n⚠ Django setup completed with warnings")
    
    print("\n=== Setup Complete ===")
    print("Development environment is ready!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Start the development server:")
    print("   python manage.py runserver")
    print("\nNote: This setup uses SQLite for development.")
    print("For production, configure PostgreSQL and Redis in the .env file.")

if __name__ == "__main__":
    main()