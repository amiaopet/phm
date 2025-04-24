<template>
  <div class="oxygen-monitor-container">
    <el-card class="monitor-section">
      <template #header>
        <div class="card-header">
          <span>机组氧气监控设置（来源 FLB）</span>
        </div>
      </template>
      <el-form :model="oxygenForm" label-width="100px" class="settings-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="飞机号">
              <el-select v-model="oxygenForm.aircraft" placeholder="请选择飞机号">
                <el-option label="全部" value="ALL"></el-option>
                <el-option v-for="ac in allAircraftList" :key="ac" :label="ac" :value="ac"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="日期范围">
              <el-select v-model="oxygenForm.dateRange" placeholder="请选择日期范围" @change="handleOxygenDateRangeChange">
                <el-option label="最近三天" value="最近三天"></el-option>
                <el-option label="最近七天" value="最近七天"></el-option>
                <el-option label="最近十四天" value="最近十四天"></el-option>
                <el-option label="最近三十天" value="最近三十天"></el-option>
                <el-option label="自定义" value="自定义"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" v-if="oxygenForm.dateRange === '自定义'">
          <el-col :xs="24" :sm="24">
            <el-form-item label="日期区间">
              <el-date-picker
                v-model="oxygenForm.dateRangeValue"
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
            <el-form-item label="PSI1阈值">
              <el-input-number v-model="oxygenForm.psi1Threshold" :min="0" :max="100" :step="1"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="PSI2阈值">
              <el-input-number v-model="oxygenForm.psi2Threshold" :min="0" :max="100" :step="1"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24">
            <el-form-item label="接收员工号">
              <el-input v-model="oxygenForm.employees" placeholder="多个员工号用英文逗号分隔"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24">
            <el-form-item label="接收邮箱">
              <el-input v-model="oxygenForm.emailRecipients" placeholder="多个邮箱用英文逗号分隔"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="startOxygenMonitoring" :loading="oxygenMonitorLoading">开始查询</el-button>
          <el-button @click="saveOxygenSettings">保存设置</el-button>
          <el-button type="success" @click="exportOxygenData" :disabled="!oxygenResults.length">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 氧气监控进度 -->
    <el-card v-if="oxygenMonitorTask" class="monitor-section">
      <template #header>
        <div class="card-header">
          <span>监控进度</span>
        </div>
      </template>
      <div class="progress-info">
        <el-progress :percentage="oxygenMonitorTask.progress" :status="getProgressStatus(oxygenMonitorTask.status)"></el-progress>
        <p>{{ oxygenMonitorTask.message }}</p>
      </div>
    </el-card>
    
    <!-- 氧气监控结果表格 -->
    <el-card v-if="oxygenResults.length" class="result-table">
      <template #header>
        <div class="card-header">
          <span>监控结果</span>
        </div>
      </template>
      <el-table :data="oxygenResults" style="width: 100%" border :row-class-name="getOxygenRowClass">
        <el-table-column prop="aircraft" label="飞机号" width="100"></el-table-column>
        <el-table-column prop="date" label="日期" width="120"></el-table-column>
        <el-table-column prop="flight_no" label="航班号" width="100"></el-table-column>
        <el-table-column prop="takeoff_time" label="起飞时间" width="100"></el-table-column>
        <el-table-column prop="step" label="阶段" width="80"></el-table-column>
        <el-table-column prop="psi1" label="PSI1" width="80"></el-table-column>
        <el-table-column prop="psi2" label="PSI2" width="80"></el-table-column>
        <el-table-column label="PSI1下降" width="100">
          <template #default="scope">
            <span :class="{ 'abnormal-row': scope.row.psi1_drop >= oxygenForm.psi1Threshold }">
              {{ scope.row.psi1_drop }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="PSI2下降" width="100">
          <template #default="scope">
            <span :class="{ 'abnormal-row': scope.row.psi2_drop >= oxygenForm.psi2Threshold }">
              {{ scope.row.psi2_drop }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === '警告' ? 'danger' : 'success'">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'OxygenMonitor',
  
  setup() {
    // 全部飞机列表
    const cfmAircraftList = [
      'B-1645', 'B-1646', 'B-1647', 'B-1681', 'B-1808', 'B-1857', 'B-1870',
      'B-1871', 'B-1872', 'B-304G', 'B-304H', 'B-6572', 'B-6640', 'B-6717',
      'B-6735', 'B-6736', 'B-6787', 'B-6788', 'B-6860', 'B-6861', 'B-6901',
      'B-6921', 'B-6922', 'B-6948', 'B-6949', 'B-6962', 'B-6963', 'B-6965',
      'B-6966', 'B-8035', 'B-8036', 'B-8068', 'B-8235', 'B-8236', 'B-8317',
      'B-8408', 'B-8536', 'B-8538', 'B-9957', 'B-9978'
    ]
    
    const v2500AircraftList = [
      'B-1001', 'B-1002', 'B-1003', 'B-1005', 'B-1006', 'B-8315', 'B-8407',
      'B-8457', 'B-8458', 'B-8459', 'B-8537', 'B-8539', 'B-8540', 'B-8587',
      'B-8955', 'B-8956', 'B-8957'
    ]
    
    const pwAircraftList = [
      'B-30C9', 'B-30CT', 'B-30EP', 'B-30EQ', 'B-30FC', 'B-30FQ', 'B-320Z', 'B-321A', 
      'B-321C', 'B-322E', 'B-323D', 'B-323R', 'B-324C', 'B-324D', 'B-324U', 'B-324V', 
      'B-325L', 'B-326H', 'B-326J', 'B-327D', 'B-327W', 'B-32CJ', 'B-32D9', 'B-32DF', 
      'B-32EA', 'B-32EC', 'B-32EG', 'B-32EH', 'B-32EJ', 'B-32EY', 'B-32HD', 'B-32HT', 
      'B-32HU', 'B-32JE', 'B-32JP', 'B-32JU'
    ]
    
    // 合并所有飞机列表并排序
    const allAircraftList = computed(() => {
      return [...cfmAircraftList, ...v2500AircraftList, ...pwAircraftList].sort()
    })
    
    // 氧气监控相关状态
    const oxygenForm = reactive({
      aircraft: 'ALL',
      dateRange: '最近三天',
      dateRangeValue: [],
      psi1Threshold: 50,
      psi2Threshold: 50,
      employees: '',
      emailRecipients: ''
    })
    
    const oxygenMonitorLoading = ref(false)
    const oxygenMonitorTask = ref(null)
    const oxygenResults = ref([])
    
    // 轮询定时器
    const pollTimers = ref({})
    
    // 日期范围相关方法
    const handleOxygenDateRangeChange = () => {
      if (oxygenForm.dateRange !== '自定义') {
        const end = new Date()
        let start = new Date()
        
        switch (oxygenForm.dateRange) {
          case '最近一天':
            start.setDate(end.getDate() - 1)
            break
          case '最近三天':
            start.setDate(end.getDate() - 3)
            break
          case '最近七天':
            start.setDate(end.getDate() - 7)
            break
          case '最近十四天':
            start.setDate(end.getDate() - 14)
            break
          case '最近三十天':
            start.setDate(end.getDate() - 30)
            break
        }
        
        oxygenForm.dateRangeValue = [
          start.toISOString().split('T')[0],
          end.toISOString().split('T')[0]
        ]
      }
    }
    
    // 保存设置
    const saveOxygenSettings = async () => {
      try {
        // 保存氧气监控相关设置
        const settings = {
          oxygenSettings: {
            lastAircraft: oxygenForm.aircraft,
            daysRange: oxygenForm.dateRange.replace('最近', '').replace('天', ''),
            psi1Threshold: oxygenForm.psi1Threshold,
            psi2Threshold: oxygenForm.psi2Threshold,
            employees: oxygenForm.employees,
            emailRecipients: oxygenForm.emailRecipients
          }
        }
        
        const response = await axios.post('/api/config', settings)
        
        if (response.data.success) {
          ElMessage.success('氧气监控设置已保存')
        } else {
          ElMessage.error(response.data.message || '保存设置失败')
        }
      } catch (error) {
        console.error('保存设置错误:', error)
        ElMessage.error(error.response?.data?.message || '保存设置失败')
      }
    }
    
    // 开始监控
    const startOxygenMonitoring = async () => {
      // 确保选择了飞机号
      if (!oxygenForm.aircraft) {
        ElMessage.warning('请选择飞机号')
        return
      }
      
      // 确保有日期范围
      if (oxygenForm.dateRange === '自定义' && (!oxygenForm.dateRangeValue || oxygenForm.dateRangeValue.length !== 2)) {
        ElMessage.warning('请选择日期范围')
        return
      }
      
      // 如果没有选择日期范围，设置默认范围
      if (oxygenForm.dateRange !== '自定义' && (!oxygenForm.dateRangeValue || oxygenForm.dateRangeValue.length !== 2)) {
        handleOxygenDateRangeChange()
      }
      
      try {
        oxygenMonitorLoading.value = true
        oxygenResults.value = []
        
        const [startDate, endDate] = oxygenForm.dateRangeValue
        
        const response = await axios.post('/api/oxygen-monitor', {
          aircraft: oxygenForm.aircraft,
          startDate,
          endDate,
          psi1Threshold: oxygenForm.psi1Threshold,
          psi2Threshold: oxygenForm.psi2Threshold,
          employees: oxygenForm.employees,
          emailRecipients: oxygenForm.emailRecipients
        })
        
        if (response.data.success) {
          ElMessage.success('氧气监控任务已启动')
          const taskId = response.data.data.taskId
          
          // 保存任务状态并开始轮询
          oxygenMonitorTask.value = {
            taskId,
            status: 'running',
            progress: 0,
            message: '开始监控任务...'
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
        oxygenMonitorLoading.value = false
      }
    }
    
    // 轮询任务状态
    const pollTaskStatus = (taskId) => {
      // 如果已有定时器，先清除
      if (pollTimers.value[taskId]) {
        clearInterval(pollTimers.value[taskId])
      }
      
      // 创建轮询定时器
      pollTimers.value[taskId] = setInterval(async () => {
        try {
          const response = await axios.get(`/api/task/${taskId}`)
          
          if (response.data.success) {
            const taskData = response.data.data
            
            // 更新任务状态
            oxygenMonitorTask.value = {
              taskId,
              status: taskData.status,
              progress: taskData.progress,
              message: taskData.message
            }
            
            // 如果任务完成，获取结果
            if (taskData.status === 'completed') {
              getTaskResult(taskId)
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
            } else if (taskData.status === 'error') {
              ElMessage.error(`监控任务出错: ${taskData.message}`)
              clearInterval(pollTimers.value[taskId])
              delete pollTimers.value[taskId]
            }
          } else {
            console.error('获取任务状态失败:', response.data.message)
            clearInterval(pollTimers.value[taskId])
            delete pollTimers.value[taskId]
          }
        } catch (error) {
          console.error('轮询任务状态错误:', error)
          clearInterval(pollTimers.value[taskId])
          delete pollTimers.value[taskId]
        }
      }, 2000) // 每2秒轮询一次
    }
    
    // 获取任务结果
    const getTaskResult = async (taskId) => {
      try {
        const response = await axios.get(`/api/task/${taskId}/result`)
        
        if (response.data.success) {
          oxygenResults.value = response.data.data.results
          ElMessage.success('氧气监控分析完成')
        } else {
          ElMessage.error(response.data.message || '获取任务结果失败')
        }
      } catch (error) {
        console.error('获取任务结果错误:', error)
        ElMessage.error(error.response?.data?.message || '获取任务结果失败')
      }
    }
    
    // 表格行样式
    const getOxygenRowClass = ({ row }) => {
      if (row.status === '警告') {
        return 'abnormal-row'
      }
      return ''
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
    const exportOxygenData = () => {
      if (!oxygenResults.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
      }
      
      // 创建CSV内容
      let csvContent = '飞机号,日期,航班号,起飞时间,阶段,PSI1,PSI2,PSI1下降,PSI2下降,状态\n'
      
      oxygenResults.value.forEach(result => {
        csvContent += `${result.aircraft},${result.date},${result.flight_no},${result.takeoff_time},${result.step},${result.psi1},${result.psi2},${result.psi1_drop},${result.psi2_drop},${result.status}\n`
      })
      
      // 创建Blob并下载
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      
      link.setAttribute('href', url)
      link.setAttribute('download', `氧气监控结果_${new Date().toISOString().slice(0, 10)}.csv`)
      link.style.visibility = 'hidden'
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    // 初始化
    onMounted(async () => {
      // 初始化日期范围
      handleOxygenDateRangeChange()
      
      // 加载用户配置
      try {
        const response = await axios.get('/api/config')
        
        if (response.data.success) {
          const config = response.data.data
          
          // 更新氧气监控设置
          if (config.oxygenSettings) {
            oxygenForm.aircraft = config.oxygenSettings.lastAircraft || 'ALL'
            oxygenForm.psi1Threshold = parseFloat(config.oxygenSettings.psi1Threshold)
            oxygenForm.psi2Threshold = parseFloat(config.oxygenSettings.psi2Threshold)
            oxygenForm.employees = config.oxygenSettings.employees || ''
            oxygenForm.emailRecipients = config.oxygenSettings.emailRecipients || ''
            
            // 日期范围
            if (config.oxygenSettings.daysRange) {
              oxygenForm.dateRange = `最近${config.oxygenSettings.daysRange}天`
              // 处理特殊情况
              if (config.oxygenSettings.daysRange === '3') {
                oxygenForm.dateRange = '最近三天'
              } else if (config.oxygenSettings.daysRange === '7') {
                oxygenForm.dateRange = '最近七天'
              } else if (config.oxygenSettings.daysRange === '14') {
                oxygenForm.dateRange = '最近十四天'
              } else if (config.oxygenSettings.daysRange === '30') {
                oxygenForm.dateRange = '最近三十天'
              }
            }
            
            // 更新日期范围值
            handleOxygenDateRangeChange()
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
      allAircraftList,
      oxygenForm,
      oxygenMonitorLoading,
      oxygenMonitorTask,
      oxygenResults,
      
      // 方法
      handleOxygenDateRangeChange,
      saveOxygenSettings,
      startOxygenMonitoring,
      getOxygenRowClass,
      getProgressStatus,
      exportOxygenData
    }
  }
}
</script>

<style scoped>
.oxygen-monitor-container {
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