"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


# ========== H5端 ==========

class H5LoginForm(BaseModel):
    userName: str
    passWord: str


class CreateOrderForm(BaseModel):
    hospital_id: int
    hospital_name: str
    demand: Optional[str] = ""
    companion_id: Optional[int] = 0
    receiveAddress: Optional[str] = ""
    tel: Optional[str] = ""
    starttime: Optional[int] = 0


class OrderListParams(BaseModel):
    state: Optional[str] = ""


class OrderDetailParams(BaseModel):
    oid: str


# ========== Admin端 ==========

class AdminLoginForm(BaseModel):
    userName: str
    passWord: str


class GetCodeForm(BaseModel):
    tel: str


class UserAuthForm(BaseModel):
    userName: str
    passWord: str
    validCode: Optional[str] = ""


class AuthAdminParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)


class MenuListParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)


class UpdateUserForm(BaseModel):
    name: str
    permissions_id: int
    mobile: Optional[str] = ""


class SetMenuForm(BaseModel):
    name: str
    permissions: str  # JSON 字符串
    id: Optional[int] = 0


class CompanionForm(BaseModel):
    id: Optional[int] = 0
    name: str
    avatar: str
    sex: str  # "1" 或 "2"
    age: int = 20
    mobile: str
    active: int = 1


class CompanionListParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)


class DeleteCompanionForm(BaseModel):
    id: list | int  # 单个ID或ID列表


class AdminOrderParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    out_trade_no: Optional[str] = ""
    trade_state: Optional[str] = ""


class UpdateOrderForm(BaseModel):
    id: str  # out_trade_no


class SimulatePayForm(BaseModel):
    out_trade_no: str
