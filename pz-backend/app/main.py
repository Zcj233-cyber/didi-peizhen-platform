"""FastAPI 主应用"""
import json
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import APP_PREFIX
from .database import get_db
from .models import H5User, AdminUser
from .utils.response import success, error
from .utils.auth import verify_password, create_token
from .routers import h5, admin, agents

app = FastAPI(
    title="医疗陪诊服务平台",
    description="医疗陪诊服务平台后端 API",
    version="1.0.0",
)

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 统一登录（通过 terminal 头部区分 H5/Admin） ====================

@app.post(f"{APP_PREFIX}/login")
async def unified_login(request: Request, db: Session = Depends(get_db)):
    """统一登录接口"""
    body = await request.json()
    username = body.get("userName", "")
    password = body.get("passWord", "")
    terminal = request.headers.get("terminal", "admin")

    if not username or not password:
        return error("请输入账号和密码")

    if terminal == "h5":
        # H5 端登录 → 查 h5_user 表
        user = db.query(H5User).filter(H5User.username == username).first()
        if not user:
            return error("用户不存在")
        if not verify_password(password, user.password):
            return error("密码错误")
        token = create_token({"user_id": user.id, "type": "h5"})
        return success({
            "token": token,
            "userInfo": {
                "name": user.name or user.username,
                "avatar": user.avatar or "",
            }
        })
    else:
        # Admin 端登录 → 查 admin_user 表
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not user:
            return error("账号不存在")
        if not verify_password(password, user.password):
            return error("密码错误")
        if not user.active:
            return error("账号已被禁用")
        token = create_token({"user_id": user.id, "type": "admin"})
        return success({
            "token": token,
            "userInfo": {
                "name": user.name or user.username,
            }
        })


# 注册路由（注意 H5 的 /login 已移除，由上面统一处理）
app.include_router(h5.router, prefix=APP_PREFIX)
app.include_router(admin.router, prefix=APP_PREFIX)
app.include_router(agents.router, prefix=APP_PREFIX)


@app.get(f"{APP_PREFIX}/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "医疗陪诊服务平台后端运行正常"}
