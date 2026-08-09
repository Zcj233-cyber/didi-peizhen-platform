"""FastAPI 主应用"""
import contextlib
import json
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .config import APP_PREFIX
from .database import get_db
from .models import H5User, AdminUser
from .utils.response import success, error
from .utils.auth import verify_password, create_token
from .routers import h5, admin, agents
from .mcp.server import mcp_app, mcp as mcp_server


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：驱动 MCP session manager 的任务组。

    mcp_app（streamable_http_app 生成的 Starlette 子应用）被 mount 进 FastAPI 后，
    其自身的 lifespan 不会执行，需在此手动初始化，否则 MCP 请求会报
    "Task group is not initialized"。
    """
    async with mcp_server._session_manager.run():
        yield


app = FastAPI(
    title="医疗陪诊服务平台",
    description="医疗陪诊服务平台后端 API",
    version="1.0.0",
    lifespan=lifespan,
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

# ==================== MCP Server ====================
# 对外 MCP 端点：http://<host>:2306/v3pz/mcp/ （注意带尾斜杠）
# Streamable HTTP 传输，外部 MCP 客户端（Claude Desktop / Cursor / Inspector）可直接连接。

# 兜底：无尾斜杠的请求 307 重定向到带尾斜杠（必须在 mount 之前注册，路径才优先命中）
@app.api_route(f"{APP_PREFIX}/mcp", methods=["GET", "POST"], include_in_schema=False)
async def mcp_no_slash_redirect():
    return RedirectResponse(f"{APP_PREFIX}/mcp/", status_code=307)

# 挂载 MCP 应用（Starlette Mount 的可用 URL 带尾斜杠）
app.mount(f"{APP_PREFIX}/mcp", mcp_app)


@app.get(f"{APP_PREFIX}/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "医疗陪诊服务平台后端运行正常"}
