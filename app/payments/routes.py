import time
from datetime import datetime
import stripe
import razorpay
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, ResumeRole

payments = Blueprint('payments', __name__, url_prefix='/payment')

def get_razorpay_client():
    key_id = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    if key_id and key_secret and not key_id.startswith('rzp_test_placeholder'):
        return razorpay.Client(auth=(key_id, key_secret))
    return None

@payments.route('/upgrade')
@login_required
def upgrade():
    """
    Paywall & Pricing page.
    Displays Monthly and Yearly plans with gateway options:
    - International (USD via Stripe)
    - India (INR via Razorpay)
    """
    role_id = request.args.get('role_id', type=int)
    role = db.session.get(ResumeRole, role_id) if role_id else None
    
    stripe_configured = bool(
        current_app.config.get('STRIPE_SECRET_KEY') and 
        not current_app.config.get('STRIPE_SECRET_KEY').startswith('sk_test_placeholder')
    )
    
    razorpay_configured = bool(
        current_app.config.get('RAZORPAY_KEY_ID') and 
        not current_app.config.get('RAZORPAY_KEY_ID').startswith('rzp_test_placeholder')
    )
    
    plans = current_app.config.get('PLANS', {})
    
    return render_template(
        'payments/upgrade.html',
        role=role,
        role_id=role_id,
        plans=plans,
        stripe_configured=stripe_configured,
        stripe_public_key=current_app.config.get('STRIPE_PUBLIC_KEY'),
        razorpay_configured=razorpay_configured,
        razorpay_key_id=current_app.config.get('RAZORPAY_KEY_ID')
    )

# -------------------------------------------------------------------------
# STRIPE (International USD Payments)
# -------------------------------------------------------------------------

@payments.route('/create-checkout-session', methods=['POST'])
@payments.route('/stripe/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Creates a Stripe Checkout Session for either Monthly or Yearly plan in USD.
    Uses fixed USD pricing (no runtime conversion).
    """
    role_id = request.form.get('role_id', type=int)
    plan_id = request.form.get('plan', 'monthly').lower()
    
    plans = current_app.config.get('PLANS', {})
    if plan_id not in plans:
        plan_id = 'monthly'
    
    selected_plan = plans[plan_id]
    
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    # Check for placeholder key in development
    if not stripe.api_key or stripe.api_key.startswith('sk_test_placeholder'):
        flash(f'Stripe API keys are in placeholder mode. Use the instant "Dev Test Upgrade" to test the {selected_plan["name"]}.', 'info')
        return redirect(url_for('payments.upgrade', role_id=role_id))
    
    try:
        success_url = url_for('payments.success', _external=True) + f'?session_id={{CHECKOUT_SESSION_ID}}&gateway=stripe&plan={plan_id}'
        if role_id:
            success_url += f'&role_id={role_id}'
            
        cancel_url = url_for('payments.cancel', _external=True)
        if role_id:
            cancel_url += f'?role_id={role_id}'

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"ResumeBuilder PRO ({selected_plan['name']})",
                        'description': selected_plan['description'],
                    },
                    'unit_amount': selected_plan['usd_cents'],  # e.g. 900 ($9) or 4900 ($49)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
            metadata={
                'user_id': str(current_user.id),
                'plan': plan_id,
                'gateway': 'stripe'
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f'Stripe checkout error: {str(e)}', 'danger')
        return redirect(url_for('payments.upgrade', role_id=role_id))

# -------------------------------------------------------------------------
# RAZORPAY (Indian INR Payments)
# -------------------------------------------------------------------------

@payments.route('/razorpay/create-order', methods=['POST'])
@login_required
def razorpay_create_order():
    """
    Creates a Razorpay Order for either Monthly or Yearly plan in INR.
    Uses fixed INR pricing (no runtime conversion).
    """
    data = request.get_json(silent=True) or request.form
    plan_id = data.get('plan', 'monthly').lower()
    role_id = data.get('role_id')
    
    plans = current_app.config.get('PLANS', {})
    if plan_id not in plans:
        plan_id = 'monthly'
    
    selected_plan = plans[plan_id]
    key_id = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    
    if not key_id or key_id.startswith('rzp_test_placeholder') or not key_secret:
        return jsonify({
            'status': 'error',
            'message': 'Razorpay credentials are in placeholder mode. Please configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env, or use the Dev Test Upgrade.'
        }), 400
    
    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order_receipt = f"rb_u{current_user.id}_{int(time.time())}"
        order_data = {
            'amount': selected_plan['inr_paise'],  # e.g. 49900 (₹499) or 249900 (₹2,499)
            'currency': 'INR',
            'receipt': order_receipt,
            'notes': {
                'user_id': str(current_user.id),
                'plan': plan_id,
                'role_id': str(role_id) if role_id else '',
                'user_email': current_user.email
            }
        }
        order = client.order.create(data=order_data)
        return jsonify({
            'status': 'success',
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': 'INR',
            'key': key_id,
            'plan': plan_id,
            'plan_name': selected_plan['name'],
            'user_name': current_user.email.split('@')[0],
            'user_email': current_user.email
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@payments.route('/razorpay/verify', methods=['POST'])
@login_required
def razorpay_verify():
    """
    Verifies Razorpay payment signature after successful completion on client.
    Upgrades user account to PRO.
    """
    data = request.get_json(silent=True) or request.form
    order_id = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')
    plan_id = data.get('plan', 'monthly')
    role_id = data.get('role_id')

    key_id = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')

    if not (order_id and payment_id and signature):
        flash('Payment verification failed: missing payment details.', 'danger')
        return redirect(url_for('payments.upgrade', role_id=role_id))

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })

        # Upgrade User
        user = db.session.get(User, current_user.id)
        user.is_premium = True
        user.plan = plan_id
        user.payment_gateway = 'razorpay'
        user.subscription_date = datetime.utcnow()
        db.session.commit()

        if request.is_json:
            success_url = url_for('payments.success', gateway='razorpay', plan=plan_id, role_id=role_id)
            return jsonify({'status': 'success', 'redirect_url': success_url})

        flash(f'Payment confirmed via Razorpay! Welcome to ResumeBuilder PRO ({plan_id.capitalize()} Plan).', 'success')
        return redirect(url_for('payments.success', gateway='razorpay', plan=plan_id, role_id=role_id))
    except razorpay.errors.SignatureVerificationError:
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Invalid signature verification'}), 400
        flash('Payment verification failed: invalid signature.', 'danger')
        return redirect(url_for('payments.upgrade', role_id=role_id))
    except Exception as e:
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        flash(f'Verification error: {str(e)}', 'danger')
        return redirect(url_for('payments.upgrade', role_id=role_id))

# -------------------------------------------------------------------------
# WEBHOOKS
# -------------------------------------------------------------------------

@payments.route('/webhook', methods=['POST'])
@payments.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """
    Stripe Webhook handler to listen for checkout.session.completed events.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    event = None
    if webhook_secret and sig_header:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400
    else:
        try:
            event = request.get_json(force=True)
        except Exception:
            return jsonify({'error': 'Invalid JSON'}), 400

    if event and event.get('type') == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id') or (session.get('metadata') or {}).get('user_id')
        plan_id = (session.get('metadata') or {}).get('plan', 'monthly')
        if user_id:
            user = db.session.get(User, int(user_id))
            if user:
                user.is_premium = True
                user.plan = plan_id
                user.payment_gateway = 'stripe'
                user.subscription_date = datetime.utcnow()
                db.session.commit()

    return jsonify({'status': 'success'}), 200

@payments.route('/razorpay/webhook', methods=['POST'])
def razorpay_webhook():
    """
    Razorpay Webhook handler to listen for order.paid and payment.captured events.
    """
    webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Razorpay-Signature')

    if webhook_secret and signature:
        key_id = current_app.config.get('RAZORPAY_KEY_ID')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        client = razorpay.Client(auth=(key_id, key_secret))
        try:
            client.utility.verify_webhook_signature(payload, signature, webhook_secret)
        except Exception:
            return jsonify({'error': 'Invalid signature'}), 400

    try:
        data = request.get_json(force=True)
        event = data.get('event')
        if event in ['order.paid', 'payment.captured']:
            payment_entity = data.get('payload', {}).get('payment', {}).get('entity', {})
            notes = payment_entity.get('notes', {})
            user_id = notes.get('user_id')
            plan_id = notes.get('plan', 'monthly')
            if user_id:
                user = db.session.get(User, int(user_id))
                if user:
                    user.is_premium = True
                    user.plan = plan_id
                    user.payment_gateway = 'razorpay'
                    user.subscription_date = datetime.utcnow()
                    db.session.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'status': 'success'}), 200

