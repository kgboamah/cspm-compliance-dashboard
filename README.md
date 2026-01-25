# CSPM Compliance Dashboard

Automated multi-framework cloud compliance monitoring for AWS environments.

## Overview

This project automates compliance assessment across ISO 27001, NIST CSF 2.0, and PCI-DSS v4.0 frameworks for AWS cloud infrastructure.

### Key Features

- Real-time compliance monitoring across multiple frameworks
- Automated security configuration scanning
- Executive and technical reporting
- Gap analysis with remediation guidance
- Trend analysis and compliance scoring

## Technology Stack

- **Frontend**: React 18, TailwindCSS, Recharts
- **Backend**: Python FastAPI, SQLAlchemy
- **Database**: PostgreSQL 15
- **Security Tools**: Prowler, ScoutSuite
- **DevOps**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop installed
- Git installed
- 8GB RAM minimum

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR-USERNAME/cspm-compliance-dashboard.git
cd cspm-compliance-dashboard
2.	Start the development environment:
docker-compose up -d
3.	Access the application:
•	Frontend: http://localhost:3000
•	Backend API: http://localhost:8000/docs
•	Database: localhost:5432
Stopping Services
docker-compose down
Project Structure
cspm-compliance-dashboard/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── schemas/     # Pydantic schemas
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   └── pages/       # Page components
│   └── public/          # Static assets
├── database/            # Database scripts
│   ├── schema.sql       # Database schema
│   └── migrations/      # Migration scripts
├── docs/                # Documentation
│   ├── architecture/    # Architecture diagrams
│   └── api/             # API documentation
└── docker-compose.yml   # Docker configuration
Development Timeline
•	Weeks 1-2: Planning & Setup ✅
•	Weeks 3-4: Backend Foundation
•	Weeks 5-6: Assessment Engine
•	Weeks 7-8: Frontend Dashboard
•	Weeks 9-10: Reporting & Enhancement
•	Weeks 11-12: Testing & Documentation
License
This project is part of a Master’s degree capstone project.
Author
Kwaku Gyamfi Boamah - MS Cybersecurity, Winter 2026, GVSU 
