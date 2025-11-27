# app/routers/customer_api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.deps import get_db, get_current_user
from app.api_auth import (
    require_api_key,
    require_api_key_scopes,
    get_current_api_key_info
)

from app.models import User, Transaction
from pydantic import BaseModel

router = APIRouter(tags=["Customer"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class CustomerProfileResponse(BaseModel):
    email: str
    full_name: Optional[str]
    mobile: Optional[str]
    org_id: Optional[int]
    onboarding_complete: bool


class TransactionCreate(BaseModel):
    transaction_ref: str
    amount: int
    currency: str = "INR"
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


class ProfileUpdateRequest(BaseModel):
    business_name: str
    phone: str
    payment_gateways: List[str]
    website: Optional[str] = None
    monthly_volume: Optional[str] = None
    industry: Optional[str] = None
    gst_number: Optional[str] = None
    recovery_channels: Optional[List[str]] = None
    email: Optional[str] = None
    
    # Phase 2 Fields
    business_size: Optional[str] = None
    monthly_gmv: Optional[str] = None
    recovery_destination: Optional[str] = "customer"
    gateway_credentials: Optional[dict] = None
    brand_name: Optional[str] = None
    support_email: Optional[str] = None
    reply_to_email: Optional[str] = None
    logo_url: Optional[str] = None
    team_contacts: Optional[dict] = None
    billing_email: Optional[str] = None


# ... (get_profile remains same) ...


@router.post("/profile", response_model=CustomerProfileResponse)
def create_or_update_profile(
    profile_data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return complete_onboarding(profile_data, db, current_user)


@router.post("/onboarding", response_model=CustomerProfileResponse)
def complete_onboarding(
    profile_data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete user onboarding by creating/updating organization and profile.
    Alternative endpoint to POST /profile with unique path.
    """
    from app.models import Organization
    import re
    
    # Find the user
    user = db.query(User).filter(User.email == current_user.email).first()
    
    if not user:
        raise HTTPException(404, "User not found")
    
    # Create or find organization
    if not user.org_id:
        # Generate a slug from business name
        slug_base = re.sub(r'[^a-z0-9]+', '-', profile_data.business_name.lower()).strip('-')
        slug = slug_base
        counter = 1
        
        # Ensure slug is unique
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{slug_base}-{counter}"
            counter += 1
        
        # Create new organization
        org = Organization(
            name=profile_data.business_name,
            slug=slug,
            is_active=True,
            
            # Basic Fields
            website=profile_data.website,
            industry=profile_data.industry,
            gst_number=profile_data.gst_number,
            payment_gateways=profile_data.payment_gateways,
            monthly_volume=profile_data.monthly_volume,
            recovery_channels=profile_data.recovery_channels or [],
            
            # Phase 2 Fields
            business_size=profile_data.business_size,
            monthly_gmv=profile_data.monthly_gmv,
            recovery_destination=profile_data.recovery_destination,
            gateway_credentials=profile_data.gateway_credentials or {},
            brand_name=profile_data.brand_name,
            support_email=profile_data.support_email,
            reply_to_email=profile_data.reply_to_email,
            logo_url=profile_data.logo_url,
            team_contacts=profile_data.team_contacts or {},
            billing_email=profile_data.billing_email
        )
        db.add(org)
        db.flush()  # Get the org.id without committing
        
        user.org_id = org.id
    
    # Update user profile
    user.full_name = profile_data.business_name
    user.mobile_number = profile_data.phone
    
    db.commit()
    db.refresh(user)
    
    return CustomerProfileResponse(
        email=user.email,
        full_name=user.full_name,
        mobile=user.mobile_number,
        org_id=user.org_id,
        onboarding_complete=True
    )


# ---------------------------------------------------------
# 2️⃣ MERCHANT PROFILE (API KEY auth)
# ---------------------------------------------------------
@router.get("/merchant/profile")
def get_merchant_profile(
    current_user: User = Depends(require_api_key),
    api_key_info: Optional[dict] = Depends(get_current_api_key_info)
):
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "account_type": current_user.account_type,
        },
        "organization": {
            "id": current_user.organization.id,
            "name": current_user.organization.name,
            "slug": current_user.organization.slug
        },
        "api_key_info": api_key_info,
    }


# ---------------------------------------------------------
# 3️⃣ CUSTOMER TRANSACTIONS (JWT)
# ---------------------------------------------------------
@router.get("/transactions", response_model=List[TransactionResponse])
def list_customer_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    txns = (
        db.query(Transaction)
        .filter(Transaction.customer_email == current_user.email)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return [
        TransactionResponse(
            id=t.id,
            transaction_ref=t.transaction_ref,
            amount=t.amount,
            currency=t.currency,
            customer_email=t.customer_email,
            customer_phone=t.customer_phone,
            created_at=t.created_at,
        )
        for t in txns
    ]


# ---------------------------------------------------------
# 4️⃣ MERCHANT TRANSACTIONS (API KEY)
# ---------------------------------------------------------
@router.get("/merchant/transactions", response_model=List[TransactionResponse])
def list_transactions_merchant(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_api_key),
    db: Session = Depends(get_db)
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.org_id == current_user.org_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [TransactionResponse.model_validate(t) for t in transactions]


# ---------------------------------------------------------
# 5️⃣ MERCHANT — Create Transaction
# ---------------------------------------------------------
@router.post("/merchant/transactions", response_model=TransactionResponse)
def create_transaction(
    tx: TransactionCreate,
    current_user: User = Depends(require_api_key_scopes(["write"])),
    db: Session = Depends(get_db)
):
    existing = db.query(Transaction).filter(
        Transaction.transaction_ref == tx.transaction_ref,
        Transaction.org_id == current_user.org_id
    ).first()

    if existing:
        raise HTTPException(400, "Transaction ref already exists")

    record = Transaction(
        transaction_ref=tx.transaction_ref,
        amount=tx.amount,
        currency=tx.currency,
        customer_email=tx.customer_email,
        customer_phone=tx.customer_phone,
        org_id=current_user.org_id
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return TransactionResponse.model_validate(record)


# ---------------------------------------------------------
# 6️⃣ DELETE ACCOUNT
# ---------------------------------------------------------
@router.delete("/profile")
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete the current user and their organization.
    """
    from app.models import Organization
    
    # Delete Organization (if exists)
    if current_user.org_id:
        org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
        if org:
            db.delete(org)
    
    # Delete User
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}
