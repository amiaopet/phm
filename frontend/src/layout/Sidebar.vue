<template>
  <div class="sidebar" :class="isCollapse ? 'sidebar-collapsed' : 'sidebar-expanded'">
    <div class="menu-logo">
      <img :src="isCollapse ? 'logo-small.png' : 'logo.png'" alt="Logo">
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      router
      @select="handleMenuSelect">
      
      <!-- 航班动态 -->
      <el-menu-item index="flight-overview" route="/flight-overview">
        <el-icon><LocationInformation /></el-icon>
        <template #title>航班动态</template>
      </el-menu-item>
      
      <!-- 故障分析诊断相关菜单 -->
      <el-sub-menu index="fault-diagnosis">
        <template #title>
          <el-icon><Warning /></el-icon>
          <span>故障分析诊断</span>
        </template>
        <el-menu-item index="fault-model" route="/fault-model">
          <el-icon><Document /></el-icon>
          <template #title>故障模型</template>
        </el-menu-item>
      </el-sub-menu>

      <!-- 故障预测预警相关菜单 -->
      <el-sub-menu index="fault-prediction">
        <template #title>
          <el-icon><Histogram /></el-icon>
          <span>故障预测预警</span>
        </template>
        <el-menu-item index="event-overview" route="/event-overview">
          <el-icon><Calendar /></el-icon>
          <template #title>事件概览</template>
        </el-menu-item>
        <el-menu-item index="trend-qar" route="/trend-qar">
          <el-icon><TrendCharts /></el-icon>
          <template #title>QAR趋势分析</template>
        </el-menu-item>
        <el-menu-item index="trend-acars" route="/trend-acars">
          <el-icon><Connection /></el-icon>
          <template #title>ACARS趋势分析</template>
        </el-menu-item>
        <el-menu-item index="trend-qar-params" route="/trend-qar-params">
          <el-icon><Setting /></el-icon>
          <template #title>QAR趋势分析参数</template>
        </el-menu-item>
      </el-sub-menu>

      <!-- 故障预测建模相关菜单 -->
      <el-sub-menu index="model-building">
        <template #title>
          <el-icon><Cpu /></el-icon>
          <span>故障预测建模</span>
        </template>
        <el-menu-item index="qar-model" route="/qar-model">
          <el-icon><Monitor /></el-icon>
          <template #title>QAR模型</template>
        </el-menu-item>
        <el-menu-item index="acars-model" route="/acars-model">
          <el-icon><Platform /></el-icon>
          <template #title>ACARS模型</template>
        </el-menu-item>
        <el-menu-item index="qar-param-set" route="/qar-param-set">
          <el-icon><Tools /></el-icon>
          <template #title>QAR参数集合管理</template>
        </el-menu-item>
      </el-sub-menu>
      
      <!-- 小工具模块 -->
      <el-sub-menu index="tools">
        <template #title>
          <el-icon><Tools /></el-icon>
          <span>小工具</span>
        </template>
        <el-menu-item index="bleedmonitor" route="/bleed-monitor">
          <el-icon><DataLine /></el-icon>
          <template #title>引气监控</template>
        </el-menu-item>
        <el-menu-item index="oxygenmonitor" route="/oxygen-monitor">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>氧气监控</template>
        </el-menu-item>
        <el-menu-item index="a320modsearch" route="/a320-mod-search">
          <el-icon><Search /></el-icon>
          <template #title>A320MOD查询</template>
        </el-menu-item>
        <el-menu-item index="customvisualization" route="/custom-visualization">
          <el-icon><PieChart /></el-icon>
          <template #title>自定义可视化</template>
        </el-menu-item>
      </el-sub-menu>
    </el-menu>
    
    <!-- 侧边栏折叠按钮 -->
    <div class="sidebar-toggle" @click="toggleSidebar">
      <el-icon :size="20">
        <Fold v-if="!isCollapse" />
        <Expand v-else />
      </el-icon>
    </div>
  </div>
</template>

<script>
import { 
  DataLine, DataAnalysis, Warning, Histogram, Calendar,
  TrendCharts, Connection, Document, Cpu, Monitor, Platform, Setting,
  Tools, LocationInformation, Fold, Expand, Search, PieChart
} from '@element-plus/icons-vue'

export default {
  name: 'AppSidebar',
  components: {
    DataLine,
    DataAnalysis,
    Warning,
    Histogram,
    Calendar,
    TrendCharts,
    Connection,
    Document,
    Cpu,
    Monitor,
    Platform,
    Setting,
    Tools,
    LocationInformation,
    Fold,
    Expand,
    Search,
    PieChart
  },
  props: {
    isCollapse: {
      type: Boolean,
      required: true
    },
    activeMenu: {
      type: String,
      default: 'flight-overview'
    }
  },
  emits: ['menu-select', 'toggle-sidebar'],
  setup(props, { emit }) {
    const handleMenuSelect = (key) => {
      emit('menu-select', key)
    }
    
    const toggleSidebar = () => {
      emit('toggle-sidebar')
    }
    
    return {
      handleMenuSelect,
      toggleSidebar
    }
  }
}
</script>

<style scoped>
.sidebar {
  transition: width 0.3s;
  background-color: #304156;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-collapsed {
  width: 64px;
}

.sidebar-expanded {
  width: 200px;
}

.menu-logo {
  padding: 10px 0;
  margin-bottom: 20px;
  text-align: center;
  height: 60px;
  line-height: 60px;
  background-color: #263445;
}

.menu-logo img {
  height: 40px;
  width: auto;
  vertical-align: middle;
}

.el-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

:deep(.el-sub-menu__title) {
  &:hover {
    background-color: #263445 !important;
  }
}

:deep(.el-menu-item) {
  &:hover {
    background-color: #263445 !important;
  }
  
  &.is-active {
    background-color: #263445 !important;
  }
}

.sidebar-toggle {
  height: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: #bfcbd9;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-toggle:hover {
  background-color: #263445;
}
</style>