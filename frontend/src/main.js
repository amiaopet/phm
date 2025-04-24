import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'
import 'echarts-gl/dist/echarts-gl.min.js'

// 设置axios默认基础URL
axios.defaults.baseURL = process.env.VUE_APP_API_URL || ''

// 从localStorage中获取会话ID
const sessionId = localStorage.getItem('sessionId')
if (sessionId) {
  axios.defaults.headers.common['Session-Id'] = sessionId
}

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response && error.response.status === 401) {
      // 未授权，清除用户信息并重定向到登录页面
      localStorage.removeItem('sessionId')
      localStorage.removeItem('username')
      router.push('/')
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册Element Plus图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局挂载echarts
app.config.globalProperties.$echarts = echarts

// 使用插件
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')