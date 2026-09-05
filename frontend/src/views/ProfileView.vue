<script setup>
// 个人中心页面（归属：前端 C）——签到 Tab、我的报名 Tab、关注/粉丝 Tab、积分展示
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getMockMyApplications, getMockFollowers, getMockFollowing } from '@/utils/mockData'

const router = useRouter()
const store = useUserStore()

const activeTab = ref('sign')
const myApplications = ref([])
const followers = ref([])
const following = ref([])

const signStatus = computed(() => store.signStatus)
const totalPoints = computed(() => store.signStatus?.totalPoints || 0)
const continuousDays = computed(() => store.signStatus?.continuousDays || 0)
const signedToday = computed(() => store.signStatus?.signedToday || false)

async function loadData() {
  await store.fetchSignStatus()
  // mock 数据
  myApplications.value = getMockMyApplications()
  followers.value = getMockFollowers(store.userInfo?.id)
  following.value = getMockFollowing(store.userInfo?.id)
}

async function handleSign() {
  if (signedToday.value) {
    ElMessage.info('今日已签到，明天再来吧')
    return
  }
  const result = await store.doSign()
  if (result) {
    ElMessage.success(`签到成功！获得 ${result.points} 积分，连续签到 ${result.continuousDays} 天`)
  }
}

function goToUserProfile(id) {
  router.push(`/user/profile/${id}`)
}

