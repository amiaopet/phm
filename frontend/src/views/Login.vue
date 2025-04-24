<template>
  <div class="login-container">
    <div class="login-box">
      <div class="logo-container">
        <img src="@/assets/logo.png" alt="Logo">
      </div>
      <h2 class="login-title">飞机监控系统</h2>
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username" label="用户名">
          <el-input v-model="loginForm.username" placeholder="请输入用户名">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password" label="密码">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password @keyup.enter="submitLogin">
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-button" :loading="loginLoading" @click="submitLogin">登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { User, Lock } from '@element-plus/icons-vue'

export default {
  name: 'Login',
  components: {
    User,
    Lock
  },
  setup() {
    const loginFormRef = ref(null)
    const router = useRouter()
    const route = useRoute()
    
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    const loginRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }
    
    const loginLoading = ref(false)
    
    const submitLogin = async () => {
      try {
        if (!loginFormRef.value) return
        
        await loginFormRef.value.validate()
        
        loginLoading.value = true
        
        const response = await axios.post('/api/login', {
          username: loginForm.username,
          password: loginForm.password
        })
        
        if (response.data.success) {
          handleLoginSuccess(response.data.data.sessionId, loginForm.username)
          ElMessage.success('登录成功')
        } else {
          ElMessage.error(response.data.message || '登录失败')
        }
      } catch (error) {
        console.error('登录错误:', error)
        ElMessage.error(error.response?.data?.message || '登录失败')
      } finally {
        loginLoading.value = false
      }
    }
    
    const handleLoginSuccess = (sessionId, username) => {
      localStorage.setItem('sessionId', sessionId)
      localStorage.setItem('username', username)
      
      // 设置 axios 默认请求头
      axios.defaults.headers.common['Session-Id'] = sessionId
      
      // 检查是否有重定向
      const redirectPath = route.query.redirect || '/flight-overview'
      router.push(redirectPath)
    }
    
    return {
      loginFormRef,
      loginForm,
      loginRules,
      loginLoading,
      submitLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-image: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%);
}

.login-box {
  width: 400px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
  box-sizing: border-box;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #409EFF;
  font-weight: 500;
}

.logo-container {
  text-align: center;
  margin-bottom: 20px;
}

.logo-container img {
  width: 100px;
  height: auto;
}

.login-form :deep(.el-form-item__label) {
  color: #606266;
}

.login-button {
  width: 100%;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .login-box {
    width: 90%;
    max-width: 400px;
  }
}
</style>