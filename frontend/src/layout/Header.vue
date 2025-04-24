<template>
  <div class="header">
    <div class="toggle-sidebar" @click="toggleSidebar">
      <el-icon :size="20">
        <Fold v-if="!isCollapse" />
        <Expand v-else />
      </el-icon>
    </div>
    <h2 class="header-title">{{ pageTitle }}</h2>
    <div class="user-info">
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="el-dropdown-link">
          {{ username }}<el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Fold, Expand } from '@element-plus/icons-vue'
import { logout } from '@/api/auth'

export default {
  name: 'AppHeader',
  components: {
    ArrowDown,
    Fold,
    Expand
  },
  props: {
    isCollapse: {
      type: Boolean,
      required: true
    },
    pageTitle: {
      type: String,
      required: true
    }
  },
  emits: ['toggle-sidebar'],
  setup(props, { emit }) {
    const router = useRouter()
    
    const username = computed(() => {
      return localStorage.getItem('username') || '用户'
    })
    
    const toggleSidebar = () => {
      emit('toggle-sidebar')
    }
    
    const handleCommand = async (command) => {
      if (command === 'logout') {
        const result = await logout()
        
        if (result.success) {
          ElMessage.success(result.message)
          router.push('/')
        } else {
          ElMessage.error(result.message)
        }
      }
    }
    
    return {
      username,
      toggleSidebar,
      handleCommand
    }
  }
}
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.toggle-sidebar {
  font-size: 20px;
  cursor: pointer;
  margin-right: 15px;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.user-info {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #606266;
}
</style>