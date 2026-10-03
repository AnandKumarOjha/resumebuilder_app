import stripe
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, ResumeRole

payments = Blueprint('payments', __name__, url_prefix='/payment')

@payments.route('/upgrade')
@login_required
def upgrade():
    """
    Paywall / Pricing page.
    Explains the benefits of PRO membership and provides checkout actions.
    """
    role_id = request.args.get('role_id', type=int)
    role = db.session.get(ResumeRole, role_id) if role_id else None
    
    stripe_configured = bool(
        current_app.config.get('STRIPE_SECRET_KEY') and 
        not current_app.config.get('STRIPE_SECRET_KEY').startswith('sk_test_placeholder')
    )
    
    return render_template(
        'payments/upgrade.html',
        role=role,
        role_id=role_id,
        stripe_configured=stripe_configured
    )

@payments.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Creates a Stripe Checkout Session for the PRO upgrade.
    If Stripe credentials are placeholders or encounter an API error in dev,
    provides friendly fallback guidance.
    """
    role_id = request.form.get('role_id', type=int)
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    # Check for placeholder key in development
    if not stripe.api_key or stripe.api_key.startswith('sk_test_placeholder'):
        flash('Stripe API keys are currently in placeholder mode. Use the instant "Dev Test Upgrade" below to test the premium unlock.', 'info')
        return redirect(url_for('payments.upgrade', role_id=role_id))
    
    try:
        success_url = url_for('payments.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
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
                        'name': 'ResumeBuilder PRO Lifetime Membership',
                        'description': 'Unlimited ATS PDF Resume Downloads & All Templates',
                    },
                    'unit_amount': 999,  # $9.99
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f'Stripe error: {str(e)}', 'danger')
        return redirect(url_for('payments.upgrade', role_id=role_id))

@payments.route('/dev-activate', methods=['POST'])
@login_required
def dev_activate():
    """
    Developer convenience endpoint to instantly simulate a successful payment
    and unlock PRO status for testing without needing external Stripe network calls.
    """
    role_id = request.form.get('role_id', type=int)
    user = db.session.get(User, current_user.id)
    user.is_premium = True
    db.session.commit()
    flash('Success! PRO membership has been activated for your account. You now have unlimited PDF downloads!', 'success')
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
    db.session.commit()
    flash('Account reset to Free tier. Paywall is now active again.', 'info')
    return redirect(url_for('payments.upgrade'))

@payments.route('/success')
@login_required
def success():
    """
    Stripe Checkout Success handler.
    Marks user as premium upon returning from Stripe checkout.
    """
    session_id = request.args.get('session_id')
    role_id = request.args.get('role_id', type=int)
    
    # Upgrade user to premium
    user = db.session.get(User, current_user.id)
    user.is_premium = True
    db.session.commit()
    
    flash('Payment confirmed! Welcome to ResumeBuilder PRO. You can now download and export all your resumes.', 'success')
    return render_template('payments/success.html', role_id=role_id)

@payments.route('/cancel')
@login_required
def cancel():
    """
    Stripe Checkout Cancel handler.
    """
    role_id = request.args.get('role_id', type=int)
    return render_template('payments/cancel.html', role_id=role_id)

@payments.route('/webhook', methods=['POST'])
def webhook():
    """
    Stripe Webhook handler to listen for checkout.session.completed events
    and activate user premium status asynchronously.
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
        # Fallback to direct JSON parsing if webhook secret is not set (e.g. testing)
        try:
            event = request.get_json(force=True)
        except Exception:
            return jsonify({'error': 'Invalid JSON'}), 400

    if event and event.get('type') == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        if user_id:
            user = db.session.get(User, int(user_id))
            if user:
                user.is_premium = True
                db.session.commit()

    return jsonify({'status': 'success'}), 200
