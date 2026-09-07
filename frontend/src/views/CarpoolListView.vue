<script setup>
// 组队拼车列表页（前端 C）——支持作者编辑/删除自己的拼车
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { getMockCarpools } from '@/utils/mockData'
import MapComponent from '@/components/MapComponent.vue'
import WeatherWidget from '@/components/WeatherWidget.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const mapRef = ref(null)

const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await carpoolApi.listCarpools({ page: 1, size: 20 })
    list.value = data.items || data || []
  } catch {
    list.value = getMockCarpools()
  } finally {
    loading.value = false
  }
}

function toDetail(id) {
  router.push(`/carpool/${id}`)
}

function toEdit(c) {
  router.push(`/carpool/publish/${c.id}`)
}

async function removeCarpool(c) {
  try {
    await ElMessageBox.confirm(`确定删除「${c.title}」吗？删除后不可恢复。`, '删除拼车', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await carpoolApi.deleteCarpool(c.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const mapCenter = ref([118.001917, 36.814013])
const mapMarkers = computed(() => [])

onMounted(load)
</script>

<template>
  <div class="page-layout">
    <div class="left-panel">
      <el-card shadow="never" class="header-card">
        <div class="header-row">
          <h2>🚗 组队拼车</h2>
          <el-button type="primary" @click="router.push('/carpool/publish')">＋ 发布拼车</el-button>
        </div>
      </el-card>

      <div v-loading="loading" class="feed">
        <el-card
          v-for="c in list"
          :key="c.id"
          class="carpool-card"
          shadow="hover"
          @click="toDetail(c.id)"
        >
          <div class="route">
            <span class="city">{{ c.from }}</span>
            <span class="arrow">→</span>
            <span class="city">{{ c.to }}</span>
          </div>
          <div class="info-row">
            <span>🕐 {{ c.depart_time }}</span>
            <span v-if="c.return_time">↩️ {{ c.return_time }}</span>
          </div>
          <div class="info-row">
            <span>👤 发布者：{{ c.author_name }}</span>
            <span>💰 {{ c.price_per_person }}元/人</span>
          </div>
          <div class="footer">
            <el-progress
              :percentage="Math.round((c.seats_total - c.seats_left) / c.seats_total * 100)"
              :stroke-width="8"
              :show-text="false"
              class="seat-progress"
            />
            <span class="seat-info">剩余 {{ c.seats_left }}/{{ c.seats_total }} 座</span>
            <el-tag :type="c.seats_left > 0 ? 'success' : 'info'" size="small">
              {{ c.seats_left > 0 ? '招募中' : '已满员' }}
            </el-tag>
            <div v-if="c.is_author" class="op-btns" @click.stop>
              <el-button size="small" type="primary" plain @click="toEdit(c)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeCarpool(c)">删除</el-button>
            </div>
          </div>
        </el-card>

        <el-empty v-if="!loading && !list.length" description="暂无拼车信息，来发布第一条吧" />
      </div>
    </div>

    <div class="right-panel">
      <WeatherWidget />
      <div class="map-wrapper">
        <div class="map-header"><span class="map-title">🗺️ 校园地图</span></div>
        <MapComponent ref="mapRef" :center="mapCenter" :zoom="14" :markers="mapMarkers" height="360px" />
      </div>
      <el-card shadow="never" class="tip-card">
        <div class="tip-title">💡 拼车安全提示</div>
        <p>· 拼车前请核实对方身份信息</p>
        <p>· 建议选择白天出行，避免夜间单独拼车</p>
        <p>· 费用建议AA制，提前沟通清楚</p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.page-layout {
  display: flex;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: calc(100vh - 60px);
}
.left-panel { flex: 1; min-width: 0; }
.right-panel {
  width: 420px; flex-shrink: 0; display: flex; flex-direction: column;
  gap: 16px; position: sticky; top: 80px; align-self: flex-start;
}
.header-card { border-radius: 12px; margin-bottom: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.header-row h2 { margin: 0; font-size: 20px; color: #303133; }
.feed { min-height: 200px; }
.carpool-card {
  margin-bottom: 14px; border-radius: 12px; cursor: pointer; transition: all 0.25s;
}
.carpool-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(230, 162, 60, 0.15) !important; }
.route { display: flex; align-items: center; gap: 10px; font-size: 17px; font-weight: 600; color: #303133; }
.city { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arrow { color: #e6a23c; }
.info-row { display: flex; justify-content: space-between; margin-top: 8px; font-size: 13px; color: #909399; }
.footer { display: flex; align-items: center; gap: 10px; margin-top: 12px; }
.seat-progress { flex: 1; }
.seat-info { font-size: 13px; color: #606266; }
.op-btns { display: flex; gap: 6px; margin-left: auto; }
.tip-card { border-radius: 12px; }
.tip-title { font-weight: 600; color: #303133; margin-bottom: 8px; }
.tip-card p { font-size: 13px; color: #606266; margin: 4px 0; }
.map-wrapper { border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); }
.map-header { padding: 10px 14px; background: #fff; border-bottom: 1px solid #f0f0f0; }
.map-title { font-weight: 600; color: #303133; }
</style>
