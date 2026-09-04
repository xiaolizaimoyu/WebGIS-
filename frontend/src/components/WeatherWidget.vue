<script setup>
// 天气组件（归属：天气模块）——紧凑天气卡片
// 对外契约：
//   props: city (城市名), useMock (是否使用模拟数据，默认 true)
//   emit:  loaded(weatherData)
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  city: { type: String, default: '北京' },
  useMock: { type: Boolean, default: true }
})

const emit = defineEmits(['loaded'])

const loading = ref(false)
const weather = ref({
  city: props.city,
  temp: '--',
  text: '加载中',
  windDir: '--',
  windScale: '--',
  humidity: '--',
  icon: '☀️'
})

// 天气图标映射
const weatherIcons = {
  '晴': '☀️',
  '多云': '⛅',
  '阴': '☁️',
  '小雨': '🌦️',
  '中雨': '🌧️',
  '大雨': '🌧️',
  '雪': '🌨️',
  '雷阵雨': '⛈️',
  '雾': '🌫️'
}

// 模拟天气数据
function getMockWeather(city) {
  const conditions = Object.keys(weatherIcons)
  const cond = conditions[Math.floor(Math.random() * conditions.length)]
  return {
    city,
    temp: Math.floor(Math.random() * 20) + 10,
    text: cond,
    windDir: ['东风', '南风', '西风', '北风'][Math.floor(Math.random() * 4)],
    windScale: Math.floor(Math.random() * 5) + 1,
    humidity: Math.floor(Math.random() * 40) + 40,
    icon: weatherIcons[cond] || '🌤️'
  }
}

// 真实API调用（和风天气，需配置 API_KEY 后启用）
async function fetchRealWeather(city) {
  // TODO: 替换为你的和风天气 API KEY
  const API_KEY = ''
  if (!API_KEY) {
    throw new Error('未配置天气 API KEY')
  }
  const res = await fetch(
    `https://devapi.qweather.com/v7/weather/now?location=${encodeURIComponent(city)}&key=${API_KEY}`
  )
  const data = await res.json()
  if (data.code !== '200') throw new Error('天气接口异常')
  const now = data.now
  return {
    city,
    temp: now.temp,
    text: now.text,
    windDir: now.windDir,
    windScale: now.windScale,
    humidity: now.humidity,
    icon: weatherIcons[now.text] || '🌤️'
  }
}

async function loadWeather() {
  loading.value = true
  try {
    let data
    if (props.useMock) {
      data = getMockWeather(props.city)
    } else {
      data = await fetchRealWeather(props.city)
    }
    weather.value = data
    emit('loaded', data)
  } catch (e) {
    ElMessage.warning(`天气获取失败：${e.message}`)
    // 失败时回退到模拟数据
    weather.value = getMockWeather(props.city)
  } finally {
    loading.value = false
  }
}

watch(() => props.city, () => loadWeather())

onMounted(loadWeather)
</script>

<template>
  <div class="weather-card" v-loading="loading">
    <div class="weather-header">
      <span class="city">📍 {{ weather.city }}</span>
      <el-button text size="small" @click="loadWeather" :loading="loading">刷新</el-button>
    </div>
    <div class="weather-body">
      <div class="weather-main">
        <span class="weather-icon">{{ weather.icon }}</span>
        <div class="temp-area">
          <span class="temp">{{ weather.temp }}°</span>
          <span class="text">{{ weather.text }}</span>
        </div>
      </div>
      <div class="weather-detail">
        <div class="detail-item">
          <span class="label">风向</span>
          <span class="value">{{ weather.windDir }} {{ weather.windScale }}级</span>
        </div>
        <div class="detail-item">
          <span class="label">湿度</span>
          <span class="value">{{ weather.humidity }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.weather-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.city {
  font-size: 14px;
  opacity: 0.9;
}

.weather-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weather-icon {
  font-size: 48px;
  line-height: 1;
}

.temp-area {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.temp {
  font-size: 36px;
  font-weight: 700;
}

.text {
  font-size: 16px;
  opacity: 0.9;
}

.weather-detail {
  display: flex;
  gap: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 10px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label {
  font-size: 12px;
  opacity: 0.7;
}

.value {
  font-size: 14px;
}
</style>
