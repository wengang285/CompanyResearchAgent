"""认证服务"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select

from ..config import get_settings
from ..database import async_session_factory
from ..models.user import User

settings = get_settings()

# JWT 配置
SECRET_KEY = settings.secret_key or "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """认证服务"""
    
    async def create_user(self, username: str, password: str, email: str = None) -> User:
        """创建用户"""
        async with async_session_factory() as db:
            # 检查用户名是否已存在
            result = await db.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                raise ValueError("用户名已存在")
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password)
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            if not verify_password(password, user.hashed_password):
                return None
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            await db.commit()
            
            return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
    
    async def get_user_count(self) -> int:
        """获取用户数量"""
        async with async_session_factory() as db:
            result = await db.execute(select(User))
            return len(result.scalars().all())


# 单例
auth_service = AuthService()

