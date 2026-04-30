"""
用户认证与权限管理API
"""
from typing import Optional
from datetime import datetime, timedelta
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import bcrypt
import jwt
from app.core.database import get_db
from app.models.indicator import User, OperationLog
import uuid

router = APIRouter(prefix="/auth", tags=["认证"])

# JWT配置
JWT_SECRET = "cgdss-secret-key-2024-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, username: str, role: str) -> str:
    """创建JWT token"""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的Token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> dict:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.is_active == 0:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return {"id": str(user.id), "username": user.username, "role": user.role}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """要求管理员权限"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def password_strength_check(password: str) -> bool:
    """密码强度检查：至少8位，含大小写字母和数字"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


# 请求/响应模型
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

class AdminCreateUserRequest(BaseModel):
    username: str
    phone: str
    email: str
    password: str
    role: str = "user"  # user or admin

class AdminUpdateUserRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None


def log_operation(db: Session, user_id: str, username: str, action: str, detail: str, ip: str = "unknown"):
    """记录操作日志"""
    log = OperationLog(
        id=uuid.uuid4(),
        user_id=user_id,
        username=username,
        action=action,
        detail=detail,
        ip_address=ip
    )
    db.add(log)
    db.commit()


# 初始化管理员账号
def init_admin_user(db: Session):
    """初始化管理员账号"""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            phone="13800138000",
            email="admin@cgdss.com",
            hashed_password=get_password_hash("admin888"),
            role="admin",
            is_active=1,
            must_change_password=1  # 首次登录需要改密码
        )
        db.add(admin)
        db.commit()


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否存在
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查手机号是否重复
    if db.query(User).filter(User.phone == request.phone).first():
        raise HTTPException(status_code=400, detail="手机号已注册")

    # 检查邮箱是否重复
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="邮箱已注册")

    # 密码强度检查
    if not password_strength_check(request.password):
        raise HTTPException(status_code=400, detail="密码至少8位，需包含大小写字母和数字")

    # 创建用户（待审批状态）
    user = User(
        id=uuid.uuid4(),
        username=request.username,
        phone=request.phone,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        role="user",
        is_active=0,  # 待审批
        must_change_password=0
    )
    db.add(user)
    db.commit()

    return {"message": "注册成功，请等待管理员审批"}


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user.is_active == 0:
        raise HTTPException(status_code=403, detail="账号待审批，请联系管理员")

    if user.is_active == -1:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    # 检查是否首次登录需要改密码
    if user.must_change_password:
        token = create_token(str(user.id), user.username, user.role)
        return {
            "token": token,
            "must_change_password": True,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "role": user.role
            }
        }

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_token(str(user.id), user.username, user.role)

    return {
        "token": token,
        "must_change_password": False,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "role": user.role
        }
    }


@router.post("/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """修改密码"""
    user = db.query(User).filter(User.id == current_user["id"]).first()

    if not verify_password(request.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    if not password_strength_check(request.new_password):
        raise HTTPException(status_code=400, detail="新密码至少8位，需包含大小写字母和数字")

    user.hashed_password = get_password_hash(request.new_password)
    user.must_change_password = 0
    user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, current_user["id"], current_user["username"], "修改密码", "用户修改了自己的密码")

    return {"message": "密码修改成功"}


@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    return {
        "id": str(user.id),
        "username": user.username,
        "phone": user.phone,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("/profile")
def update_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新用户信息"""
    user = db.query(User).filter(User.id == current_user["id"]).first()

    if request.phone and request.phone != user.phone:
        if db.query(User).filter(User.phone == request.phone, User.id != user.id).first():
            raise HTTPException(status_code=400, detail="手机号已被使用")
        user.phone = request.phone

    if request.email and request.email != user.email:
        if db.query(User).filter(User.email == request.email, User.id != user.id).first():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = request.email

    if request.full_name is not None:
        user.full_name = request.full_name

    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "信息更新成功"}


# 管理员接口
@router.get("/admin/users")
def list_users(
    status: Optional[int] = Query(None, description="状态筛选: 0=待审批, 1=正常, -1=禁用"),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """获取用户列表"""
    query = db.query(User)
    if status is not None:
        query = query.filter(User.is_active == status)

    users = query.order_by(User.created_at.desc()).all()
    return {
        "count": len(users),
        "users": [{
            "id": str(u.id),
            "username": u.username,
            "phone": u.phone,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None
        } for u in users]
    }


@router.post("/admin/users")
def admin_create_user(request: AdminCreateUserRequest, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """管理员创建用户"""
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.phone == request.phone).first():
        raise HTTPException(status_code=400, detail="手机号已注册")
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="邮箱已注册")

    user = User(
        id=uuid.uuid4(),
        username=request.username,
        phone=request.phone,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        role=request.role,
        is_active=1,  # 管理员创建直接激活
        must_change_password=1
    )
    db.add(user)
    db.commit()

    log_operation(db, admin["id"], admin["username"], "创建用户", f"创建了用户 {request.username}")

    return {"message": "用户创建成功"}


@router.put("/admin/users/{user_id}")
def admin_update_user(user_id: str, request: AdminUpdateUserRequest, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """管理员更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.phone and request.phone != user.phone:
        if db.query(User).filter(User.phone == request.phone, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="手机号已被使用")
        user.phone = request.phone

    if request.email and request.email != user.email:
        if db.query(User).filter(User.email == request.email, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = request.email

    if request.full_name is not None:
        user.full_name = request.full_name

    if request.role:
        user.role = request.role

    if request.is_active is not None:
        user.is_active = request.is_active

    user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, admin["id"], admin["username"], "更新用户", f"更新了用户 {user.username} 的信息")

    return {"message": "用户更新成功"}


@router.post("/admin/users/{user_id}/approve")
def approve_user(user_id: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """审批通过用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.is_active != 0:
        raise HTTPException(status_code=400, detail="用户不在待审批状态")

    user.is_active = 1
    user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, admin["id"], admin["username"], "审批用户", f"审批通过了用户 {user.username}")

    return {"message": "审批成功，用户已激活"}


@router.post("/admin/users/{user_id}/reject")
def reject_user(user_id: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """拒绝用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = -1
    user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, admin["id"], admin["username"], "拒绝用户", f"拒绝了用户 {user.username} 的注册申请")

    return {"message": "已拒绝该用户"}


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")

    db.delete(user)
    db.commit()

    log_operation(db, admin["id"], admin["username"], "删除用户", f"删除了用户 {user.username}")

    return {"message": "用户已删除"}


@router.get("/admin/logs")
def list_logs(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """获取操作日志"""
    logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(limit).all()
    return {
        "count": len(logs),
        "logs": [{
            "id": str(log.id),
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs]
    }


@router.post("/forgot-password")
def forgot_password(phone: str = Query(...), db: Session = Depends(get_db)):
    """忘记密码 - 发送验证码（模拟，实际应对接短信服务）"""
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="该手机号未注册")

    # 实际应该发送短信验证码，这里简化为返回成功
    # 验证码应该存储到Redis或数据库，设置过期时间
    return {"message": "验证码已发送到手机", "code": "123456"}  # 演示用，实际应隐藏


@router.post("/reset-password")
def reset_password(phone: str = Query(...), code: str = Query(...), new_password: str = Query(...), db: Session = Depends(get_db)):
    """重置密码"""
    # 实际应验证验证码，这里简化处理
    if code != "123456":  # 演示用
        raise HTTPException(status_code=400, detail="验证码错误")

    if not password_strength_check(new_password):
        raise HTTPException(status_code=400, detail="密码至少8位，需包含大小写字母和数字")

    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "密码重置成功"}
