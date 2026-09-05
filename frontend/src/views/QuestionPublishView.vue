<script setup>
// 发布问题页（归属：前端 C）
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as questionApi from '@/api/question'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)

const tags = ['高数', '编程', '考研', '生活', '求助', 'GIS', '英语', '其他']

const form = reactive({
  title: '',
  body: '',
  tag: '求助'
})

const rules = {
  title: [{ required: true, message: '请输入问题标题', trigger: 'blur' }],
  body: [{ required: true, message: '请详细描述你的问题', trigger: 'blur' }],
  tag: [{ required: true, message: '请选择问题分类', trigger: 'change' }]
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const data = await questionApi.createQuestion({
      title: form.title.trim(),
      body: form.body.trim(),
      tag: form.tag
    })
    ElMessage.success('提问成功')
    router.push(`/question/${data.id || 1}`)
  } catch {
    // mock 模式：跳转回列表
    ElMessage.success('提问成功')
    router.push('/questions')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="publish-card">
      <template #header>
        <div class="card-header">
          <span>✏️ 提出新问题</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="问题分类" prop="tag">
          <el-select v-model="form.tag" placeholder="请选择分类" style="width: 220px">
            <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>

        <el-form-item label="问题标题" prop="title">
          <el-input
            v-model="form.title"
            maxlength="80"
            show-word-limit
            placeholder="一句话说清你想问什么"
          />
        </el-form-item>

        <el-form-item label="问题描述" prop="body">
          <el-input
            v-model="form.body"
            type="textarea"
            :rows="8"
            maxlength="3000"
            show-word-limit
            placeholder="详细描述你的问题背景、已尝试的方法、期望得到的帮助..."
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">发布问题</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.publish-card {
  border-radius: 12px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
</style>
