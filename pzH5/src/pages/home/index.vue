<template>
  <div>
    <div class="header">
      <div class="header-left" @click="showCityPicker = true">{{ currentCity }}<van-icon name="arrow-down" /></div>
      <van-search
        v-model="searchValue"
        placeholder="请输入搜索关键词"
        shape="round"
      />
    </div>
    <!-- 城市选择器 -->
    <van-action-sheet v-model:show="showCityPicker" :actions="cityActions" @select="onCitySelect"
      cancel-text="取消" close-on-click-action />

    <!-- 天气出行提示 - 点击展开 -->
    <div class="weather-bar" v-if="weatherData.condition" @click="showWeather = !showWeather">
      <van-icon :name="weatherIcon" class="weather-icon" />
      <div class="weather-info">
        <span class="weather-temp">{{ weatherData.temperature }}°C</span>
        <span class="weather-cond">{{ weatherData.condition }}</span>
      </div>
      <div class="weather-advice">{{ weatherData.advice ? weatherData.advice.split('；')[0] : '点击查看出行建议' }}</div>
      <van-icon :name="showWeather ? 'arrow-up' : 'arrow'" color="#ccc" size="14" />
    </div>
    <!-- 天气详情展开 -->
    <div class="weather-detail" v-if="showWeather && weatherData.condition">
      <div class="weather-detail-content">
        <div class="wd-row">
          <span class="wd-label">🌡 温度</span>
          <span class="wd-value">{{ weatherData.temperature }}°C</span>
        </div>
        <div class="wd-row">
          <span class="wd-label">☁️ 天气</span>
          <span class="wd-value">{{ weatherData.condition }}</span>
        </div>
        <div class="wd-row" v-if="weatherData.wind">
          <span class="wd-label">💨 风力</span>
          <span class="wd-value">{{ weatherData.wind }}</span>
        </div>
        <div class="wd-row" v-if="weatherData.humidity">
          <span class="wd-label">💧 湿度</span>
          <span class="wd-value">{{ weatherData.humidity }}</span>
        </div>
        <div class="wd-divider"></div>
        <div class="wd-advice">{{ weatherData.advice }}</div>
      </div>
    </div>
    <!-- AI智能就医规划入口 -->
    <div class="ai-triage-entry planning-entry" @click="router.push('/agent/planning')">
      <van-image width="40" height="40" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%23667eea'/%3E%3Ctext x='50' y='68' text-anchor='middle' font-size='45' fill='white'%3E📋%3C/text%3E%3C/svg%3E" />
      <div class="ai-triage-text">
        <div class="ai-triage-title">🏥 智能就医规划 <van-tag plain size="small" color="#ff6b35" style="margin-left:4px">NEW</van-tag></div>
        <div class="ai-triage-desc">分析症状→推荐医院→准备清单→费用预估，一站式攻略</div>
      </div>
      <van-icon name="arrow" color="#ccc" />
    </div>
    <van-swipe
      class="my-swipe"
      :autoplay="3000"
      indicator-color="white"
      height="170"
    >
      <van-swipe-item v-for="item in homeData.slides" :key="item.id" @click="goOrder(item)">
        <div class="slide-map-btn" @click.stop="viewMap(item)">📍 查看地图</div>
        <van-image :src="item.pic_image_url" />
        <div class="slide-label" v-if="item.hospital_name">
          <span>{{ item.hospital_name }}</span>
          <van-tag v-if="item.hospital_rank" plain size="small">{{ item.hospital_rank }}</van-tag>
        </div>
      </van-swipe-item>
    </van-swipe>

    <van-row justify="space-around" style="margin-top: 8px;">
      <van-col
        v-for="(item, index) in homeData.nav2s"
        :key="item.id"
        class="center-img"
        span="11"
        @click="goOrderTwo(index)"
      >
        <van-image :src="item.pic_image_url" />
      </van-col>
    </van-row>
    <van-row class="yy-list" v-for="item in homeData.hospitals" :key="item.id" @click="goOrder(item)" justify="space-around">
      <van-col span="6">
        <van-image :src="item.avatar_url" width="100" height="90" />
      </van-col>
      <van-col span="15" class="yy">
        <div class="yy-name">
          {{ item.name }}
        </div>

        <div class="yy-type">
          <span>{{ item.rank }}</span>&nbsp;&nbsp;<span>{{ item.label }}</span>
        </div>

        <div class="yy-text">
          {{ item.intro }}
        </div>
        <div class="yy-distance" v-if="item.distance">
          <van-icon name="location-o" color="#999" /> 距您约 {{ formatDistance(item.distance) }}
        </div>
        <div class="yy-actions" v-if="item.latitude && item.longitude">
          <van-tag plain type="warning" size="small" @click.stop="viewMap(item)" class="nav-tag">
            <van-icon name="map-marked" /> 查看地图
          </van-tag>
          <van-tag plain type="primary" size="small" @click.stop="navigateTo(item)" class="nav-tag">
            <van-icon name="location-o" /> 导航到院
          </van-tag>
          <van-tag plain type="success" size="small" @click.stop="goOrder(item)" class="order-tag">
            <van-icon name="plus" /> 预约陪诊
          </van-tag>
        </div>
      </van-col>
    </van-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, getCurrentInstance } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const searchValue = ref("");

