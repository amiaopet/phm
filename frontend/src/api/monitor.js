import axios from 'axios'

/**
 * 引气监控相关API调用
 */

/**
 * 获取用户配置
 * @returns {Promise} 请求Promise对象
 */
export const getUserConfig = () => {
  return axios.get('/api/config')
}

/**
 * 保存用户配置
 * @param {Object} config 配置对象
 * @returns {Promise} 请求Promise对象
 */
export const saveUserConfig = (config) => {
  return axios.post('/api/config', config)
}

/**
 * 启动引气监控任务
 * @param {Object} params 监控参数
 * @returns {Promise} 请求Promise对象
 */
export const startBleedMonitor = (params) => {
  return axios.post('/api/bleed-monitor', params)
}

/**
 * 启动氧气监控任务
 * @param {Object} params 监控参数
 * @returns {Promise} 请求Promise对象
 */
export const startOxygenMonitor = (params) => {
  return axios.post('/api/oxygen-monitor', params)
}

/**
 * 获取任务状态
 * @param {String} taskId 任务ID
 * @returns {Promise} 请求Promise对象
 */
export const getTaskStatus = (taskId) => {
  return axios.get(`/api/task/${taskId}`)
}

/**
 * 获取任务结果
 * @param {String} taskId 任务ID
 * @returns {Promise} 请求Promise对象
 */
export const getTaskResult = (taskId) => {
  return axios.get(`/api/task/${taskId}/result`)
}

/**
 * 保存引气监控设置
 * @param {Object} settings 引气监控设置
 * @returns {Promise} 请求Promise对象
 */
export const saveBleedSettings = (settings) => {
  return axios.post('/api/config', {
    bleedSettings: settings
  })
}

/**
 * 保存氧气监控设置
 * @param {Object} settings 氧气监控设置
 * @returns {Promise} 请求Promise对象
 */
export const saveOxygenSettings = (settings) => {
  return axios.post('/api/config', {
    oxygenSettings: settings
  })
}