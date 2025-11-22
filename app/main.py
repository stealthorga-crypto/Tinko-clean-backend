from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import dev_test_email
from dotenv import load_dotenv
load_dotenv()


from app.routers import (
    auth,
    email_auth,
    customer_api,
    payments,
    payments_razorpay,
    stripe_payments,
    razorpay_webhooks,
    webhooks_stripe,
    recoveries,
    recovery_links,
    retry,
    retry_policies,
    events,
    analytics,
    schedule,
    recon,
    maintenance,
    profile,
    classifier,
    dev,
    admin_db,
    early_access,
)

app = FastAPI(
    title="Tinko Backend API",
    version="1.0.0"
)

# CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])
app.include_router(email_auth.router, prefix="/v1/auth", tags=["Auth"])
app.include_router(customer_api.router, prefix="/v1/customer", tags=["Customer API"])
app.include_router(payments.router, prefix="/v1/payments", tags=["Payments"])
app.include_router(payments_razorpay.router, prefix="/v1/payments/razorpay", tags=["Razorpay Payments"])
app.include_router(stripe_payments.router, prefix="/v1/payments/stripe", tags=["Stripe Payments"])
app.include_router(razorpay_webhooks.router, prefix="/v1/webhooks/razorpay", tags=["Razorpay Webhooks"])
app.include_router(webhooks_stripe.router, prefix="/v1/webhooks/stripe", tags=["Stripe Webhooks"])
app.include_router(recoveries.router, prefix="/v1/recoveries", tags=["Recoveries"])
app.include_router(recovery_links.router, prefix="/v1/recovery-links", tags=["Recovery Links"])
app.include_router(retry.router, prefix="/v1/retry", tags=["Retry"])
app.include_router(retry_policies.router, prefix="/v1/retry/policies", tags=["Retry Policies"])
app.include_router(events.router, prefix="/v1/events", tags=["Events"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(schedule.router, prefix="/v1/schedule", tags=["Schedule"])
app.include_router(recon.router, prefix="/v1/recon", tags=["Reconciliation"])
app.include_router(maintenance.router, prefix="/v1/maintenance", tags=["Maintenance"])
app.include_router(profile.router, prefix="/v1/profile", tags=["Profile"])
app.include_router(classifier.router, prefix="/v1/classify", tags=["Classifier"])
app.include_router(dev.router, prefix="/_dev", tags=["Developer"])
app.include_router(admin_db.router, prefix="/admin/db", tags=["Admin DB"])
app.include_router(early_access.router)


@app.get("/")
def root():
    return {"message": "Tinko Backend is running"}
