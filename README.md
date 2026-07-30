# 🏥 DIDI陪诊服务平台

> 基于 AI Agent 的智慧医疗陪诊服务平台，包含 C端用户端（H5）和后台管理系统。

## 📸 功能截图

### 📱 H5 移动端

| 首页 | 智能分诊(输入症状) | 分诊结果(科室推荐) | AI客服聊天 |
|------|-------------------|-------------------|-----------|
| ![H5首页](screenshots/h5-home.png) | ![分诊输入](screenshots/h5-triage-input.png) | ![分诊结果](screenshots/h5-triage-result.png) | ![聊天](screenshots/h5-chat.png) |

### 🖥 后台管理

| 控制台 | 运营数据助手 | FAQ知识库 | 订单管理 |
|--------|------------|----------|---------|
| ![控制台](screenshots/admin-dashboard.png) | ![运营数据助手](screenshots/admin-agent-overview.png) | ![FAQ](screenshots/admin-faq.png) | ![订单管理](screenshots/admin-order.png) |

---

## 📱 项目概览

一个完整的陪诊服务数字化平台，用户可以通过 H5 端预约陪诊服务、智能分诊、AI客服咨询，管理员通过后台管理系统进行订单、陪护师、权限等全流程管理。系统集成了 **DeepSeek 大模型** 驱动的多 AI Agent 智能体系。

### 核心能力

| 端 | 面向 | 核心功能 |
|----|------|---------|
| **pzH5** | 就诊用户 | 智能分诊、AI客服、预约下单、订单管理、医院导航 |
| **pzadmin** | 管理员 | 订单管理、陪护师管理、菜单权限、AI运营分析、FAQ知识库 |
| **pz-backend** | API服务 | AI Agent 编排、业务API、数据持久化 |

---

## 🧠 AI Agent 系统

系统集成了 **6 个专业 AI Agent**，由 LangChain + DeepSeek API 驱动：

| Agent | 职责 | 使用场景 |
|-------|------|---------|
| 🤖 **分诊推荐Agent** | 症状分析 → 推荐科室、医院 | 用户描述症状后获得就诊建议 |
| 💬 **智能客服Agent** | FAQ匹配 + LLM增强回答 | 解答价格、流程、订单等常见问题 |
| 📋 **订单助手Agent** | 订单查询、改约、取消 | 用户询问订单状态或需要操作订单 |
| 📊 **运营数据助手** | 数据统计、运营分析 | 管理员对话查询业务数据 |
| 🧠 **协作合成Agent** | 汇总多Agent输出 | 复合问题时整合多个Agent的回答 |
| 🤝 **关键词路由** | 意图识别分发 | 替代调度中心，用关键词匹配路由 |

### 多 Agent 协作流程

```
用户提问 → 关键词路由 → 检测复合意图
                          ↓
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    分诊Agent       订单助手Agent      客服Agent
         └────────────────┼────────────────┘
                          ↓
                   协作合成Agent → 统一回复
```

---

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | Python FastAPI |
| **AI框架** | LangChain + DeepSeek API |
| **数据库** | MySQL + SQLAlchemy ORM |
| **认证** | JWT (python-jose) + bcrypt |
| **前端(H5)** | Vue3 + Vant4（移动端） |
| **前端(Admin)** | Vue3 + ElementPlus |
| **地图服务** | 高德地图 API（POI搜索 + 导航） |
| **天气服务** | wttr.in |

---

## 📂 项目结构

