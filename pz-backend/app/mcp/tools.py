"""MCP 工具定义（唯一来源）

所有 Agent 的外部数据访问能力都收敛在这里，并通过 TOOL_REGISTRY 注册进 MCP Server。
工具全部为只读（DB 查询 + 天气/地图/距离等外部数据），返回 JSON 安全的纯 dict。

约束：
- 不在 TOOL_REGISTRY 里的函数，既进不了 MCP Server，也进不了 Agent。
- 工具内部统一使用 SessionLocal 查库，Agent 不再直接访问数据库。
- utils/* 是底层实现，工具在这里包一层复用（routers/h5.py 仍直接使用 utils）。
"""
import difflib
from datetime import datetime, timedelta

from sqlalchemy import func

from app.database import SessionLocal
from app.models import Hospital, Companion, Service, Order, H5User
from app.agent_models import FAQ

# ==================== 业务数据查询 ====================


def search_hospitals(city: str = "", name: str = "", limit: int = 10) -> dict:
    """按城市/名称搜索医院，返回医院列表。city 为空表示全部城市。"""
    db = SessionLocal()
    try:
        q = db.query(Hospital)
        if city:
            q = q.filter(Hospital.city == city)
        if name:
            q = q.filter(Hospital.name.like(f"%{name}%"))
        rows = q.limit(min(max(limit, 1), 200)).all()
        hospitals = [{
            "id": h.id,
            "name": h.name or "",
            "rank": h.rank or "",
            "label": h.label or "",
            "intro": (h.intro or "")[:200],
            "address": h.address or "",
            "latitude": h.latitude or "",
            "longitude": h.longitude or "",
            "avatar_url": h.avatar_url or "",
            "city": h.city or "",
        } for h in rows]
        return {"total": len(hospitals), "hospitals": hospitals}
    finally:
        db.close()


def list_companions(active_only: bool = True, limit: int = 10) -> dict:
    """查询陪诊师列表。active_only 为 True 时只返回在职（active==1）的陪诊师。"""
    db = SessionLocal()
    try:
        q = db.query(Companion)
        if active_only:
            q = q.filter(Companion.active == 1)
        rows = q.limit(min(max(limit, 1), 200)).all()
        companions = [{
            "id": c.id,
            "name": c.name or "",
            "sex": c.sex or 1,  # 1男 2女
            "age": c.age or 0,
            "mobile": c.mobile or "",
            "active": c.active or 0,
        } for c in rows]
        return {"total": len(companions), "companions": companions}
    finally:
        db.close()


def list_services(limit: int = 20) -> dict:
    """查询平台服务项目（陪诊服务）及价格。"""
    db = SessionLocal()
    try:
        rows = db.query(Service).limit(min(max(limit, 1), 200)).all()
        services = [{
            "id": s.id,
            "name": s.name or "",
            "price": float(s.price or 0),
            "service_img": s.service_img or "",
        } for s in rows]
        return {"total": len(services), "services": services}
    finally:
        db.close()


def get_user_orders(user_id: int, limit: int = 5, status: str = "") -> dict:
    """查询指定用户的订单列表，按创建时间倒序。status 为空表示全部状态。"""
    db = SessionLocal()
    try:
        q = db.query(Order).filter(Order.user_id == user_id)
        if status:
            q = q.filter(Order.trade_state == status)
        rows = q.order_by(Order.created_at.desc()).limit(min(max(limit, 1), 100)).all()
        orders = [{
            "id": o.id,
            "out_trade_no": o.out_trade_no or "",
            "hospital_name": o.hospital_name or "",
            "service_name": o.service_name or "",
            "trade_state": o.trade_state or "",
            "price": float(o.price or 0),
            "starttime": o.starttime or "",
            "client_name": o.client_name or "",
            "companion_name": o.companion_name or "",
            "demand": o.demand or "",
            "created_at": str(o.created_at) if o.created_at else "",
        } for o in rows]
        return {"total": len(orders), "orders": orders}
    finally:
        db.close()


def search_faq(query: str, top_k: int = 5) -> dict:
    """搜索 FAQ 知识库：关键词命中 + 文本相似度综合打分，按分数倒序返回。"""
    db = SessionLocal()
    try:
        faqs = db.query(FAQ).filter(FAQ.enabled == 1).all()
        scored = []
        for faq in faqs:
            score = 0.0
            # 维度1：关键词命中
            if faq.keywords:
                keywords = [k.strip() for k in faq.keywords.split(",")]
                keyword_hits = sum(1 for k in keywords if k and k in query)
                if keyword_hits > 0:
                    score += min(keyword_hits / 2, 1.0) * 0.5
            # 维度2：问题文本相似度
            seq_score = difflib.SequenceMatcher(None, query, faq.question).ratio()
            score += seq_score * 0.5
            scored.append({
                "question": faq.question or "",
                "answer": faq.answer or "",
                "category": faq.category or "",
                "score": round(score, 2),
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:min(max(top_k, 1), 20)]}
    finally:
        db.close()