const { proxy } = getCurrentInstance();

const homeData = reactive({
  hospitals: [],
  nav2s: [],
  navs: [],
  now: "",
  slides: [],
});

const weatherData = reactive({
  condition: "",
  temperature: "",
  wind: "",
  humidity: "",
  advice: "",
});
const showWeather = ref(false);

const weatherIcon = computed(() => {
  const cond = weatherData.condition || "";
  if (cond.includes("雨")) return "underway-o";
  if (cond.includes("雪")) return "snow-o";
  if (cond.includes("云")) return "cloud-upload-o";
  if (cond.includes("晴")) return "sun-o";
  if (cond.includes("雾") || cond.includes("霾")) return "eye-o";
  return "fire-o";
});

const goOrderTwo = (index) => {
  router.push(`/createOrder?id=${homeData.hospitals[index].id}`)
};

const goOrder = (item) => {
  router.push(`/createOrder?id=${item.id}`)
}

const navigateTo = (item) => {
  // 使用高德URI scheme唤起APP导航
  const name = encodeURIComponent(item.name)
  const url = `https://uri.amap.com/navigation?to=${item.longitude},${item.latitude},${name}&mode=car&coordinate=gaode`
  window.open(url, '_blank')
}

const viewMap = (item) => {
  if (item.map_url) {
    window.open(item.map_url, '_blank')
  } else {
    const name = encodeURIComponent(item.name)
    window.open(`https://uri.amap.com/marker?position=${item.longitude},${item.latitude}&name=${name}&coordinate=gaode`, '_blank')
  }
}

const currentCity = ref("定位中...")
const userLocation = ref(null)
const showCityPicker = ref(false)
const cityActions = ref([])
const cityList = ref([])

const formatDistance = (km) => {
  if (!km) return ""
  if (km < 1) return Math.round(km * 1000) + "m"
  if (km < 10) return km.toFixed(1) + "km"
  return Math.round(km) + "km"
}

const loadData = async (city) => {
  try {
    const params = {}
    if (userLocation.value) {
      params.lat = userLocation.value.lat
      params.lng = userLocation.value.lng
    }
    if (city) params.city = city
    const { data } = await proxy.$api.index(params)
    Object.assign(homeData, data.data)
    // 更新城市名
    if (data.data.city) {
      currentCity.value = data.data.city === "全国" ? (city || "全国") : data.data.city
    }
    // 天气
    try {
      const { data: wd } = await proxy.$api.getWeather({ city: currentCity.value })
      if (wd.code === 10000) {
        weatherData.condition = wd.data.weather.condition
        weatherData.temperature = wd.data.weather.temperature
        weatherData.wind = wd.data.weather.wind || ""
        weatherData.humidity = wd.data.weather.humidity || ""
        weatherData.advice = wd.data.advice
      }
    } catch (e) { /* ignore */ }
  } catch (e) { /* ignore */ }
}

