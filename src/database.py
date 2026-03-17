from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
import json
import os
import base64

# 1. DATABASE SETUP
SQLALCHEMY_DATABASE_URL = "sqlite:///./neurostamp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. ENCRYPTION SETUP (For Watermark Keys)
KEY_FILE = "secret.key"

def load_key():
    # On Render (or any cloud env), read from the SECRET_KEY environment variable.
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        # Render auto-generates a base64 value; ensure it's valid Fernet (32 url-safe base64 bytes)
        try:
            return env_key.encode() if len(base64.urlsafe_b64decode(env_key + '==')) == 32 else Fernet.generate_key()
        except Exception:
            return env_key.encode()
    # Local dev fallback: use key file
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    return key

CIPHER_SUITE = Fernet(load_key())

# 3. MODELS

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # <--- NEW: Stores the password hash
    user_uid = Column(String, unique=True, index=True)
    
    # STORED AS ENCRYPTED BYTES
    encrypted_key_data = Column(LargeBinary, nullable=True) 

    def set_key_data(self, data_list):
        if data_list is None: return
        json_str = json.dumps(data_list)
        self.encrypted_key_data = CIPHER_SUITE.encrypt(json_str.encode())

    def get_key_data(self):
        if not self.encrypted_key_data: return None
        try:
            decrypted_json = CIPHER_SUITE.decrypt(self.encrypted_key_data).decode()
            return json.loads(decrypted_json)
        except Exception as e:
            print(f"Encryption Error: {e}")
            return None

class ImageRegistry(Base):
    __tablename__ = "image_registry"
    id = Column(Integer, primary_key=True, index=True)
    image_hash = Column(String, unique=True, index=True)
    owner_uid = Column(String)
    original_width = Column(Integer, default=0)
    original_height = Column(Integer, default=0)

def init_db():
    Base.metadata.create_all(bind=engine)