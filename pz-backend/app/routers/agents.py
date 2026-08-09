"""AI Agent 路由"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order, H5User
from ..agent_models import AgentConversation, AgentMessage, AgentTask, AgentFeedback, FAQ
from ..agent_schemas import AgentChatRequest, TriageRequest, AgentTaskParams, VisitPlanRequest
from ..utils.response import success, error
from ..utils.auth import verify_h5_token, verify_admin_token
from ..agents.orchestrator import AgentOrchestrator
from ..agents.visit_planner import VisitPlannerOrchestrator
from ..agents.admin_dashboard import AdminOrchestrator as AdminDashboardOrchestrator

router = APIRouter(prefix="/agent")
orchestrator = AgentOrchestrator()
visit_planner = VisitPlannerOrchestrator()
admin_dashboard = AdminDashboardOrchestrator()


# ==================== H5 端接口 ====================

@router.post("/chat")
async def agent_chat(form: AgentChatRequest, request: Request):
    """Agent 聊天"""
    terminal = request.headers.get("terminal", "h5")
    payload = verify_admin_token(request) if terminal == "admin" else verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    result = await orchestrator.chat(
        message=form.message,
        agent_type=form.agent_type,
        user_id=payload.get("user_id"),
        conversation_id=form.conversation_id,
    )
    return success(result)


@router.post("/triage/recommend")
async def triage_recommend(form: TriageRequest, request: Request):
    """分诊推荐"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    meta_data = await orchestrator.triage_recommend(
        symptoms=form.symptoms,
        patient_age=form.patient_age,
        patient_gender=form.patient_gender,
    )
    return success(meta_data)


@router.post("/visit-plan")
async def visit_plan(form: VisitPlanRequest, request: Request):
    """
    智能就医规划 - 多Agent协作生成完整就诊攻略
    """
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    result = await visit_planner.plan(
        symptoms=form.symptoms,
        patient_age=form.patient_age,
        patient_gender=form.patient_gender,
        city=form.city,
        lat=form.lat,
        lng=form.lng,
        user_id=payload.get("user_id", 0),
    )
    return success(result)


@router.get("/conversation/list")
def get_conversation_list(request: Request, db: Session = Depends(get_db)):
    """用户会话列表"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    user_id = payload.get("user_id")

    conversations = db.query(AgentConversation).filter(
        AgentConversation.user_id == user_id
    ).order_by(AgentConversation.updated_at.desc()).limit(20).all()

    return success([{
        "conversation_id": c.conversation_id,
        "agent_type": c.agent_type,
        "title": c.title or "",
        "message_count": db.query(AgentMessage).filter(
            AgentMessage.conversation_id == c.conversation_id
        ).count(),
        "created_at": str(c.created_at) if c.created_at else "",
    } for c in conversations])


@router.get("/conversation/{conv_id}/messages")
def get_conversation_messages(conv_id: str, request: Request, db: Session = Depends(get_db)):
    """获取会话消息"""
    payload = verify_admin_token(request) if request.headers.get("terminal") == "admin" else verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    messages = db.query(AgentMessage).filter(
        AgentMessage.conversation_id == conv_id
    ).order_by(AgentMessage.created_at).all()

    return success([{
        "role": m.role, "content": m.content, "content_type": m.content_type,
        "meta_data": m.meta_data, "created_at": str(m.created_at) if m.created_at else "",
    } for m in messages])


@router.post("/feedback")
def submit_feedback(form: dict, request: Request, db: Session = Depends(get_db)):
    """客服评价"""
    payload = verify_h5_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    db.add(AgentFeedback(
        conversation_id=form.get("conversation_id", ""),
        rating=form.get("rating", 0),
        feedback_text=form.get("feedback_text", ""),
        user_id=payload.get("user_id"),
    ))
    db.commit()
    return success(None, message="感谢您的反馈")


@router.get("/faq/search")
def search_faq(keyword: str = "", db: Session = Depends(get_db)):
    """FAQ搜索"""
    query = db.query(FAQ).filter(FAQ.enabled == 1)
    if keyword:
        query = query.filter(FAQ.question.like(f"%{keyword}%") | FAQ.keywords.like(f"%{keyword}%"))
    faqs = query.order_by(FAQ.sort).limit(20).all()
    return success([{
        "id": f.id, "question": f.question, "answer": f.answer[:100],
        "category": f.category,
    } for f in faqs])


# ==================== Admin 端接口 ====================

@router.get("/admin/overview")
def get_admin_overview(request: Request):
    """运营数据总览"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    return success(orchestrator.get_overview())


@router.get("/admin/business/stats")
def get_business_stats(request: Request, db: Session = Depends(get_db)):
    """业务统计"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload

    # 订单统计
    order_status = {}
    for s in ["待支付", "待服务", "已完成", "已取消"]:
        c = db.query(Order).filter(Order.trade_state == s).count()
        if c > 0:
            order_status[s] = c

    # 咨询统计
    conv_by_type = {}
    for t in db.query(AgentConversation.agent_type).all():
        at = t[0] or "unknown"
        conv_by_type[at] = conv_by_type.get(at, 0) + 1

    return success({
        "orders": {"total": db.query(Order).count(), "by_status": order_status},
        "users": {"total": db.query(H5User).count()},
        "conversations": {"total": db.query(AgentConversation).count(), "by_type": conv_by_type},
        "faq_count": db.query(FAQ).filter(FAQ.enabled == 1).count(),
    })


# ==================== Admin 智能运营中心 ====================


@router.get("/admin/dashboard")
async def get_admin_dashboard(request: Request):
    """智能运营仪表盘：预警+分析+报告 一站式"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    result = await admin_dashboard.dashboard()
    return success(result)


# ==================== FAQ 管理 ====================

@router.get("/admin/faq/list")
def get_faq_list(params: AgentTaskParams = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """FAQ列表"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    query = db.query(FAQ)
    total = query.count()
    faqs = query.order_by(FAQ.sort).offset(
        (params.pageNum - 1) * params.pageSize
    ).limit(params.pageSize).all()
    return success({
        "list": [{"id": f.id, "question": f.question, "answer": f.answer,
                  "category": f.category, "keywords": f.keywords, "sort": f.sort, "enabled": f.enabled} for f in faqs],
        "total": total,
    })


@router.post("/admin/faq/create")
def create_faq(form: dict, request: Request, db: Session = Depends(get_db)):
    """新建FAQ"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    db.add(FAQ(question=form.get("question",""), answer=form.get("answer",""),
               category=form.get("category","general"), keywords=form.get("keywords",""),
               sort=form.get("sort",0), enabled=form.get("enabled",1)))
    db.commit()
    return success(None, message="创建成功")


@router.post("/admin/faq/update")
def update_faq(form: dict, request: Request, db: Session = Depends(get_db)):
    """更新FAQ"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    faq = db.query(FAQ).filter(FAQ.id == form.get("id")).first()
    if not faq:
        return error("FAQ不存在")
    for field in ["question", "answer", "category", "keywords", "sort", "enabled"]:
        if field in form:
            setattr(faq, field, form[field])
    db.commit()
    return success(None, message="更新成功")


@router.post("/admin/faq/delete")
def delete_faq(form: dict, request: Request, db: Session = Depends(get_db)):
    """删除FAQ"""
    payload = verify_admin_token(request)
    if isinstance(payload, dict) and payload.get("code") == -2:
        return payload
    db.query(FAQ).filter(FAQ.id == form.get("id")).delete()
    db.commit()
    return success(None, message="已删除")
