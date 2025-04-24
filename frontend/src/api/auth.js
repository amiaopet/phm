import axios from 'axios'

// 登录
export async function login(username, password) {
  try {
    const response = await axios.post('/api/login', {
      username, 
      password
    })
    
    if (response.data.success) {
      // 设置全局请求头
      axios.defaults.headers.common['Session-Id'] = response.data.data.sessionId
    }
    
    return response.data
  } catch (error) {
    console.error('登录请求错误:', error)
    return {
      success: false,
      message: error.response?.data?.message || '登录请求失败'
    }
  }
}

// 登出
export async function logout() {
  try {
    // 清除全局请求头
    delete axios.defaults.headers.common['Session-Id']
    
    // 清除本地存储
    localStorage.removeItem('sessionId')
    localStorage.removeItem('username')
    
    return {
      success: true,
      message: '已退出登录'
    }
  } catch (error) {
    console.error('登出错误:', error)
    return {
      success: false,
      message: '登出失败'
    }
  }
}

// 检查登录状态
export function checkLoginStatus() {
  const sessionId = localStorage.getItem('sessionId')
  return !!sessionId
}