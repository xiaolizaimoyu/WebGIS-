<script setup>
// 发布页（归属：前端 B）——活动/会议/动态/广告 统一发布，支持多图
// 说明：本路由 requiresAuth，未登录会被全局守卫拦截到登录页
// TODO(前端B)：草稿、发布后再次编辑、预览弹窗美化等扩展点
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as postApi from '@/api/post'
import { AD_CATEGORIES } from '@/api/const'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  title: '',
  body: '',
  type: 'activity',
  category: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文内容', trigger: 'blur' }]
}

const isAd = computed(() => form.type === 'ad')
const fileList = ref([]) // el-upload 双向列表，成功上传后 file.response = { url }
const previewVisible = ref(false)
const previewUrl = ref('')

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
    const images = fileList.value.filter((f) => f.response).map((f) => f.response.url)
    const data = await postApi.createContent({
      title: form.title.trim(),
      body: form.body.trim(),
      type: form.type,
      category: isAd.value ? form.category : undefined,
      images
    })
    ElMessage.success('发布成功')
    router.push(`/content/${data.id}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>发布新内容</template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="内容分类" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button value="activity">校园活动</el-radio-button>
            <el-radio-button value="meeting">校园会议</el-radio-button>
            <el-radio-button value="news">校园动态</el-radio-button>
            <el-radio-button value="ad">校园广告</el-radio-button>
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
          <el-button type="primary" :loading="submitting" @click="submit">立即发布</el-button>
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
</style>
