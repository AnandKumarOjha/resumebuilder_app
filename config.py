import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_for_dev'
    # Handle Render's DATABASE_URL which uses 'postgres://' (rejected by SQLAlchemy 1.4+)
    _db_url = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'resume_app.db')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Serverless PostgreSQL optimization (Neon auto-suspend / connection recovery)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Stripe Configuration (International USD Payments)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_placeholder')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    # Stripe Price IDs (from Stripe Dashboard Product)
    STRIPE_PRICE_MONTHLY_ID = os.environ.get('STRIPE_PRICE_MONTHLY_ID', '')
    STRIPE_PRICE_YEARLY_ID = os.environ.get('STRIPE_PRICE_YEARLY_ID', '')

    # Razorpay Configuration (Indian INR Payments)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_placeholder')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'placeholder_secret')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

    # Fixed Plan Pricing (No runtime conversion)
    PLANS = {
        'monthly': {
            'id': 'monthly',
            'name': 'Monthly Plan',
            'period': '/ month',
            'billing': 'Billed monthly',
            'usd': 9.00,
            'usd_cents': 900,
            'stripe_price_id': os.environ.get('STRIPE_PRICE_MONTHLY_ID', ''),
            'inr': 499,
            'inr_paise': 49900,
            'description': 'Unlimited ATS PDF resume exports & access to all templates for 1 month.'
        },
        'yearly': {
            'id': 'yearly',
            'name': 'Yearly Plan',
            'period': '/ year',
            'billing': 'Billed annually',
            'badge': 'BEST VALUE · SAVE 55%',
            'usd': 49.00,
            'usd_cents': 4900,
            'stripe_price_id': os.environ.get('STRIPE_PRICE_YEARLY_ID', ''),
            'inr': 2499,
            'inr_paise': 249900,
            'savings_note_usd': 'Equivalent to just $4.08/mo',
            'savings_note_inr': 'Equivalent to just ₹208/mo',
            'description': 'Full 1-year unlimited access with all present and upcoming templates.'
        }
    }

    # Resend Email Configuration
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')