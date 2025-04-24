<template>
  <div class="aircraft-detail">
    <div class="page-header">
      <h2 class="page-title"><span class="aircraft-reg">{{ acReg }}</span></h2>
    </div>
    
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <h3>基本信息</h3>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="aircraftInfo">
        <el-descriptions :column="5" border>
          <el-descriptions-item label="飞机号">{{ acReg }}</el-descriptions-item>
          <el-descriptions-item label="机型">{{ aircraftInfo.aircraft_type }}</el-descriptions-item>
          <el-descriptions-item label="MSN">{{ aircraftInfo.msn }}</el-descriptions-item>
          <el-descriptions-item label="FSN">{{ aircraftInfo.fsn }}</el-descriptions-item>
          <el-descriptions-item label="座椅布局">{{ aircraftInfo.seat_layout }}</el-descriptions-item>
          
          <el-descriptions-item label="首飞日期">{{ aircraftInfo.first_fly_date }}</el-descriptions-item>
          <el-descriptions-item label="交付日期">{{ aircraftInfo.deliver_date }}</el-descriptions-item>
          <el-descriptions-item label="最大起飞重量">{{ formatWeight(aircraftInfo.max_weight_takeoff) }}</el-descriptions-item>
          <el-descriptions-item label="最大着陆重量">{{ formatWeight(aircraftInfo.max_weight_landing) }}</el-descriptions-item>
          <el-descriptions-item label="最大零燃油重量">{{ formatWeight(aircraftInfo.max_weight_oilless) }}</el-descriptions-item>

          <el-descriptions-item label="发动机型号">{{ aircraftInfo.engine_type }}</el-descriptions-item>
          <el-descriptions-item label="左发序号">{{ aircraftInfo.left_engine_sn }}</el-descriptions-item>
          <el-descriptions-item label="右发序号">{{ aircraftInfo.right_engine_sn }}</el-descriptions-item>
          <el-descriptions-item label="APU型号">{{ aircraftInfo.apu_type }}</el-descriptions-item>
          <el-descriptions-item label="APU序号">{{ aircraftInfo.apu_sn }}</el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-else class="no-data">
        <el-empty description="未找到飞机信息" />
      </div>
    </el-card>
    
    <!-- 近期航班记录 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <h3>近期航班记录（前一天后两天）</h3>
          <el-tag v-if="dateRangeInfo" size="small" type="info">{{ dateRangeInfo }}</el-tag>
        </div>
      </template>
      
      <el-table
        v-loading="flightsLoading"
        :data="recentFlights"
        border
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="flight_no" label="航班号" align="center" width="90">
          <template #default="scope">
            <span v-if="scope.row.is_stopping">当天停场</span>
            <span v-else :class="{ 'last-flight': scope.row.is_last_flight }">{{ scope.row.flight_no }}</span>
          </template>
        </el-table-column>
        <el-table-column label="航班日期" align="center" width="130">
          <template #default="scope">
            <span :class="{ 'last-flight': scope.row.is_last_flight && !scope.row.is_stopping }">
              {{ scope.row.flight_date }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="起飞机场" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ formatAirportName(scope.row.dep_code) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="降落机场" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ formatAirportName(scope.row.arr_code) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="std" label="计划起飞时间" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ scope.row.std }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="atd" label="实际起飞时间" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ scope.row.atd }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="sta" label="计划到达时间" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ scope.row.sta }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="eta" label="预计到达时间" align="center" width="120">
          <template #default="scope">
            <span v-if="!scope.row.is_stopping" :class="{ 'last-flight': scope.row.is_last_flight }">
              {{ scope.row.eta }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="!flightsLoading && recentFlights.length === 0" class="no-data">
        <el-empty description="暂无航班记录" />
      </div>
    </el-card>
    
    <!-- 故障保留信息 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <h3>故障保留信息</h3>
          <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick">
            <el-tab-pane label="外站故障保留" name="outstation"></el-tab-pane>
            <el-tab-pane label="故障保留" name="fault"></el-tab-pane>
            <el-tab-pane label="缺陷保留" name="defect"></el-tab-pane>
          </el-tabs>
        </div>
      </template>
      
      <!-- 外站故障保留表格 -->
      <div v-if="activeTab === 'outstation'">
        <el-table
          v-loading="outstationFaultsLoading"
          :data="outstationFaults"
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column prop="out_no" label="保留编号" align="center" width="100"></el-table-column>
          <el-table-column prop="out_date" label="保留日期" align="center" width="120"></el-table-column>
          <el-table-column prop="ata" label="ATA" align="center" width="80"></el-table-column>
          <el-table-column prop="mel" label="MEL" align="center" width="150"></el-table-column>
          <el-table-column prop="out_desc" label="描述" align="left" min-width="250"></el-table-column>
          <el-table-column label="航站" align="center" width="100">
            <template #default="scope">
              {{ formatAirportName(scope.row.flight_site) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" align="center" width="80"></el-table-column>
        </el-table>
        
        <div v-if="!outstationFaultsLoading && outstationFaults.length === 0" class="no-data">
          <el-empty description="暂无外站故障保留记录" />
        </div>
      </div>
      
      <!-- 故障保留表格 -->
      <div v-if="activeTab === 'fault'">
        <el-table
          v-loading="faultRetentionsLoading"
          :data="faultRetentions"
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column prop="ddf_no" label="保留编号" align="center" width="100"></el-table-column>
          <el-table-column prop="apply_date" label="申请日期" align="center" width="120"></el-table-column>
          <el-table-column prop="ata" label="ATA" align="center" width="80"></el-table-column>
          <el-table-column prop="blbs_no" label="依据文件" align="center" width="150"></el-table-column>
          <el-table-column prop="faurep" label="描述" align="left" min-width="250"></el-table-column>
          <el-table-column label="航站" align="center" width="100">
            <template #default="scope">
              {{ formatAirportName(scope.row.terminal) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" align="center" width="80"></el-table-column>
          <el-table-column prop="dyd" label="保留天数" align="center" width="80"></el-table-column>
          <el-table-column prop="working_date" label="工作日期" align="center" width="80"></el-table-column>
        </el-table>
        
        <div v-if="!faultRetentionsLoading && faultRetentions.length === 0" class="no-data">
          <el-empty description="暂无故障保留记录" />
        </div>
      </div>
      
      <!-- 缺陷保留表格 -->
      <div v-if="activeTab === 'defect'">
        <el-table
          v-loading="defectRetentionsLoading"
          :data="defectRetentions"
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column prop="ddf_no" label="保留编号" align="center" width="100"></el-table-column>
          <el-table-column prop="apply_date" label="申请日期" align="center" width="120"></el-table-column>
          <el-table-column prop="ata" label="ATA" align="center" width="80"></el-table-column>
          <el-table-column prop="blbs_no" label="依据文件" align="center" width="150"></el-table-column>
          <el-table-column prop="faurep" label="描述" align="left" min-width="250"></el-table-column>
          <el-table-column label="航站" align="center" width="100">
            <template #default="scope">
              {{ formatAirportName(scope.row.terminal) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" align="center" width="80"></el-table-column>
          <el-table-column prop="fc" label="飞行循环" align="center" width="80"></el-table-column>
          <el-table-column prop="repair_date" label="修复日期" align="center" width="120"></el-table-column>
          <el-table-column prop="working_date" label="工作日期" align="center" width="80"></el-table-column>
        </el-table>
        
        <div v-if="!defectRetentionsLoading && defectRetentions.length === 0" class="no-data">
          <el-empty description="暂无缺陷保留记录" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { formatAirportName } from '@/utils/airport-codes'

const route = useRoute()
const router = useRouter()

// 获取路由参数中的飞机号
const acReg = ref(route.params.acReg || '')

// 数据加载状态
const loading = ref(true)
const flightsLoading = ref(true)

// 飞机基本信息
const aircraftInfo = ref(null)

// 近期航班记录
const recentFlights = ref([])

// 日期范围信息
const dateRangeInfo = ref('')

// 故障保留相关数据
const activeTab = ref('outstation')

// 外站故障保留数据
const outstationFaults = ref([])
const outstationFaultsLoading = ref(false)

// 故障保留数据
const faultRetentions = ref([])
const faultRetentionsLoading = ref(false)

// 缺陷保留数据
const defectRetentions = ref([])
const defectRetentionsLoading = ref(false)

// 页面加载时获取数据
onMounted(async () => {
  if (!acReg.value) {
    ElMessage.error('飞机号参数缺失')
    router.push('/flight-overview')
    return
  }
  
  await Promise.all([
    fetchAircraftInfo(),
    fetchRecentFlights(),
    fetchOutstationFaults()  // 默认加载外站故障保留信息
  ])
})

// 处理Tab切换
const handleTabClick = (tab) => {
  const tabName = tab.props.name
  if (tabName === 'outstation' && outstationFaults.value.length === 0) {
    fetchOutstationFaults()
  } else if (tabName === 'fault' && faultRetentions.value.length === 0) {
    fetchFaultRetentions()
  } else if (tabName === 'defect' && defectRetentions.value.length === 0) {
    fetchDefectRetentions()
  }
}

// 获取飞机基本信息
const fetchAircraftInfo = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/api/aircraft/detail/${acReg.value}`)
    if (response.data && response.data.success) {
      aircraftInfo.value = response.data.data
    } else {
      ElMessage.warning(response.data.message || '获取飞机信息失败')
    }
  } catch (error) {
    console.error('获取飞机信息出错:', error)
    ElMessage.error('获取飞机信息请求失败')
  } finally {
    loading.value = false
  }
}

// 获取近期航班记录
const fetchRecentFlights = async () => {
  flightsLoading.value = true
  try {
    // 计算日期范围 - 前一天到后两天
    const today = new Date()
    
    // 格式化日期为YYYY-MM-DD格式
    const formatDate = (date) => {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
    
    // 计算前一天和后两天的日期
    const startDate = new Date(today)
    startDate.setDate(today.getDate() - 1)
    const endDate = new Date(today)
    endDate.setDate(today.getDate() + 2)
    
    // 存储日期范围为字符串
    const startDateStr = formatDate(startDate)
    const endDateStr = formatDate(endDate)
    
    // 设置日期范围信息显示
    dateRangeInfo.value = `${startDateStr} 至 ${endDateStr}`
    
    // 一次性请求指定日期范围内的所有航班（而不是按天请求）
    const response = await axios.get(`/api/aircraft/recent-flights/${acReg.value}`, {
      params: { 
        start_date: startDateStr,
        end_date: endDateStr,
        include_all: true
      }
    })
    
    if (response.data && response.data.success) {
      let flights = response.data.data || []
      
      // 用于存储最终显示的航班数据（包括停场信息）
      let processedFlights = []
      
      // 建立日期到航班的映射
      const flightsByDate = {}
      
      // 对日期范围内的每一天进行初始化
      let currentDate = new Date(startDate)
      while (currentDate <= endDate) {
        const dateStr = formatDate(currentDate)
        flightsByDate[dateStr] = []
        currentDate.setDate(currentDate.getDate() + 1)
      }
      
      // 将航班按日期分组
      flights.forEach(flight => {
        if (flightsByDate.hasOwnProperty(flight.flight_date)) {
          flightsByDate[flight.flight_date].push(flight)
        }
      })
      
      // 遍历日期范围，为没有航班的日期添加"当天停场"记录，为有航班的日期标记最后一个航班
      for (const [date, dateFlights] of Object.entries(flightsByDate)) {
        if (dateFlights.length === 0) {
          // 添加一个标记为停场的记录
          processedFlights.push({
            flight_no: '停场',
            flight_date: date,
            is_stopping: true,
            is_last_flight: false
          })
        } else {
          // 先按计划起飞时间排序，以确定最后一个航班
          const sortedFlights = [...dateFlights].sort((a, b) => a.std.localeCompare(b.std))
          
          // 将每个航班添加到处理后的列表中
          sortedFlights.forEach((flight, index) => {
            processedFlights.push({
              ...flight,
              is_stopping: false,
              // 标记是否为当天最后一个航班
              is_last_flight: index === sortedFlights.length - 1
            })
          })
        }
      }
      
      // 按日期和计划起飞时间排序
      recentFlights.value = processedFlights.sort((a, b) => {
        // 先按日期升序
        if (a.flight_date < b.flight_date) return -1
        if (a.flight_date > b.flight_date) return 1
        
        // 如果是停场记录，放在当天的最前面
        if (a.is_stopping && !b.is_stopping) return -1
        if (!a.is_stopping && b.is_stopping) return 1
        
        // 同一天的正常航班按计划起飞时间排序
        if (!a.is_stopping && !b.is_stopping) {
          return a.std.localeCompare(b.std)
        }
        
        return 0
      })
    } else {
      ElMessage.warning(response.data.message || '获取航班记录失败')
    }
  } catch (error) {
    console.error('获取航班记录出错:', error)
    ElMessage.error('获取航班记录请求失败')
  } finally {
    flightsLoading.value = false
  }
}

// 获取外站故障保留信息
const fetchOutstationFaults = async () => {
  outstationFaultsLoading.value = true
  try {
    const response = await axios.get(`/api/aircraft/outstation-faults/${acReg.value}`)
    if (response.data && response.data.success) {
      outstationFaults.value = response.data.data || []
    } else {
      ElMessage.warning(response.data.message || '获取外站故障保留信息失败')
    }
  } catch (error) {
    console.error('获取外站故障保留信息出错:', error)
    ElMessage.error('获取外站故障保留信息请求失败')
  } finally {
    outstationFaultsLoading.value = false
  }
}

// 获取故障保留信息
const fetchFaultRetentions = async () => {
  faultRetentionsLoading.value = true
  try {
    const response = await axios.get(`/api/aircraft/fault-retentions/${acReg.value}`)
    if (response.data && response.data.success) {
      faultRetentions.value = response.data.data || []
    } else {
      ElMessage.warning(response.data.message || '获取故障保留信息失败')
    }
  } catch (error) {
    console.error('获取故障保留信息出错:', error)
    ElMessage.error('获取故障保留信息请求失败')
  } finally {
    faultRetentionsLoading.value = false
  }
}

// 获取缺陷保留信息
const fetchDefectRetentions = async () => {
  defectRetentionsLoading.value = true
  try {
    const response = await axios.get(`/api/aircraft/defect-retentions/${acReg.value}`)
    if (response.data && response.data.success) {
      defectRetentions.value = response.data.data || []
    } else {
      ElMessage.warning(response.data.message || '获取缺陷保留信息失败')
    }
  } catch (error) {
    console.error('获取缺陷保留信息出错:', error)
    ElMessage.error('获取缺陷保留信息请求失败')
  } finally {
    defectRetentionsLoading.value = false
  }
}

// 格式化重量（添加千克单位）
const formatWeight = (weight) => {
  if (!weight) return '未知'
  return `${weight} kg`
}
</script>

<style scoped>
.aircraft-detail {
  padding: 1px;
}

.page-header {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.page-title {
  margin: 0;
  color: #303133;
}

.aircraft-reg {
  color: #f56c6c;
  font-weight: bold;
  margin-left: 10px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.loading-container {
  padding: 20px 0;
}

.last-flight {
  color: #f56c6c;
  font-weight: bold;
}

/* 选项卡样式调整 */
:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 0;
}

:deep(.el-tabs__item) {
  height: 30px;
  line-height: 30px;
  padding: 0 15px;
}

/* 表格描述列文本显示 */
:deep(.el-table .cell) {
  word-break: break-all;
  line-height: 1.5;
  padding: 8px;
}
</style>