<script setup>
// 问答详情页（归属：前端 C）——问题详情 + 回答列表 + 发表回答
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as questionApi from '@/api/question'
import { formatTime } from '@/api/const'
import { getMockQuestionDetail, getMockAnswers } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const questionId = Number(route.params.id)
const question = ref(null)
const answers = ref([])
const answerText = ref('')
const sending = ref(false)

async function loadDetail() {
  try {
    question.value = await questionApi.getQuestion(questionId)
  } catch {
    question.value = getMockQuestionDetail(questionId)
  }
}

async function loadAnswers() {
  try {
    answers.value = await questionApi.listAnswers(questionId)
  } catch {
    answers.value = getMockAnswers(questionId)
  }
}

async function sendAnswer() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再回答')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const text = answerText.value.trim()
  if (!text) return
  sending.value = true
  try {
    await questionApi.createAnswer(questionId, text)
    answerText.value = ''
    ElMessage.success('回答成功')
    await loadAnswers()
  } catch {
    // mock 模式：本地添加
    answers.value.unshift({
      id: Date.now(),
      question_id: questionId,
      body: text,
      author_name: store.userInfo?.nickname || '我',
      author_avatar: '',
      created_at: Date.now(),
      likes: 0,
      adopted: false
    })
    answerText.value = ''
    ElMessage.success('回答成功')
  } finally {
    sending.value = false
  }
}

async function adoptAnswer(answerId) {
  try {
    await questionApi.adoptAnswer(questionId, answerId)
    ElMessage.success('已采纳该回答')
  } catch {
    // mock
  }
  answers.value.forEach((a) => (a.adopted = a.id === answerId))
  if (question.value) question.value.adopted = true
}

onMounted(() => {
  loadDetail()
  loadAnswers()
})
</script>

<template>
  <div class="page-container" v-if="question">
    <el-card shadow="never" class="detail-card">
      <div class="head">
        <el-tag type="warning" size="small">{{ question.tag }}</el-tag>
        <el-tag v-if="question.adopted" type="success" effect="dark" size="small">已解决</el-tag>
        <span class="meta">
          {{ question.author_name }} 提问于 {{ formatTime(question.created_at) }}
        </span>
      </div>

      <h1 class="title">{{ question.title }}</h1>
      <div class="body">{{ question.body }}</div>

      <div class="stats">
        <span>👁 {{ question.views }} 浏览</span>
        <span>💬 {{ question.answer_count }} 回答</span>
      </div>
    </el-card>

    <el-card shadow="never" class="answer-card">
      <template #header>回答（{{ answers.length }}）</template>

      <div class="answer-input">
        <el-input
          v-model="answerText"
          type="textarea"
          :rows="3"
          maxlength="2000"
          placeholder="写下你的回答，帮助他人解决问题..."
        />
        <div class="input-actions">
          <el-button type="primary" :loading="sending" @click="sendAnswer">发表回答</el-button>
        </div>
      </div>

      <el-empty v-if="!answers.length" description="还没有回答，来抢沙发～" :image-size="80" />

      <div v-for="a in answers" :key="a.id" class="answer-item" :class="{ adopted: a.adopted }">
        <div v-if="a.adopted" class="adopted-badge">✅ 最佳回答</div>
        <div class="answer-head">
          <el-avatar :size="36" class="answer-avatar">{{ a.author_name.slice(0, 1) }}</el-avatar>
          <div class="answer-who">
            <span class="nick">{{ a.author_name }}</span>
            <span class="time">{{ formatTime(a.created_at) }}</span>
          </div>
          <div class="answer-actions">
            <el-button text size="small" @click="a.likes++">👍 {{ a.likes }}</el-button>
            <el-button
              v-if="!a.adopted && !question.adopted"
              text
              type="success"
              size="small"
              @click="adoptAnswer(a.id)"
            >
              采纳
            </el-button>
          </div>
        </div>
        <div class="answer-text">{{ a.body }}</div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}

.detail-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta {
  margin-left: auto;
  color: #a8abb2;
  font-size: 12px;
}

.title {
  font-size: 24px;
  margin: 12px 0;
  color: #303133;
}

.body {
  color: #4b4b4b;
  font-size: 15px;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.stats {
  margin-top: 16px;
  display: flex;
  gap: 20px;
  color: #909399;
  font-size: 13px;
  padding-top: 12px;
  border-top: 1px solid #f0f2f5;
}

.answer-card {
  border-radius: 12px;
}

.answer-input {
  margin-bottom: 16px;
}

.input-actions {
  margin-top: 8px;
  text-align: right;
}

.answer-item {
  padding: 16px 0;
  border-top: 1px solid #f0f2f5;
  position: relative;
}

.answer-item.adopted {
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
  border-radius: 8px;
  padding: 16px;
  margin: 0 -16px;
}

.adopted-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
}

.answer-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.answer-avatar {
  background: linear-gradient(135deg, #4facfe, #1d6df0);
  color: #fff;
  flex-shrink: 0;
}

.answer-who {
  display: flex;
  flex-direction: column;
}

.nick {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.time {
  color: #a8abb2;
  font-size: 12px;
}

.answer-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.answer-text {
  color: #4b4b4b;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  padding-left: 46px;
}
</style>
