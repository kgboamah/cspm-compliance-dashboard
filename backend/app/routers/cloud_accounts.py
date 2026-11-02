from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cloud_account import CloudAccount
from app.schemas.cloud_account import CloudAccountCreate
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/cloud-accounts", tags=["Cloud Accounts"])

@router.post("/")
async def create_cloud_account(account: CloudAccountCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(CloudAccount).filter(CloudAccount.account_id == account.account_id).first()
        if existing:
            return JSONResponse(status_code=400, content={"detail": f"Account exists"})
        
        db_account = CloudAccount(
            account_name=account.account_name,
            cloud_provider=account.cloud_provider,
            account_id=account.account_id,
            regions=list(account.regions) if account.regions else [],
            is_active=True if account.is_active is None else account.is_active,
            credentials=dict(account.credentials) if account.credentials else {}
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        
        result = {
            "id": str(db_account.id),
            "account_name": str(db_account.account_name),
            "cloud_provider": str(db_account.cloud_provider),
            "account_id": str(db_account.account_id),
            "regions": list(db_account.regions) if db_account.regions else [],
            "is_active": bool(db_account.is_active),
            "created_at": db_account.created_at.isoformat() if db_account.created_at else None,
            "updated_at": db_account.updated_at.isoformat() if db_account.updated_at else None
        }
        return JSONResponse(status_code=201, content=result)
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/")
async def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(CloudAccount).all()
    return JSONResponse(content=[{"id": str(a.id), "account_name": str(a.account_name)} for a in accounts])
