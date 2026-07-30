"""种子数据初始化脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models import (
    H5User, AdminUser, Menu, MenuRole, Hospital,
    Companion, Service, Slide, Photo, Order,
)
from app.utils.auth import hash_password


def init_database():
    """创建所有表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成!")


def seed_data():
    """插入种子数据"""
    db = SessionLocal()

    try:
        # 检查是否已有数据
        if db.query(AdminUser).first():
            print("数据库已有数据，跳过种子数据插入")
            return

        print("正在插入种子数据...")

        # ===== 1. H5用户 =====
        h5_users = [
            H5User(username="zhangsan", password=hash_password("123456"), name="张三",
                   avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan", mobile="13800138001"),
            H5User(username="lisi", password=hash_password("123456"), name="李四",
                   avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=lisi", mobile="13800138002"),
        ]
        db.add_all(h5_users)

        # ===== 2. 管理员 =====
        admin_users = [
            AdminUser(username="13800000000", password=hash_password("admin123"),
                       name="超级管理员", mobile="13800000000", permissions_id=0, active=1),
            AdminUser(username="13800000001", password=hash_password("123456"),
                       name="运营人员", mobile="13800000001", permissions_id=1, active=1),
        ]
        db.add_all(admin_users)

        # ===== 3. 菜单 =====
        menus = [
            # 一级菜单
            Menu(id=1, name="控制台", parent_id=0, icon="Platform", path="/dashboard",
                 describe="用于展示当前系统中的统计数据、统计报表及重要实时数据", sort=1),
            Menu(id=2, name="权限管理", parent_id=0, icon="Grid", sort=2),
            Menu(id=3, name="DIDI陪诊", parent_id=0, icon="BellFilled", sort=3),
            # 二级菜单 - 权限管理
            Menu(id=4, name="账号管理", parent_id=2, icon="Avatar", path="/auth/admin",
                 describe="管理员可以进行编辑，权限修改后需要登出才会生效", sort=1),
            Menu(id=5, name="菜单管理", parent_id=2, icon="Menu", path="/auth/group",
                 describe="菜单规则通常对应一个控制器的方法，同时菜单栏数据也从规则中获取", sort=2),
            # 二级菜单 - DIDI陪诊
            Menu(id=6, name="陪护管理", parent_id=3, icon="Checked", path="/vppz/staff",
                 describe="陪护师可以进行创建和修改，设置对应生效状态控制C端选择", sort=1),
            Menu(id=7, name="订单管理", parent_id=3, icon="List", path="/vppz/order",
                 describe="C端下单后可以查看所有订单状态，已支付的订单可以完成陪护状态修改", sort=2),
        ]
        db.add_all(menus)

        # ===== 4. 菜单角色 =====
        roles = [
            MenuRole(id=1, name="运营组", permissions=[1, 4, 5, 6, 7]),
        ]
        db.add_all(roles)

        # ===== 5. 医院（每所医院独立建筑实景图） =====
        hospitals = [
            # 北京
            Hospital(name="北京协和医院", rank="三甲", label="全国顶级",
                     intro="北京协和医院是集医疗、教学、科研于一体的现代化综合三级甲等医院",
                     avatar_url="https://images.unsplash.com/photo-1551076805-e1869033e561?w=400&h=300&fit=crop",
                     latitude="39.9120", longitude="116.4147",
                     address="北京市东城区帅府园1号", city="北京"),
            Hospital(name="北京大学第三医院", rank="三甲", label="综合医院",
                     intro="北医三院是国内顶尖的三级甲等综合医院，运动医学、生殖医学等特色专科享誉全国",
                     avatar_url="https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=400&h=300&fit=crop",
                     latitude="39.9842", longitude="116.3499",
                     address="北京市海淀区花园北路49号", city="北京"),
            Hospital(name="北京同仁医院", rank="三甲", label="专科特色",
                     intro="北京同仁医院以眼科、耳鼻咽喉科为重点，是一所大型三级甲等综合医院",
                     avatar_url="https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=400&h=300&fit=crop",
                     latitude="39.9000", longitude="116.4167",
                     address="北京市东城区东交民巷1号", city="北京"),
            # 上海
            Hospital(name="上海交通大学医学院附属瑞金医院", rank="三甲", label="综合医院",
                     intro="瑞金医院是一所大型综合性教学医院，拥有多个国家级重点学科",
                     avatar_url="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&h=300&fit=crop",
                     latitude="31.2093", longitude="121.4675",
                     address="上海市黄浦区瑞金二路197号", city="上海"),
            Hospital(name="复旦大学附属华山医院", rank="三甲", label="综合医院",
                     intro="华山医院是国家卫生部和上海市共建的知名三级甲等医院，神经外科、手外科等领先",
                     avatar_url="https://images.unsplash.com/photo-1579154204601-01588f351e67?w=400&h=300&fit=crop",
                     latitude="31.2200", longitude="121.4450",
                     address="上海市静安区乌鲁木齐中路12号", city="上海"),
            Hospital(name="上海长海医院", rank="三甲", label="综合医院",
                     intro="长海医院是第二军医大学附属医院，肝胆外科、消化内科等特色鲜明",
                     avatar_url="https://images.unsplash.com/photo-1570498839593-e565b39455fc?w=400&h=300&fit=crop",
                     latitude="31.2990", longitude="121.5180",
                     address="上海市杨浦区长海路168号", city="上海"),
            # 广州
            Hospital(name="中山大学附属第一医院", rank="三甲", label="综合医院",
                     intro="中山一院是国家重点大学附属医院中规模最大、综合实力最强的附属医院",
                     avatar_url="https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=400&h=300&fit=crop",
                     latitude="23.1340", longitude="113.2832",
                     address="广东省广州市越秀区中山二路58号", city="广州"),
            Hospital(name="南方医科大学南方医院", rank="三甲", label="综合医院",
                     intro="南方医院是一所集医疗、教学、科研于一体的三级甲等综合性医院",
                     avatar_url="https://images.unsplash.com/photo-1584515933487-779824d29309?w=400&h=300&fit=crop",
                     latitude="23.1900", longitude="113.3300",
                     address="广东省广州市白云区广州大道北1838号", city="广州"),
            # 武汉
            Hospital(name="华中科技大学同济医学院附属协和医院", rank="三甲", label="综合医院",
                     intro="武汉协和医院是国家卫生健康委员会直属的大型综合性三级甲等医院",
                     avatar_url="https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=400&h=300&fit=crop",
                     latitude="30.5826", longitude="114.2772",
                     address="湖北省武汉市江汉区解放大道1277号", city="武汉"),
            Hospital(name="武汉大学人民医院", rank="三甲", label="综合医院",
                     intro="武汉大学人民医院是一所集医疗、教学、科研为一体的三级甲等医院",
                     avatar_url="https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=400&h=300&fit=crop",
                     latitude="30.5600", longitude="114.3100",
                     address="湖北省武汉市武昌区张之洞路99号", city="武汉"),
            # 成都
            Hospital(name="四川大学华西医院", rank="三甲", label="综合医院",
                     intro="华西医院是中国西部疑难危急重症诊疗的国家级中心",
                     avatar_url="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
                     latitude="30.6455", longitude="104.0669",
                     address="四川省成都市武侯区国学巷37号", city="成都"),
            Hospital(name="四川省人民医院", rank="三甲", label="综合医院",
                     intro="四川省人民医院是一所集临床医疗、保健医疗、教学科研为一体的三级甲等医院",
                     avatar_url="https://images.unsplash.com/photo-1584982751601-97dcc096659c?w=400&h=300&fit=crop",
                     latitude="30.6600", longitude="104.0500",
                     address="四川省成都市青羊区一环路西二段32号", city="成都"),
            # 深圳
            Hospital(name="北京大学深圳医院", rank="三甲", label="综合医院",
                     intro="北京大学深圳医院是一所现代化三级甲等综合性医院，是北京大学附属医院之一",
                     avatar_url="https://images.unsplash.com/photo-1504439468489-c8920d796a29?w=400&h=300&fit=crop",
                     latitude="22.5550", longitude="114.0600",
                     address="广东省深圳市福田区莲花路1120号", city="深圳"),
            Hospital(name="深圳市人民医院", rank="三甲", label="综合医院",
                     intro="深圳市人民医院是深圳首家三级甲等医院，市级综合性医院",
                     avatar_url="https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=300&fit=crop",
                     latitude="22.5400", longitude="114.0790",
                     address="广东省深圳市罗湖区东门北路1017号", city="深圳"),
            # 杭州
            Hospital(name="浙江大学医学院附属第一医院", rank="三甲", label="综合医院",
                     intro="浙大一院是浙江省最大的三级甲等综合性医院，综合实力位居全国前列",
                     avatar_url="https://images.unsplash.com/photo-1562778612-e1e0cda9915c?w=400&h=300&fit=crop",
                     latitude="30.2700", longitude="120.1600",
                     address="浙江省杭州市上城区庆春路79号", city="杭州"),
            Hospital(name="浙江省人民医院", rank="三甲", label="综合医院",
                     intro="浙江省人民医院是一所集医疗、科研、教学为一体的大型综合性三级甲等医院",
                     avatar_url="https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&h=300&fit=crop",
                     latitude="30.2800", longitude="120.1700",
                     address="浙江省杭州市下城区上塘路158号", city="杭州"),
        ]
        db.add_all(hospitals)

        # ===== 6. 陪诊师 =====
        companions = [
            Companion(name="小王", avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=wang",
                      sex=2, age=28, mobile="13900000001", active=1),
            Companion(name="小李", avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=li",
                      sex=1, age=32, mobile="13900000002", active=1),
            Companion(name="小张", avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=zhang",
                      sex=2, age=26, mobile="13900000003", active=1),
            Companion(name="小刘", avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=liu",
                      sex=1, age=30, mobile="13900000004", active=0),
        ]
        db.add_all(companions)

        # ===== 7. 服务项目 =====
        services = [
            Service(name="全程陪诊", service_img="https://picsum.photos/seed/service1/100/100", price=0.5),
            Service(name="代办取药", service_img="https://picsum.photos/seed/service2/100/100", price=0.3),
        ]
        db.add_all(services)

        # ===== 8. 轮播图（使用医院实景图片） =====
        slides = [
            Slide(pic_image_url="https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&h=340&fit=crop", sort=1),
            Slide(pic_image_url="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=340&fit=crop", sort=2),
            Slide(pic_image_url="https://images.unsplash.com/photo-1587351021759-3772687cbfc8?w=800&h=340&fit=crop", sort=3),
        ]
        db.add_all(slides)

        # ===== 9. 图片库 =====
        photos = [
            Photo(url="https://api.dicebear.com/7.x/avataaars/svg?seed=avatar1", name="默认头像1"),
            Photo(url="https://api.dicebear.com/7.x/avataaars/svg?seed=avatar2", name="默认头像2"),
            Photo(url="https://api.dicebear.com/7.x/avataaars/svg?seed=avatar3", name="默认头像3"),
            Photo(url="https://api.dicebear.com/7.x/avataaars/svg?seed=avatar4", name="默认头像4"),
        ]
        db.add_all(photos)

        db.commit()
        print("种子数据插入完成!")
        print()
        print("=" * 50)
        print("默认登录账号:")
        print("  H5端:  用户名 zhangsan  密码 123456")
        print("  H5端:  用户名 lisi      密码 123456")
        print("  后台:  账号 admin       密码 admin123")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    seed_data()
