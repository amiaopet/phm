<template>
  <div class="a320-mod-search">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>A320MOD查询系统-数据截止2024.12.31</span>
        </div>
      </template>
      
      <el-row>
        <el-col :span="24">
          <el-alert
            v-if="statusMessage"
            :title="statusMessage"
            :type="statusType"
            :closable="false"
            show-icon
          />
        </el-col>
      </el-row>
      
      <!-- 搜索区域 -->
      <el-form :model="searchForm" class="search-form" @submit.prevent>
        <el-row :gutter="20">
          <el-col :xs="10" :sm="10">
            <el-form-item>
              <el-input 
                v-model="searchForm.modNumber" 
                placeholder="请输入MOD编号" 
                @keyup.enter="searchMod"
              >
                <template #append>
                  <el-button type="primary" @click="searchMod" :loading="loading">立即查询</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <!-- 基本信息显示区域 -->
      <el-card v-if="modInfo" class="info-card">
        <div class="mod-basic-info">
          <div><strong>MOD:</strong> {{ modInfo.mod_num }}</div>
          <div><strong>ATA:</strong> {{ modInfo.ata }}</div>
          <div><strong>标题:</strong> {{ modInfo.description }}</div>
          <div v-if="modInfo.is_anti_mod_of"><strong>反改装于:</strong> {{ modInfo.is_anti_mod_of }}</div>
          <div v-if="modInfo.has_for_anti_mod"><strong>拥有反改装:</strong> {{ modInfo.has_for_anti_mod }}</div>
          <div v-if="modInfo.all_execution_status"><strong>执行状态:</strong> ALL</div>
        </div>
      </el-card>
      
      <!-- 表格区域 -->
      <el-card v-if="modInfo" class="result-card">
        <el-table 
          :data="tableData" 
          border 
          style="width: 100%"
          :header-cell-style="{ background: '#f7f7f7', color: '#606266' }"
          stripe
        >
          <el-table-column prop="aircraft_type" label="机型" width="120"></el-table-column>
          <el-table-column prop="reg_nums" label="机号范围" min-width="200">
            <template #default="scope">
              <div v-html="scope.row.reg_nums.replace(/\n/g, '<br>')"></div>
            </template>
          </el-table-column>
          <el-table-column prop="fsn_range" label="FSN区间" width="180"></el-table-column>
          <el-table-column prop="msn_list" label="MSN列表" min-width="200">
            <template #default="scope">
              <div v-html="scope.row.msn_list.replace(/\n/g, '<br>')"></div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="table-actions">
          <el-button type="success" @click="exportData" :disabled="!tableData.length">导出数据</el-button>
        </div>
      </el-card>
      
      <!-- 未找到MOD提示 -->
      <el-empty v-if="noData" description="未找到MOD数据"></el-empty>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'A320MODSearch',
  setup() {
    // 表单数据
    const searchForm = reactive({
      modNumber: ''
    })
    
    // 状态变量
    const loading = ref(false)
    const statusMessage = ref('')
    const statusType = ref('info')
    const modInfo = ref(null)
    const tableData = ref([])
    const noData = ref(false)
    
    // 初始化
    onMounted(() => {
      checkDbStatus()
    })
    
    // 检查数据库状态
    const checkDbStatus = async () => {
      try {
        statusMessage.value = '正在检查数据库状态...'
        statusType.value = 'info'
        
        const response = await axios.get('/api/tools/mod-search/status')
        if (response.data.success) {
          statusMessage.value = `数据库连接成功，共 ${response.data.mod_count} 条MOD记录`
          statusType.value = 'success'
        } else {
          statusMessage.value = response.data.message || '数据库状态检查失败'
          statusType.value = 'warning'
        }
      } catch (error) {
        statusMessage.value = error.response?.data?.message || '数据库检查失败'
        statusType.value = 'error'
      }
    }
    
    // 搜索MOD
    const searchMod = async () => {
      if (!searchForm.modNumber) {
        ElMessage.warning('请输入MOD编号')
        return
      }
      
      try {
        loading.value = true
        noData.value = false
        modInfo.value = null
        tableData.value = []
        
        const response = await axios.get(`/api/tools/mod-search/${searchForm.modNumber}`)
        
        if (response.data.success) {
          if (response.data.mod_data) {
            modInfo.value = response.data.mod_data
            tableData.value = response.data.executions || []
            
            if (!tableData.value.length) {
              ElMessage.info(`MOD ${searchForm.modNumber} 未在任何飞机上执行`)
            }
          } else {
            noData.value = true
            ElMessage.info(`未找到MOD: ${searchForm.modNumber}`)
          }
        } else {
          ElMessage.error(response.data.message || '查询失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '查询执行失败')
      } finally {
        loading.value = false
      }
    }
    
    // 导出数据为CSV
    const exportData = () => {
      if (!tableData.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
      }
      
      // 创建CSV内容
      let csvContent = '机型,机号范围,FSN区间,MSN列表\n'
      
      tableData.value.forEach(row => {
        // 替换换行符，将内容放在双引号中以保证CSV格式正确
        csvContent += `${row.aircraft_type},"${row.reg_nums.replace(/\n/g, ' ')}",${row.fsn_range},"${row.msn_list.replace(/\n/g, ' ')}"\n`
      })
      
      // 创建Blob并下载
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      
      link.setAttribute('href', url)
      link.setAttribute('download', `MOD查询结果_${searchForm.modNumber}_${new Date().toISOString().slice(0, 10)}.csv`)
      link.style.visibility = 'hidden'
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    return {
      searchForm,
      loading,
      statusMessage,
      statusType,
      modInfo,
      tableData,
      noData,
      searchMod,
      exportData
    }
  }
}
</script>

<style scoped>
.a320-mod-search {
  padding: 0 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-top: 20px;
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.mod-basic-info {
  line-height: 1.8;
}

.table-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.result-card {
  margin-bottom: 20px;
}
</style> 