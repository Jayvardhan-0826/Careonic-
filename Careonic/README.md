# Careonic

A simple Django-based web application for tracking health metrics such as blood pressure, weight, diet, and symptoms, with secure user authentication including a PIN-based security layer.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features
- **User Authentication**: Secure login with username, password, and a 4-digit PIN.
- **Health Tracking**: Log and view blood pressure, weight, diet, and symptom data with date-based filtering.
- **Responsive Design**: Mobile-friendly interface using Bootstrap.
- **Data Encryption**: PINs are encrypted using the `cryptography.fernet` library for security.
- **Error Handling**: Robust error messages and logging for debugging.
- **Loading States**: Visual feedback during form submissions.

## Prerequisites
- Python 3.12.4 or higher
- Django 4.2.11
- pip (Python package manager)
- Virtual environment (recommended)
- Git (for version control)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Mdwaseel/Careonic.git
cd Careonic
```

### 2. Set Up a Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install django==4.2.11 cryptography python-decouple
```

### 4. Configure Environment Variables
Create a `.env` file in the project root and add the following:

```text
FERNET_KEY=<your-32-byte-base64-encoded-key>  # Generate with `Fernet.generate_key()`
SECRET_KEY=<your-django-secret-key>  # Generate with `django.core.management.utils.get_random_secret_key()`
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=127.0.0.1,localhost  # Add your domain in production
```

Generate a `FERNET_KEY` by running:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Generate a `SECRET_KEY` by running:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 5. Apply Migrations
```bash
python manage.py makemigrations app
python manage.py migrate
```

### 6. Create a Superuser
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/ in your browser.

## Configuration

- **Settings**: Update `careonic/settings.py` with your production settings (e.g., `DEBUG = False`, `ALLOWED_HOSTS`).
- **Templates**: Ensure `templates/app/` contains `base.html`, `login.html`, and `bp_tracking.html`.
- **Static Files**: Collect static files for production:
```bash
python manage.py collectstatic
```

## Usage

### Login:
- Access the login page at `/`.
- Enter your username, password, and 4-digit PIN (set during signup).
- Click "Login" to access the dashboard.

### Health Tracking:
- Navigate to the `/bp_tracking/` page after logging in.
- Fill out forms for blood pressure, weight, diet, or symptoms.
- Use "Submit All" to save all valid entries or individual submit buttons for single entries.
- View logged data filtered by date.

### Forgot PIN:
- Use the "Forgot your PIN?" link on the login page (if implemented) to reset your PIN.

## Development

### Project Structure
```text
careonic/
├── app/
│   ├── migrations/
│   ├── templates/
│   │   ├── app/
│   │   │   ├── base.html
│   │   │   ├── login.html
│   │   │   ├── bp_tracking.html
│   ├── templatetags/
│   │   ├── app_filters.py
│   ├── models.py
│   ├── views.py
├── careonic/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
├── manage.py
├── .env
├── README.md
```

### Running Tests
```bash
python manage.py test app
```

### Adding Features
- Add new health metrics by extending `models.py` and updating `bp_tracking` views/templates.
- Enhance security with two-factor authentication or OAuth.

### Custom Filters
The `add_class` filter is defined in `app/templatetags/app_filters.py` to add CSS classes to form fields. Example content:

```python
from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()})
```

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit changes (`git commit -m "Add feature-name"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
- **Author**: Md Waseel Mohiuddin  
- **Email**: mdwaseel2311@gmail.com  
- **GitHub**: Mdwaseel 
