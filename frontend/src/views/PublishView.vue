<script setup>
// 发布 / 编辑页（归属：前端 B）
// - 无 :id 路由 = 新建发布
// - 带 :id 路由（/publish/:id）＝ 编辑已有内容（仅作者可进入，编辑由后端校验权限）
// 说明：本路由 requiresAuth，未登录会被全局守卫拦截到登录页
// TODO(前端B)：草稿、富文本编辑器、发布后二次编辑预览等扩展点
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as postApi from '@/api/post'
import { AD_CATEGORIES } from '@/api/const'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)

// ===== 地图选点配置（归属：前端 B，《新增功能规划书》5-2 发帖拾取经纬度）=====
// 高德 key 需在 https://lbs.amap.com 免费申请（Web端(JS API)类型）后填入；
// 未配置 key 时自动降级为手动输入经纬度，不影响发布流程。
const AMAP_KEY = ''
// 校园中心坐标（示例为广州大学城，可改成本校坐标）
const CAMPUS_CENTER = { lng: 113.3946, lat: 23.0392 }
const hasKey = !!AMAP_KEY

// 编辑模式：/publish/:id 存在 id 即为编辑
const isEdit = computed(() => !!route.params.id)
const editId = computed(() => (route.params.id ? Number(route.params.id) : null))

const form = reactive({
  title: '',
  body: '',
  type: 'activity',
  category: '',
  longitude: null, // 经度，未选点为 null（后端 E 联调后入库，当前后端会忽略该字段）
  latitude: null // 纬度
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文内容', trigger: 'blur' }]
}

const isAd = computed(() => form.type === 'ad')
const fileList = ref([]) // el-upload 双向列表；新传成功 file.response={url}；历史图无 response，直接用 file.url
const previewVisible = ref(false)
const previewUrl = ref('')

// 编辑模式：拉取原内容回填表单与图片（经纬度字段待后端 E 联调后返回）
async function loadEditing() {
  const data = await postApi.getContent(editId.value)
  form.title = data.title
  form.body = data.body
  form.type = data.type
  form.category = data.category || ''
  form.longitude = data.longitude ?? null
  form.latitude = data.latitude ?? null
  fileList.value = (data.images || []).map((url) => ({ name: url.split('/').pop(), url }))
  // 地图已就绪且原内容带坐标 → 在地图上标出原位置
  if (mapReady.value && form.longitude != null) {
    setPoint(form.longitude, form.latitude, false)
  }
}

// ===== 高德地图动态加载 + 点击选点 =====
const mapBox = ref(null) // 地图容器 DOM
const mapReady = ref(false) // 地图是否渲染成功
let map = null
let marker = null

// 按需注入高德 JS API 脚本（官方 callback 方式，避免污染 index.html）
function loadAMap() {
  return new Promise((resolve, reject) => {
    if (window.AMap) return resolve(window.AMap)
    const cbName = `__amap_cb_${Date.now()}`
    window[cbName] = () => resolve(window.AMap)
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&callback=${cbName}`
    script.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.head.appendChild(script)
  })
}

async function initMap() {
  if (!hasKey || !mapBox.value) return
  try {
    await loadAMap()
    map = new window.AMap.Map(mapBox.value, {
      zoom: 16,
      center: [CAMPUS_CENTER.lng, CAMPUS_CENTER.lat]
    })
    // 点击地图任意位置拾取坐标
    map.on('click', (e) => setPoint(e.lnglat.lng, e.lnglat.lat))
    mapReady.value = true
  } catch (err) {
    console.warn('高德地图加载失败，已降级为手动输入坐标：', err)
  }
}

function setPoint(lng, lat, moveTo = true) {
  form.longitude = Number(Number(lng).toFixed(6))
  form.latitude = Number(Number(lat).toFixed(6))
  if (!map) return
  if (!marker) {
    marker = new window.AMap.Marker({ position: [form.longitude, form.latitude] })
    map.add(marker)
  } else {
    marker.setPosition([form.longitude, form.latitude])
  }
  if (moveTo) map.setCenter([form.longitude, form.latitude])
}

function clearPoint() {
  form.longitude = null
  form.latitude = null
  if (marker && map) {
    map.remove(marker)
    marker = null
  }
}

onMounted(() => {
  if (isEdit.value) loadEditing()
  initMap()
})

// 自定义上传：替换默认 xhr，走我们的 /api/upload（已带 Token）
async function doUpload(options) {
  const data = await postApi.uploadImage(options.file)
  options.onSuccess(data, options.file)
}

function imageUrl(file) {
  return file.response ? file.response.url : file.url
}

function onPreview(file) {
  previewUrl.value = imageUrl(file)
  previewVisible.value = true
}

function onExceed() {
  ElMessage.warning('最多上传 5 张图片')
}

// 收集待提交图片：新传图用 response.url，历史图用自身 url（相对路径 /uploads/...）
function collectImages() {
  return fileList.value
    .map((f) => (f.response ? f.response.url : isEdit.value ? f.url : null))
    .filter(Boolean)
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  if (isAd.value && !form.category) {
    ElMessage.warning('请选择广告的子分类（如闲置 / 求助 / 宣传）')
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      type: form.type,
      category: isAd.value ? form.category : undefined,
      images: collectImages()
    }
    let data
    if (isEdit.value) {
      data = await postApi.updateContent(editId.value, payload)
      ElMessage.success('修改成功')
      router.push('/mine') // 编辑后回到我的发布，列表自动刷新
    } else {
      data = await postApi.createContent(payload)
      ElMessage.success('发布成功')
      router.push(`/content/${data.id}`)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>{{ isEdit ? '编辑内容' : '发布新内容' }}</template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="内容分类" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button value="activity">校园活动</el-radio-button>
            <el-radio-button value="meeting">校园会议</el-radio-button>
            <el-radio-button value="news">校园动态</el-radio-button>
            <el-radio-button value="ad">校园广告</el-radio-button>
            <!-- 新增分类（规划书 5-2）：美食分享 / 失物招领 -->
            <el-radio-button value="food">美食分享</el-radio-button>
            <el-radio-button value="lost">失物招领</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="isAd" label="子分类" required>
          <el-select v-model="form.category" placeholder="请选择广告子分类" style="width: 220px">
            <el-option v-for="c in AD_CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            maxlength="80"
            show-word-limit
            placeholder="一句话说清内容标题"
          />
        </el-form-item>

        <el-form-item label="正文" prop="body">
          <el-input
            v-model="form.body"
            type="textarea"
            :rows="6"
            maxlength="5000"
            placeholder="详细描述内容……（活动可写时间地点，广告可写价格联系方式等）"
          />
        </el-form-item>

        <el-form-item label="图片">
          <el-upload
            v-model:file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="5"
            :http-request="doUpload"
            :on-preview="onPreview"
            :on-exceed="onExceed"
          >
            <div class="upload-tip">＋<br />上传图片</div>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">
            {{ isEdit ? '保存修改' : '立即发布' }}
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog v-model="previewVisible" title="图片预览" width="600px">
      <img v-if="previewUrl" :src="previewUrl" alt="preview" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<style scoped>
.upload-tip {
  color: #8c939d;
  font-size: 13px;
  line-height: 1.6;
}

.map-block {
  width: 100%;
}

.map-box {
  width: 100%;
  height: 260px;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  position: relative;
  overflow: hidden;
}

.map-tip {
  color: #909399;
  font-size: 13px;
}

.map-box .map-tip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.map-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0;
}

.map-manual {
  display: flex;
  gap: 10px;
}
</style>
