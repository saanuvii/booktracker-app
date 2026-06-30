from app import app
from models import db, User

with app.app_context():
    # 1. Show all available users
    print("Current users in your database:")
    users = User.query.all()
    for u in users:
        status = "(Admin)" if u.is_admin else "(User)"
        print(f"- {u.username} {status}")

    # 2. Ask which one to upgrade
    target = input("\nType the exact username you want to make an admin: ").strip()

    # 3. Apply the upgrade
    user = User.query.filter_by(username=target).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"\n👑 Success! '{user.username}' has been promoted to Super Admin!")
    else:
        print(f"\n❌ Error: Could not find a user named '{target}'. Please check the spelling.")