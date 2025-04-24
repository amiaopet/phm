<template>
  <div class="flight-overview">
    <!-- 查询表单 -->
    <el-form :model="queryForm" label-width="100px" class="query-form">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="航班日期">
            <el-date-picker
              v-model="queryForm.flightDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="飞机号">
            <el-select v-model="queryForm.acReg" filterable placeholder="选择飞机号" style="width: 100%">
              <el-option v-for="item in aircraftList" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="航班号">
            <el-input v-model="queryForm.flightNo" placeholder="输入航班号（如 HO1234 或 1234）" />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="起飞机场">
            <el-select
              v-model="queryForm.depCode"
              filterable
              remote
              reserve-keyword
              placeholder="输入机场代码或中文名称"
              :remote-method="remoteSearchDepAirport"
              :loading="depAirportLoading"
              style="width: 100%"
            >
              <el-option
                v-for="item in depAirportOptions"
                :key="item.code"
                :label="item.display"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="降落机场">
            <el-select
              v-model="queryForm.arrCode"
              filterable
              remote
              reserve-keyword
              placeholder="输入机场代码或中文名称"
              :remote-method="remoteSearchArrAirport"
              :loading="arrAirportLoading"
              style="width: 100%"
            >
              <el-option
                v-for="item in arrAirportOptions"
                :key="item.code"
                :label="item.display"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="&nbsp;">
            <div class="button-container">
              <el-button type="primary" @click="fetchFlightInfo" :loading="loading">查询</el-button>
              <el-button @click="resetForm">重置</el-button>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    
    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="flightList"
      border
      style="width: 100%; margin-top: 20px"
      :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
    >
      <el-table-column prop="ac_reg" label="飞机号" align="center" width="90">
        <template #default="scope">
          <el-link type="primary" @click="navigateToAircraftDetail(scope.row.ac_reg)">
            {{ scope.row.ac_reg }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="flight_no" label="航班号" align="center" width="90" />
      <el-table-column prop="flight_date" label="航班日期" align="center" width="100" />
      <el-table-column label="起飞机场" align="center" width="120">
        <template #default="scope">
          {{ formatAirportName(scope.row.dep_code) }}
        </template>
      </el-table-column>
      <el-table-column label="降落机场" align="center" width="120">
        <template #default="scope">
          {{ formatAirportName(scope.row.arr_code) }}
        </template>
      </el-table-column>
      <el-table-column prop="std" label="计划起飞时间" align="center" width="120" />
      <el-table-column prop="atd" label="实际起飞时间" align="center" width="120" />
      <el-table-column prop="close_door_time" label="关舱时间" align="center" width="120" />
      <el-table-column prop="data_out" label="滑出时间" align="center" width="120" />
      <el-table-column prop="dep_delay_time" label="延误时间(分钟)" align="center" width="120" />
      <el-table-column prop="sta" label="计划到达时间" align="center" width="120" />
      <el-table-column prop="eta" label="预计到达时间" align="center" width="120" />
    </el-table>
    
    <!-- 分页器 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFlightInfo } from '@/api/FlightOverview'
import { formatDate } from '@/utils/dateUtils'
import { formatAirportName, searchAirportByName, getAllAirports } from '@/utils/airport-codes'
import axios from 'axios'

// 导入路由
const router = useRouter()

// 飞机列表
const aircraftList = ref([])

// 机场相关
const depAirportOptions = ref([])
const arrAirportOptions = ref([])
const depAirportLoading = ref(false)
const arrAirportLoading = ref(false)

// 查询表单数据
const queryForm = reactive({
  flightDate: formatDate(new Date()),
  acReg: '',
  flightNo: '',
  depCode: '',
  arrCode: ''
})

// 表格数据
const flightList = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 处理 ResizeObserver 错误
const errorHandler = (event) => {
  if (event.message && event.message.includes('ResizeObserver loop')) {
    event.stopImmediatePropagation()
  }
}

// 初始加载
onMounted(() => {
  fetchAircraftList()
  fetchFlightInfo()
  // 初始化加载部分常用机场
  initAirportOptions()
  
  // 添加错误处理器
  window.addEventListener('error', errorHandler, true)
})

// 组件卸载前清理
onBeforeUnmount(() => {
  window.removeEventListener('error', errorHandler, true)
})

