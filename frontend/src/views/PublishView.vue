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
import { TYPE_LIST } from '@/api/const'
import LocationPicker from '@/components/map/LocationPicker.vue'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)

// 编辑模式：/publish/:id 存在 id 即为编辑
const isEdit = computed(() => !!route.params.id)
const editId = computed(() => (route.params.id ? Number(route.params.id) : null))

const form = reactive({
  title: '',
  body: '',
  type: 'meeting',
  category: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文内容', trigger: 'blur' }]
}

const fileList = ref([]) // el-upload 双向列表；新传成功 file.response={url}；历史图无 response，直接用 file.url
const previewVisible = ref(false)
const previewUrl = ref('')

// 地图定位（可选）：开启后在地图上点选，保存经纬度供地图页展示
const locEnabled = ref(false)
const location = ref(null) // { lng, lat } 或 null

// 编辑模式：拉取原内容回填表单与图片
// 说明：历史图把服务器地址包进 response.url，和「新上传成功」的 file 结构统一，
//      提交收集时就只认 response.url 一条通道，避免混入 blob: 本地临时地址。
async function loadEditing() {
  const data = await postApi.getContent(editId.value)
  form.title = data.title
  form.body = data.body
  form.type = data.type
  form.category = data.category || ''
  fileList.value = (data.images || []).map((url) => ({
    name: url.split('/').pop(),
    url,
    response: { url }
  }))
  // 已有位置则回填选点
  if (data.longitude != null && data.latitude != null) {
    locEnabled.value = true
    location.value = { lng: Number(data.longitude), lat: Number(data.latitude) }
  }
}

onMounted(() => {
  if (isEdit.value) loadEditing()
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

// 收集待提交图片：只认「后端返回的服务器地址」file.response.url
// 本地预览用的 blob: 临时地址一律不入库；未上传完成/失败的文件没有 response，会被安全跳过。
function collectImages() {
  return fileList.value
    .map((f) => (f.response && f.response.url ? f.response.url : null))
    .filter(Boolean)
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      type: form.type,
      images: collectImages()
    }
    if (locEnabled.value && location.value) {
      payload.longitude = location.value.lng
      payload.latitude = location.value.lat
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
            <el-radio-button v-for="t in TYPE_LIST" :key="t.value" :value="t.value">
              {{ t.label }}
            </el-radio-button>
          </el-radio-group>
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
            placeholder="详细描述内容……（会议可写时间地点，美食可写推荐理由，失物可写拾取地点等）"
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

        <el-form-item label="地图位置">
          <div class="loc-line">
            <el-switch v-model="locEnabled" />
            <span class="loc-hint">开启后在地图上点击即可拾取位置（会显示在校园地图页）</span>
          </div>
          <LocationPicker v-if="locEnabled" v-model="location" />
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

.loc-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.loc-hint {
  font-size: 13px;
  color: #a8abb2;
}
</style>
