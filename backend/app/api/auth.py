"""认证 API"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from ..services.auth_service import (
    auth_service, 
    create_access_token, 
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models.user import User

router = APIRouter()

# OAuth2 密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    email: Optional[str] = None


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: Optional[str]
    is_admin: bool


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """获取当前用户（可选认证）"""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = await auth_service.get_user_by_id(user_id)
    return user


async def require_user(token: str = Depends(oauth2_scheme)) -> User:
    """要求用户认证"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """用户注册"""
    # 检查是否是第一个用户（自动设为管理员）
    user_count = await auth_service.get_user_count()
    
    try:
        user = await auth_service.create_user(
            username=request.username,
            password=request.password,
            email=request.email
        )
        
        # 第一个用户自动成为管理员
        if user_count == 0:
            from ..database import async_session_factory
            from sqlalchemy import select
            async with async_session_factory() as db:
                result = await db.execute(
                    select(User).where(User.id == user.id)
                )
                db_user = result.scalar_one_or_none()
                if db_user:
                    db_user.is_admin = True
                    await db.commit()
        
        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username}
        )
        
        return LoginResponse(
            access_token=access_token,
            user=user.to_dict()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    user = await auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    return LoginResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_admin=current_user.is_admin
    )


@router.post("/logout")
async def logout(current_user: User = Depends(require_user)):
    """用户登出（前端清除 token 即可）"""
    return {"message": "登出成功"}




