<template>
  <div class="admin-dashboard">
    <panel-head :route="route" />

    <!-- ==================== 预警横幅 ==================== -->
    <div v-if="alerts.length > 0" class="alert-banner" :class="alertBannerClass">
      <div class="alert-header" @click="showAlerts = !showAlerts">
        <el-icon :size="20"><WarningFilled /></el-icon>
        <span class="alert-title">发现 {{ alerts.length }} 项业务预警</span>
        <el-tag v-if="dangerAlerts > 0" size="small" effect="dark" type="danger">{{ dangerAlerts }}项紧急</el-tag>
        <el-icon :class="['arrow', showAlerts ? 'arrow-up' : '']"><ArrowDown /></el-icon>
      </div>
      <div v-if="showAlerts" class="alert-list">
        <div v-for="(a, i) in alerts" :key="i" class="alert-item" :class="'alert-' + (a.level || 'info')">
          <el-tag size="small" :type="alertTagType(a.level)" effect="dark" class="alert-level">
            {{ alertLevelLabel(a.level) }}
          </el-tag>
          <div class="alert-body">
            <div class="alert-dimension">{{ a.dimension }}</div>
            <div class="alert-detail">{{ a.detail }}</div>
            <div v-if="a.suggestion" class="alert-suggestion">💡 {{ a.suggestion }}</div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="!loading" class="alert-banner alert-safe">
      <el-icon :size="20"><SuccessFilled /></el-icon>
      <span>✅ 暂无异常，一切正常</span>
    </div>

    <!-- ==================== 操作栏 ==================== -->
    <div class="action-bar">
      <el-button type="primary" :icon="Refresh" @click="loadAll" :loading="loading" round>
        {{ loading ? 'AI分析中...' : '🔄 刷新智能分析' }}
      </el-button>
      <span class="action-hint" v-if="loading">正在调用多个AI专家分析业务数据...</span>
    </div>

    <!-- ==================== 主内容：标签页 ==================== -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- Tab 1: 预警监控 -->
      <el-tab-pane label="🚨 预警监控" name="alerts">
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="4" animated />
        </div>
        <div v-else>
          <div class="metrics-grid">
            <div class="metric-card" v-for="(m, i) in alertMetricsList" :key="i">
              <div class="metric-value">{{ m.value }}</div>
              <div class="metric-label">{{ m.label }}</div>
              <div class="metric-sub" v-if="m.sub">{{ m.sub }}</div>
            </div>
          </div>
          <div class="section-card">
            <div class="section-title">📋 预警规则说明</div>
            <div class="rule-list">
              <div class="rule-item" v-for="(r, i) in alertRules" :key="i">
                <el-icon :size="16" color="#f56c6c"><Warning /></el-icon>
                <span>{{ r }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 深度分析 -->
      <el-tab-pane label="📊 深度分析" name="analytics">
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="6" animated />
        </div>
        <div v-else>
          <!-- 核心发现 -->
          <div class="section-card" v-if="analytics.key_findings && analytics.key_findings.length">
            <div class="section-title">🎯 核心发现</div>
            <div class="finding-list">
              <div v-for="(f, i) in analytics.key_findings" :key="i" class="finding-item">
                <el-tag size="small" :type="i === 0 ? 'danger' : 'warning'" effect="plain">{{ i + 1 }}</el-tag>
                <span>{{ f }}</span>
              </div>
            </div>
          </div>

          <!-- 各维度分析 -->
          <div class="dimension-grid">
            <div class="dimension-card" v-for="(d, i) in analytics.dimensions || []" :key="i">
              <div class="dim-header">
                <span class="dim-name">{{ d.name || d.title }}</span>
              </div>
              <div class="dim-data" v-if="d.data">{{ d.data }}</div>
              <div class="dim-insight">
                <el-icon :size="14" color="#409eff"><InfoFilled /></el-icon>
                {{ d.insight }}
              </div>
              <div v-if="d.suggestion" class="dim-suggestion">
                <el-icon :size="14" color="#67c23a"><Lightning /></el-icon>
                {{ d.suggestion }}
              </div>
            </div>
          </div>

          <!-- 量化指标 -->
          <div class="section-card" v-if="analytics.analytics">
            <div class="section-title">📈 量化数据</div>
            <div class="q-grid">
              <div class="q-item" v-if="analytics.analytics.orders">
                <div class="q-label">总订单</div>
                <div class="q-val">{{ analytics.analytics.orders.total }}</div>
              </div>
              <div class="q-item" v-if="analytics.analytics.users">
                <div class="q-label">总用户</div>
                <div class="q-val">{{ analytics.analytics.users.total }}</div>
              </div>
              <div class="q-item" v-if="analytics.analytics.ai_service">
                <div class="q-label">AI满意度</div>
                <div class="q-val">{{ analytics.analytics.ai_service.satisfaction_rate }}%</div>
              </div>
              <div class="q-item">
                <div class="q-label">陪诊师</div>
                <div class="q-val">{{ analytics.analytics.companions?.total || 0 }}</div>
              </div>
            </div>
          </div>

          <!-- 行动建议 -->
          <div class="section-card" v-if="analytics.action_items && analytics.action_items.length">
            <div class="section-title">💡 建议行动</div>
            <div class="action-list">
              <div v-for="(a, i) in analytics.action_items" :key="i" class="action-item">
                <el-checkbox :checked="false" />
                <span>{{ a }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 3: 运营报告 -->
      <el-tab-pane label="📋 运营报告" name="report">
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="8" animated />
        </div>
        <div v-else>
          <div class="report-header">
            <div class="report-title">{{ report.report_title || '运营日报' }}</div>
            <div class="report-date">{{ report.report_date || '' }}</div>
            <div class="report-actions">
              <el-button size="small" @click="genReport(1)" :disabled="loading">📅 今日日报</el-button>
              <el-button size="small" @click="genReport(7)" :disabled="loading">📆 本周周报</el-button>
            </div>
          </div>

          <!-- 报告段落 -->
          <div class="report-sections" v-if="report.sections && report.sections.length">
            <div class="report-section" v-for="(s, i) in report.sections" :key="i">
              <div class="rs-header">{{ s.icon }} {{ s.title }}</div>
              <div class="rs-body">{{ s.content }}</div>
            </div>
          </div>

          <!-- 亮点与风险 -->
          <el-row :gutter="16" class="report-row">
            <el-col :span="12">
              <div class="section-card highlights-card">
                <div class="section-title">🌟 亮点</div>
                <div v-if="report.highlights && report.highlights.length">
                  <div v-for="(h, i) in report.highlights" :key="i" class="hl-item">✅ {{ h }}</div>
                </div>
                <div v-else class="empty-text">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="section-card risks-card">
                <div class="section-title">⚠️ 风险</div>
                <div v-if="report.risks && report.risks.length">
                  <div v-for="(r, i) in report.risks" :key="i" class="risk-item">🔴 {{ r }}</div>
                </div>
                <div v-else class="empty-text">暂无风险</div>
              </div>
            </el-col>
          </el-row>

          <!-- 改进建议 -->
          <div class="section-card" v-if="report.suggestions && report.suggestions.length">
            <div class="section-title">💪 改进建议</div>
            <div v-for="(s, i) in report.suggestions" :key="i" class="suggestion-item">👉 {{ s }}</div>
          </div>

          <div class="report-closing" v-if="report.closing">{{ report.closing }}</div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import {
  adminDashboard, adminDashboardAlerts,
  adminDashboardAnalytics, adminDashboardReport
} from "../../../api";
import {
  WarningFilled, SuccessFilled, Refresh, ArrowDown,
  Warning, InfoFilled, Lightning,
} from "@element-plus/icons-vue";

const route = useRoute();

const loading = ref(false);
const activeTab = ref("alerts");
const showAlerts = ref(true);

const alerts = ref([]);
const analytics = reactive({ key_findings: [], dimensions: [], action_items: [], analytics: {} });
const report = reactive({ sections: [], highlights: [], risks: [], suggestions: [], closing: "" });
const alertMetricsData = reactive({});

const dangerAlerts = computed(() => alerts.value.filter(a => a.level === "danger").length);

const alertBannerClass = computed(() => {
  if (dangerAlerts.value > 0) return "alert-danger";
  if (alerts.value.length > 0) return "alert-warning";
  return "";
});

const alertMetricsList = computed(() => {
  const m = alertMetricsData;
  return [
    { label: "今日订单", value: m.today_orders ?? "-", sub: `昨日 ${m.yesterday_orders ?? "-"}` },
    { label: "今日新用户", value: m.new_users_today ?? "-", sub: `昨日 ${m.new_users_yesterday ?? "-"}` },
    { label: "取消率", value: m.cancel_rate ? m.cancel_rate + "%" : "-", sub: "总订单" },
    { label: "超时未支付", value: m.long_unpaid ?? "-", sub: ">30分钟" },
    { label: "总订单", value: m.total_orders ?? "-", sub: "" },
    { label: "总用户", value: m.total_users ?? "-", sub: "" },
  ];
});

const alertRules = [
  "今日零订单且昨日有订单 → 紧急预警",
  "超时未支付订单 ≥ 3个 → 黄色预警",
  "订单取消率 > 30% → 橙色预警",
  "陪诊师工作量严重不均 → 提示预警",
  "新用户注册数较昨日下降 > 50% → 提示预警",
];

const alertTagType = (level) => {
  const map = { danger: "danger", warning: "warning", info: "info" };
  return map[level] || "info";
};

const alertLevelLabel = (level) => {
  const map = { danger: "紧急", warning: "提醒", info: "提示" };
  return map[level] || "提示";
};

const loadAll = async () => {
  if (loading.value) return;
  loading.value = true;
  showAlerts.value = true;

  try {
    // 并行加载
    const [dashRes, alertRes, analyticsRes] = await Promise.all([
      adminDashboard().catch(() => ({ data: { code: -1 } })),
      adminDashboardAlerts().catch(() => ({ data: { code: -1 } })),
      adminDashboardAnalytics({ focus: "all" }).catch(() => ({ data: { code: -1 } })),
    ]);

    // Dashboard
    if (dashRes.data.code === 10000) {
      const d = dashRes.data.data || {};
      alerts.value = d.alerts || [];
      Object.assign(alertMetricsData, d.alert_metrics || {});

      if (d.report) {
        Object.assign(report, d.report);
      }
    }

    // Alerts (补充)
    if (alertRes.data.code === 10000) {
      const a = alertRes.data.data || {};
      if (a.alerts && a.alerts.length > (alerts.value.length || 0)) {
        alerts.value = a.alerts;
      }
      Object.assign(alertMetricsData, a.metrics || {});
    }

    // Analytics
    if (analyticsRes.data.code === 10000) {
      const a = analyticsRes.data.data || {};
      analytics.key_findings = a.key_findings || [];
      analytics.dimensions = a.dimensions || [];
      analytics.action_items = a.action_items || [];
      analytics.analytics = a.analytics || {};
    }
  } catch (e) {
    console.error("Dashboard load error:", e);
  }

  loading.value = false;
};

const genReport = async (days) => {
  loading.value = true;
  try {
    const { data } = await adminDashboardReport({ days });
    if (data.code === 10000) {
      const d = data.data || {};
      report.sections = d.sections || [];
      report.highlights = d.highlights || [];
      report.risks = d.risks || [];
      report.suggestions = d.suggestions || [];
      report.closing = d.closing || "";
      report.report_title = d.report_title || (days === 1 ? "运营日报" : "运营周报");
      report.report_date = d.report_date || "";
    }
  } catch (e) { /* ignore */ }
  loading.value = false;
};

onMounted(() => {
  loadAll();
});
</script>

<style lang="less" scoped>
.admin-dashboard { padding: 0 0 20px; }

/* 预警横幅 */
.alert-banner {
  background: #fff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  display: flex; flex-direction: column; gap: 8px;
  cursor: pointer; transition: all .3s;
  &.alert-danger { border-left: 4px solid #f56c6c; background: #fef0f0; }
  &.alert-warning { border-left: 4px solid #e6a23c; background: #fdf6ec; }
  &.alert-safe { border-left: 4px solid #67c23a; background: #f0f9eb; flex-direction: row; align-items: center; gap: 8px; cursor: default; }
  .alert-header { display: flex; align-items: center; gap: 8px; }
  .alert-title { flex: 1; font-weight: 600; font-size: 14px; }
  .arrow { transition: transform .3s; &.arrow-up { transform: rotate(180deg); } }
}
.alert-list { display: flex; flex-direction: column; gap: 8px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,.06); }
.alert-item {
  display: flex; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,.7); border-radius: 6px;
  &.alert-danger { border-left: 3px solid #f56c6c; }
  &.alert-warning { border-left: 3px solid #e6a23c; }
  &.alert-info { border-left: 3px solid #909399; }
  .alert-body { flex: 1; }
  .alert-dimension { font-weight: 600; font-size: 13px; margin-bottom: 2px; }
  .alert-detail { font-size: 12px; color: #666; }
  .alert-suggestion { font-size: 12px; color: #e6a23c; margin-top: 4px; }
}

/* 操作栏 */
.action-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  .action-hint { font-size: 12px; color: #999; }
}

/* 标签页 */
.main-tabs { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.06); :deep(.el-tabs__content) { padding: 16px; } }

.loading-state { padding: 40px 0; }

/* 指标网格 */
.metrics-grid {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 16px;
  .metric-card {
    background: #f8f9fb; border-radius: 8px; padding: 14px 12px; text-align: center;
    .metric-value { font-size: 22px; font-weight: 700; color: #1a1a1a; }
    .metric-label { font-size: 12px; color: #999; margin-top: 2px; }
    .metric-sub { font-size: 11px; color: #bbb; margin-top: 2px; }
  }
}

/* 通用区块卡片 */
.section-card {
  background: #f8f9fb; border-radius: 8px; padding: 16px; margin-bottom: 16px;
  .section-title { font-size: 15px; font-weight: 600; color: #1a1a1a; margin-bottom: 12px; }
}
.rule-list { display: flex; flex-direction: column; gap: 8px; }
.rule-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #666; }

/* 发现列表 */
.finding-list { display: flex; flex-direction: column; gap: 8px; }
.finding-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #555; line-height: 1.5; }

/* 维度分析 */
.dimension-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.dimension-card {
  background: #f8f9fb; border-radius: 8px; padding: 14px;
  .dim-header { margin-bottom: 6px; }
  .dim-name { font-size: 14px; font-weight: 600; color: #333; }
  .dim-data { font-size: 12px; color: #666; margin-bottom: 8px; line-height: 1.5; white-space: pre-wrap; background: #fff; padding: 8px 10px; border-radius: 6px; }
  .dim-insight { display: flex; align-items: flex-start; gap: 4px; font-size: 12px; color: #409eff; margin-bottom: 4px; line-height: 1.5; }
  .dim-suggestion { display: flex; align-items: flex-start; gap: 4px; font-size: 12px; color: #67c23a; line-height: 1.5; }
}

/* 量化数据 */
.q-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.q-item { text-align: center; padding: 12px; background: #fff; border-radius: 8px; }
.q-label { font-size: 12px; color: #999; }
.q-val { font-size: 24px; font-weight: 700; color: #333; margin-top: 4px; }

/* 行动列表 */
.action-list { display: flex; flex-direction: column; gap: 8px; }
.action-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; }

/* 报告 */
.report-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.report-title { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.report-date { font-size: 13px; color: #999; flex: 1; }
.report-actions { display: flex; gap: 8px; }
.report-sections { display: flex; flex-direction: column; gap: 16px; margin-bottom: 16px; }
.report-section {
  background: #f8f9fb; border-radius: 8px; padding: 14px 16px;
  .rs-header { font-size: 15px; font-weight: 600; margin-bottom: 6px; }
  .rs-body { font-size: 13px; color: #555; line-height: 1.7; white-space: pre-wrap; }
}
.report-row { margin-bottom: 16px; }
.highlights-card { background: #f0f9eb; }
.risks-card { background: #fef0f0; }
.hl-item { font-size: 13px; color: #67c23a; padding: 4px 0; }
.risk-item { font-size: 13px; color: #f56c6c; padding: 4px 0; }
.suggestion-item { font-size: 13px; color: #e6a23c; padding: 6px 0; border-bottom: 1px solid #f0f0f0; &:last-child { border: none; } }
.report-closing {
  margin-top: 16px; padding: 14px 16px; background: #f0f5ff; border-radius: 8px;
  font-size: 13px; color: #409eff; line-height: 1.6;
}
.empty-text { font-size: 13px; color: #999; padding: 8px 0; }
</style>
