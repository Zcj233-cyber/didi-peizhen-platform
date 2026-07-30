<template>
  <div class="dashboard">
    <panel-head :route="route" />

    <!-- 顶部核心指标 -->
    <div class="stat-grid">
      <div class="stat-card" style="border-left:4px solid #409eff">
        <div class="stat-icon" style="background:#e6f7ff"><el-icon :size="24"><Document /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.orders }}</div>
          <div class="stat-lbl">总订单</div>
        </div>
        <div class="stat-change" style="color:#409eff">+{{ stats.orders || 0 }}</div>
      </div>
      <div class="stat-card" style="border-left:4px solid #52c41a">
        <div class="stat-icon" style="background:#f6ffed"><el-icon :size="24"><User /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.users }}</div>
          <div class="stat-lbl">注册用户</div>
        </div>
      </div>
      <div class="stat-card" style="border-left:4px solid #722ed1">
        <div class="stat-icon" style="background:#f9f0ff"><el-icon :size="24"><ChatDotSquare /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.convs }}</div>
          <div class="stat-lbl">AI咨询</div>
        </div>
      </div>
      <div class="stat-card" style="border-left:4px solid #fa8c16">
        <div class="stat-icon" style="background:#fff7e6"><el-icon :size="24"><UserFilled /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.companions }}</div>
          <div class="stat-lbl">陪护师</div>
        </div>
      </div>
    </div>

    <div class="main-grid">
      <!-- 订单概览 -->
      <div class="card">
        <div class="card-hd">
          <span><el-icon><List /></el-icon> 订单概览</span>
          <el-button text type="primary" size="small" @click="router.push('/vppz/order')">查看全部 →</el-button>
        </div>
        <div class="card-body">
          <div class="order-overview">
            <div v-for="(cnt, status) in orderStatus" :key="status" class="oo-item" @click="router.push('/vppz/order')">
              <div class="oo-num" :style="{color:statusColor(status)}">{{ cnt }}</div>
              <div class="oo-lbl">{{ status }}</div>
            </div>
          </div>
          <div class="order-bar">
            <div v-for="(cnt, status) in orderStatus" :key="status"
              class="order-bar-seg" :style="{width:orderPct(status)+'%', background:statusColor(status)}"
              :title="status + ': ' + cnt + '单'">
            </div>
          </div>
          <div class="order-total">共 {{ totalOrders }} 单</div>
        </div>
      </div>

      <!-- 咨询统计 -->
      <div class="card">
        <div class="card-hd">
          <span><el-icon><ChatDotSquare /></el-icon> AI咨询统计</span>
          <el-button text type="primary" size="small" @click="router.push('/agent/overview')">查看详情 →</el-button>
        </div>
        <div class="card-body">
          <div v-for="{label,value,color,pct} in convStats" :key="label" class="cs-item">
            <div class="cs-hd">
              <span><span class="cs-dot" :style="{background:color}"></span>{{ label }}</span>
              <span>{{ value }}次</span>
            </div>
            <el-progress :percentage="pct" :color="color" :stroke-width="8" />
          </div>
        </div>
      </div>
    </div>

    <div class="main-grid" style="margin-top:16px">
      <!-- 快捷操作 -->
      <div class="card">
        <div class="card-hd">
          <span><el-icon><Opportunity /></el-icon> 快捷操作</span>
        </div>
        <div class="card-body">
          <div class="quick-grid">
            <div class="quick-item" @click="router.push('/vppz/staff')">
              <div class="qi-icon" style="background:#e6f7ff;color:#1890ff">👤</div>
              <div class="qi-name">陪护管理</div>
            </div>
            <div class="quick-item" @click="router.push('/vppz/order')">
              <div class="qi-icon" style="background:#f6ffed;color:#52c41a">📦</div>
              <div class="qi-name">订单管理</div>
            </div>
            <div class="quick-item" @click="router.push('/agent/overview')">
              <div class="qi-icon" style="background:#f9f0ff;color:#722ed1">🤖</div>
              <div class="qi-name">运营助手</div>
            </div>
            <div class="quick-item" @click="router.push('/auth/admin')">
              <div class="qi-icon" style="background:#fff7e6;color:#fa8c16">⚙️</div>
              <div class="qi-name">账号管理</div>
            </div>
            <div class="quick-item" @click="router.push('/agent/config')">
              <div class="qi-icon" style="background:#fff0f6;color:#eb2f96">📚</div>
              <div class="qi-name">FAQ管理</div>
            </div>
            <div class="quick-item" @click="router.push('/auth/group')">
              <div class="qi-icon" style="background:#f0f5ff;color:#2f54eb">🔐</div>
              <div class="qi-name">菜单权限</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 须知 -->
      <div class="card">
        <div class="card-hd">
          <span><el-icon><InfoFilled /></el-icon> 平台信息</span>
        </div>
        <div class="card-body">
          <div class="info-list">
            <div class="info-item">
              <span class="info-lbl">平台名称</span>
              <span class="info-val">DIDI陪诊服务平台</span>
            </div>
            <div class="info-item">
              <span class="info-lbl">服务端</span>
              <span class="info-val">Python FastAPI</span>
            </div>
            <div class="info-item">
              <span class="info-lbl">AI模型</span>
              <span class="info-val">DeepSeek Chat</span>
            </div>
            <div class="info-item">
              <span class="info-lbl">知识库</span>
              <span class="info-val">{{ faqCount }} 条FAQ</span>
            </div>
            <div class="info-item">
              <span class="info-lbl">覆盖城市</span>
              <span class="info-val">7城16家医院</span>
            </div>
            <div class="info-item">
              <span class="info-lbl">陪诊师</span>
              <span class="info-val">{{ stats.companions }}人</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { agentBusinessStats, authAdmin, companionList } from "../../api";
