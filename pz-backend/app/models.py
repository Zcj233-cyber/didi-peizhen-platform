"""SQLAlchemy 数据模型"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, BigInteger,
    DateTime, JSON, SmallInteger, func
)
from .database import Base


class H5User(Base):
    """C端用户"""
    __tablename__ = "h5_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    name = Column(String(50), comment="昵称")
    avatar = Column(String(500), comment="头像")
    mobile = Column(String(20), comment="手机号")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AdminUser(Base):
    """后台管理员"""
    __tablename__ = "admin_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名/手机号")
    password = Column(String(255), nullable=False, comment="密码")
    name = Column(String(50), comment="昵称")
    mobile = Column(String(20), comment="手机号")
    permissions_id = Column(Integer, default=0, comment="权限组ID")
    active = Column(SmallInteger, default=1, comment="状态 1正常 0失效")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Menu(Base):
    """菜单"""
    __tablename__ = "menu"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="菜单名称")
    parent_id = Column(Integer, default=0, comment="父级ID")
    icon = Column(String(50), comment="图标")
    path = Column(String(200), comment="前端路由path")
    component = Column(String(200), comment="组件路径")
    describe = Column(Text, comment="描述")
    sort = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MenuRole(Base):
    """菜单角色/权限组"""
    __tablename__ = "menu_role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="角色名称")
    permissions = Column(JSON, comment="权限菜单ID列表")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Hospital(Base):
    """医院"""
    __tablename__ = "hospital"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="医院名称")
    rank = Column(String(50), comment="等级")
    label = Column(String(100), comment="标签")
    intro = Column(Text, comment="简介")
    avatar_url = Column(String(500), comment="图片URL")
    latitude = Column(String(20), comment="纬度")
    longitude = Column(String(20), comment="经度")
    address = Column(String(200), comment="地址")
    city = Column(String(50), comment="所在城市")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Companion(Base):
    """陪诊师"""
    __tablename__ = "companion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="名称")
    avatar = Column(String(500), comment="头像")
    sex = Column(SmallInteger, default=1, comment="性别 1男 2女")
    age = Column(Integer, default=20, comment="年龄")
    mobile = Column(String(20), comment="手机号")
    active = Column(SmallInteger, default=1, comment="状态 1正常 0失效")
    create_time = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Service(Base):
    """服务项目"""
    __tablename__ = "service"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="服务名称")
    service_img = Column(String(500), comment="服务图片")
    price = Column(Float, default=0, comment="价格")
    created_at = Column(DateTime, default=func.now())


class Order(Base):
    """订单"""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    out_trade_no = Column(String(50), unique=True, nullable=False, comment="订单号")
    user_id = Column(Integer, comment="用户ID")
    hospital_id = Column(Integer, comment="医院ID")
    hospital_name = Column(String(100), comment="医院名称")
    service_id = Column(Integer, comment="服务ID")
    service_name = Column(String(100), comment="服务名称")
    service_img = Column(String(500), comment="服务图片")
    companion_id = Column(Integer, comment="陪诊师ID")
    companion_name = Column(String(50), comment="陪诊师名称")
    client_name = Column(String(50), comment="就诊人")
    client_mobile = Column(String(20), comment="就诊人电话")
    starttime = Column(BigInteger, comment="期望就诊时间戳")
    receive_address = Column(String(500), comment="接送地址")
    tel = Column(String(20), comment="联系电话")
    demand = Column(Text, comment="其他需求")
    trade_state = Column(String(20), default="待支付", comment="订单状态")
    price = Column(Float, default=0, comment="总价")
    paid_price = Column(Float, default=0, comment="已付")
    order_start_time = Column(BigInteger, comment="下单时间戳")
    code_url = Column(String(500), comment="支付二维码链接")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Slide(Base):
    """轮播图"""
    __tablename__ = "slides"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pic_image_url = Column(String(500), comment="图片URL")
    sort = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=func.now())


class Photo(Base):
    """图片库"""
    __tablename__ = "photo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), comment="图片URL")
    name = Column(String(100), comment="图片名称")
    created_at = Column(DateTime, default=func.now())
