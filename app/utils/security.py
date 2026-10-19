import base64
import hashlib
import jwt
import hmac
import os 
from datetime import datetime,timedelta,timezone

from dotenv import load_dotenv

from app.utils.errors import BusinessException,UnauthorizedException

load_dotenv()

JWT_ALGORITHM="HS256"
JWT_SECRET=os.getenv("JWT_SECRET","dev-only-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES=120

def hash_password(password:str,iterations:int=200_000)->str:

    if len(password)<8:
        raise BusinessException(code=40003,message="密码至少八位")


    salt=os.urandom(16)

    digest=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,iterations)

    return(
        f"pbkdf2_sha256${iterations}"
        f"${base64.b64encode(salt).decode()}"
        f"${base64.b64encode(digest).decode()}"
    )


def verify_password(password:str,stored:str)-> bool:

    try:
        algorithm,iterations,salt_b64,digest_b64=stored.split("$")

    except ValueError:
            return False

    if algorithm !="pbkdf2_sha256":
         return False

    salt=base64.b64decode(salt_b64)
    expected=base64.b64decode(digest_b64)
    actual=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,int(iterations))

    return hmac.compare_digest(actual,expected)


def create_access_token(user_id:int,expires_minutes:int=ACCESS_TOKEN_EXPIRE_MINUTES)-> str:
    payload={
         "sub":str(user_id),
         "exp":datetime.now(timezone.utc)+timedelta(minutes=expires_minutes)

    }
    return jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGORITHM)

def decode_access_token(token:str)->int:
    try:
        payload=jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("登录已过期，请重新登录") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException("无效的登录凭证") from exc

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedException("凭证内容不完整") from exc