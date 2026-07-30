"""AI Agent 种子数据初始化脚本"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models import Menu, MenuRole
from app.agent_models import AgentConversation, AgentMessage, AgentTask, AgentConfig


def init_agent_tables():
    """创建 Agent 相关表"""
    print("正在创建 AI Agent 数据库表...")
    Base.metadata.create_all(bind=engine)
    print("AI Agent 数据库表创建完成!")


def seed_agent_data():
    """插入 AI Agent 种子数据"""
    db = SessionLocal()

    try:
        # ===== 1. Agent 配置 =====
        configs = [
            AgentConfig(
                agent_type="triage",
                display_name="分诊推荐Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.7,
                max_tokens=2048,
                system_prompt=(
                    "你是一个专业的医疗分诊助手。请根据用户的症状描述，推荐合适的就诊科室和医院。\n\n"
                    "重要规则：\n"
                    "1. 你只能推荐科室和医院，绝不下诊断或开药方\n"
                    "2. 必须在推荐中注明推荐仅供参考\n"
                    "3. 如果症状紧急（如胸痛、大出血等），必须提示紧急就医\n\n"
                    "请以JSON格式输出结果，包含以下字段：\n"
                    "- recommended_department: 推荐的科室名称\n"
                    "- symptom_summary: 症状分析摘要\n"
                    "- urgency_level: 紧急程度 normal/urgent/emergency\n"
                    "- disclaimer: 免责声明"
                ),
            ),
            AgentConfig(
                agent_type="customer_service",
                display_name="智能客服Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.8,
                max_tokens=2048,
                system_prompt=(
                    "你是一个专业的医疗陪诊平台客服助手。你的职责是：\n"
                    "1. 回答用户关于陪诊服务流程的问题\n"
                    "2. 介绍服务项目和价格\n"
                    "3. 解答预约、支付、取消等常见问题\n"
                    "4. 保持友好、耐心、专业的语气\n\n"
                    "注意：如果用户询问订单状态或需要订单操作，请引导用户使用订单查询功能。"
                ),
            ),
            AgentConfig(
                agent_type="order_assistant",
                display_name="订单助手Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.7,
                max_tokens=2048,
                system_prompt=(
                    "你是一个订单助手，负责处理用户的订单相关问题。包括：\n"
                    "1. 查询订单状态\n"
                    "2. 处理改约请求\n"
                    "3. 处理取消订单\n"
                    "4. 发送催单提醒\n\n"
                    "注意：只能查询当前登录用户的订单信息。保持友好专业的语气。"
                ),
            ),
            AgentConfig(
                agent_type="dispatch",
                display_name="调度中心Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.3,
                max_tokens=1024,
                system_prompt=(
                    "你是一个智能路由助手，负责分析用户的问题并判断应该由哪个AI助理来处理。\n\n"
                    "分类规则，只返回以下类别之一：\n"
                    "1. triage — 用户描述症状、询问科室、推荐医院或陪诊师时\n"
                    "2. customer_service — 用户询问服务价格、流程、一般性问题、咨询客服时\n"
                    "3. order_assistant — 用户查询订单、取消订单、改约、催单等订单相关操作时\n"
                    "4. unknown — 无法判断时\n\n"
                    "请以JSON格式输出：intent字段放分类结果，reasoning字段放判断理由"
                ),
            ),
            AgentConfig(
                agent_type="operations",
                display_name="运营分析Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.7,
                max_tokens=2048,
                system_prompt=(
                    "你是医疗陪诊平台的运营数据分析师。你可以：\n"
                    "1. 分析订单数据（总量、状态分布、趋势）\n"
                    "2. 分析用户数据（注册量、活跃度）\n"
                    "3. 分析陪诊师数据（工作量、效率）\n"
                    "4. 提供运营优化建议\n\n"
                    "基于客观数据给出分析结论，数据用具体数字说话。"
                ),
            ),
            AgentConfig(
                agent_type="collaboration",
                display_name="协作合成Agent",
                enabled=1,
                model_name="deepseek-chat",
                temperature=0.5,
                max_tokens=2048,
                system_prompt=(
                    "你是一个协作汇总助手。你的职责是接收多个AI助理对同一问题的分析结果，"
                    "将它们整合成一份连贯、友好的回复给用户。\n\n"
                    "要求：\n"
                    "1. 综合各助理的观点，不要简单罗列\n"
                    "2. 保持语气一致、自然流畅\n"
                    "3. 如果各助理观点有冲突，取最合理的一个并说明\n"
                    "4. 最终回复要包含所有关键信息，但简洁明了"
                ),
            ),
        ]

        for cfg in configs:
            existing = db.query(AgentConfig).filter(
                AgentConfig.agent_type == cfg.agent_type
            ).first()
            if not existing:
                db.add(cfg)
                print(f"  新增 AgentConfig: {cfg.agent_type}")

        # ===== 2. 菜单（AI智能代理） =====
        agent_menus = [
            Menu(id=8, name="AI智能运营", parent_id=0, icon="Monitor", sort=4),
            Menu(id=9, name="运营数据助手", parent_id=8, icon="ChatLineSquare",
                 path="/agent/overview",
                 describe="通过对话查询运营数据", sort=1),
            Menu(id=10, name="FAQ知识库", parent_id=8, icon="Setting",
                 path="/agent/config",
                 describe="管理常见问题与回答", sort=2),
        ]
        for m in agent_menus:
            existing = db.query(Menu).filter(Menu.id == m.id).first()
            if not existing:
                db.add(m)
                print(f"  新增菜单: {m.name}")

        # ===== 3. 更新运营组权限 =====
        role = db.query(MenuRole).filter(MenuRole.id == 1).first()
        if role:
            current_perms = set(role.permissions or [])
            new_perms = {9, 10}
            if not new_perms.issubset(current_perms):
                role.permissions = list(current_perms | new_perms)
                print(f"  更新运营组权限: 添加AI代理菜单")

        db.commit()
        print("\nAI Agent 种子数据插入完成!")

    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_agent_tables()
    seed_agent_data()
