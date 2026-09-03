<script setup>
// 校园地图页（归属：前端 A）——全屏地图 + 分类点位浏览（无需登录）
// 数据来自内容列表接口（返回带经纬度的帖子）；点击标记弹窗可跳详情。
// TODO(前端A)：左右双栏布局、模拟导航、热力图、按真实学校坐标替换 MAP_CONFIG.center
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import MapBrowser from '@/components/map/MapBrowser.vue'

const router = useRouter()
const rawList = ref([])
const loading = ref(false)
const errText = ref('')

const list = computed(() =>
  rawList.value.filter((p) => p.longitude != null && p.latitude != null)
)

async function load() {
  loading.value = true
  errText.value = ''
  try {
    const data = await postApi.listContents({ page: 1, size: 50 })
    rawList.value = data.items
  } catch {
    // 请求已由 request.js 统一提示，这里只让底图不被挡住
    errText.value = '未能获取点位数据（请确认后端已启动）'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="head">
      <div class="title">
        校园地图
        <span class="tip">共 {{ list.length }} 个点位 · 点击标记查看详情，可按类型筛选</span>
      </div>
      <el-button type="primary" size="small" @click="router.push('/publish')">＋ 发帖并定位</el-button>
    </div>

    <div class="map-body">
      <MapBrowser :points="list" />
      <div class="status-line">
        <span v-if="errText" class="err">{{ errText }}</span>
        <span v-else-if="loading" class="loading-tip">正在加载点位…</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  height: calc(100vh - 60px); /* 减去顶部导航高度 */
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  box-sizing: border-box;
}

.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.tip {
  font-size: 12px;
  font-weight: 400;
  color: #a8abb2;
  margin-left: 8px;
}

.map-body {
  position: relative;
  flex: 1;
  min-height: 0;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.status-line {
  position: absolute;
  left: 12px;
  bottom: 14px;
  z-index: 600;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 12px;
  color: #a8abb2;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.status-line .err {
  color: #e6a23c;
}
</style>
