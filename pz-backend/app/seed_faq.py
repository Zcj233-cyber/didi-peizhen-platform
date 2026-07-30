"""FAQ 知识库种子数据"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.agent_models import FAQ, AgentFeedback


def init_tables():
    print("正在创建 FAQ 等数据表...")
    Base.metadata.create_all(bind=engine)
    print("完成!")


def seed_faq():
    db = SessionLocal()
    try:
        if db.query(FAQ).first():
            print("FAQ 已有数据，跳过")
            return

        faqs = [
            FAQ(question="全程陪诊服务包括哪些内容？",
                answer="全程陪诊服务包括：就诊前咨询与准备、陪同就诊、协助与医生沟通、取报告单、代取药、缴费协助等一站式服务。我们的陪诊师会全程陪伴您完成整个就诊流程。",
                category="service", keywords="全程陪诊,服务内容,包括什么", sort=1),
            FAQ(question="陪诊服务如何收费？",
                answer="目前平台提供两种服务：\n1. 全程陪诊：0.5元/次（半日），包含陪同就诊全流程\n2. 代办取药：0.3元/次，代取药并配送\n首次注册用户可享受优惠体验价。",
                category="price", keywords="价格,收费,多少钱,费用", sort=2),
            FAQ(question="如何预约陪诊服务？",
                answer="预约流程：\n1. 打开APP首页 → 选择医院\n2. 选择就诊日期和陪诊师\n3. 填写就诊人信息和需求\n4. 提交订单 → 在线支付 → 预约成功\n建议提前1-2天预约，以便安排合适的陪诊师。",
                category="process", keywords="预约,下单,怎么预约", sort=3),
            FAQ(question="取消订单后费用会退吗？",
                answer="取消订单的退款规则：\n1. 就诊前24小时取消：全额退款\n2. 就诊前12-24小时取消：退80%\n3. 就诊前12小时内取消：不退费\n取消后款项将在1-3个工作日原路返回。",
                category="order", keywords="取消,退款,退费,取消订单", sort=4),
            FAQ(question="陪诊师的专业程度如何？",
                answer="我们的陪诊师均经过严格筛选和培训：\n1. 具备医护背景或相关工作经验\n2. 通过平台专业培训考核\n3. 服务意识强，耐心细致\n4. 平台会对每位陪诊师进行服务评价跟踪",
                category="service", keywords="陪诊师,专业,资质,靠谱", sort=5),
            FAQ(question="可以指定陪诊师吗？",
                answer="可以的。在创建订单时，您可以从陪诊师列表中选择心仪的陪诊师。如果选择的陪诊师当日已被预约，系统会提示您选择其他陪诊师或更换日期。",
                category="service", keywords="指定陪诊师,选择,更换", sort=6),
            FAQ(question="就诊当天需要带什么？",
                answer="就诊当天建议携带：\n1. 身份证/医保卡\n2. 既往病历和检查报告\n3. 就诊卡（如有）\n4. 手机（保持畅通）\n5. 口罩等防护用品\n陪诊师会提前与您联系确认集合地点。",
                category="process", keywords="就诊,准备,带什么,需要", sort=7),
            FAQ(question="服务范围覆盖哪些医院？",
                answer="目前平台已覆盖全国主要城市的三甲医院，包括：\n• 北京协和医院\n• 上海瑞金医院\n• 广州中山一院\n• 武汉协和医院\n• 成都华西医院\n更多医院正在陆续接入中。",
                category="service", keywords="医院,范围,覆盖,哪些城市", sort=8),
            FAQ(question="支付方式有哪些？",
                answer="目前支持微信支付。订单提交后会生成支付二维码，使用微信扫码即可完成支付。后续将开通支付宝、银联等更多支付方式。",
                category="order", keywords="支付,付款,微信,支付宝", sort=9),
            FAQ(question="可以开发票吗？",
                answer="可以的。完成服务后，您可以在订单详情页申请开具电子发票。发票内容为「陪诊服务费」，我们将以电子邮件形式发送给您。",
                category="order", keywords="发票,开票,报销", sort=10),
            FAQ(question="如何联系客服？",
                answer="您可以通过以下方式联系我们：\n1. 在线客服：APP内AI智能助手（7x24小时）\n2. 客服电话：400-888-8888（工作日9:00-18:00）\n3. 在线留言：在APP内提交留言，我们将在24小时内回复",
                category="general", keywords="客服,联系,电话,人工", sort=11),
            FAQ(question="改约如何操作？",
                answer="如需改约，请在订单详情页点击「改约」按钮。改约规则：\n1. 提前24小时以上：免费改约1次\n2. 12-24小时：收取20%改约费\n3. 12小时内：不可改约，建议取消重新预约",
                category="order", keywords="改约,改时间,延期,修改", sort=12),
            FAQ(question="陪诊服务有时间限制吗？",
                answer="全程陪诊服务按半日计算（约4小时）。如果就诊时间超过服务时长，陪诊师会根据实际情况与您沟通，超时部分按小时计费（需现场支付给陪诊师）。",
                category="service", keywords="时间,时长,超时,多久", sort=13),
            FAQ(question="可以帮家人预约陪诊吗？",
                answer="当然可以！您可以为家人或朋友预约陪诊服务。在填写就诊人信息时，请准确填写实际就诊人的姓名、手机号和相关信息，以便陪诊师联系。",
                category="service", keywords="家人,朋友,代预约,老人", sort=14),
            FAQ(question="平台安全保障如何？",
                answer="平台高度重视用户安全：\n1. 陪诊师均通过实名认证和背景审核\n2. 服务过程全程GPS追踪\n3. 平台提供服务保险保障\n4. 用户信息加密存储，严格保护隐私",
                category="general", keywords="安全,保障,保险,隐私", sort=15),
        ]
        db.add_all(faqs)
        db.commit()
        print(f"FAQ 种子数据插入完成! 共{len(faqs)}条")
    except Exception as e:
        db.rollback()
        print(f"FAQ 插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_tables()
    seed_faq()
