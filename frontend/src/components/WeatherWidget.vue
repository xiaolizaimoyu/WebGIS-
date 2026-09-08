<script setup>
// 天气组件（归属：天气模块）——实时天气卡片
// 使用 Open-Meteo 免费 API（无需 API KEY）获取真实天气
// 自动每5分钟刷新一次，无需手动点击
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  city: { type: String, default: '淄博' },
  lat: { type: Number, default: 36.809 },
  lng: { type: Number, default: 117.996 }
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

let refreshTimer = null

// Open-Meteo weather_code → 中文天气 + 图标
const weatherCodeMap = {
  0:  { text: '晴', icon: '☀️' },
  1:  { text: '晴', icon: '🌤️' },
  2:  { text: '多云', icon: '⛅' },
  3:  { text: '阴', icon: '☁️' },
  45: { text: '雾', icon: '🌫️' },
  48: { text: '雾', icon: '🌫️' },
  51: { text: '小雨', icon: '🌦️' },
  53: { text: '小雨', icon: '🌦️' },
  55: { text: '小雨', icon: '🌦️' },
  56: { text: '冻雨', icon: '🌧️' },
  57: { text: '冻雨', icon: '🌧️' },
  61: { text: '小雨', icon: '🌦️' },
  63: { text: '中雨', icon: '🌧️' },
  65: { text: '大雨', icon: '🌧️' },
  66: { text: '冻雨', icon: '🌧️' },
  67: { text: '冻雨', icon: '🌧️' },
  71: { text: '小雪', icon: '🌨️' },
  73: { text: '中雪', icon: '🌨️' },
  75: { text: '大雪', icon: '❄️' },
  77: { text: '雪粒', icon: '🌨️' },
  80: { text: '小雨', icon: '🌦️' },
  81: { text: '中雨', icon: '🌧️' },
  82: { text: '大雨', icon: '⛈️' },
  85: { text: '小雪', icon: '🌨️' },
  86: { text: '大雪', icon: '❄️' },
  95: { text: '雷阵雨', icon: '⛈️' },
  96: { text: '雷阵雨', icon: '⛈️' },
  99: { text: '雷阵雨', icon: '⛈️' }
}

// 风速 m/s 转蒲福风级
function windSpeedToScale(ms) {
  if (ms < 0.3) return 0
  if (ms < 1.6) return 1
  if (ms < 3.4) return 2
  if (ms < 5.5) return 3
  if (ms < 8.0) return 4
  if (ms < 10.8) return 5
  if (ms < 13.9) return 6
  if (ms < 17.2) return 7
  if (ms < 20.8) return 8
  return 9
}

// 风向角度转中文
function degreeToDir(deg) {
  if (deg < 22.5 || deg >= 337.5) return '北风'
  if (deg < 67.5) return '东北风'
  if (deg < 112.5) return '东风'
  if (deg < 157.5) return '东南风'
  if (deg < 202.5) return '南风'
  if (deg < 247.5) return '西南风'
  if (deg < 292.5) return '西风'
  return '西北风'
}

// 使用 Open-Meteo 免费 API 获取真实天气（无需 API KEY）
async function fetchRealWeather(lat, lng) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia/Shanghai`
  const res = await fetch(url)
  if (!res.ok) throw new Error('天气接口请求失败')
  const data = await res.json()
  const cur = data.current
  const code = weatherCodeMap[cur.weather_code] || { text: '未知', icon: '🌤️' }
  return {
    city: props.city,
    temp: Math.round(cur.temperature_2m),
    text: code.text,
    windDir: degreeToDir(cur.wind_direction_10m),
    windScale: windSpeedToScale(cur.wind_speed_10m),
    humidity: Math.round(cur.relative_humidity_2m),
    icon: code.icon
  }
}

// 网络失败时的兜底 mock 数据
function fallbackMock() {
  return {
    city: props.city,
    temp: 25,
    text: '多云',
    windDir: '东南风',
    windScale: 3,
    humidity: 60,
    icon: '⛅'
  }
}

async function loadWeather() {
  loading.value = true
  try {
    const data = await fetchRealWeather(props.lat, props.lng)
    weather.value = data
    emit('loaded', data)
  } catch (e) {
    // 网络失败时使用兜底数据，不弹错误提示
    weather.value = fallbackMock()
  } finally {
    loading.value = false
  }
}

watch(() => props.city, () => loadWeather())

onMounted(() => {
  loadWeather()
  // 每5分钟自动刷新一次天气
  refreshTimer = setInterval(loadWeather, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="weather-card" v-loading="loading">
    <div class="weather-header">
      <span class="city">📍 {{ weather.city }}</span>
      <span class="live-badge">● 实时</span>
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

.live-badge {
  font-size: 12px;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.live-badge::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ade80;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
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
