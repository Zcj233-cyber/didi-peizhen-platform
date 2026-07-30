"""Admin 后台管理端接口"""
import json
import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import AdminUser, Menu, MenuRole, Order, Companion, Photo
from ..schemas import (
    GetCodeForm, UserAuthForm, AuthAdminParams,
    MenuListParams, UpdateUserForm, SetMenuForm,
    CompanionForm, CompanionListParams, DeleteCompanionForm,
    AdminOrderParams, UpdateOrderForm,
)
from ..utils.response import success, error
from ..utils.auth import hash_password, verify_admin_token

router = APIRouter()


# ==================== 验证码 & 注册 ====================

@router.post("/get/code")
def get_code(form: GetCodeForm):
    """模拟获取短信验证码"""
    # 模拟验证码发送，实际不发送短信
    return success({"code": "123456"}, message="验证码发送成功")


@router.post("/user/authentication")
def user_authentication(form: UserAuthForm, db: Session = Depends(get_db)):
    """用户注册"""
    existing = db.query(AdminUser).filter(AdminUser.username == form.userName).first()
    if existing:
        return error("该手机号已注册")

    # 模拟验证码校验：接受任意验证码
    user = AdminUser(
        username=form.userName,
        password=hash_password(form.passWord),
        name=f"用户{form.userName[-4:]}",
        mobile=form.userName,
        permissions_id=0,
        active=1,
    )
    db.add(user)
    db.commit()
    return success(None, message="注册成功，请登录")


# ==================== 菜单权限 ====================

def build_menu_tree(menus: list, parent_id: int = 0) -> list:
    """构建菜单树"""
    tree = []
    for m in menus:
        if m.parent_id == parent_id:
            children = build_menu_tree(menus, m.id)
            node = {
                "id": str(m.id),
                "name": m.name,
                "meta": {
                    "id": str(m.id),
                    "name": m.name,
                    "icon": m.icon or "",
                },
            }
            if m.path:
                node["meta"]["path"] = m.path
            if m.describe:
                node["meta"]["describe"] = m.describe
            if children:
                node["children"] = children
            else:
                # 叶子节点 -> 生成 path/meta.path
                node["path"] = m.path or f"/{m.name}"
                if m.path:
                    node["meta"]["path"] = m.path
            tree.append(node)
    return tree


def flatten_menu_ids(menu_tree: list) -> list:
    """从菜单树中提取所有 ID"""
    ids = []
    for node in menu_tree:
        ids.append(int(node["id"]))
        if "children" in node:
            ids.extend(flatten_menu_ids(node["children"]))
    return ids


@router.get("/menu/permissions")
def get_menu_permissions(request: Request, db: Session = Depends(get_db)):
    """获取当前用户的菜单权限（用于动态路由）"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload
    user_id = payload.get("user_id")

    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        return error("用户不存在")

    all_menus = db.query(Menu).order_by(Menu.sort).all()
    tree = build_menu_tree(all_menus)

    # 如果有权限组限制
    if user.permissions_id and user.permissions_id > 0:
        role = db.query(MenuRole).filter(MenuRole.id == user.permissions_id).first()
        if role and role.permissions:
            allowed_ids = set(role.permissions)
            filtered = filter_menu_tree(tree, allowed_ids)
            return success(filtered)
        return success([])

    return success(tree)


def filter_menu_tree(tree: list, allowed_ids: set) -> list:
    """根据权限 ID 过滤菜单树"""
    result = []
    for node in tree:
        node_id = int(node["id"])
        if node_id in allowed_ids:
            filtered_node = dict(node)
            if "children" in filtered_node:
                filtered_node["children"] = filter_menu_tree(filtered_node["children"], allowed_ids)
            result.append(filtered_node)
        elif "children" in node:
            filtered_children = filter_menu_tree(node["children"], allowed_ids)
            if filtered_children:
                filtered_node = dict(node)
                filtered_node["children"] = filtered_children
                result.append(filtered_node)
    return result


# ==================== 菜单管理 ====================

@router.get("/user/getmenu")
def get_user_menu(db: Session = Depends(get_db)):
    """获取所有菜单树（用于菜单管理页面）"""
    all_menus = db.query(Menu).order_by(Menu.sort).all()
    tree = build_menu_tree(all_menus)
    return success(tree)


@router.post("/user/setmenu")
def set_user_menu(form: SetMenuForm, db: Session = Depends(get_db)):
    """新增/编辑菜单角色"""
    permissions = json.loads(form.permissions) if isinstance(form.permissions, str) else form.permissions
    if form.id:
        role = db.query(MenuRole).filter(MenuRole.id == form.id).first()
        if role:
            role.name = form.name
            role.permissions = permissions
    else:
        role = MenuRole(name=form.name, permissions=permissions)
        db.add(role)
    db.commit()
    return success(None, message="保存成功")


@router.get("/menu/list")
def get_menu_list(params: MenuListParams = Depends(), db: Session = Depends(get_db)):
    """菜单角色列表"""
    query = db.query(MenuRole)
    total = query.count()
    roles = query.order_by(desc(MenuRole.id)).offset(
        (params.pageNum - 1) * params.pageSize
    ).limit(params.pageSize).all()

    return success({
        "list": [
            {
                "id": r.id,
                "name": r.name,
                "permissionName": ", ".join(
                    [row[0] for row in db.query(Menu.name).filter(Menu.id.in_(r.permissions)).all()]
                    if r.permissions else []
                ),
                "permission": r.permissions or [],
            }
            for r in roles
        ],
        "total": total,
    })


@router.get("/menu/selectlist")
def get_menu_select_list(db: Session = Depends(get_db)):
    """菜单选择列表（下拉框用）"""
    roles = db.query(MenuRole).all()
    return success([
        {"id": r.id, "name": r.name} for r in roles
    ])


# ==================== 管理员管理 ====================

@router.get("/auth/admin")
def get_auth_admin(params: AuthAdminParams = Depends(), db: Session = Depends(get_db)):
    """管理员列表"""
    query = db.query(AdminUser)
    total = query.count()
    users = query.order_by(desc(AdminUser.id)).offset(
        (params.pageNum - 1) * params.pageSize
    ).limit(params.pageSize).all()

    return success({
        "list": [
            {
                "id": u.id,
                "name": u.name or "",
                "username": u.username,
                "mobile": u.mobile or u.username,
                "permissions_id": u.permissions_id or 0,
                "active": u.active,
                "createTime": str(u.created_at) if u.created_at else "",
            }
            for u in users
        ],
        "total": total,
    })


@router.post("/update/user")
def update_user(form: UpdateUserForm, request: Request, db: Session = Depends(get_db)):
    """更新用户信息"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload
    user_id = payload.get("user_id")

    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        return error("用户不存在")

    user.name = form.name
    user.permissions_id = form.permissions_id
    db.commit()

    return success(None, message="更新成功")


