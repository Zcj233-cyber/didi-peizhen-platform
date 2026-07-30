<template>
  <div class="container">
    <!-- ============ 顶部导航 ============ -->
    <van-nav-bar title="智能就医规划" left-arrow @click-left="goBack" />

    <!-- ============ 输入阶段 ============ -->
    <div class="input-section" v-if="!loading && !result">
      <!-- 功能介绍 -->
      <div class="intro-banner">
        <div class="intro-icon">🏥</div>
        <div class="intro-text">
          <div class="intro-title">一站式就医攻略</div>
          <div class="intro-desc">描述症状，AI自动分析→推荐医院→准备清单→费用预估→出行建议，一步到位</div>
        </div>
      </div>

      <!-- 症状输入 -->
      <div class="form-card">
        <div class="form-label">🩺 请描述患者症状 <span class="required">*</span></div>
        <van-field
          v-model="form.symptoms"
          type="textarea"
          rows="4"
          maxlength="500"
          show-word-limit
          placeholder="请详细描述症状，例如：我妈妈肚子疼了两天，还有点发烧，胃口也不太好..."
          class="symptom-input"
        />
      </div>

      <!-- 患者信息 -->
      <div class="form-card">
        <div class="form-label">👤 患者信息（选填，填得更准）</div>
        <van-row gutter="12">
          <van-col span="12">
            <van-field v-model="form.patient_age" type="digit" placeholder="年龄" label="年龄" label-width="40px" />
          </van-col>
          <van-col span="12">
            <van-field v-model="form.patient_gender" placeholder="性别" label="性别" label-width="40px"
              @click="showGender = true" readonly right-icon="arrow-down" />
          </van-col>
        </van-row>
        <van-field v-model="form.city" placeholder="所在城市（自动定位）" label="城市" label-width="40px"
          @click="showCityPicker = true" readonly right-icon="arrow-down" />
      </div>

      <!-- 开始按钮 -->
      <van-button type="primary" block round size="large" class="submit-btn"
        :loading="loading" loading-text="AI正在分析..." @click="doPlanning">
        <template #icon><van-icon name="medel" /></template>
        {{ loading ? '' : '开始规划就诊攻略' }}
      </van-button>

      <!-- 底部提示 -->
      <div class="footer-tip">
        <van-icon name="info-o" /> 分析结果仅供参考，不构成医疗诊断建议
      </div>
    </div>

    <!-- ============ 加载阶段 ============ -->
    <div class="loading-section" v-if="loading">
      <div class="loading-animation">
        <div class="loading-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="loading-title">AI 智能分析中...</div>
      <div class="loading-steps">
        <div class="step" :class="{ active: loadStep >= 1, done: loadStep > 1 }">
          <div class="step-icon">{{ loadStep > 1 ? '✓' : '1' }}</div>
          <div class="step-text">症状分析 & 科室推荐</div>
        </div>
        <div class="step" :class="{ active: loadStep >= 2, done: loadStep > 2 }">
          <div class="step-icon">{{ loadStep > 2 ? '✓' : '2' }}</div>
          <div class="step-text">医院对比 & 专家推荐</div>
        </div>
        <div class="step" :class="{ active: loadStep >= 3, done: loadStep > 3 }">
          <div class="step-icon">{{ loadStep > 3 ? '✓' : '3' }}</div>
          <div class="step-text">准备清单 & 费用预估</div>
        </div>
        <div class="step" :class="{ active: loadStep >= 4, done: loadStep > 4 }">
          <div class="step-icon">{{ loadStep > 4 ? '✓' : '4' }}</div>
          <div class="step-text">出行天气 & 综合攻略</div>
        </div>
      </div>
      <div class="loading-hint">正在调用多个AI专家协作分析...</div>
    </div>

    <!-- ============ 结果阶段 ============ -->
    <div class="result-section" v-if="!loading && result">
      <!-- 攻略头部 -->
      <div class="guide-header">
        <div class="guide-badge">AI生成攻略</div>
        <div class="guide-title">📋 {{ result.guide_title || '就诊攻略' }}</div>
        <div class="guide-summary" v-if="result.guide_summary">{{ result.guide_summary }}</div>
      </div>

      <!-- 攻略分段 -->
      <div class="guide-sections" v-if="result.guide_sections && result.guide_sections.length">
        <div class="guide-section" v-for="(section, idx) in result.guide_sections" :key="idx">
          <div class="section-icon">{{ section.icon || '📌' }}</div>
          <div class="section-content">
            <div class="section-title">{{ section.title || '' }}</div>
            <div class="section-body">{{ section.content || '' }}</div>
          </div>
        </div>
      </div>

      <!-- 结构化数据卡片（用于补充LLM可能遗漏的细节） -->
      <!-- 1. 分诊建议 -->
      <div class="data-card" v-if="result.triage">
        <div class="card-header">
          <span class="card-icon">🩺</span>
          <span class="card-title">分诊建议</span>
        </div>
        <div class="card-body">
          <div class="info-row">
            <span class="info-label">推荐科室</span>
            <van-tag type="primary" size="medium">{{ result.triage.recommended_department }}</van-tag>
          </div>
          <div class="info-row" v-if="result.triage.symptom_summary">
            <span class="info-label">症状分析</span>
            <span class="info-value">{{ result.triage.symptom_summary }}</span>
          </div>
          <div class="info-row" v-if="result.triage.urgency_level">
            <span class="info-label">紧急程度</span>
            <van-tag :type="urgencyTagType(result.triage.urgency_level)">
              {{ urgencyText(result.triage.urgency_level) }}
            </van-tag>
          </div>
          <div class="disclaimer" v-if="result.triage.disclaimer">{{ result.triage.disclaimer }}</div>
        </div>
      </div>

      <!-- 2. 医院推荐 -->
      <div class="data-card" v-if="result.hospitals && result.hospitals.list && result.hospitals.list.length">
        <div class="card-header">
          <span class="card-icon">🏥</span>
          <span class="card-title">推荐医院 · {{ result.hospitals.city }}</span>
        </div>
        <div class="card-body">
          <div class="best-choice" v-if="result.hospitals.best_choice">
            <van-icon name="medal" color="#ff6b35" /> 最佳推荐：<strong>{{ result.hospitals.best_choice }}</strong>
          </div>
          <div class="hospital-item" v-for="h in result.hospitals.list" :key="h.id" @click="goOrder(h)">
            <div class="hosp-info">
              <div class="hosp-name">{{ h.name }}</div>
              <div class="hosp-tags">
                <van-tag v-if="h.rank" plain size="small">{{ h.rank }}</van-tag>
                <van-tag v-if="h.label" plain size="small" type="warning">{{ h.label }}</van-tag>
              </div>
              <div class="hosp-addr" v-if="h.address">
                <van-icon name="location-o" /> {{ h.address }}
              </div>
            </div>
            <van-icon name="arrow" class="hosp-arrow" />
          </div>
        </div>
      </div>

      <!-- 3. 就诊准备清单 -->
      <div class="data-card" v-if="result.prep_guide">
        <div class="card-header">
          <span class="card-icon">📝</span>
          <span class="card-title">就诊准备清单</span>
        </div>
        <div class="card-body">
          <!-- 证件 -->
          <div class="prep-section" v-if="result.prep_guide.documents && result.prep_guide.documents.length">
            <div class="prep-subtitle">📄 需携带材料</div>
            <div class="check-item" v-for="(doc, i) in result.prep_guide.documents" :key="'doc'+i">
              <van-icon name="success" color="#07c160" /><span>{{ doc }}</span>
            </div>
          </div>
          <!-- 饮食 -->
          <div class="prep-section" v-if="result.prep_guide.diet_before">
            <div class="prep-subtitle">🍽 饮食注意</div>
            <div class="prep-text">{{ result.prep_guide.diet_before }}</div>
          </div>
          <!-- 着装 -->
          <div class="prep-section" v-if="result.prep_guide.clothing">
            <div class="prep-subtitle">👔 着装建议</div>
            <div class="prep-text">{{ result.prep_guide.clothing }}</div>
          </div>
          <!-- 特别提醒 -->
          <div class="prep-section" v-if="result.prep_guide.special_notes && result.prep_guide.special_notes.length">
            <div class="prep-subtitle">⚠️ 特别提醒</div>
            <div class="check-item" v-for="(note, i) in result.prep_guide.special_notes" :key="'note'+i">
              <van-icon name="warning" color="#ee6a55" /><span>{{ note }}</span>
            </div>
          </div>
          <!-- 完整清单 -->
          <div class="prep-checklist" v-if="result.prep_guide.checklist" @click="showChecklist = !showChecklist">
            <van-icon :name="showChecklist ? 'eye-o' : 'eye'" /> {{ showChecklist ? '收起完整清单' : '查看完整清单' }}
          </div>
          <div class="checklist-detail" v-if="showChecklist && result.prep_guide.checklist">
            <div style="white-space: pre-wrap; font-size: 13px; color: #666; line-height: 1.8;">
              {{ result.prep_guide.checklist }}
            </div>
          </div>
        </div>
      </div>

      <!-- 4. 费用预估 -->
      <div class="data-card" v-if="result.cost_estimate">
        <div class="card-header">
          <span class="card-icon">💰</span>
          <span class="card-title">费用预估</span>
        </div>
        <div class="card-body">
          <div class="cost-grid">
            <div class="cost-item" v-if="result.cost_estimate.registration_fee">
              <div class="cost-label">挂号费</div>
              <div class="cost-value">{{ result.cost_estimate.registration_fee }}</div>
            </div>
            <div class="cost-item" v-if="result.cost_estimate.exam_fee">
              <div class="cost-label">检查费</div>
              <div class="cost-value">{{ result.cost_estimate.exam_fee }}</div>
            </div>
            <div class="cost-item" v-if="result.cost_estimate.medicine_fee">
              <div class="cost-label">药费</div>
              <div class="cost-value">{{ result.cost_estimate.medicine_fee }}</div>
            </div>
            <div class="cost-item total" v-if="result.cost_estimate.total_range">
              <div class="cost-label">预估总计</div>
              <div class="cost-value total-value">{{ result.cost_estimate.total_range }}</div>
            </div>
          </div>
          <div class="cost-insurance" v-if="result.cost_estimate.insurance_ratio">
            <van-icon name="shield-o" /> 医保预计报销：{{ result.cost_estimate.insurance_ratio }}
          </div>
          <div class="cost-companion" v-if="result.cost_estimate.companion_fee">
            <van-icon name="service-o" /> 陪诊服务费：<strong>{{ result.cost_estimate.companion_fee }}</strong>/次（含全程陪护）
          </div>
          <div class="cost-breakdown" v-if="result.cost_estimate.breakdown && result.cost_estimate.breakdown.length">
            <div class="breakdown-item" v-for="(item, i) in result.cost_estimate.breakdown" :key="'cost'+i">
              <span>{{ item.name || '' }}</span>
              <span>{{ item.range || '' }}</span>
              <span class="note">{{ item.note || '' }}</span>
            </div>
          </div>
          <div class="disclaimer" v-if="result.cost_estimate.disclaimer">{{ result.cost_estimate.disclaimer }}</div>
        </div>
      </div>

      <!-- 5. 天气与出行 -->
      <div class="data-card" v-if="result.weather">
        <div class="card-header">
          <span class="card-icon">🌤</span>
          <span class="card-title">天气与出行建议</span>
        </div>
        <div class="card-body">
          <div class="weather-display" v-if="result.weather.condition">
            <span class="weather-icon">{{ weatherEmoji(result.weather.condition) }}</span>
            <span class="weather-info">
              {{ result.weather.condition }} {{ result.weather.temperature }}°C
              <span v-if="result.weather.wind"> · {{ result.weather.wind }}</span>
            </span>
          </div>
          <div class="travel-advice" v-if="result.travel_advice">
            <van-icon name="location-o" color="#f57c00" />
            {{ result.travel_advice }}
          </div>
        </div>
      </div>

      <!-- 结尾提示 -->
      <div class="closing-tip" v-if="result.closing_tip">
        <van-icon name="bulb-o" color="#ff6b35" />
        {{ result.closing_tip }}
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <van-button type="primary" block round size="large" @click="goOrder()">
          <template #icon><van-icon name="plus" /></template>
          立即预约陪诊服务
        </van-button>
        <van-button plain block round size="small" class="retry-btn" @click="reset">
          重新描述症状
        </van-button>
      </div>
    </div>

    <!-- 性别选择器 -->
    <van-action-sheet v-model:show="showGender" :actions="genderOptions" @select="onGenderSelect" cancel-text="取消" close-on-click-action />
    <!-- 城市选择器 -->
    <van-action-sheet v-model:show="showCityPicker" :actions="cityActions" @select="onCitySelect" cancel-text="取消" close-on-click-action />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, getCurrentInstance } from "vue";
