"""H5 端 (C端用户) 接口"""
import time
import random
import string
import urllib.parse
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import H5User, Hospital, Companion, Service, Slide, Order
from ..schemas import CreateOrderForm, OrderListParams, OrderDetailParams
from ..utils.response import success, error
from ..utils.auth import verify_h5_token
from ..utils.weather import fetch_weather, get_travel_advice
from ..utils.distance import haversine_distance
from ..utils.map import get_static_map_url

router = APIRouter()


def generate_order_no() -> str:
    """生成订单号：时间戳 + 6位随机数字"""
    ts = str(int(time.time()))
    rand = "".join(random.choices(string.digits, k=6))
    return f"PZ{ts}{rand}"


# ==================== 首页 ====================

# 城市中心坐标映射表（用于定位后匹配最近城市）
CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "武汉": (30.5928, 114.3055),
    "成都": (30.5728, 104.0668),
    "杭州": (30.2741, 120.1551),
    "南京": (32.0603, 118.7969),
    "重庆": (29.4316, 106.9123),
    "西安": (34.3416, 108.9398),
    "长沙": (28.2282, 112.9388),
    "郑州": (34.7466, 113.6254),
}


def find_nearest_city(lat: float, lng: float) -> str:
    """根据坐标找到最近的城市"""
    nearest = "北京"
    min_dist = float("inf")
    for city, (clat, clng) in CITY_COORDS.items():
        dist = haversine_distance(lat, lng, clat, clng)
        if dist < min_dist:
            min_dist = dist
            nearest = city
    return nearest


@router.get("/index/index")
def get_index(lat: float = None, lng: float = None, city: str = None, db: Session = Depends(get_db)):
    """首页数据（支持传入位置过滤城市医院）"""
    slides = db.query(Slide).order_by(Slide.sort).all()

    # 如果传了坐标但没传城市，自动匹配最近城市
    if not city and lat is not None and lng is not None:
        city = find_nearest_city(lat, lng)

    # 按城市过滤医院
    query = db.query(Hospital)
    if city:
        query = query.filter(Hospital.city == city)
    hospitals = query.all()

    # 无该城市医院时返回所有
    if not hospitals:
        hospitals = db.query(Hospital).all()
        city = ""

    hospital_list = []
    for h in hospitals:
        distance = None
        if lat is not None and lng is not None and h.latitude and h.longitude:
            try:
                distance = haversine_distance(lat, lng, float(h.latitude), float(h.longitude))
            except (ValueError, TypeError):
                pass
        # 地图链接（打开高德网页版查看位置）
        map_link = f"https://uri.amap.com/marker?position={h.longitude},{h.latitude}&name={urllib.parse.quote(h.name or '医院')}&coordinate=gaode"
        hospital_list.append({
            "id": h.id,
            "name": h.name,
            "rank": h.rank or "",
            "label": h.label or "",
            "intro": h.intro or "",
            "avatar_url": h.avatar_url or "",
            "latitude": h.latitude or "",
            "longitude": h.longitude or "",
            "address": h.address or "",
            "city": h.city or "",
            "distance": distance,
            "map_url": map_link,
        })

    # 有位置时按距离排序
    if lat is not None and lng is not None:
        hospital_list.sort(key=lambda x: x["distance"] if x["distance"] is not None else 99999)

    # 前4个医院做导航图
    nav2s = []
    for i, h in enumerate(hospital_list[:4]):
        nav2s.append({
            "id": h["id"],
            "pic_image_url": h["avatar_url"],
        })

    # 轮播图使用前3个医院图片（带医院名称）
    slide_hospitals = hospital_list[:3] if hospital_list else []
    slides_out = [
        {
            "id": h["id"],
            "pic_image_url": h["avatar_url"],
            "hospital_name": h["name"],
            "hospital_rank": h["rank"],
            "map_url": h["map_url"],
        }
        for h in slide_hospitals
    ]

    return success({
        "slides": slides_out if slides_out else [{"id": s.id, "pic_image_url": s.pic_image_url} for s in slides],
        "nav2s": nav2s,
        "navs": [],
        "now": str(int(time.time())),
        "city": city or "全国",
        "hospitals": hospital_list,
    })


# ==================== 创建订单页获取数据 ====================

@router.get("/h5/companion")
def get_h5_companion(db: Session = Depends(get_db)):
    """获取创建订单页所需数据"""
    hospitals = db.query(Hospital).all()
    companions = db.query(Companion).filter(Companion.active == 1).all()
    service = db.query(Service).first()

    return success({
        "hospitals": [
            {
                "id": h.id, "name": h.name,
                "latitude": h.latitude or "", "longitude": h.longitude or "",
                "address": h.address or "",
                "map_url": f"https://uri.amap.com/marker?position={h.longitude},{h.latitude}&name={urllib.parse.quote(h.name or '')}&coordinate=gaode",
            }
            for h in hospitals
        ],
        "companion": [
            {"id": c.id, "name": c.name, "avatar": c.avatar or ""}
            for c in companions
        ],
        "service": {
            "serviceName": service.name if service else "陪诊服务",
            "serviceImg": service.service_img if service else "",
            "price": service.price if service else 0,
        }
    })


# ==================== 医院导航 ====================

