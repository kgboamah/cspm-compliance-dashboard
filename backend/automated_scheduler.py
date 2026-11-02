"""
Automated Email Scheduler - Runs inside FastAPI
Add this to your backend to auto-send weekly emails every Monday
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import atexit

def setup_email_scheduler():
    """
    Setup automatic weekly email scheduler
    Runs every Monday at 9:00 AM
    """
    scheduler = BackgroundScheduler()
    
    # Import the weekly summary function
    from weekly_email_scheduler import send_weekly_summaries
    
    # Schedule weekly summary emails every Monday at 9:00 AM
    scheduler.add_job(
        func=send_weekly_summaries,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_summary_email',
        name='Send weekly compliance summary emails',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    print("[Scheduler] ✅ Weekly email scheduler started - runs every Monday at 9:00 AM")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler


# ============================================
# ADD TO backend/app/main.py:
# ============================================
# 
# At the top, import:
# from automated_scheduler import setup_email_scheduler
#
# After creating the FastAPI app, add:
# @app.on_event("startup")
# async def startup_event():
#     setup_email_scheduler()
#     print("✅ Application started with automated email scheduler")
