from src.database import SessionLocal, User
db = SessionLocal()
u = db.query(User).filter(User.username == "ren").first()
if u:
    print(f"UID is: {u.user_uid!r}")
else:
    print("User 'ren' not found")
