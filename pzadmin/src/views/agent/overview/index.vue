<template>
  <div class="agent-dashboard">
    <panel-head :route="route" />

    <!-- 顶部统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card stat-card--blue">
        <div class="stat-icon"><el-icon :size="28"><DataBoard /></el-icon></div>
        <div class="stat-body">
          <div class="stat-number">{{ stats.total_orders }}</div>
          <div class="stat-label">总订单量</div>
          <div class="stat-trend" v-if="stats.total_orders > 0">📈 平台运营数据</div>
        </div>
      </div>
      <div class="stat-card stat-card--green">
        <div class="stat-icon"><el-icon :size="28"><User /></el-icon></div>
        <div class="stat-body">
          <div class="stat-number">{{ stats.total_users }}</div>
          <div class="stat-label">注册用户</div>
        </div>
      </div>
      <div class="stat-card stat-card--purple">
        <div class="stat-icon"><el-icon :size="28"><ChatDotSquare /></el-icon></div>
        <div class="stat-body">
          <div class="stat-number">{{ stats.total_convs }}</div>
          <div class="stat-label">AI咨询次数</div>
        </div>
      </div>
      <div class="stat-card stat-card--orange">
        <div class="stat-icon"><el-icon :size="28"><Collection /></el-icon></div>
        <div class="stat-body">
          <div class="stat-number">{{ stats.faq_count }}</div>
          <div class="stat-label">知识库条目</div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-grid">
      <!-- 左侧：运营对话 -->
      <div class="main-card ai-chat-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon><ChatLineSquare /></el-icon>
            <span>AI运营数据助手</span>
          </div>
          <el-tag size="small" type="success" effect="dark">在线</el-tag>
        </div>
        <div class="chat-area" ref="chatRef">
          <div v-for="(msg,i) in chatMessages" :key="i"
            :class="['msg-row', msg.role === 'user' ? 'msg-right' : 'msg-left']">
            <div v-if="msg.role === 'assistant'" class="msg-avatar">
              <el-avatar :size="32" style="background:#409eff">AI</el-avatar>
            </div>
            <div class="msg-content">
              <div class="msg-text">{{ msg.content }}</div>
              <div v-if="msg.role === 'assistant'" class="msg-time">运营分析助手</div>
            </div>
          </div>
          <div v-if="chatLoading" class="msg-row msg-left">
            <div class="msg-avatar"><el-avatar :size="32" style="background:#409eff">AI</el-avatar></div>
            <div class="msg-content"><div class="msg-text thinking">⏳ 正在分析数据...</div></div>
          </div>
        </div>
        <div class="chat-bottom">
          <div class="quick-tags">
            <el-tag size="small" effect="plain" @click="quickChat('各状态订单数量')">📊 各状态订单</el-tag>
            <el-tag size="small" effect="plain" @click="quickChat('哪个医院预约最多')">🏥 热门医院</el-tag>
            <el-tag size="small" effect="plain" @click="quickChat('陪诊师工作量')">👥 陪诊师分析</el-tag>
            <el-tag size="small" effect="plain" @click="quickChat('最近一周订单趋势')">📈 订单趋势</el-tag>
          </div>
          <div class="chat-input-area">
            <el-input v-model="chatInput" placeholder="输入问题，按Enter发送..." @keyup.enter="sendChat" clearable />
            <el-button type="primary" :icon="Promotion" @click="sendChat" :loading="chatLoading">发送</el-button>
          </div>
        </div>
      </div>

      <!-- 右侧：订单状态 + 快速概览 -->
      <div class="right-col">
        <div class="main-card">
          <div class="card-header">
            <div class="card-title"><el-icon><DataAnalysis /></el-icon><span>订单状态分布</span></div>
            <span class="card-sub">共 {{ Object.values(orderStatus).reduce((a,b)=>a+b,0) }} 单</span>
          </div>
          <div class="order-stats">
            <div v-for="(cnt,status) in orderStatus" :key="status" class="order-item" @click="quickChat(status + '订单')">
              <div class="order-item-header">
                <span class="order-status">
                  <span class="status-dot" :style="{background:statusColor(status)}"></span>
                  {{ status }}
                </span>
                <span class="order-count">{{ cnt }}</span>
              </div>
              <el-progress :percentage="orderPercent(status)" :color="statusColor(status)" :stroke-width="8" />
            </div>
          </div>
        </div>
        <div class="main-card" style="margin-top:16px">
          <div class="card-header">
            <div class="card-title"><el-icon><Warning /></el-icon><span>快捷概览</span></div>
          </div>
          <div class="quick-grid">
            <div class="quick-item" @click="quickChat('今日新增订单')">
              <div class="qi-icon" style="background:#e6f7ff;color:#1890ff">📦</div>
              <div class="qi-label">今日订单</div>
            </div>
            <div class="quick-item" @click="quickChat('待服务订单')">
              <div class="qi-icon" style="background:#fff7e6;color:#fa8c16">⏳</div>
              <div class="qi-label">待服务</div>
            </div>
            <div class="quick-item" @click="quickChat('新注册用户')">
              <div class="qi-icon" style="background:#f6ffed;color:#52c41a">👤</div>
              <div class="qi-label">新用户</div>
            </div>
            <div class="quick-item" @click="quickChat('已完成订单')">
              <div class="qi-icon" style="background:#f0f5ff;color:#2f54eb">✅</div>
              <div class="qi-label">已完成</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from "vue";
