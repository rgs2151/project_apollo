import string
import secrets
import hashlib
import base64
import json
from cryptography.fernet import Fernet


def generate_secret(length=5):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_string = ''.join(secrets.choice(characters) for _ in range(length))
    return secret_string


# hash password
def encrypt_with_salt(secret: str, salt:bytes=None, iterations=100000, hash_algorithm='sha256'):
    if salt is None: salt = secrets.token_bytes(16)
    else: salt = salt.encode() if not isinstance(salt, bytes) else salt
    encrypted_secret = hashlib.pbkdf2_hmac(hash_algorithm, secret.encode(), salt, iterations)
    return encrypted_secret, salt


# generate secret string
def generate_secret_meta(secret: str, salt:bytes=None, iterations=100000, hash_algorithm='sha256'):
    
    available_hash_algorithms = ['sha1', 'sha256', 'sha512', 'md5']
    if hash_algorithm not in available_hash_algorithms:
        raise ValueError(f"hash_algorithm should be one of the following: {', '.join(available_hash_algorithms)}")
    
    encrypted_secret, salt = encrypt_with_salt(secret)
    secret_meta = {
        "encrypted_secret": base64.b64encode(encrypted_secret).decode(),
        "salt": base64.b64encode(salt).decode(),
        "iterations": 100000,
        "hash_algorithm": 'sha256'
    }
    return json.dumps(secret_meta)


class InvalidSecret(Exception): pass
def validate_secret(validate_secret: str, secret_meta: str, url_safe_base64encode=False):
    
    try: secret_meta = json.loads(secret_meta)
    except json.decoder.JSONDecodeError:
        raise InvalidSecret("secret meta should be json decodable")
    
    encrypted_secret: str = secret_meta.get("encrypted_secret", None)
    if not encrypted_secret: raise InvalidSecret("secret_meta missing key encrypted_secret")
    if not isinstance(encrypted_secret, str): raise InvalidSecret("secret_meta.encrypted_secret should be of type str")
    try: encrypted_secret = base64.b64decode(encrypted_secret.encode())
    except Exception: raise InvalidSecret("secret_meta.encrypted_secret is not b64decoodable")
    secret_meta.pop("encrypted_secret")
    
    salt: str = secret_meta.get("salt", None)
    if not salt: raise InvalidSecret("secret_meta missing key salt")
    if not isinstance(salt, str): raise InvalidSecret("secret_meta.salt should be of type str")
    try: salt = base64.b64decode(salt.encode())
    except Exception: raise InvalidSecret("secret_meta.salt is not b64decoodable")
    secret_meta["salt"] = salt
    
    validate_secret = base64.urlsafe_b64decode(str(validate_secret).encode()).decode() if url_safe_base64encode else str(validate_secret)
    
    check_encrypted_secret, salt = encrypt_with_salt(validate_secret, **secret_meta)
    return encrypted_secret == check_encrypted_secret


def generate_random_secret_meta(length=5, salt:bytes=None, iterations=100000, hash_algorithm='sha256', url_safe_base64encode=False):
    secret = generate_secret(length=length)
    secret_meta = generate_secret_meta(secret)
    secret = base64.urlsafe_b64encode(secret.encode()).decode() if url_safe_base64encode else secret
    return secret, secret_meta


def generate_fernet_key():
    return Fernet.generate_key()


def encrypt_fernet_token(data, key):
    
    if isinstance(key, str): key = key.encode()
    
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(str(data).encode())
    return encrypted_data


def decrypt_fernet_token(encrypted_data, key):
    
    if isinstance(key, str): key = key.encode()
    
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return eval(decrypted_data.decode())
