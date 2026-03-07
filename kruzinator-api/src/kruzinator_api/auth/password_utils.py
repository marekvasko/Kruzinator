from pwdlib import PasswordHash
from pwdlib.hashers import argon2

hasher = PasswordHash((argon2.Argon2Hasher(),))

def hash_password(password: str) -> str:
    return hasher.hash(password)

def check_password(plain_password: str, hashed_password: str) -> bool:
    return hasher.verify(plain_password, hashed_password)