# ==================== 图片库 ====================

@router.get("/photo/list")
def get_photo_list(db: Session = Depends(get_db)):
    """图片库列表"""
    photos = db.query(Photo).all()
    return success([
        {"name": p.name or f"img_{p.id}", "url": p.url} for p in photos
    ])


# ==================== 陪护师管理 ====================

@router.post("/companion")
def add_or_update_companion(form: CompanionForm, db: Session = Depends(get_db)):
    """新增/编辑陪护师"""
    if form.id:
        companion = db.query(Companion).filter(Companion.id == form.id).first()
        if not companion:
            return error("陪护师不存在")
        companion.name = form.name
        companion.avatar = form.avatar
        companion.sex = int(form.sex) if form.sex else 1
        companion.age = form.age
        companion.mobile = form.mobile
        companion.active = form.active
    else:
        companion = Companion(
            name=form.name,
            avatar=form.avatar,
            sex=int(form.sex) if form.sex else 1,
            age=form.age,
            mobile=form.mobile,
            active=form.active,
        )
        db.add(companion)
    db.commit()
    return success(None, message="保存成功")


@router.get("/companion/list")
def get_companion_list(params: CompanionListParams = Depends(), db: Session = Depends(get_db)):
    """陪护师列表"""
    query = db.query(Companion)
    total = query.count()
    companions = query.order_by(desc(Companion.create_time)).offset(
        (params.pageNum - 1) * params.pageSize
    ).limit(params.pageSize).all()

    return success({
        "list": [
            {
                "id": c.id,
                "name": c.name,
                "avatar": c.avatar or "",
                "sex": c.sex,
                "age": c.age,
                "mobile": c.mobile or "",
                "active": c.active,
                "create_time": str(c.create_time) if c.create_time else "",
            }
            for c in companions
        ],
        "total": total,
    })


@router.post("/delete/companion")
def delete_companion(form: DeleteCompanionForm, db: Session = Depends(get_db)):
    """删除陪护师"""
    ids = form.id
    if isinstance(ids, int):
        ids = [ids]
    elif isinstance(ids, list):
        # 可能传入的是 [{id: 1}, {id: 2}]
        if ids and isinstance(ids[0], dict):
            ids = [item.get("id") for item in ids if item.get("id")]
    db.query(Companion).filter(Companion.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return success(None, message="删除成功")


# ==================== 订单管理 ====================

@router.get("/admin/order")
def get_admin_order(params: AdminOrderParams = Depends(), db: Session = Depends(get_db)):
    """后台订单列表"""
    query = db.query(Order)
    if params.out_trade_no:
        query = query.filter(Order.out_trade_no.like(f"%{params.out_trade_no}%"))
    if params.trade_state:
        query = query.filter(Order.trade_state == params.trade_state)

    total = query.count()
    orders = query.order_by(desc(Order.order_start_time)).offset(
        (params.pageNum - 1) * params.pageSize
    ).limit(params.pageSize).all()

    return success({
        "list": [
            {
                "out_trade_no": o.out_trade_no,
                "hospital_name": o.hospital_name,
                "service_name": o.service_name,
                "service_img": o.service_img or "",
                "companion": {
                    "avatar": (db.query(Companion).filter(Companion.id == o.companion_id).first().avatar or "")
                    if o.companion_id else "",
                    "mobile": (db.query(Companion).filter(Companion.id == o.companion_id).first().mobile or "")
                    if o.companion_id else "",
                },
                "price": o.price,
                "paid_price": o.paid_price,
                "order_start_time": o.order_start_time,
                "trade_state": o.trade_state,
                "order_state": o.trade_state,
                "service_state": "",
                "tel": o.tel or "",
            }
            for o in orders
        ],
        "total": total,
    })


@router.post("/update/order")
def update_order(form: UpdateOrderForm, db: Session = Depends(get_db)):
    """更新订单状态（服务完成）"""
    order = db.query(Order).filter(Order.out_trade_no == form.id).first()
    if not order:
        return error("订单不存在")
    if order.trade_state != "待服务":
        return error("只有待服务的订单可以标记完成")

    order.trade_state = "已完成"
    db.commit()
    return success(None, message="操作成功")
