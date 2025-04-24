<template>
  <div class="main-container">
    <!-- 侧边栏 -->
    <AppSidebar 
      :is-collapse="isCollapse" 
      :active-menu="activeMenu" 
      @menu-select="handleMenuSelect"
      @toggle-sidebar="toggleSidebar"
    />
    
    <!-- 内容区域 -->
    <div class="content-container">
      <!-- 顶部栏：包含标签导航和用户信息 -->
      <div class="content-header">
        <!-- 标签导航 -->
        <div class="tabs-container">
          <el-tabs 
            v-model="activeTab" 
            type="card" 
            closable 
            @tab-remove="removeTab"
            @tab-click="clickTab">
            <el-tab-pane
              v-for="item in visitedViews"
              :key="item.path"
              :label="item.title"
              :name="item.path">
            </el-tab-pane>
          </el-tabs>
        </div>
        
        <!-- 用户信息 -->
        <div class="user-info">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="el-dropdown-link">
              {{ username }}<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <div class="content-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import AppSidebar from './Sidebar.vue'

export default {
  name: 'MainLayout',
  components: {
    AppSidebar,
    ArrowDown
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const isCollapse = ref(false)
    const activeMenu = ref('flight-overview')
    const pageTitle = ref('航班动态')
    const username = ref(localStorage.getItem('username') || '用户')
    
    // 已访问的视图记录
    const visitedViews = ref([
      { path: '/flight-overview', title: '航班动态' }
    ])
    
    // 当前激活的标签
    const activeTab = ref('/flight-overview')
    
    // 添加已访问视图
    const addVisitedView = (view) => {
      // 如果已存在相同路径的视图，则不重复添加
      if (visitedViews.value.some(v => v.path === view.path)) return
      
      // 添加新视图
      visitedViews.value.push(Object.assign({}, view))
      
      // 激活新添加的标签
      activeTab.value = view.path
    }
    
    // 监听路由变化，同步激活的菜单项
    watch(() => route.path, (path) => {
      // 找到当前路由对应的路由配置
      const currentRoute = router.getRoutes().find(route => route.path === path)
      
      if (currentRoute) {
        let title = currentRoute.meta.title || '未知页面'
        
        // 特殊处理飞机详情页面，将飞机号作为标签名
        if (path.startsWith('/aircraft-detail/') && route.params.acReg) {
          title = `${route.params.acReg}` // 使用飞机号作为标签名
        }
        
        // 设置页面标题
        pageTitle.value = title
        
        // 根据路径格式，获取对应的菜单索引
        // 如果是飞机详情页，保持航班动态菜单为激活状态
        if (path.startsWith('/aircraft-detail/')) {
          activeMenu.value = 'flight-overview'
        } else {
          const menuKey = path.substring(1).replace(/-/g, '')
          activeMenu.value = menuKey
        }
        
        // 添加到已访问视图
        addVisitedView({
          path: path,
          title: title
        })
      }
    }, { immediate: true })
    
    // 移除标签
    const removeTab = (targetPath) => {
      // 找到要删除的标签索引
      const index = visitedViews.value.findIndex(item => item.path === targetPath)
      
      // 如果找到了对应标签
      if (index !== -1) {
        // 如果删除的是当前激活的标签，需要激活其他标签
        if (activeTab.value === targetPath) {
          // 优先激活右侧标签，如果没有右侧标签，则激活左侧标签
          const nextTab = visitedViews.value[index + 1] || visitedViews.value[index - 1]
          
          if (nextTab) {
            activeTab.value = nextTab.path
            router.push(nextTab.path)
          }
        }
        
        // 从已访问视图中移除
        visitedViews.value.splice(index, 1)
      }
      
      // 航班动态
      if (visitedViews.value.length === 0) {
        router.push('/flight-overview')
      }
    }
    
    // 点击标签
    const clickTab = (tab) => {
      // 导航到对应路由
      router.push(tab.props.name)
    }
    
    // 切换侧边栏展开/折叠状态
    const toggleSidebar = () => {
      isCollapse.value = !isCollapse.value
    }
    
    // 处理菜单选择
    const handleMenuSelect = (key) => {
      // 根据菜单索引构造对应的路由路径
      let path = ''
      
      switch (key) {
        case 'flight-overview':
          path = '/flight-overview'
          break
        case 'bleedmonitor':
          path = '/bleed-monitor'
          break
        case 'oxygenmonitor':
          path = '/oxygen-monitor'
          break
        case 'a320modsearch':
          path = '/a320-mod-search'
          break
        case 'customvisualization':
          path = '/custom-visualization'
          break
        case 'fault-model':
          path = '/fault-model'
          break
        case 'event-overview':
          path = '/event-overview'
          break
        case 'trend-qar':
          path = '/trend-qar'
          break
        case 'trend-acars':
          path = '/trend-acars'
          break
        case 'trend-qar-params':
          path = '/trend-qar-params'
          break
        case 'qar-model':
          path = '/qar-model'
          break
        case 'acars-model':
          path = '/acars-model'
          break
        case 'qar-param-set':
          path = '/qar-param-set'
          break
      }
      
      // 导航到对应路由
      if (path) {
        router.push(path)
      }
    }
    
    // 处理下拉菜单命令
    const handleCommand = (command) => {
      if (command === 'logout') {
        // 清除本地存储的会话信息
        localStorage.removeItem('sessionId')
        localStorage.removeItem('username')
        
        // 导航到登录页面
        router.push('/')
      }
    }
    
    return {
      isCollapse,
      activeMenu,
      pageTitle,
      username,
      visitedViews,
      activeTab,
      toggleSidebar,
      handleMenuSelect,
      handleCommand,
      removeTab,
      clickTab
    }
  }
}
</script>

<style scoped>
.main-container {
  height: 100vh;
  display: flex;
}

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.content-header {
  display: flex;
  align-items: center;
  padding: 0 15px;
  height: 50px;
  background-color: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.tabs-container {
  flex: 1;
  overflow: hidden;
  min-width: 0; /* 确保容器可以缩小 */
}

.user-info {
  display: flex;
  align-items: center;
  margin-left: 15px;
  white-space: nowrap;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #606266;
}

.content-main {
  flex: 1;
  padding: 20px;
  overflow: auto;
  background-color: #f5f7fa;
}

:deep(.el-tabs__nav-wrap) {
  padding-left: 0;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none; /* 移除底部线条 */
}

:deep(.el-tabs__nav-scroll) {
  overflow-x: auto; /* 启用水平滚动 */
}

:deep(.el-tabs__nav) {
  white-space: nowrap; /* 确保标签不换行 */
  position: relative;
  transition: transform 0.3s;
}

:deep(.el-tabs__item) {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
}

:deep(.el-tabs__item.is-active) {
  font-weight: bold;
}

/* 自定义滚动条样式 */
:deep(.el-tabs__nav-scroll::-webkit-scrollbar) {
  height: 4px;
}

:deep(.el-tabs__nav-scroll::-webkit-scrollbar-thumb) {
  background: rgba(144, 147, 153, 0.3);
  border-radius: 4px;
}

:deep(.el-tabs__nav-scroll::-webkit-scrollbar-track) {
  background: transparent;
}
</style>