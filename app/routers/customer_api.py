"""
Customer API endpoints - demonstrating API key authentication
These are the endpoints Ram would use with his API keys
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db
from ..models import User, Transaction, Organization
from ..api_auth import require_api_key, require_api_key_scopes, get_current_api_key_info
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/v1/customer", tags=["customer-api"])


class TransactionCreate(BaseModel):
    transaction_ref: str
    amount: int
    currency: str = "USD"
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    transaction_ref: str
    amount: Optional[int]
    currency: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApiKeyUsageResponse(BaseModel):
    key_name: str
    scopes: List[str]
    usage_count: int
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


@router.get("/profile")
def get_customer_profile(
    current_user: User = Depends(require_api_key),
    api_key_info: Optional[dict] = Depends(get_current_api_key_info)
):
    """
    Get customer profile information
    Requires: Valid API key (any scope)
    
    Example usage for Ram:
    curl -H "Authorization: Bearer sk_your_api_key_here" \\
         http://localhost:8010/v1/customer/profile
    """
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "account_type": current_user.account_type,
            "is_active": current_user.is_active
        },
        "organization": {
            "id": current_user.organization.id,
            "name": current_user.organization.name,
            "slug": current_user.organization.slug
        },
        "api_key_info": api_key_info
    }


@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_api_key),
    db: Session = Depends(get_db)
):
    """
    List customer's transactions
    Requires: API key with 'read' scope
    
    Example usage for Ram:
    curl -H "X-API-Key: sk_your_api_key_here" \\
         "http://localhost:8010/v1/customer/transactions?limit=10"
    """
    transactions = db.query(Transaction).filter(
        Transaction.org_id == current_user.org_id
    ).offset(offset).limit(limit).all()
    
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.post("/transactions", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(require_api_key_scopes(["write"])),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction
    Requires: API key with 'write' scope
    
    Example usage for Ram:
    curl -X POST \\
         -H "Authorization: Bearer sk_your_api_key_here" \\
         -H "Content-Type: application/json" \\
         -d '{"transaction_ref": "TXN-001", "amount": 10000, "currency": "USD"}' \\
         http://localhost:8010/v1/customer/transactions
    """
    # Check if transaction ref already exists in this org
    existing = db.query(Transaction).filter(
        Transaction.transaction_ref == transaction_data.transaction_ref,
        Transaction.org_id == current_user.org_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction reference '{transaction_data.transaction_ref}' already exists"
        )
    
    # Create transaction
    transaction = Transaction(
        transaction_ref=transaction_data.transaction_ref,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        customer_email=transaction_data.customer_email,
        customer_phone=transaction_data.customer_phone,
        org_id=current_user.org_id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.model_validate(transaction)


@router.get("/transactions/{transaction_ref}", response_model=TransactionResponse)
def get_transaction(
    transaction_ref: str,
    current_user: User = Depends(require_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a specific transaction by reference
    Requires: API key with 'read' scope
    
    Example usage for Ram:
    curl -H "Authorization: Bearer sk_your_api_key_here" \\
         http://localhost:8010/v1/customer/transactions/TXN-001
    """
    transaction = db.query(Transaction).filter(
        Transaction.transaction_ref == transaction_ref,
        Transaction.org_id == current_user.org_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_ref}' not found"
        )
    
    return TransactionResponse.model_validate(transaction)


@router.get("/api-key/usage", response_model=ApiKeyUsageResponse)
def get_api_key_usage(
    api_key_info: dict = Depends(get_current_api_key_info)
):
    """
    Get current API key usage statistics
    Requires: Valid API key
    
    Example usage for Ram:
    curl -H "X-API-Key: sk_your_api_key_here" \\
         http://localhost:8010/v1/customer/api-key/usage
    """
    if not api_key_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint requires API key authentication"
        )
    
    return ApiKeyUsageResponse(**api_key_info)


@router.get("/organization/stats")
def get_organization_stats(
    current_user: User = Depends(require_api_key),
    db: Session = Depends(get_db)
):
    """
    Get organization statistics
    Requires: API key with 'read' scope
    
    Example usage for Ram:
    curl -H "Authorization: Bearer sk_your_api_key_here" \\
         http://localhost:8010/v1/customer/organization/stats
    """
    # Count transactions
    total_transactions = db.query(Transaction).filter(
        Transaction.org_id == current_user.org_id
    ).count()
    
    # Count users in organization
    total_users = db.query(User).filter(
        User.org_id == current_user.org_id,
        User.is_active == True
    ).count()
    
    return {
        "organization": {
            "name": current_user.organization.name,
            "slug": current_user.organization.slug,
            "total_transactions": total_transactions,
            "total_active_users": total_users
        },
        "requested_by": {
            "user_email": current_user.email,
            "account_type": current_user.account_type
        }
    }