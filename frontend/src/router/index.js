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
        meta: { title: '发布', requiresAuth: true } // 未登录访问会被拦截到登录页
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
      }
      // TODO(前端C/后续)：会员中心、我的发布等页面在 children 中追加
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
