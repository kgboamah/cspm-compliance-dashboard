# CSPM Dashboard - System Architecture

## Overview
The CSPM Compliance Dashboard follows a 5-layer architecture pattern.

## Layers

### 1. Presentation Layer (React Frontend)
- **Technology**: React 18, TailwindCSS, Recharts
- **Port**: 3000
- **Purpose**: User interface for viewing compliance data
- **Key Components**: Dashboard, Findings Explorer, Reports

### 2. API Layer (FastAPI Backend)
- **Technology**: Python FastAPI, JWT Authentication
- **Port**: 8000
- **Purpose**: RESTful API for data access and operations
- **Key Endpoints**: /accounts, /scans, /findings, /reports

### 3. Assessment Engine
- **Technology**: Prowler, Custom Python logic
- **Purpose**: Execute compliance checks and score results
- **Key Functions**: Control mapping, Finding categorization

### 4. Data Collection Layer
- **Technology**: Boto3 (AWS SDK)
- **Purpose**: Interface with AWS APIs to retrieve configurations
- **Permissions**: ReadOnly access to AWS account

### 5. Data Persistence Layer
- **Technology**: PostgreSQL 15
- **Port**: 5432
- **Purpose**: Store all application data
- **Key Tables**: cloud_accounts, scans, findings, controls

## Communication Patterns
- Frontend ↔ Backend: REST API (JSON over HTTPS)
- Backend ↔ Database: SQLAlchemy ORM
- Backend ↔ AWS: Boto3 SDK (AWS API calls)

## Security Considerations
- JWT tokens for API authentication
- AWS credentials stored in environment variables
- Database credentials in .env file (never committed to Git)
- HTTPS for all external communication

