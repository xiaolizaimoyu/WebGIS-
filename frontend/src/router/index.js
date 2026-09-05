// 路由配置（归属：前端 C）——统一管理页面跳转与登录守卫
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  // 登录 / 注册使用独立全屏布局（不套 MainLayout 外壳）
  {
    path: '/login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册' }
  },
  // 业务页面统一套 MainLayout 外壳（顶部导航）
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '首页' } },
      {
        path: 'publish',
        name: 'publish',
        component: () => import('@/views/PublishView.vue'),
        meta: { title: '发布', requiresAuth: true }
      },
      {
        path: 'publish/:id',
        name: 'publish-edit',
        component: () => import('@/views/PublishView.vue'),
        meta: { title: '编辑内容', requiresAuth: true }
      },
      {
        path: 'mine',
        name: 'mine',
        component: () => import('@/views/MineView.vue'),
        meta: { title: '我的发布', requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      {
        path: 'content/:id',
        name: 'detail',
        component: () => import('@/views/DetailView.vue'),
        meta: { title: '详情' }
      },
      // ====== 校园问答模块 ======
      {
        path: 'questions',
        name: 'questions',
        component: () => import('@/views/QuestionsView.vue'),
        meta: { title: '校园问答' }
      },
      {
        path: 'question/:id',
        name: 'question-detail',
        component: () => import('@/views/QuestionDetailView.vue'),
        meta: { title: '问题详情' }
      },
      {
        path: 'question/publish',
        name: 'question-publish',
        component: () => import('@/views/QuestionPublishView.vue'),
        meta: { title: '提出问题', requiresAuth: true }
      },
      // ====== 学习资料模块 ======
      {
        path: 'materials',
        name: 'materials',
        component: () => import('@/views/MaterialsView.vue'),
        meta: { title: '学习资料' }
      },
      {
        path: 'material/:id',
        name: 'material-detail',
        component: () => import('@/views/MaterialDetailView.vue'),
        meta: { title: '资料详情' }
      },
      {
        path: 'material/upload',
        name: 'material-upload',
        component: () => import('@/views/MaterialUploadView.vue'),
        meta: { title: '上传资料', requiresAuth: true }
      },
      // ====== 组队拼车模块 ======
      {
        path: 'carpool',
        name: 'carpool-list',
        component: () => import('@/views/CarpoolListView.vue'),
        meta: { title: '组队拼车' }
      },
      {
        path: 'carpool/publish',
        name: 'carpool-publish',
        component: () => import('@/views/CarpoolPublishView.vue'),
        meta: { title: '发布拼车', requiresAuth: true }
      },
      {
        path: 'carpool/:id',
        name: 'carpool-detail',
        component: () => import('@/views/CarpoolDetailView.vue'),
        meta: { title: '拼车详情' }
      },
      // ====== 失物招领模块 ======
      {
        path: 'lost-found',
        name: 'lost-found-list',
        component: () => import('@/views/LostFoundListView.vue'),
        meta: { title: '失物招领' }
      },
      {
        path: 'lost-found/publish',
        name: 'lost-found-publish',
        component: () => import('@/views/LostFoundPublishView.vue'),
        meta: { title: '发布失物招领', requiresAuth: true }
      },
      {
        path: 'lost-found/:id',
        name: 'lost-found-detail',
        component: () => import('@/views/LostFoundDetailView.vue'),
        meta: { title: '失物招领详情' }
      },
      // ====== 用户系统 ======
      {
        path: 'user/profile/:id',
        name: 'user-profile',
        component: () => import('@/views/UserProfileView.vue'),
        meta: { title: '用户主页' }
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/NotificationsView.vue'),
        meta: { title: '消息通知', requiresAuth: true }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫：需要登录的页面未登录时，跳登录页并记录回跳地址
router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})

// 动态更新浏览器标签标题
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 校园活动交流平台` : '校园活动交流平台'
})

export default router