# -------------------------------------------------------------------------
# DEVELOPER / EVALUATION HELPERS
# -------------------------------------------------------------------------

@payments.route('/dev-activate', methods=['POST'])
@login_required
def dev_activate():
    """
    Developer convenience endpoint to instantly simulate a successful payment
    and unlock PRO status for testing without needing external gateway API calls.
    Supports selecting plan (monthly/yearly) and gateway (stripe/razorpay).
    """
    role_id = request.form.get('role_id', type=int)
    plan_id = request.form.get('plan', 'monthly')
    gateway = request.form.get('gateway', 'dev')

    user = db.session.get(User, current_user.id)
    user.is_premium = True
    user.plan = plan_id
    user.payment_gateway = gateway
    user.subscription_date = datetime.utcnow()
    db.session.commit()

    flash(f'Success! PRO membership has been activated for your account ({plan_id.capitalize()} Plan). You now have unlimited PDF downloads!', 'success')
    if role_id:
        return redirect(url_for('dashboard.role_detail', role_id=role_id))
    return redirect(url_for('dashboard.index'))

@payments.route('/dev-deactivate', methods=['POST'])
@login_required
def dev_deactivate():
    """
    Developer convenience endpoint to reset account back to Free tier
    to verify paywall redirection.
    """
    user = db.session.get(User, current_user.id)
    user.is_premium = False
    user.plan = None
    user.payment_gateway = None
    user.subscription_date = None
    db.session.commit()
    flash('Account reset to Free tier. Paywall is now active again.', 'info')
    return redirect(url_for('payments.upgrade'))

# -------------------------------------------------------------------------
# SUCCESS & CANCEL
# -------------------------------------------------------------------------

@payments.route('/success')
@login_required
def success():
    """
    Payment Success handler.
    """
    session_id = request.args.get('session_id')
    role_id = request.args.get('role_id', type=int)
    gateway = request.args.get('gateway', 'stripe')
    plan_id = request.args.get('plan', 'monthly')
    
    # Ensure current user is marked premium
    user = db.session.get(User, current_user.id)
    if not user.is_premium:
        user.is_premium = True
        user.plan = plan_id
        user.payment_gateway = gateway
        user.subscription_date = datetime.utcnow()
        db.session.commit()
    
    flash('Payment confirmed! Welcome to ResumeBuilder PRO. You can now download and export all your resumes.', 'success')
    return render_template('payments/success.html', role_id=role_id, gateway=gateway, plan_id=plan_id)

@payments.route('/cancel')
@login_required
def cancel():
    """
    Payment Cancel handler.
    """
    role_id = request.args.get('role_id', type=int)
    return render_template('payments/cancel.html', role_id=role_id)

