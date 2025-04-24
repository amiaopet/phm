/**
 * 日期工具函数
 */

/**
 * 获取当前日期的字符串表示，格式为 YYYY-MM-DD
 * @returns {String} 当前日期的字符串表示
 */
export const getCurrentDate = () => {
  const date = new Date()
  return date.toISOString().split('T')[0]
}

/**
 * 获取指定天数前的日期，格式为 YYYY-MM-DD
 * @param {Number} days 天数
 * @returns {String} 指定天数前的日期字符串
 */
export const getDateBefore = (days) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

/**
 * 获取指定月数前的日期，格式为 YYYY-MM-DD
 * @param {Number} months 月数
 * @returns {String} 指定月数前的日期字符串
 */
export const getDateMonthsBefore = (months) => {
  const date = new Date()
  date.setMonth(date.getMonth() - months)
  return date.toISOString().split('T')[0]
}

/**
 * 根据指定的日期范围类型获取开始和结束日期
 * @param {String} rangeType 日期范围类型，如"一周"，"一个月"，"三个月"等
 * @returns {Array} 包含开始和结束日期的数组 [startDate, endDate]
 */
export const getDateRangeByType = (rangeType) => {
  const endDate = getCurrentDate()
  let startDate = endDate
  
  switch (rangeType) {
    case '最近一天':
      startDate = getDateBefore(1)
      break
    case '一周':
    case '最近七天':
      startDate = getDateBefore(7)
      break
    case '最近十四天':
      startDate = getDateBefore(14)
      break
    case '一个月':
    case '最近三十天':
      startDate = getDateMonthsBefore(1)
      break
    case '三个月':
      startDate = getDateMonthsBefore(3)
      break
    case '半年':
      startDate = getDateMonthsBefore(6)
      break
    default:
      startDate = getDateBefore(3)
  }
  
  return [startDate, endDate]
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param {Date} date 日期对象
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date) {
  if (!date) return ''
  
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

/**
 * 将时间对象格式化为字符串，格式为 HH:MM
 * @param {Date} date 时间对象
 * @returns {String} 格式化后的时间字符串
 */
export const formatTime = (date) => {
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * 格式化日期时间为 YYYY-MM-DD HH:MM:SS 格式
 * @param {Date|string} dateTime 日期对象或日期字符串
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(dateTime) {
  if (!dateTime) return ''
  
  const date = typeof dateTime === 'string' ? new Date(dateTime) : dateTime
  
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const seconds = date.getSeconds().toString().padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 解析日期字符串，格式为 YYYY-MM-DD
 * @param {String} dateStr 日期字符串
 * @returns {Date} 解析后的日期对象
 */
export const parseDate = (dateStr) => {
  const [year, month, day] = dateStr.split('-').map(num => parseInt(num, 10))
  return new Date(year, month - 1, day)
}

/**
 * 计算两个日期之间的天数差
 * @param {String|Date} date1 第一个日期
 * @param {String|Date} date2 第二个日期
 * @returns {Number} 天数差
 */
export const daysBetween = (date1, date2) => {
  const d1 = date1 instanceof Date ? date1 : parseDate(date1)
  const d2 = date2 instanceof Date ? date2 : parseDate(date2)
  
  // 复制日期，以避免修改原始日期
  const copy1 = new Date(d1.getTime())
  const copy2 = new Date(d2.getTime())
  
  // 重置时间部分以确保只计算日期差异
  copy1.setHours(0, 0, 0, 0)
  copy2.setHours(0, 0, 0, 0)
  
  // 计算毫秒差，然后转换为天数
  const diffTime = Math.abs(copy2 - copy1)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return diffDays
}