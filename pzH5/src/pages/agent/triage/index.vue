<template>
  <div class="container">
    <div class="header">
      <van-icon name="arrow-left" class="header-left" @click="goBack" size="22" />
      AI智能分诊
    </div>
    <div class="content" v-if="!result">
      <div class="section-title">请描述您的症状</div>
      <van-field v-model="form.symptoms" type="textarea" rows="5"
        placeholder="请详细描述您的症状，例如：咳嗽、发烧、头痛、腹泻..." class="symptom-input" />
      <van-row gutter="16" class="info-row">
        <van-col span="12">
          <van-field v-model="form.patient_age" type="number" placeholder="年龄(选填)" label="年龄" />
        </van-col>
        <van-col span="12">
          <van-field v-model="form.patient_gender" placeholder="性别(选填)" label="性别"
            @click="showGender = true" readonly />
        </van-col>
      </van-row>
      <van-button type="primary" block class="submit-btn" :loading="loading" @click="doTriage">
        {{ loading ? '正在分析...' : '开始分诊' }}
      </van-button>
    </div>
    <div class="content" v-else>
      <div class="result-section">
        <div class="result-header"><van-icon name="medel" color="#409eff" size="24" /><span>分诊建议</span></div>
        <div class="dept-tag"><van-tag type="primary" size="large">{{ result.recommended_department }}</van-tag></div>
        <div class="summary-text">{{ result.symptom_summary }}</div>
        <van-divider />
        <div class="sub-title">推荐医院</div>
        <div v-for="h in (result.recommended_hospitals || [])" :key="h.id" class="rec-item" @click="goOrder(h.id)">
          <van-icon name="hospital" color="#409eff" /><span class="rec-name">{{ h.name }}</span>
          <van-tag v-if="h.rank" plain>{{ h.rank }}</van-tag>
        </div>
        <van-divider />
        <div class="sub-title">推荐陪诊师</div>
        <div v-for="c in (result.recommended_companions || [])" :key="c.id" class="rec-item">
          <van-icon name="contact" color="#07c160" /><span class="rec-name">{{ c.name }}</span>
        </div>
        <van-divider />
        <div class="disclaimer">{{ result.disclaimer || '以上推荐仅供参考，请以医生诊断为准' }}</div>
        <van-button type="primary" block class="submit-btn" @click="goOrder()">立即预约陪诊</van-button>
        <van-button plain block class="retry-btn" @click="reset">重新描述</van-button>
      </div>
    </div>
    <van-action-sheet v-model:show="showGender" :actions="genderOptions" @select="onGenderSelect" />
  </div>
</template>

<script setup>
import { ref, reactive, getCurrentInstance } from "vue";
import { useRouter } from "vue-router";
import { showToast } from "vant";

const { proxy } = getCurrentInstance();
const router = useRouter();
const loading = ref(false);
const result = ref(null);
const showGender = ref(false);
const form = reactive({ symptoms: "", patient_age: "", patient_gender: "" });
const genderOptions = [{ name: "男" }, { name: "女" }];
const onGenderSelect = (item) => { form.patient_gender = item.name; showGender.value = false; };
const goBack = () => router.go(-1);

const doTriage = async () => {
  if (!form.symptoms.trim()) { showToast("请描述您的症状"); return; }
  loading.value = true;
  try {
    const { data } = await proxy.$api.triageRecommend({
      symptoms: form.symptoms,
      patient_age: Number(form.patient_age) || 0,
      patient_gender: form.patient_gender,
    });
    if (data.code === 10000) result.value = data.data;
    else showToast(data.message || "分诊失败");
  } catch (e) { showToast("网络错误"); }
  loading.value = false;
};

const goOrder = (hid) => router.push(hid ? `/createOrder?id=${hid}` : "/createOrder");
const reset = () => { result.value = null; form.symptoms = ""; form.patient_age = ""; form.patient_gender = ""; };
</script>

<style lang="less" scoped>
.container { background: #f0f0f0; min-height: 100vh; }
.header { background: #fff; line-height: 44px; text-align: center; font-size: 16px; font-weight: bold; position: relative; .header-left { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); } }
.content { padding: 15px; }
.section-title { font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #333; }
.symptom-input { background: #fff; border-radius: 8px; }
.info-row { margin-top: 10px; }
.submit-btn { margin-top: 20px; border-radius: 8px; }
.retry-btn { margin-top: 10px; border-radius: 8px; }
.result-section { background: #fff; border-radius: 10px; padding: 20px; }
.result-header { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: bold; margin-bottom: 15px; }
.dept-tag { text-align: center; margin: 15px 0; }
.summary-text { color: #666; line-height: 1.6; font-size: 14px; }
.sub-title { font-size: 15px; font-weight: bold; color: #333; margin-bottom: 10px; }
.rec-item { display: flex; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid #f0f0f0; .rec-name { flex: 1; font-size: 14px; } }
.disclaimer { color: #999; font-size: 12px; text-align: center; padding: 10px; }
</style>