import { useRouter } from "vue-router";
import { showToast } from "vant";

const { proxy } = getCurrentInstance();
const router = useRouter();

const loading = ref(false);
const result = ref(null);
const showGender = ref(false);
const showCityPicker = ref(false);
const showChecklist = ref(false);
const loadStep = ref(0);
const cityActions = ref([{ name: "武汉" }, { name: "全国" }]);

const form = reactive({
  symptoms: "",
  patient_age: "",
  patient_gender: "",
  city: "",
});

const genderOptions = [
  { name: "男", value: "男" },
  { name: "女", value: "女" },
];

const onGenderSelect = (item) => {
  form.patient_gender = item.value;
  showGender.value = false;
};

const onCitySelect = (item) => {
  form.city = item.name;
  showCityPicker.value = false;
};

const goBack = () => router.go(-1);

const goOrder = (hospital) => {
  if (hospital && hospital.id) {
    router.push(`/createOrder?id=${hospital.id}`);
  } else {
    router.push("/createOrder");
  }
};

const reset = () => {
  result.value = null;
  form.symptoms = "";
  form.patient_age = "";
  form.patient_gender = "";
  form.city = "";
  showChecklist.value = false;
};

const urgencyTagType = (level) => {
  const map = { emergency: "danger", urgent: "warning", normal: "success" };
  return map[level] || "default";
};