// 初始化机场选项
const initAirportOptions = () => {
  const commonAirports = getAllAirports().slice(0, 20) // 只显示前20个常用机场
  depAirportOptions.value = commonAirports
  arrAirportOptions.value = commonAirports
}

// 搜索起飞机场
const remoteSearchDepAirport = (query) => {
  if (query) {
    depAirportLoading.value = true
    setTimeout(() => {
      depAirportOptions.value = searchAirportByName(query)
      depAirportLoading.value = false
    }, 200)
  } else {
    depAirportOptions.value = getAllAirports().slice(0, 20)
  }
}

// 搜索降落机场
const remoteSearchArrAirport = (query) => {
  if (query) {
    arrAirportLoading.value = true
    setTimeout(() => {
      arrAirportOptions.value = searchAirportByName(query)
      arrAirportLoading.value = false
    }, 200)
  } else {
    arrAirportOptions.value = getAllAirports().slice(0, 20)
  }
}

// 获取飞机列表
const fetchAircraftList = async () => {
  try {
    const response = await axios.get('/api/utils/aircraft-list')
    if (response.data && response.data.success) {
      aircraftList.value = response.data.data || []
    } else {
      console.error('获取飞机列表失败:', response.data.message)
    }
  } catch (error) {
    console.error('获取飞机列表出错:', error)
  }
}

// 获取航班信息
const fetchFlightInfo = async () => {
  if (!queryForm.flightDate) {
    ElMessage.warning('请选择航班日期')
    return
  }
  
  loading.value = true
  try {
    // 处理航班号格式
    let formattedFlightNo = queryForm.flightNo.trim()
    if (formattedFlightNo && !formattedFlightNo.toLowerCase().startsWith('ho') && /^\d{4}$/.test(formattedFlightNo)) {
      formattedFlightNo = 'HO' + formattedFlightNo
    }
    
    // 处理飞机号格式 - 去除"B-"前缀
    let formattedAcReg = queryForm.acReg
    if (formattedAcReg && formattedAcReg.startsWith('B-')) {
      formattedAcReg = formattedAcReg.substring(2)
    }
    
    const response = await getFlightInfo({
      ...queryForm,
      flightNo: formattedFlightNo,
      acReg: formattedAcReg, // 使用处理后的飞机号
      page: currentPage.value,
      rows: pageSize.value
    })
    
    if (response.data.success) {
      flightList.value = response.data.data.flights || []
      total.value = response.data.data.total || 0
      
      if (flightList.value.length === 0) {
        ElMessage.info('未查询到符合条件的航班信息')
      }
    } else {
      ElMessage.error(response.data.message || '获取航班信息失败')
    }
  } catch (error) {
    console.error('获取航班信息出错:', error)
    ElMessage.error(error.response?.data?.message || '获取航班信息请求失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  queryForm.flightDate = formatDate(new Date())
  queryForm.acReg = ''
  queryForm.flightNo = ''
  queryForm.depCode = ''
  queryForm.arrCode = ''
  currentPage.value = 1
  // 重置机场选项
  initAirportOptions()
  fetchFlightInfo()
}

// 页码改变
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchFlightInfo()
}

// 每页条数改变
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchFlightInfo()
}

// 导航到飞机详情页
const navigateToAircraftDetail = (acReg) => {
  if (!acReg) {
    ElMessage.warning('飞机号不能为空')
    return
  }
  
  // 使用Router导航到飞机详情页，并传递飞机号参数
  router.push({
    name: 'AircraftDetail',
    params: { acReg }
  })
}
</script>

<style scoped>
.flight-overview {
  padding: 10px;
  overflow-x: hidden; /* 防止水平溢出 */
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.query-form {
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.button-container {
  display: flex;
  gap: 10px;
}

/* 确保所有表单项高度一致 */
:deep(.el-form-item__content) {
  display: flex;
  align-items: center;
  min-height: 40px;
}

/* 调整表单项间距 */
:deep(.el-form-item) {
  margin-bottom: 10px;
}

/* 调整表格布局以避免调整大小错误 */
:deep(.el-table) {
  table-layout: fixed;
}

:deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

/* 确保选择器不会导致布局问题 */
:deep(.el-select-dropdown) {
  max-width: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