const applicationStatusMap = {
  pending: { label: '待确认', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' }
}

onMounted(loadData)
</script>

<template>
  <div class="profile-page">
    <!-- 用户信息头部 -->
    <el-card shadow="never" class="user-header-card">
      <div class="user-header">
        <el-avatar :size="80" class="user-avatar">
          {{ store.userInfo?.nickname?.slice(0, 1) || '?' }}
        </el-avatar>
        <div class="user-info">
          <h2 class="nickname">{{ store.userInfo?.nickname || '未登录用户' }}</h2>
          <p class="bio">{{ store.userInfo?.bio || '这个人很懒，什么都没留下' }}</p>
          <div class="user-stats">
            <div class="stat" @click="activeTab = 'following'">
              <span class="num">{{ following.length }}</span>
              <span class="label">关注</span>
            </div>
            <div class="stat" @click="activeTab = 'followers'">
              <span class="num">{{ followers.length }}</span>
              <span class="label">粉丝</span>
            </div>
            <div class="stat">
              <span class="num points">{{ totalPoints }}</span>
              <span class="label">积分</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="router.push('/mine')">📝 我的发布</el-button>
        </div>
      </div>
    </el-card>

    <!-- Tab 内容 -->
    <el-card shadow="never" class="tab-card">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <!-- 签到 Tab -->
        <el-tab-pane label="📅 每日签到" name="sign">
          <div class="sign-section">
            <div class="sign-banner">
              <div class="sign-info">
                <div class="sign-title">每日签到</div>
                <div class="sign-desc">连续签到 <span class="highlight">{{ continuousDays }}</span> 天 · 总积分 <span class="highlight">{{ totalPoints }}</span></div>
              </div>
              <el-button
                type="primary"
                size="large"
                :class="{ signed: signedToday }"
                :disabled="signedToday"
                :loading="store.signLoading"
                @click="handleSign"
              >
                {{ signedToday ? '✅ 今日已签' : '立即签到 +10' }}
              </el-button>
            </div>

            <div class="sign-calendar">
              <div class="calendar-title">最近签到记录</div>
              <div class="calendar-grid">
                <div
                  v-for="(record, i) in signStatus?.signRecords || []"
                  :key="i"
                  class="calendar-day"
                  :class="{ signed: record.points > 0 }"
                >
                  <div class="day-date">{{ record.date.slice(5) }}</div>
                  <div class="day-points">+{{ record.points }}</div>
                </div>
              </div>
            </div>

            <div class="points-rules">
              <div class="rules-title">🎁 积分规则</div>
              <ul>
                <li>每日签到 +10 积分</li>
                <li>连续签到 7 天额外奖励 +20 积分</li>
                <li>发布内容 +5 积分，被点赞 +1 积分</li>
                <li>回答问题被采纳 +20 积分</li>
                <li>上传资料通过审核 +15 积分</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <!-- 我的报名 Tab -->
        <el-tab-pane label="🚗 我的报名" name="applications">
          <div class="applications-section">
            <el-empty v-if="!myApplications.length" description="暂无报名记录" :image-size="100" />
            <div v-for="app in myApplications" :key="app.id" class="app-item" @click="router.push(`/carpool/${app.carpool_id}`)">
              <div class="app-info">
                <h4>{{ app.title }}</h4>
                <span class="app-time">报名时间：{{ new Date(app.apply_time).toLocaleString() }}</span>
              </div>
              <el-tag :type="applicationStatusMap[app.status]?.type" size="small">
                {{ applicationStatusMap[app.status]?.label }}
              </el-tag>
            </div>
          </div>
        </el-tab-pane>

        <!-- 关注 Tab -->
        <el-tab-pane :label="`👥 关注 (${following.length})`" name="following">
          <div class="follow-section">
            <el-empty v-if="!following.length" description="还没有关注任何人" :image-size="100" />
            <div v-for="u in following" :key="u.id" class="follow-item" @click="goToUserProfile(u.id)">
              <el-avatar :size="48">{{ u.nickname.slice(0, 1) }}</el-avatar>
              <div class="follow-info">
                <div class="follow-name">{{ u.nickname }}</div>
                <div class="follow-bio">{{ u.bio || '暂无简介' }}</div>
              </div>
              <el-button size="small">已关注</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 粉丝 Tab -->
        <el-tab-pane :label="`❤️ 粉丝 (${followers.length})`" name="followers">
          <div class="follow-section">
            <el-empty v-if="!followers.length" description="还没有粉丝" :image-size="100" />
            <div v-for="u in followers" :key="u.id" class="follow-item" @click="goToUserProfile(u.id)">
              <el-avatar :size="48">{{ u.nickname.slice(0, 1) }}</el-avatar>
              <div class="follow-info">
                <div class="follow-name">{{ u.nickname }}</div>
                <div class="follow-bio">{{ u.bio || '暂无简介' }}</div>
              </div>
              <el-button size="small" type="primary">回关</el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.user-header-card {
  border-radius: 12px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.user-header-card :deep(.el-card__body) {
  padding: 24px;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-avatar {
  background: #fff;
  color: #667eea;
  font-size: 32px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.nickname {
  color: #fff;
  font-size: 22px;
  margin: 0 0 4px 0;
}

.bio {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  margin: 0 0 12px 0;
}

.user-stats {
  display: flex;
  gap: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.stat .num {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.stat .num.points {
  color: #ffd700;
}

.stat .label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.header-actions {
  flex-shrink: 0;
}

.tab-card {
  border-radius: 12px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

/* 签到 */
.sign-section {
  padding: 0 10px;
}

.sign-banner {
  background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sign-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 6px;
}

.sign-desc {
  font-size: 14px;
  color: #606266;
}

.highlight {
  color: #f56c6c;
  font-weight: 700;
}

.sign-banner .el-button.signed {
  background: #67c23a;
  border-color: #67c23a;
}

.sign-calendar {
  margin-bottom: 20px;
}

.calendar-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.calendar-grid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-day {
  width: 70px;
  padding: 10px;
  border-radius: 10px;
  background: #f5f7fa;
  text-align: center;
  transition: all 0.2s;
}

.calendar-day.signed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: #fff;
}

.day-date {
  font-size: 13px;
  font-weight: 600;
}

.day-points {
  font-size: 11px;
  margin-top: 2px;
  opacity: 0.8;
}

.points-rules {
  background: #fdf6ec;
  border-radius: 10px;
  padding: 16px 20px;
}

.rules-title {
  font-weight: 600;
  color: #e6a23c;
  margin-bottom: 8px;
}

.points-rules ul {
  margin: 0;
  padding-left: 20px;
}

.points-rules li {
  font-size: 13px;
  color: #606266;
  line-height: 2;
}

/* 报名 */
.applications-section {
  min-height: 200px;
}

.app-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.app-item:hover {
  background: #ecf5ff;
  transform: translateX(4px);
}

.app-info h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  color: #303133;
}

.app-time {
  font-size: 12px;
  color: #909399;
}

/* 关注/粉丝 */
.follow-section {
  min-height: 200px;
}

.follow-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.follow-item:hover {
  background: #ecf5ff;
}

.follow-info {
  flex: 1;
  min-width: 0;
}

.follow-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.follow-bio {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
</style>