```
e:/vscode代码/项目/
├── pz-backend/                  # 后端服务
│   ├── app/
│   │   ├── agents/              # AI Agent 核心
│   │   │   ├── base.py          # BaseAgent 抽象类
│   │   │   ├── customer_service.py  # 客服Agent
│   │   │   ├── triage_agent.py      # 分诊Agent
│   │   │   ├── order_assistant.py   # 订单助手
│   │   │   ├── operations_agent.py  # 运营分析
│   │   │   ├── orchestrator.py      # Agent编排器
│   │   │   └── deepseek_llm.py      # DeepSeek 封装
│   │   ├── routers/
│   │   │   ├── h5.py            # H5端 API
│   │   │   ├── admin.py         # 后台管理 API
│   │   │   └── agents.py        # Agent API
│   │   ├── models.py            # ORM 模型
│   │   ├── schemas.py           # Pydantic 校验
│   │   ├── config.py            # 配置
│   │   └── utils/               # 工具（天气、地图、距离）
│   ├── seed.py                  # 种子数据
│   ├── seed_agents.py           # Agent种子数据
│   ├── seed_faq.py              # FAQ种子数据
│   └── requirements.txt
├── pzH5/                        # H5移动端
│   └── src/
│       ├── pages/               # 页面
│       │   ├── home/            # 首页（医院列表、轮播）
│       │   ├── login/           # 登录
│       │   ├── order/           # 订单列表
│       │   ├── detail/          # 订单详情
│       │   ├── createOrder/     # 创建订单
│       │   ├── user/            # 个人中心
│       │   └── agent/           # AI功能
│       │       ├── triage/      # 智能分诊
│       │       └── chat/        # AI客服聊天
│       ├── api/index.js         # API 封装
│       └── router/index.js      # 路由配置
└── pzadmin/                     # 后台管理
    └── src/
        ├── views/
        │   ├── dashboard/       # 控制台
        │   ├── vppz/            # 陪诊业务
        │   │   ├── order/       # 订单管理
        │   │   └── staff/       # 陪护师管理
        │   ├── auth/            # 权限管理
        │   └── agent/           # AI运营
        │       ├── overview/    # 运营数据助手
        │       └── config/      # FAQ知识库
        ├── api/index.js         # API 封装
        └── router/index.js      # 路由配置
```

---

## 🚀 快速启动

### 1. 后端

```bash
cd pz-backend

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 初始化数据库（首次运行）
python app/seed.py
python app/seed_agents.py
python app/seed_faq.py
python app/seed_amap_images.py

# 启动服务
python run.py
# 服务运行在 http://localhost:2306
```

### 2. H5 移动端

```bash
cd pzH5
npm install
npm run dev
# 运行在 http://localhost:5500
```

### 3. 后台管理

```bash
cd pzadmin
npm install
npm run dev
# 运行在 http://localhost:5173
```

---

## 🔑 默认账号

| 端 | 账号 | 密码 |
|----|------|------|
| H5端 | `zhangsan` | `123456` |
| H5端 | `lisi` | `123456` |
| 后台管理 | `13800000000` | `admin123` |
| 后台管理 | `13800000001` | `123456` |

---

## ⚙️ 环境变量配置

项目使用 `.env` 文件管理敏感配置，**不要提交到 Git**：

```ini
# pz-backend/.env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
AMAP_KEY=your-amap-key-here
```

---

## 🌐 API 概览

### H5 端

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v3pz/login` | 用户登录（H5/Admin） |
| GET | `/v3pz/index/index` | 首页数据（医院列表、轮播） |
| GET | `/v3pz/h5/companion` | 创建订单页数据 |
| POST | `/v3pz/createOrder` | 创建订单 |
| GET | `/v3pz/order/list` | 订单列表 |
| GET | `/v3pz/order/detail` | 订单详情 |
| GET | `/v3pz/weather` | 天气出行建议 |
| POST | `/v3pz/agent/chat` | AI聊天 |
| POST | `/v3pz/agent/triage/recommend` | AI分诊推荐 |

### Admin 端

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v3pz/agent/admin/overview` | 运营数据总览 |
| GET | `/v3pz/agent/admin/business/stats` | 业务统计 |
| GET/POST | `/v3pz/agent/admin/faq/*` | FAQ CRUD |
| GET | `/v3pz/menu/permissions` | 动态菜单权限 |
| GET | `/v3pz/companion/list` | 陪护师列表 |
| GET | `/v3pz/admin/order` | 订单管理 |

---

## ✨ 核心功能截图

### H5 端功能

| 功能 | 说明 |
|------|------|
| 🏠 **首页** | 城市选择、天气出行提示、AI智能分诊、医院列表（含距离/导航/预约） |
| 🤖 **AI智能分诊** | 输入症状→推荐科室/医院/陪诊师 |
| 💬 **AI客服** | 订单页悬浮球唤起，自动分发到对应Agent |
| 📋 **订单管理** | 按状态筛选、倒计时、模拟支付、一键导航 |

### 后台管理功能

| 功能 | 说明 |
|------|------|
| 📊 **控制台** | 订单概览、AI咨询统计、快捷操作、平台信息 |
| 🤖 **运营数据助手** | 自然语言对话查询运营数据 |
| 📚 **FAQ知识库** | 增删改查常见问题，AI客服优先匹配 |
| 👥 **陪护师管理** | CRUD + 图片选择器 |
| 📦 **订单管理** | 状态筛选、服务完成确认 |

---

## 📄 许可证

MIT

---

## 👨‍💻 开发者

[Zcj233-cyber](https://github.com/Zcj233-cyber)
