# KPIs 2.0

A web application for managing and monitoring production KPIs across various plants and business units.

## Features

- User management with admin and regular user roles
- Multi-plant and business unit structure
- KPI data collection and visualization
- Equipment configuration management
- Plant layout visualization
- Historical data tracking and reporting

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy

## Setup for Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`

## Deployment

This project is configured for continuous deployment through AWS CodePipeline:

1. Code changes are pushed to GitHub
2. AWS CodePipeline detects changes and triggers the pipeline
3. AWS CodeBuild builds the application
4. AWS CodeDeploy deploys the application to the target environment

## Project Structure

- `app.py` - Main application file
- `config.py` - Configuration settings
- `wsgi.py` - WSGI entry point for production
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JS, images)
- `scripts/` - Deployment scripts for AWS CodeDeploy

## Default Admin Access

- Username: admin
- Password: PEPCODE