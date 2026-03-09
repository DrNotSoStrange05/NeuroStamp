from src.database import SessionLocal, User
db = SessionLocal()
u = db.query(User).filter(User.username == "ren").first()

key = u.get_key_data()
print("Expected UID:", u.user_uid)
print(f"Len of expected: {len('ID:' + u.user_uid)*8} bits")
print("Len of stored key:", len(key))