@router.get("/hospital/location")
def get_hospital_location(hospital_id: int, db: Session = Depends(get_db)):
    """获取医院位置信息"""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        return error("医院不存在")
    return success({
        "id": hospital.id,
        "name": hospital.name,
        "latitude": hospital.latitude or "",
        "longitude": hospital.longitude or "",
        "address": hospital.address or "",
    })


@router.get("/hospital/cities")
def get_hospital_cities(db: Session = Depends(get_db)):
    """获取有医院的城市列表"""
    from sqlalchemy import func
    cities = db.query(Hospital.city).filter(Hospital.city != "").distinct().order_by(Hospital.city).all()
    city_list = [c[0] for c in cities if c[0]]
    return success(city_list)


# ==================== 创建订单 ====================

@router.post("/createOrder")
def create_order(form: CreateOrderForm, request: Request, db: Session = Depends(get_db)):
    """创建订单"""
    # 验证 token
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload
    user_id = payload.get("user_id")

    service = db.query(Service).first()
    companion = db.query(Companion).filter(Companion.id == form.companion_id).first()

    now_ts = int(time.time() * 1000)
    out_trade_no = generate_order_no()

    # 生成模拟的微信支付二维码链接（实际是一个模拟链接）
    mock_code_url = f"weixin://pay/mock?order_no={out_trade_no}&amount={service.price if service else 0.5}"

    order = Order(
        out_trade_no=out_trade_no,
        user_id=user_id,
        hospital_id=form.hospital_id,
        hospital_name=form.hospital_name,
        service_id=service.id if service else 0,
        service_name=service.name if service else "陪诊服务",
        service_img=service.service_img if service else "",
        companion_id=form.companion_id,
        companion_name=companion.name if companion else "",
        starttime=form.starttime,
        receive_address=form.receiveAddress,
        tel=form.tel,
        demand=form.demand,
        trade_state="待支付",
        price=service.price if service else 0.5,
        paid_price=0,
        order_start_time=now_ts,
        code_url=mock_code_url,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return success({
        "out_trade_no": order.out_trade_no,
        "wx_code": mock_code_url,
    })


# ==================== 订单列表 ====================

@router.get("/order/list")
def get_order_list(params: OrderListParams = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """获取订单列表"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload
    user_id = payload.get("user_id")

    query = db.query(Order).filter(Order.user_id == user_id)
    if params.state:
        state_map = {"1": "待支付", "2": "待服务", "3": "已完成", "4": "已取消"}
        state_name = state_map.get(params.state)
        if state_name:
            query = query.filter(Order.trade_state == state_name)

    orders = query.order_by(desc(Order.order_start_time)).all()

    return success([
        {
            "out_trade_no": o.out_trade_no,
            "serviceImg": o.service_img or "",
            "service_name": o.service_name,
            "hospital_name": o.hospital_name,
            "starttime": o.starttime or "",
            "trade_state": o.trade_state,
            "order_start_time": o.order_start_time,
            "timer": (o.order_start_time + 7200000 - int(time.time() * 1000)) if o.order_start_time else 0,
        }
        for o in orders
    ])


# ==================== 订单详情 ====================

@router.get("/order/detail")
def get_order_detail(params: OrderDetailParams = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """获取订单详情"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload

    order = db.query(Order).filter(Order.out_trade_no == params.oid).first()
    if not order:
        return error("订单不存在")

    companion = db.query(Companion).filter(Companion.id == order.companion_id).first()

    # 获取医院位置信息
    hospital = db.query(Hospital).filter(Hospital.id == order.hospital_id).first()

    return success({
        "out_trade_no": order.out_trade_no,
        "service_name": order.service_name,
        "hospital_name": order.hospital_name,
        "service_img": order.service_img or "",
        "starttime": order.starttime or "",
        "receiveAddress": order.receive_address or "",
        "demand": order.demand or "",
        "tel": order.tel or "",
        "trade_state": order.trade_state,
        "price": order.price,
        "paid_price": order.paid_price,
        "order_start_time": order.order_start_time,
        "code_url": order.code_url or "",
        "client": {
            "name": order.client_name or order.companion_name or "",
            "mobile": order.client_mobile or "",
        },
        "companion": {
            "avatar": companion.avatar if companion else "",
            "mobile": companion.mobile if companion else "",
        } if companion else {},
        "hospital_location": {
            "latitude": hospital.latitude or "",
            "longitude": hospital.longitude or "",
            "address": hospital.address or "",
        } if hospital else {},
    })


# ==================== 模拟支付 ====================

@router.post("/simulatePay")
def simulate_pay(form: dict, request: Request, db: Session = Depends(get_db)):
    """模拟支付：将待支付订单改为待服务"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and "code" in payload and payload["code"] == -2:
        return payload

    out_trade_no = form.get("out_trade_no")
    if not out_trade_no:
        return error("缺少订单号")

    order = db.query(Order).filter(Order.out_trade_no == out_trade_no).first()
    if not order:
        return error("订单不存在")
    if order.trade_state != "待支付":
        return error("订单状态不正确")

    order.trade_state = "待服务"
    order.paid_price = order.price
    db.commit()

    return success({"trade_state": order.trade_state})


# ==================== 天气与出行建议 ====================

@router.get("/weather")
async def get_weather(city: str = "北京", dest: str = "医院"):
    """获取天气及出行建议"""
    weather = await fetch_weather(city)
    advice = get_travel_advice(weather, dest)
    return success({
        "weather": weather,
        "advice": advice,
    })
