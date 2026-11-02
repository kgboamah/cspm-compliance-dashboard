"""
Cloud Accounts API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.cloud_account import CloudAccount
from app.schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountUpdate,
    CloudAccountResponse
)


router = APIRouter(
    prefix="/api/cloud-accounts",
    tags=["Cloud Accounts"]
)


@router.post("/", status_code=201)
def create_cloud_account(
    account: CloudAccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new cloud account"""
    
    try:
        # Check if account already exists
        existing = db.query(CloudAccount).filter(
            CloudAccount.account_id == account.account_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Account with account_id {account.account_id} already exists"
            )
        
        # Create new cloud account
        db_account = CloudAccount(
            account_name=account.account_name,
            cloud_provider=account.cloud_provider,
            account_id=account.account_id,
            regions=account.regions,
            is_active=account.is_active,
            credentials=account.credentials
        )
        
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        
        # Return as dictionary to avoid Pydantic validation issues
        return {
            "id": str(db_account.id),
            "account_name": db_account.account_name,
            "cloud_provider": db_account.cloud_provider,
            "account_id": db_account.account_id,
            "regions": db_account.regions if db_account.regions else [],
            "is_active": db_account.is_active,
            "created_at": db_account.created_at.isoformat() if db_account.created_at else None,
            "updated_at": db_account.updated_at.isoformat() if db_account.updated_at else None
        }
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Database integrity error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"Error creating cloud account: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating cloud account: {str(e)}"
        )


@router.get("/")
def list_cloud_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all cloud accounts"""
    
    accounts = db.query(CloudAccount).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(acc.id),
            "account_name": acc.account_name,
            "cloud_provider": acc.cloud_provider,
            "account_id": acc.account_id,
            "regions": acc.regions if acc.regions else [],
            "is_active": acc.is_active,
            "created_at": acc.created_at.isoformat() if acc.created_at else None,
            "updated_at": acc.updated_at.isoformat() if acc.updated_at else None
        }
        for acc in accounts
    ]


@router.get("/{account_id}")
def get_cloud_account(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific cloud account"""
    
    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    return {
        "id": str(account.id),
        "account_name": account.account_name,
        "cloud_provider": account.cloud_provider,
        "account_id": account.account_id,
        "regions": account.regions if account.regions else [],
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.put("/{account_id}")
def update_cloud_account(
    account_id: UUID,
    account_update: CloudAccountUpdate,
    db: Session = Depends(get_db)
):
    """Update a cloud account"""
    
    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    # Update only provided fields
    update_data = account_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(account, field, value)
    
    try:
        db.commit()
        db.refresh(account)
        
        return {
            "id": str(account.id),
            "account_name": account.account_name,
            "cloud_provider": account.cloud_provider,
            "account_id": account.account_id,
            "regions": account.regions if account.regions else [],
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating cloud account: {str(e)}"
        )


@router.delete("/{account_id}")
def delete_cloud_account(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a cloud account"""
    
    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    try:
        db.delete(account)
        db.commit()
        return {"message": "Cloud account deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting cloud account: {str(e)}"
        )
