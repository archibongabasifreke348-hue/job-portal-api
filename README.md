# Job Portal API

A Flask-based REST API for a simple job portal.

The application allows users to register and log in, companies to be added, jobs to be posted, and users to apply for available jobs.

## Features

- User registration
- Secure password hashing
- User login
- Add companies
- View companies
- Add jobs
- View available jobs
- Filter jobs by location
- Delete jobs
- Apply for jobs
- Prevent duplicate job applications
- View a user's applications
- View applicants for a specific job
- SQLite database
- Automated testing with pytest
- Code coverage with pytest-cov
- Code quality checking with Ruff
- Continuous Integration with GitHub Actions

## Technologies

- Python
- Flask
- SQLite
- Werkzeug Security
- pytest
- pytest-cov
- Ruff
- GitHub Actions

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
│
├── tests/
│   ├── conftest.py
│   └── test_app.py
│
└── .github/
    └── workflows/
        └── ci.yml