const urgencyText = (level) => {
  const map = { emergency: "🚨 紧急", urgent: "⚡ 较急", normal: "✅ 常规" };
  return map[level] || level;
};

const weatherEmoji = (condition) => {
  if (!condition) return "🌤";
  if (condition.includes("晴")) return "☀️";
  if (condition.includes("云")) return "⛅";
  if (condition.includes("雨") || condition.includes("雷")) return "🌧";
  if (condition.includes("雪")) return "❄️";
  if (condition.includes("雾") || condition.includes("霾")) return "🌫";
  if (condition.includes("阴")) return "☁️";
  return "🌤";
};

// 模拟加载进度动画
const startLoadAnimation = () => {
  loadStep.value = 0;
  const steps = [1, 2, 3, 4];
  let i = 0;
  const timer = setInterval(() => {
    if (i < steps.length) {
      loadStep.value = steps[i];
      i++;
    } else {
      clearInterval(timer);
    }
  }, 1500);
  return timer;
};

const doPlanning = async () => {
  if (!form.symptoms.trim()) {
    showToast("请描述症状");
    return;
  }
  if (form.symptoms.length < 5) {
    showToast("请详细描述症状，至少5个字");
    return;
  }

  loading.value = true;
  result.value = null;
  const animTimer = startLoadAnimation();

  try {
    const { data } = await proxy.$api.visitPlan({
      symptoms: form.symptoms,
      patient_age: Number(form.patient_age) || 0,
      patient_gender: form.patient_gender,
      city: form.city,
    });
    if (data.code === 10000) {
      result.value = data.data;
    } else {
      showToast(data.message || "规划失败，请稍后重试");
      loading.value = false;
    }
  } catch (e) {
    showToast("网络错误，请稍后重试");
    loading.value = false;
  }

  // 等动画完成再隐藏loading
  setTimeout(() => {
    loading.value = false;
  }, 500);
};

