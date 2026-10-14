from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    # Ensure new subscription columns exist on existing databases
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        # Table might be 'user'
        if 'user' in table_names:
            cols = [c['name'] for c in inspector.get_columns('user')]
            with db.engine.connect() as conn:
                changed = False
                if 'plan' not in cols:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN plan VARCHAR(20)'))
                    changed = True
                if 'payment_gateway' not in cols:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN payment_gateway VARCHAR(20)'))
                    changed = True
                if 'subscription_date' not in cols:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN subscription_date TIMESTAMP'))
                    changed = True
                if changed:
                    conn.commit()
    except Exception as e:
        pass

if __name__ == '__main__':
    app.run(debug=True)