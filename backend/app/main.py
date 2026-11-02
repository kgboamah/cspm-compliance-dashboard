"""
FastAPI Main Application - WITH AUTOMATIC WEEKLY EMAIL SCHEDULER + MFA
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# Import routers from the routers folder
from app.routers import cloud_accounts, scans, scores, email, auth, users
from app.auth.mfa_routes import router as mfa_router
from app.routers import audit_logs

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="CSPM Compliance Dashboard API",
    description="Cloud Security Posture Management and Compliance Monitoring",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cloud_accounts.router)
app.include_router(scans.router)
app.include_router(scores.router)
app.include_router(email.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(mfa_router)  # MFA routes
app.include_router(audit_logs.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CSPM Compliance Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============================================
# AUTOMATIC EMAIL SCHEDULER - STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    Initializes the automatic weekly email scheduler
    """
    try:
        from automated_scheduler import setup_email_scheduler
        setup_email_scheduler()
        print("✅ Application started with automated weekly email scheduler")
        print("   📧 Weekly summary emails will be sent every Monday at 9:00 AM")
    except Exception as e:
        print(f"⚠️ Warning: Could not start email scheduler: {e}")
        print("   Application will continue without automated emails")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Application shutting down...")
