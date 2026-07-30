"""AI 智能运营菜单种子脚本 - 补全数据库菜单表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Menu


def seed_agent_menus():
    """插入 AI 智能运营相关菜单"""
    db = SessionLocal()
    try:
        # 检查是否已有AI运营菜单
        existing = db.query(Menu).filter(Menu.name == "AI智能运营").first()
        if existing:
            print("AI智能运营菜单已存在，跳过")
            return

        print("正在插入 AI 智能运营菜单...")

        agent_menus = [
            # 一级菜单
            Menu(id=8, name="AI智能运营", parent_id=0, icon="Monitor",
                 sort=4, describe="AI驱动的运营分析、预警与报告"),
            # 二级菜单
            Menu(id=9, name="运营数据助手", parent_id=8, icon="ChatLineSquare",
                 path="/agent/overview",
                 describe="通过对话查询订单、用户等运营数据", sort=1),
            Menu(id=10, name="FAQ知识库", parent_id=8, icon="Setting",
                 path="/agent/config",
                 describe="管理常见问题与回答", sort=2),
            Menu(id=11, name="智能运营中心", parent_id=8, icon="DataAnalysis",
                 path="/agent/dashboard",
                 describe="AI驱动的运营分析、预警与报告", sort=3),
        ]
        db.add_all(agent_menus)
        db.commit()
        print("AI 智能运营菜单插入完成!")
        print("  新增了: AI智能运营 → 运营数据助手 / FAQ知识库 / 智能运营中心")
    except Exception as e:
        db.rollback()
        print(f"插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_agent_menus()
