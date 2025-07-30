# Geriatric Administration System

A comprehensive Django-based web application for managing geriatric centers, including infrastructure management, resident care, staff administration, and reporting capabilities.

## Features

- **Multi-Center Support**: Manage multiple geriatric centers from a single installation
- **Infrastructure Management**: Room and bed management with occupancy tracking
- **Resident Management**: Comprehensive resident profiles and care plans
- **Staff Management**: Task assignment, and productivity tracking
- **Medical Records**: Medication management and health monitoring
- **Reporting & Analytics**: Comprehensive reports and dashboards
- **Security & Compliance**: Healthcare data protection and audit trails

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd geriatric_admin
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements/development.txt
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Update the `.env` file with your database and Redis configuration.

6. Run database migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Start the development server:
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Project Structure

```
geriatric_admin/
├── config/                 # Django configuration
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── apps/                  # Django applications
│   ├── core/             # Core functionality and shared components
│   ├── facilities/       # Infrastructure management
│   ├── residents/        # Resident management
│   ├── staff/           # Staff management
│   ├── medical/         # Medical records and medications
│   └── reporting/       # Reports and analytics
├── static/               # Static files (CSS, JS, images)
├── templates/           # Django templates
├── media/              # User-uploaded files
└── requirements/       # Python dependencies
```

## Development

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

### Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## Deployment

See the deployment documentation for production setup instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.