import { Document, User, ChatDotSquare, UserFilled, List, Opportunity, InfoFilled } from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();

const stats = reactive({ orders:0, users:0, convs:0, companions:0 });
const orderStatus = reactive({});
const convRaw = reactive({});
const faqCount = ref(0);

const statusColor = (s) => ({ "待支付":"#f56c6c","待服务":"#409eff","已完成":"#67c23a","已取消":"#909399" }[s]||"#999");
const totalOrders = computed(() => Object.values(orderStatus).reduce((a,b)=>a+b,0));
const orderPct = (s) => { const t = totalOrders.value; return t > 0 ? Math.round((orderStatus[s]/t)*100) : 0; };

const convStats = computed(() => {
  const labels = { customer_service:"客服咨询", triage:"智能分诊", order_assistant:"订单助手" };
  const colors = { customer_service:"#409eff", triage:"#52c41a", order_assistant:"#fa8c16" };
  const raw = convRaw || {};
  const total = Object.values(raw).reduce((a,b)=>a+b,0);
  return Object.entries(raw).map(([k,v]) => ({
    label: labels[k]||k, value: v, color: colors[k]||"#999",
    pct: total > 0 ? Math.round(v/total*100) : 0,
  }));
});

onMounted(() => {
  agentBusinessStats().then(({ data }) => {
    if (data.code !== 10000 || !data.data) return;
    const d = data.data;
    stats.orders = d.orders?.total_orders || 0;
    stats.users = d.users?.total_users || 0;
    stats.convs = d.customer_service?.total_conversations || 0;
    faqCount.value = d.customer_service?.faq_count || 0;
    Object.assign(orderStatus, d.orders?.by_status || {});
    Object.assign(convRaw, d.customer_service?.conversation_by_type || {});
  }).catch(() => {});
  companionList({ pageNum:1, pageSize:1 }).then(({ data }) => {
    if (data.code === 10000) stats.companions = data.data.total || 0;
  }).catch(() => {});
});
</script>

<style lang="less" scoped>
.dashboard { padding: 0 0 20px; }
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:20px; }
.stat-card { display:flex; align-items:center; gap:14px; background:#fff; border-radius:8px; padding:18px 20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.stat-icon { width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.stat-info { flex:1; }
.stat-num { font-size:24px; font-weight:700; color:#1a1a1a; line-height:1.2; }
.stat-lbl { font-size:13px; color:#999; margin-top:2px; }
.stat-change { font-size:13px; font-weight:500; }

.main-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.card { background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; }
.card-hd { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #f0f0f0; font-size:14px; font-weight:600; color:#1a1a1a; .el-icon { color:#409eff; margin-right:6px; vertical-align:middle; } }
.card-body { padding:16px; }

/* 订单概览 */
.order-overview { display:flex; gap:20px; margin-bottom:12px; }
.oo-item { flex:1; text-align:center; cursor:pointer; padding:8px; border-radius:6px; transition:background .2s; &:hover { background:#f5f7fa; } }
.oo-num { font-size:28px; font-weight:700; }
.oo-lbl { font-size:12px; color:#999; margin-top:2px; }
.order-bar { display:flex; height:10px; border-radius:5px; overflow:hidden; background:#f0f0f0; }
.order-bar-seg { transition:width .5s; }
.order-total { text-align:center; font-size:12px; color:#999; margin-top:6px; }

/* AI咨询 */
.cs-item { margin-bottom:12px; }
.cs-hd { display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px; }
.cs-dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; }

/* 快捷操作 */
.quick-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.quick-item { text-align:center; padding:14px 6px; border-radius:8px; cursor:pointer; transition:all .2s; &:hover { background:#f5f7fa; transform:translateY(-1px); } }
.qi-icon { width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:22px; margin:0 auto 6px; }
.qi-name { font-size:12px; color:#666; }

/* 平台信息 */
.info-list { display:flex; flex-direction:column; gap:0; }
.info-item { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f5f5f5; font-size:13px; &:last-child { border:none; } }
.info-lbl { color:#999; }
.info-val { color:#333; font-weight:500; }
</style>
