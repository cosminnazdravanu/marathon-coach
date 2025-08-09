from passlib.hash import bcrypt
def hash_password(p: str) -> str: return bcrypt.hash(p)
def verify_password(p: str, h: str) -> bool: return bcrypt.verify(p, h)