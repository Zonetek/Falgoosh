# Shodan.io Clone

A Django-based REST API service that provides similar functionality to Shodan.io - a search engine for Internet-connected devices.

## Features

- User Authentication & Authorization
- Device Scanning & Indexing
- Search Functionality
- Billing System
- Activity Logging
- Session Management
- Reports Generation
- Notifications System
- Admin Tools

## Tech Stack

- Python 3.12.7
- Django 5.2
- Django REST Framework
- PostgreSQL (Production)
- SQLite (Development)
- JWT Authentication
- Django AllAuth

## Project Structure

```
backend/
├── api_applications/      # Main applications directory
│   ├── accounts/         # User management
│   ├── scan/            # Device scanning
│   ├── indexer/         # Data indexing
│   ├── search/          # Search functionality
│   ├── billing/         # Payment & subscription
│   ├── reports/         # Report generation
│   └── ...
├── config/              # Project configuration
│   ├── settings/        # Split settings
│   │   ├── base.py     # Base settings
│   │   ├── dev.py      # Development settings
│   │   └── prod.py     # Production settings
│   └── ...
├── utils/               # Utility files
│   ├── static/         # Static files
│   └── templates/      # HTML templates
└── requirements/        # Project dependencies
    ├── base.txt        # Base requirements
    └── dev.txt         # Development requirements
```

## Setup & Installation

1. Clone the repository
```bash
git clone [repository-url]
cd shodan
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r backend/requirements/dev.txt
```

4. Create .env file in backend directory
```bash
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

5. Apply migrations
```bash
cd backend
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

## Running the Project

### Development
```bash
python manage.py runserver
```

### Production
```bash
python manage.py collectstatic
python manage.py runserver --settings=config.settings.prod
```

## API Documentation

The API documentation is available at `/api/docs/` when the server is running.

## dockerize help

After your container coming up and django server run, you can see urls in 127.0.0.1:8000 not in 0.0.0.0:8000

## Testing

```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

No licence yet.