def get_business_stats(
    include_yesterday: bool = False,
    include_week: bool = False,
    include_revenue: bool = False,
) -> dict:
    """获取运营业务统计（订单/用户/陪诊师）。

    include_yesterday 返回昨日订单/昨日新增用户；
    include_week 返回近7日订单/近7日新增用户；
    include_revenue 返回今日收入（paid_price 合计）。
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)

        total_orders = db.query(func.count(Order.id)).scalar() or 0
        today_orders = db.query(func.count(Order.id)).filter(
            Order.created_at >= today
        ).scalar() or 0

        status_distribution = {}
        for s in ["待支付", "待服务", "已完成", "已取消"]:
            status_distribution[s] = db.query(func.count(Order.id)).filter(
                Order.trade_state == s
            ).scalar() or 0

        total_users = db.query(func.count(H5User.id)).scalar() or 0
        today_users = db.query(func.count(H5User.id)).filter(
            H5User.created_at >= today
        ).scalar() or 0

        total_companions = db.query(func.count(Companion.id)).scalar() or 0
        active_companions = db.query(func.count(Companion.id)).filter(
            Companion.active == 1
        ).scalar() or 0

        result = {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "status_distribution": status_distribution,
            "total_users": total_users,
            "today_users": today_users,
            "total_companions": total_companions,
            "active_companions": active_companions,
        }

        if include_yesterday:
            result["yesterday_orders"] = db.query(func.count(Order.id)).filter(
                Order.created_at >= yesterday, Order.created_at < today
            ).scalar() or 0
            result["yesterday_users"] = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= yesterday, H5User.created_at < today
            ).scalar() or 0
        if include_week:
            result["week_orders"] = db.query(func.count(Order.id)).filter(
                Order.created_at >= week_ago
            ).scalar() or 0
            result["week_users"] = db.query(func.count(H5User.id)).filter(
                H5User.created_at >= week_ago
            ).scalar() or 0
        if include_revenue:
            result["revenue_today"] = float(
                db.query(func.sum(Order.paid_price)).filter(
                    Order.created_at >= today
                ).scalar() or 0
            )
        return result
    finally:
        db.close()


# ==================== 外部数据工具（包一层复用 utils） ====================


async def get_weather(city: str = "北京") -> dict:
    """获取指定城市当前天气（优先真实 API，失败用模拟数据）。"""
    from app.utils.weather import fetch_weather
    return await fetch_weather(city)


def get_travel_advice(
    condition: str, temperature: int, wind: str = "", dest_name: str = "医院"
) -> dict:
    """根据天气情况生成出行建议文案。"""
    from app.utils.weather import get_travel_advice as _advice
    weather = {"temperature": temperature, "condition": condition, "wind": wind}
    return {"advice": _advice(weather, dest_name)}


def calc_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> dict:
    """计算两经纬度点间的球面直线距离（公里）。"""
    from app.utils.distance import haversine_distance
    return {"distance_km": haversine_distance(lat1, lng1, lat2, lng2)}


def get_static_map_url(latitude: str, longitude: str, hospital_name: str = "") -> dict:
    """生成高德静态地图图片 URL，可直接用于 <img> src。"""
    from app.utils.map import get_static_map_url as _get_url
    return {"url": _get_url(latitude, longitude, hospital_name)}


async def get_hospital_image(hospital_name: str) -> dict:
    """获取医院实景图片 URL（高德 POI）。"""
    from app.utils.hospital_image import fetch_hospital_image
    url = await fetch_hospital_image(hospital_name)
    return {"url": url or ""}


# ==================== 工具注册表（唯一来源） ====================

TOOL_REGISTRY = [
    ("search_hospitals", search_hospitals, "按城市/名称搜索医院，返回医院列表"),
    ("list_companions", list_companions, "查询陪诊师列表"),
    ("list_services", list_services, "查询平台服务项目及价格"),
    ("get_user_orders", get_user_orders, "查询指定用户的订单列表"),
    ("search_faq", search_faq, "搜索 FAQ 知识库，按相关度打分返回"),
    ("get_business_stats", get_business_stats, "获取运营业务统计（订单/用户/陪诊师/收入）"),
    ("get_weather", get_weather, "获取指定城市当前天气"),
    ("get_travel_advice", get_travel_advice, "根据天气生成出行建议"),
    ("calc_distance", calc_distance, "计算两经纬度点间的直线距离"),
    ("get_static_map_url", get_static_map_url, "生成高德静态地图图片 URL"),
    ("get_hospital_image", get_hospital_image, "获取医院实景图片 URL"),
]