const onCitySelect = (item) => {
  showCityPicker.value = false
  if (item.name === "全国") {
    userLocation.value = null
    currentCity.value = "全国"
    loadData()
  } else {
    loadData(item.name)
  }
}

onMounted(async () => {
  // 获取城市列表
  try {
    const { data } = await proxy.$api.getCities()
    if (data.code === 10000) {
      cityList.value = data.data
      cityActions.value = [
        { name: "全国" },
        ...data.data.map(c => ({ name: c })),
      ]
    }
  } catch (e) { /* ignore */ }

  // 获取位置
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userLocation.value = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        }
        loadData()
      },
      () => {
        // 定位失败，默认选第一个城市
        if (cityList.value.length) {
          currentCity.value = cityList.value[0]
          loadData(cityList.value[0])
        } else {
          loadData()
        }
      },
      { enableHighAccuracy: false, timeout: 5000 }
    )
  } else {
    if (cityList.value.length) {
      currentCity.value = cityList.value[0]
      loadData(cityList.value[0])
    } else {
      loadData()
    }
  }
})
</script>

<style lang="less" scoped>
.header {
  display: flex;
  justify-content: space-between;
  margin: 5px;
  line-height: 54px;
  .header-left {
    padding-left: 22px;
    background: url(data:image/png;base64,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)
      no-repeat left center;
    background-size: 20px;
    font-size: 20px;
    font-weight: bold;
    color: #666666;
  }
}
.my-swiper {
  margin: 5px;
}
.yy-list {
  padding-bottom: 10px;
  margin: 20px 0;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 6px 0 rgba(0, 0, 0, 0.04), 0 1px 6px 0 rgba(0, 0, 0, 0.04);
  .yy {
    .yy-name {
      font-size: 20px;
      line-height: 30px;
      font-weight: bold;
    }
    .yy-type {
      font-weight: bold;
      line-height: 25px;
      font-size: 15px;
      color: #0ca7ae;
    }
    .yy-text {
      font-size: 14px;
      color: #999999;
    }
    .yy-distance {
      font-size: 12px;
      color: #999;
      margin-top: 4px;
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .yy-actions {
      margin-top: 8px;
      display: flex;
      gap: 10px;
      .nav-tag, .order-tag { padding: 2px 6px; }
    }
  }
}
.slide-map-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.5);
  color: #fff;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10;
}
.slide-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}
.my-swipe { position: relative; }
.weather-detail { margin: 0 8px 4px; background: #fffdf0; border-radius: 0 0 10px 10px; padding: 8px 12px; border-top: none; }
.weather-detail-content { font-size: 13px; }
.wd-row { display: flex; justify-content: space-between; padding: 5px 0; }
.wd-label { color: #888; }
.wd-value { color: #333; font-weight: bold; }
.wd-divider { height: 1px; background: #f0e8d0; margin: 8px 0; }
.wd-advice { color: #795548; font-size: 12px; line-height: 1.6; }
.weather-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 8px 4px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #fffbe6, #fff8dc);
  border-radius: 10px;
  font-size: 13px;
  .weather-icon { font-size: 22px; color: #f57c00; }
  .weather-info { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
  .weather-temp { font-weight: bold; color: #e65100; font-size: 16px; }
  .weather-cond { color: #666; }
  .weather-advice { flex: 1; color: #795548; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
.ai-triage-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 8px;
  padding: 12px 15px;
  background: linear-gradient(135deg, #e8f4ff, #f0f8ff);
  border-radius: 12px;
  cursor: pointer;
  .ai-triage-text { flex: 1; }
  .ai-triage-title { font-size: 15px; font-weight: bold; color: #333; }
  .ai-triage-desc { font-size: 12px; color: #999; margin-top: 2px; }
}
.planning-entry {
  background: linear-gradient(135deg, #ede7f6, #f3e5f5) !important;
}
.bottom-text {
  line-height: 50px;
  text-align: center;
  color: #999999;
}
</style>