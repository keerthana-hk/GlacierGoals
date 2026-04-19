import app
with app.app.app_context():
    users = app.User.query.all()
    print("--- User List ---")
    for u in users:
        print(f"Email: {u.email}, Name: {u.name}")
    print("-----------------")
