"""从高德地图获取医院真实图片并写入数据库"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Hospital
from app.utils.hospital_image import fetch_hospital_image


async def update_hospital_images():
    """获取高德图片并更新到数据库"""
    db = SessionLocal()
    try:
        hospitals = db.query(Hospital).all()
        print(f"共 {len(hospitals)} 家医院，开始获取高德图片...")
        ok = 0
        for h in hospitals:
            img = await fetch_hospital_image(h.name)
            if img:
                h.avatar_url = img
                ok += 1
                print(f"  [OK] {h.name}")
            else:
                print(f"  [--] {h.name} (无高德图片)")
        db.commit()
        print(f"\n成功更新 {ok}/{len(hospitals)} 家医院图片")
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(update_hospital_images())
