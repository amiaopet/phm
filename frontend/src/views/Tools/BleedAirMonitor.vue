<template>
  <div class="bleed-monitor-container">
    <el-card class="monitor-section">
      <template #header>
        <div class="card-header">
          <span>引气监控设置（IAE取发动机预冷器出口压力/CFM取巡航引气压力）</span>
        </div>
      </template>
      <el-form :model="bleedForm" label-width="100px" class="settings-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="飞机类型">
              <el-radio-group v-model="bleedForm.aircraftType">
                <el-radio value="CFM">CFM</el-radio>
                <el-radio value="V2500">V2500</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="飞机号">
              <el-select v-model="bleedForm.aircraftNo" placeholder="请选择飞机号">
                <el-option label="全部" value="全部"></el-option>
                <el-option v-for="ac in filteredAircraftList" :key="ac" :label="ac" :value="ac"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="数据范围">
              <el-select v-model="bleedForm.dateRange" placeholder="请选择日期范围" @change="handleDateRangeChange">
                <el-option label="一周" value="一周"></el-option>
                <el-option label="一个月" value="一个月"></el-option>
                <el-option label="三个月" value="三个月"></el-option>
                <el-option label="半年" value="半年"></el-option>
                <el-option label="自定义" value="自定义"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" v-if="bleedForm.dateRange === '自定义'">
            <el-form-item label="日期区间">
              <el-date-picker
                v-model="bleedForm.dateRangeValue"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD">
              </el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item :label="bleedForm.aircraftType + '压力阈值'">
              <el-input-number v-model="bleedForm.thresholdValue" :min="0" :max="100" :step="1"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="接收员工号">
              <el-input v-model="bleedForm.employees" placeholder="多个员工号用英文逗号分隔"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="接收邮箱">
              <el-input v-model="bleedForm.emailRecipients" placeholder="多个邮箱用英文逗号分隔"></el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用自动运行">
              <el-switch v-model="bleedForm.autoRun.enabled"></el-switch>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="bleedForm.autoRun.enabled">
          <el-col :xs="24" :sm="12">
            <el-form-item label="每天运行时间">
              <el-time-picker
                v-model="bleedForm.autoRun.time"
                format="HH:mm"
                placeholder="选择时间"
                style="width: 150px;">
              </el-time-picker>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="运行数据范围">
              <el-select v-model="bleedForm.autoRun.dateRange" placeholder="请选择日期范围">
                <el-option label="最近一天" value="最近一天"></el-option>
                <el-option label="一周" value="一周"></el-option>
                <el-option label="一个月" value="一个月"></el-option>
                <el-option label="三个月" value="三个月"></el-option>
                <el-option label="半年" value="半年"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="startBleedMonitoring" :loading="bleedMonitorLoading">开始分析</el-button>
          <el-button @click="saveBleedSettings">保存设置</el-button>
          <el-button type="success" @click="exportBleedData" :disabled="!bleedResults.length">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 引气监控结果展示 -->
    <el-card v-if="bleedMonitorTask" class="monitor-section">
      <template #header>
        <div class="card-header">
          <span>监控进度</span>
        </div>
      </template>
      <div class="progress-info">
        <el-progress :percentage="bleedMonitorTask.progress" :status="getProgressStatus(bleedMonitorTask.status)"></el-progress>
        <p>{{ bleedMonitorTask.message }}</p>
      </div>
    </el-card>
    
    <el-card v-if="bleedResults.length" class="result-table">
      <template #header>
        <div class="card-header">
          <span>监控结果</span>
        </div>
      </template>
      <el-table :data="bleedResults" style="width: 100%" border :row-class-name="getBleedRowClass">
        <el-table-column prop="acno" label="飞机号" width="100"></el-table-column>
        <el-table-column label="T1平均值" width="120">
          <template #default="scope">
            <span :class="{ 'abnormal-row': scope.row.t1_avg <= bleedForm.thresholdValue }">
              {{ scope.row.t1_avg.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="T2平均值" width="120">
          <template #default="scope">
            <span :class="{ 'abnormal-row': scope.row.t2_avg <= bleedForm.thresholdValue }">
              {{ scope.row.t2_avg.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="T1最大值航班" width="200">
          <template #default="scope">
            <div v-if="scope.row.max_flights && scope.row.max_flights.length">
              <div v-for="flight in scope.row.max_flights.filter(f => f.type === 'T1')" :key="flight.flight_no">
                {{ flight.flight_no }} ({{ flight.date }})
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="T2最大值航班" width="200">
          <template #default="scope">
            <div v-if="scope.row.max_flights && scope.row.max_flights.length">
              <div v-for="flight in scope.row.max_flights.filter(f => f.type === 'T2')" :key="flight.flight_no">
                {{ flight.flight_no }} ({{ flight.date }})
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getBleedStatusType(scope.row, bleedForm.thresholdValue)">
              {{ getBleedStatusLabel(scope.row, bleedForm.thresholdValue) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="viewBleedDetail(scope.row)" v-if="scope.row.all_flights && scope.row.all_flights.length">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 引气监控详情对话框 -->
    <el-dialog v-model="bleedDetailVisible" title="航班详情" width="80%">
      <el-table :data="currentBleedDetail.all_flights" style="width: 100%" border>
        <el-table-column prop="flight_no" label="航班号" width="120"></el-table-column>
        <el-table-column prop="date" label="日期" width="120"></el-table-column>
        <el-table-column prop="time" label="时间" width="100"></el-table-column>
        <el-table-column prop="dep_station" label="始发站" width="100"></el-table-column>
        <el-table-column prop="arr_station" label="目的站" width="100"></el-table-column>
        <el-table-column prop="t1" label="T1" width="80"></el-table-column>
        <el-table-column prop="t2" label="T2" width="80"></el-table-column>
        <el-table-column prop="s_line" label="S行" width="80"></el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getTaskStatus, getTaskResult } from '@/api/monitor'

export default {
  name: 'BleedAirMonitor',
  
  setup() {
    // CFM飞机列表
    const cfmAircraftList = [
      'B-1645', 'B-1646', 'B-1647', 'B-1681', 'B-1808', 'B-1857', 'B-1870',
      'B-1871', 'B-1872', 'B-304G', 'B-304H', 'B-6572', 'B-6640', 'B-6717',
      'B-6735', 'B-6736', 'B-6787', 'B-6788', 'B-6860', 'B-6861', 'B-6901',
      'B-6921', 'B-6922', 'B-6948', 'B-6949', 'B-6962', 'B-6963', 'B-6965',
      'B-6966', 'B-8035', 'B-8036', 'B-8068', 'B-8235', 'B-8236', 'B-8317',
      'B-8408', 'B-8536', 'B-8538', 'B-9957', 'B-9978'
    ]
    
    // V2500飞机列表
    const v2500AircraftList = [
      'B-1001', 'B-1002', 'B-1003', 'B-1005', 'B-1006', 'B-8315', 'B-8407',
      'B-8457', 'B-8458', 'B-8459', 'B-8537', 'B-8539', 'B-8540', 'B-8587',
      'B-8955', 'B-8956', 'B-8957'
    ]
    
    // 引气监控相关状态
    const bleedForm = reactive({
      aircraftType: 'CFM',
      aircraftNo: '全部',
      dateRange: '三个月',
      dateRangeValue: [],
      thresholdValue: 38,
      employees: '',
      emailRecipients: '',
      autoRun: {
        enabled: false,
        time: null,
        dateRange: '三个月'
      }
    })
    
    const bleedMonitorLoading = ref(false)
    const bleedMonitorTask = ref(null)
    const bleedResults = ref([])
    const bleedDetailVisible = ref(false)
    const currentBleedDetail = ref({})
    
    // 轮询定时器
    const pollTimers = ref({})
    
    // 根据当前选择的机型筛选飞机列表
    const filteredAircraftList = computed(() => {
      return bleedForm.aircraftType === 'CFM' ? cfmAircraftList : v2500AircraftList
    })
    
    // 日期范围相关方法
    const handleDateRangeChange = () => {
      if (bleedForm.dateRange !== '自定义') {
        const end = new Date()
        let start = new Date()
        
        switch (bleedForm.dateRange) {
          case '最近一天':
            start.setDate(end.getDate() - 1)
            break
          case '一周':
            start.setDate(end.getDate() - 7)
            break
          case '一个月':
            start.setMonth(end.getMonth() - 1)
            break
          case '三个月':
            start.setMonth(end.getMonth() - 3)
            break
          case '半年':
            start.setMonth(end.getMonth() - 6)
            break
        }
        
        bleedForm.dateRangeValue = [
          start.toISOString().split('T')[0],
          end.toISOString().split('T')[0]
        ]
      }
    }
    
    // 保存设置
    const saveBleedSettings = async () => {
      try {
        // 保存引气监控相关设置
        const settings = {
          bleedSettings: {
            cfmThreshold: bleedForm.aircraftType === 'CFM' ? bleedForm.thresholdValue : undefined,
            v2500Threshold: bleedForm.aircraftType === 'V2500' ? bleedForm.thresholdValue : undefined,
            employees: bleedForm.employees,
            emailRecipients: bleedForm.emailRecipients,
            autoRun: {
              enabled: bleedForm.autoRun.enabled,
              hour: bleedForm.autoRun.time ? bleedForm.autoRun.time.getHours().toString().padStart(2, '0') : '08',
              minute: bleedForm.autoRun.time ? bleedForm.autoRun.time.getMinutes().toString().padStart(2, '0') : '00',
              dateRange: bleedForm.autoRun.dateRange || '三个月'
            }
          }
        }
        
        const response = await axios.post('/api/config', settings)
        
        if (response.data.success) {
          ElMessage.success('引气监控设置已保存')
        } else {
          ElMessage.error(response.data.message || '保存设置失败')
        }
      } catch (error) {
        console.error('保存设置错误:', error)
        ElMessage.error(error.response?.data?.message || '保存设置失败')
      }
    }
    
    // 开始监控
    const startBleedMonitoring = async () => {
      // 确保有日期范围
      if (bleedForm.dateRange === '自定义' && (!bleedForm.dateRangeValue || bleedForm.dateRangeValue.length !== 2)) {
        ElMessage.warning('请选择日期范围')
        return
      }
      
      // 如果没有选择日期范围，设置默认三个月
      if (bleedForm.dateRange !== '自定义' && (!bleedForm.dateRangeValue || bleedForm.dateRangeValue.length !== 2)) {
        handleDateRangeChange()
      }
      
      try {
        bleedMonitorLoading.value = true
        bleedResults.value = []
        
        const [startDate, endDate] = bleedForm.dateRangeValue
        
        const response = await axios.post('/api/bleed-monitor', {
          aircraftType: bleedForm.aircraftType,
          aircraftNo: bleedForm.aircraftNo,
          startDate,
          endDate,
          thresholdValue: bleedForm.thresholdValue,
          employees: bleedForm.employees,
          emailRecipients: bleedForm.emailRecipients,
          autoRun: {
            enabled: bleedForm.autoRun.enabled,
            time: bleedForm.autoRun.time,
            dateRange: bleedForm.autoRun.dateRange
          }
        })
        
        if (response.data.success) {
          ElMessage.success('引气监控任务已启动')
          const taskId = response.data.data.taskId
          
          // 保存任务状态并开始轮询
          bleedMonitorTask.value = {
            taskId,
            status: 'running',
            progress: 0,
            message: '开始分析任务...'
          }
          
          // 开始轮询任务状态
          pollTaskStatus(taskId)
        } else {
          ElMessage.error(response.data.message || '启动监控任务失败')
        }
      } catch (error) {
        console.error('启动监控任务错误:', error)
        ElMessage.error(error.response?.data?.message || '启动监控任务失败')
      } finally {
        bleedMonitorLoading.value = false
      }
    }
    
    // 轮询任务状态
    const pollTaskStatus = (taskId) => {
      // 如果已有定时器，先清除
      if (pollTimers.value[taskId]) {
        clearInterval(pollTimers.value[taskId])
      }
      
      console.log(`开始轮询任务 ${taskId} 的状态...`)
      
      // 设置最大轮询次数和错误计数器
      let pollCount = 0
      let errorCount = 0
      const maxPollCount = 30 // 最多轮询30次（约1分钟）
      const maxErrorCount = 3 // 最多连续出错3次
      
      // 创建轮询定时器
      pollTimers.value[taskId] = setInterval(async () => {
        try {
          pollCount++
          console.log(`轮询任务 ${taskId} 的状态...第${pollCount}次`)
          
          // 如果超过最大次数，停止轮询
          if (pollCount > maxPollCount) {
            console.error(`轮询任务 ${taskId} 超过最大次数，停止轮询`)
            ElMessage.warning('任务状态查询超时，请稍后在历史记录中查看结果')
            clearInterval(pollTimers.value[taskId])
            delete pollTimers.value[taskId]
            return
          }
          
          // 尝试直接获取任务结果而不是先获取状态
          // 如果任务已完成，这会直接获取结果；如果任务未完成，API会返回相应错误
          try {
            console.log(`尝试直接获取任务 ${taskId} 的结果...`)
            const resultResponse = await getTaskResult(taskId)
            
            if (resultResponse.data.success) {
              console.log('任务已完成，成功获取结果:', resultResponse.data)
              
              // 更新任务状态
              bleedMonitorTask.value = {
                taskId,
                status: 'completed',
                progress: 100,
                message: '分析任务已完成'
              }
              
              // 保存结果
              bleedResults.value = resultResponse.data.data.results || []
              
              // 更新阈值
              const threshold = resultResponse.data.data.threshold || bleedForm.thresholdValue
              
              // 安全地更新结果中的阈值
              if (Array.isArray(bleedResults.value)) {
                bleedResults.value.forEach(result => {
                  if (result && typeof result === 'object') {
                    result.threshold = threshold
                  }
                })
              }
              
              console.log(`成功加载 ${bleedResults.value.length} 条结果数据:`, bleedResults.value)
              
              if (bleedResults.value.length > 0) {
                ElMessage.success('引气监控分析完成')
              } else {
                ElMessage.info('引气监控分析完成，但没有找到相关数据')
              }
              
              // 停止轮询
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
              return
            }
          } catch (resultError) {
            // 忽略这个错误，任务可能尚未完成
            console.log(`任务 ${taskId} 可能尚未完成，继续轮询状态`)
          }
          
          // 如果无法获取结果，继续获取任务状态
          const response = await getTaskStatus(taskId)
          
          // 重置错误计数
          errorCount = 0
          
          if (response.data.success) {
            const taskData = response.data.data
            
            // 更新任务状态
            bleedMonitorTask.value = {
              taskId,
              status: taskData.status,
              progress: taskData.progress,
              message: taskData.message
            }
            
            console.log(`任务状态更新: ${taskData.status}, 进度: ${taskData.progress}%, 消息: ${taskData.message}`)
            
            // 如果任务完成，获取结果
            if (taskData.status === 'completed') {
              console.log('任务已完成，正在获取结果...')
              
              // 停止轮询
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
              
              // 获取结果
              fetchTaskResult(taskId)
            } else if (taskData.status === 'error') {
              console.error(`监控任务出错: ${taskData.message}`)
              ElMessage.error(`监控任务出错: ${taskData.message}`)
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
            }
          } else {
            console.error('获取任务状态失败:', response.data.message)
            ElMessage.error(`获取任务状态失败: ${response.data.message}`)
            
            // 增加错误计数
            errorCount++
            if (errorCount >= maxErrorCount) {
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
            }
          }
        } catch (error) {
          console.error('轮询任务状态错误:', error)
          
          // 增加错误计数
          errorCount++
          
          // 如果连续出错达到上限，停止轮询并尝试直接获取结果
          if (errorCount >= maxErrorCount) {
            console.log(`连续${maxErrorCount}次获取任务状态失败，尝试直接获取结果...`)
            
            // 停止轮询
            clearInterval(pollTimers.value[taskId])
            delete pollTimers.value[taskId]
            
            // 尝试直接获取结果
            fetchTaskResult(taskId)
          } else {
            console.warn(`获取任务状态出错 (${errorCount}/${maxErrorCount})，继续尝试...`)
          }
        }
      }, 2000) // 每2秒轮询一次
    }
    
    // 获取任务结果
    const fetchTaskResult = async (taskId) => {
      console.log(`开始获取任务 ${taskId} 的最终结果...`)
      try {
        const response = await getTaskResult(taskId)
        
        if (response.data.success) {
          console.log('成功获取任务结果:', response.data)
          
          if (!response.data.data) {
            console.error('响应中没有data字段:', response.data)
            ElMessage.warning('服务器返回的数据格式不正确')
            return
          }
          
          // 检查results是否存在
          if (!response.data.data.results) {
            console.error('任务结果中没有results字段:', response.data.data)
            ElMessage.warning('任务结果格式不正确')
            return
          }
          
          // 保存结果
          bleedResults.value = response.data.data.results || []
          
          // 更新阈值
          const threshold = response.data.data.threshold || bleedForm.thresholdValue
          
          // 安全地更新结果中的阈值
          if (Array.isArray(bleedResults.value)) {
            bleedResults.value.forEach(result => {
              if (result && typeof result === 'object') {
                result.threshold = threshold
              }
            })
          }
          
          console.log(`成功加载 ${bleedResults.value.length} 条结果数据:`, bleedResults.value)
          
          if (bleedResults.value.length > 0) {
            ElMessage.success('引气监控分析完成')
          } else {
            ElMessage.info('引气监控分析完成，但没有找到相关数据')
          }
        } else {
          console.error('获取任务结果失败:', response.data.message)
          ElMessage.error(response.data.message || '获取任务结果失败')
        }
      } catch (error) {
        console.error('获取任务结果错误:', error)
        ElMessage.error('获取任务结果失败，请稍后重试')
      }
    }
    
    // 查看详情
    const viewBleedDetail = (row) => {
      currentBleedDetail.value = row
      bleedDetailVisible.value = true
    }
    
    // 表格行样式
    const getBleedRowClass = ({ row }) => {
      const isT1Abnormal = row.t1_avg <= bleedForm.thresholdValue
      const isT2Abnormal = row.t2_avg <= bleedForm.thresholdValue
      
      if (isT1Abnormal || isT2Abnormal) {
        return 'abnormal-row'
      }
      return ''
    }
    
    // 获取状态类型
    const getBleedStatusType = (row, threshold) => {
      const isT1Abnormal = row.t1_avg <= threshold
      const isT2Abnormal = row.t2_avg <= threshold
      
      if (isT1Abnormal || isT2Abnormal) {
        return 'danger'
      }
      return 'success'
    }
    
    // 获取状态标签
    const getBleedStatusLabel = (row, threshold) => {
      const isT1Abnormal = row.t1_avg <= threshold
      const isT2Abnormal = row.t2_avg <= threshold
      
      if (isT1Abnormal || isT2Abnormal) {
        return '异常'
      }
      return '正常'
    }
    
    // 获取进度状态
    const getProgressStatus = (status) => {
      if (status === 'completed') {
        return 'success'
      } else if (status === 'error') {
        return 'exception'
      }
      return ''
    }
    
    // 导出数据
    const exportBleedData = () => {
      if (!bleedResults.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
      }
      
      // 创建CSV内容
      let csvContent = '飞机号,T1平均值,T2平均值,阈值,状态\n'
      
      bleedResults.value.forEach(result => {
        const isT1Abnormal = result.t1_avg <= bleedForm.thresholdValue
        const isT2Abnormal = result.t2_avg <= bleedForm.thresholdValue
        const status = isT1Abnormal || isT2Abnormal ? '异常' : '正常'
        
        csvContent += `${result.acno},${result.t1_avg.toFixed(1)},${result.t2_avg.toFixed(1)},${bleedForm.thresholdValue},${status}\n`
      })
      
      // 创建Blob并下载
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      
      link.setAttribute('href', url)
      link.setAttribute('download', `引气监控结果_${new Date().toISOString().slice(0, 10)}.csv`)
      link.style.visibility = 'hidden'
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    // 监听飞机类型变化
    watch(() => bleedForm.aircraftType, (newVal) => {
      // 当飞机类型改变时，只重置飞机列表
      bleedForm.aircraftNo = '全部'
    })
    
    // 初始化
    onMounted(async () => {
      // 初始化日期范围
      handleDateRangeChange()
      
      // 加载用户配置
      try {
        const response = await axios.get('/api/config')
        
        if (response.data.success) {
          const config = response.data.data
          
          // 更新引气监控设置
          if (config.bleedSettings) {
            bleedForm.thresholdValue = parseFloat(config.bleedSettings.cfmThreshold)
            bleedForm.employees = config.bleedSettings.employees
            bleedForm.emailRecipients = config.bleedSettings.emailRecipients || ''
            
            // 更新自动运行设置
            if (config.bleedSettings.autoRun) {
              bleedForm.autoRun = {
                enabled: config.bleedSettings.autoRun.enabled,
                dateRange: config.bleedSettings.autoRun.dateRange || '三个月',
                time: null
              }
              
              // 如果有时间设置，创建时间对象
              if (config.bleedSettings.autoRun.hour && config.bleedSettings.autoRun.minute) {
                const now = new Date()
                now.setHours(parseInt(config.bleedSettings.autoRun.hour))
                now.setMinutes(parseInt(config.bleedSettings.autoRun.minute))
                bleedForm.autoRun.time = now
              }
            }
          }
        }
      } catch (error) {
        console.error('加载配置错误:', error)
        ElMessage.error('加载配置失败')
      }
    })
    
    // 组件卸载时清除轮询
    onBeforeUnmount(() => {
      Object.values(pollTimers.value).forEach(timer => clearInterval(timer))
      pollTimers.value = {}
    })
    
    return {
      // 数据
      cfmAircraftList,
      v2500AircraftList,
      filteredAircraftList,
      bleedForm,
      bleedMonitorLoading,
      bleedMonitorTask,
      bleedResults,
      bleedDetailVisible,
      currentBleedDetail,
      
      // 方法
      handleDateRangeChange,
      saveBleedSettings,
      startBleedMonitoring,
      viewBleedDetail,
      getBleedRowClass,
      getBleedStatusType,
      getBleedStatusLabel,
      getProgressStatus,
      exportBleedData
    }
  }
}
</script>

<style scoped>
.bleed-monitor-container {
  padding: 20px;
}

.monitor-section {
  margin-bottom: 20px;
}

.settings-form .el-form-item {
  margin-bottom: 18px;
}

.settings-form .el-input, .settings-form .el-select {
  width: 100%;
}

.progress-info {
  margin: 20px 0;
}

.result-table {
  margin-top: 20px;
}

.abnormal-row {
  color: #F56C6C;
  font-weight: bold;
}

.normal-row {
  color: #67C23A;
}
</style>