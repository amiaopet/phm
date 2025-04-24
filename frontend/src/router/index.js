import { createRouter, createWebHistory } from 'vue-router'

// 导入视图组件
const Login = () => import('../views/Login.vue')
const MainLayout = () => import('../layout/MainLayout.vue')
const BleedAirMonitor = () => import('../views/Tools/BleedAirMonitor.vue')
const OxygenMonitor = () => import('../views/Tools/OxygenMonitor.vue')
const CustomVisualization = () => import('../views/Tools/CustomVisualization.vue')
const FaultModel = () => import('../views/FaultDiagnosis/FaultModel.vue')
const EventOverview = () => import('../views/FaultPrediction/EventOverview.vue')
const TrendQAR = () => import('../views/FaultPrediction/TrendQAR.vue')
const TrendACARS = () => import('../views/FaultPrediction/TrendACARS.vue')
const TrendQARParams = () => import('../views/FaultPrediction/TrendQARParams.vue')
const QARModel = () => import('../views/ModelBuilding/QARModel.vue')
const ACARSModel = () => import('../views/ModelBuilding/ACARSModel.vue')
const QARParamSet = () => import('../views/ModelBuilding/QARParamSet.vue')
const FlightOverview = () => import('../views/FlightOverview.vue')
const AircraftDetail = () => import('../views/AircraftDetail.vue')

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/main',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/flight-overview'
      },
      // 航班动态
      {
        path: '/flight-overview',
        name: 'FlightOverview',
        component: FlightOverview,
        meta: { title: '航班动态' }
      },
      // 飞机详情页面
      {
        path: '/aircraft-detail/:acReg',
        name: 'AircraftDetail',
        component: AircraftDetail,
        meta: { title: '飞机详情' }
      },
      // 小工具相关路由
      {
        path: '/bleed-monitor',
        name: 'BleedAirMonitor',
        component: BleedAirMonitor,
        meta: { title: '引气监控', category: '小工具' }
      },
      {
        path: '/oxygen-monitor',
        name: 'OxygenMonitor',
        component: OxygenMonitor,
        meta: { title: '氧气监控', category: '小工具' }
      },
      {
        path: '/a320-mod-search',
        name: 'A320MODSearch',
        component: () => import('@/views/Tools/A320MODSearch.vue'),
        meta: { title: 'A320MOD查询', category: '小工具' }
      },
      {
        path: '/custom-visualization',
        name: 'CustomVisualization',
        component: CustomVisualization,
        meta: { title: '自定义可视化', category: '小工具' }
      },
      // 故障分析诊断相关路由
      {
        path: '/fault-model',
        name: 'FaultModel',
        component: FaultModel,
        meta: { title: '故障模型' }
      },
      // 故障预测预警相关路由
      {
        path: '/event-overview',
        name: 'EventOverview',
        component: EventOverview,
        meta: { title: '事件概览' }
      },
      {
        path: '/trend-qar',
        name: 'TrendQAR',
        component: TrendQAR,
        meta: { title: 'QAR趋势分析' }
      },
      {
        path: '/trend-acars',
        name: 'TrendACARS',
        component: TrendACARS,
        meta: { title: 'ACARS趋势分析' }
      },
      {
        path: '/trend-qar-params',
        name: 'TrendQARParams',
        component: TrendQARParams,
        meta: { title: 'QAR趋势分析参数' }
      },
      // 故障预测建模相关路由
      {
        path: '/qar-model',
        name: 'QARModel',
        component: QARModel,
        meta: { title: 'QAR模型' }
      },
      {
        path: '/acars-model',
        name: 'ACARSModel',
        component: ACARSModel,
        meta: { title: 'ACARS模型' }
      },
      {
        path: '/qar-param-set',
        name: 'QARParamSet',
        component: QARParamSet,
        meta: { title: 'QAR参数设置' }
      }
    ]
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = !!localStorage.getItem('sessionId')
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isLoggedIn) {
      // 未登录，重定向到登录页面
      next({
        path: '/',
        query: { redirect: to.fullPath }
      })
    } else {
      // 已登录，正常导航
      next()
    }
  } else {
    // 不需要身份验证的页面
    if (isLoggedIn && to.path === '/') {
      // 重定向到航班动态页面
      next({ path: '/flight-overview' })
    } else {
      // 正常导航
      next()
    }
  }
})

export default router