onMounted(async () => {
  // 自动定位获取城市
  try {
    const { data } = await proxy.$api.getCities();
    if (data.code === 10000 && data.data.length) {
      cityActions.value = [
        { name: "全国" },
        ...data.data.map((c) => ({ name: c })),
      ];
      // 默认选第一个非全国的城市
      if (!form.city && data.data.length > 0) {
        form.city = data.data[0];
      }
    }
  } catch (e) { /* ignore */ }

  // 浏览器定位
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      () => { /* 定位成功，城市在后端自动匹配 */ },
      () => { /* 定位失败，用默认城市 */ },
      { enableHighAccuracy: false, timeout: 3000 }
    );
  }
});
</script>

<style lang="less" scoped>
.container {
  background: #f5f7fa;
  min-height: 100vh;
  padding-bottom: 30px;
}

/* ============ 输入阶段 ============ */
.intro-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 12px 12px 0;
  padding: 16px;
  background: linear-gradient(135deg, #e8f5e9, #e3f2fd);
  border-radius: 12px;
  .intro-icon { font-size: 32px; }
  .intro-text { flex: 1; }
  .intro-title { font-weight: bold; font-size: 16px; color: #333; }
  .intro-desc { font-size: 12px; color: #666; line-height: 1.5; margin-top: 4px; }
}

.form-card {
  margin: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  .form-label {
    font-size: 15px;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
    .required { color: #ee6a55; }
  }
  .van-field { background: #f5f7fa; border-radius: 8px; margin-bottom: 4px; }
}

.symptom-input { background: #f5f7fa !important; border-radius: 8px; }

.submit-btn {
  margin: 20px 12px;
  height: 48px;
  font-size: 16px;
  font-weight: bold;
  background: linear-gradient(135deg, #409eff, #337ecc);
  border: none;
}

.footer-tip {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin: -10px 12px 20px;
}

/* ============ 加载阶段 ============ */
.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
}
.loading-animation { margin-bottom: 20px; }
.loading-dots {
  display: flex;
  gap: 8px;
  span {
    width: 12px; height: 12px;
    background: #409eff;
    border-radius: 50%;
    animation: bounce 1.4s infinite;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-16px); opacity: 1; }
}
.loading-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 30px; }
.loading-steps { width: 100%; max-width: 280px; }
.loading-steps .step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  opacity: 0.3;
  transition: all 0.5s;
  &.active { opacity: 1; }
  &.done { opacity: 0.7; .step-icon { background: #07c160; color: #fff; } }
  .step-icon {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #e0e0e0;
    color: #999;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: bold;
    flex-shrink: 0;
  }
  .step-text { font-size: 14px; color: #333; }
}
.loading-hint { margin-top: 30px; font-size: 13px; color: #999; }

/* ============ 结果阶段 ============ */
.guide-header {
  margin: 12px 12px 0;
  padding: 20px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  color: #fff;
  .guide-badge {
    display: inline-block;
    padding: 2px 10px;
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    font-size: 11px;
    margin-bottom: 10px;
  }
  .guide-title { font-size: 20px; font-weight: bold; margin-bottom: 8px; }
  .guide-summary { font-size: 13px; line-height: 1.6; opacity: 0.9; }
}

/* 攻略分段 */
.guide-sections {
  margin: 12px;
}
.guide-section {
  display: flex;
  gap: 10px;
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  .section-icon { font-size: 24px; flex-shrink: 0; }
  .section-content { flex: 1; }
  .section-title { font-weight: bold; font-size: 15px; color: #333; margin-bottom: 4px; }
  .section-body { font-size: 13px; color: #666; line-height: 1.7; white-space: pre-wrap; }
}

/* 数据卡片 */
.data-card {
  margin: 12px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 16px 0;
    .card-icon { font-size: 20px; }
    .card-title { font-size: 16px; font-weight: bold; color: #333; }
  }
  .card-body { padding: 12px 16px 16px; }
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
  &:last-child { border-bottom: none; }
  .info-label { font-size: 13px; color: #999; min-width: 60px; flex-shrink: 0; }
  .info-value { font-size: 14px; color: #333; flex: 1; }
}

.best-choice {
  padding: 10px 12px;
  background: #fff8e1;
  border-radius: 8px;
  font-size: 14px;
  color: #e65100;
  margin-bottom: 12px;
}

.hospital-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child { border-bottom: none; }
  .hosp-info { flex: 1; }
  .hosp-name { font-size: 15px; font-weight: bold; color: #333; margin-bottom: 4px; }
  .hosp-tags { display: flex; gap: 6px; margin-bottom: 4px; }
  .hosp-addr { font-size: 12px; color: #999; }
  .hosp-arrow { color: #ccc; }
}

.prep-section {
  margin-bottom: 14px;
  .prep-subtitle { font-size: 14px; font-weight: bold; color: #333; margin-bottom: 6px; }
  .prep-text { font-size: 13px; color: #666; line-height: 1.6; }
}
.check-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 0;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  .van-icon { margin-top: 2px; flex-shrink: 0; }
}
.prep-checklist {
  padding: 10px 0;
  font-size: 13px;
  color: #409eff;
  cursor: pointer;
  text-align: center;
}
.checklist-detail {
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.cost-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
  .cost-item {
    padding: 12px;
    background: #f5f7fa;
    border-radius: 8px;
    text-align: center;
    &.total {
      grid-column: 1 / -1;
      background: #e8f5e9;
    }
    .cost-label { font-size: 12px; color: #999; margin-bottom: 4px; }
    .cost-value { font-size: 16px; font-weight: bold; color: #333; }
    .total-value { color: #e65100; font-size: 20px; }
  }
}
.cost-insurance, .cost-companion {
  padding: 8px 10px;
  background: #f0f7ff;
  border-radius: 6px;
  font-size: 13px;
  color: #555;
  margin-bottom: 6px;
}
.cost-breakdown { margin-top: 8px; }
.breakdown-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  color: #666;
  border-bottom: 1px dashed #f0f0f0;
  span:first-child { width: 70px; flex-shrink: 0; }
  span:nth-child(2) { font-weight: bold; color: #333; width: 80px; }
  .note { color: #999; font-size: 12px; flex: 1; }
}

.weather-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff8e1;
  border-radius: 8px;
  margin-bottom: 8px;
  .weather-icon { font-size: 24px; }
  .weather-info { font-size: 14px; color: #555; }
}
.travel-advice {
  padding: 10px 12px;
  font-size: 13px;
  color: #795548;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.closing-tip {
  margin: 12px;
  padding: 14px 16px;
  background: #fff3e0;
  border-radius: 10px;
  font-size: 13px;
  color: #bf360c;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.action-buttons {
  padding: 0 12px 20px;
  .retry-btn {
    margin-top: 10px;
    color: #999;
    border-color: #ddd;
  }
}

.disclaimer {
  padding: 8px 10px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  text-align: center;
}
</style>