import { useRoute } from "vue-router";
import { agentOverview, agentBusinessStats, agentAdminChat } from "../../../api";
import { DataBoard, User, ChatDotSquare, Collection, ChatLineSquare, Promotion, DataAnalysis, Warning } from "@element-plus/icons-vue";

const route = useRoute();
const chatRef = ref(null);
const stats = reactive({ total_orders:0, total_users:0, total_convs:0, faq_count:0 });
const orderStatus = reactive({});
const chatMessages = ref([]);
const chatInput = ref("");
const chatLoading = ref(false);

const statusColor = (s) => ({ "待支付":"#f56c6c","待服务":"#409eff","已完成":"#67c23a","已取消":"#909399" }[s]||"#409eff");

const orderPercent = (s) => {
  const t = Object.values(orderStatus).reduce((a,b)=>a+b,0);
  return t > 0 ? Math.round((orderStatus[s]/t)*100) : 0;
};

const scrollChat = () => {
  nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight; });
};

const sendChat = async () => {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  chatMessages.value.push({ role:"user", content:text });
  scrollChat();
  chatLoading.value = true;
  try {
    const { data } = await agentAdminChat({ message:text, agent_type:"operations" });
    if (data.code === 10000) chatMessages.value.push({ role:"assistant", content:data.data.reply });
    else chatMessages.value.push({ role:"assistant", content:"查询失败，请稍后重试" });
  } catch(e) {
    chatMessages.value.push({ role:"assistant", content:"网络异常，请稍后重试" });
  }
  chatLoading.value = false;
  scrollChat();
};

const quickChat = (t) => { chatInput.value = t; sendChat(); };

onMounted(() => {
  agentOverview().then(({ data }) => {
    if (data.code !== 10000 || !data.data) return;
    const d = data.data;
    stats.total_orders = d.total_orders || 0;
    stats.total_users = d.total_users || 0;
    stats.total_convs = d.total_conversations || 0;
    stats.faq_count = d.faq_count || 0;
  }).catch(() => {});
  agentBusinessStats().then(({ data }) => {
    if (data.code === 10000 && data.data) {
      Object.assign(orderStatus, data.data.orders?.by_status || {});
    }
  }).catch(() => {});
  chatMessages.value.push({ role:"assistant", content:"您好！我是运营数据助手，您可以问我订单统计、用户增长等问题。" });
});
</script>

<style lang="less" scoped>
.agent-dashboard { padding: 0 0 20px; }

/* 统计卡片 */
.stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 16px; background:#fff; border-radius:8px; padding:20px; transition:all .3s; box-shadow:0 1px 4px rgba(0,0,0,.06); cursor:pointer; &:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,.1); } }
.stat-icon { width: 56px; height:56px; border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.stat-card--blue .stat-icon { background:#e6f7ff; color:#1890ff; }
.stat-card--green .stat-icon { background:#f6ffed; color:#52c41a; }
.stat-card--purple .stat-icon { background:#f9f0ff; color:#722ed1; }
.stat-card--orange .stat-icon { background:#fff7e6; color:#fa8c16; }
.stat-body { flex:1; }
.stat-number { font-size:28px; font-weight:700; color:#1a1a1a; line-height:1.2; }
.stat-label { font-size:13px; color:#999; margin-top:2px; }
.stat-trend { font-size:11px; color:#52c41a; margin-top:2px; }

/* 主布局 */
.main-grid { display:grid; grid-template-columns:1.5fr 1fr; gap:16px; }
.main-card { background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; }

/* 卡片头 */
.card-header { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #f0f0f0; }
.card-title { display:flex; align-items:center; gap:8px; font-size:15px; font-weight:600; color:#1a1a1a; .el-icon { font-size:18px; color:#409eff; } }
.card-sub { font-size:12px; color:#999; }

/* 聊天区 */
.chat-area { height:340px; overflow-y:auto; padding:16px; background:#f8f9fb; }
.msg-row { display:flex; gap:10px; margin-bottom:14px; }
.msg-right { justify-content:flex-end; .msg-avatar { order:1; } .msg-content { order:0; } }
.msg-left { justify-content:flex-start; }
.msg-content { max-width:75%; }
.msg-text { padding:10px 14px; border-radius:10px; font-size:13px; line-height:1.6; white-space:pre-wrap; .msg-right & { background:#409eff; color:#fff; border-radius:10px 2px 10px 10px; } .msg-left & { background:#fff; border:1px solid #e8e8e8; border-radius:2px 10px 10px 10px; } }
.msg-time { font-size:11px; color:#bbb; margin-top:3px; padding-left:4px; }
.thinking { color:#999; font-style:italic; }

/* 聊天底部 */
.chat-bottom { padding:12px 16px; border-top:1px solid #f0f0f0; }
.quick-tags { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; .el-tag { cursor:pointer; } }
.chat-input-area { display:flex; gap:8px; }

/* 订单状态 */
.order-stats { padding:12px 16px; }
.order-item { margin-bottom:14px; cursor:pointer; padding:6px 8px; border-radius:6px; transition:background .2s; &:hover { background:#f5f7fa; } }
.order-item-header { display:flex; justify-content:space-between; margin-bottom:5px; font-size:13px; }
.order-status { display:flex; align-items:center; gap:6px; }
.status-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.order-count { font-weight:600; color:#333; }

/* 快捷概览 */
.quick-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; padding:12px 16px; }
.quick-item { text-align:center; cursor:pointer; padding:10px 4px; border-radius:8px; transition:background .2s; &:hover { background:#f5f7fa; } }
.qi-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; margin:0 auto 6px; }
.qi-label { font-size:12px; color:#666; }
</style>
