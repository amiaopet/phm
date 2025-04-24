<template>
  <div class="table-container">
    <div class="table-toolbar" v-if="showToolbar">
      <div class="left-actions">
        <el-input
          v-if="options.showSearch"
          v-model="searchQuery"
          placeholder="搜索..."
          clearable
          @input="handleSearch"
          style="width: 200px; margin-right: 10px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-if="options.showColumnSelector"
          v-model="visibleColumns"
          multiple
          collapse-tags
          placeholder="选择显示列"
          style="width: 200px; margin-right: 10px;"
          @change="updateVisibleColumns"
        >
          <el-option
            v-for="col in tableColumns"
            :key="col.prop"
            :label="col.label"
            :value="col.prop"
          ></el-option>
        </el-select>
      </div>
      
      <div class="right-actions">
        <el-button-group v-if="options.allowExport">
          <el-button type="primary" @click="exportData('csv')">
            <el-icon><Document /></el-icon>导出CSV
          </el-button>
          <el-button type="primary" @click="exportData('excel')">
            <el-icon><Document /></el-icon>导出Excel
          </el-button>
        </el-button-group>
        
        <el-button v-if="options.allowPrint" @click="printTable">
          <el-icon><Printer /></el-icon>打印
        </el-button>
      </div>
    </div>
    
    <el-table
      ref="tableRef"
      :data="filteredData"
      :height="options.height"
      border
      stripe
      highlight-current-row
      :max-height="options.maxHeight"
      :default-sort="defaultSort"
      @sort-change="handleSortChange"
      v-loading="loading"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="options.showSelectionColumn"
        type="selection"
        width="55"
      ></el-table-column>
      
      <!-- 索引列 -->
      <el-table-column
        v-if="options.showIndexColumn"
        type="index"
        width="50"
        label="#"
      ></el-table-column>
      
      <!-- 动态列 -->
      <el-table-column
        v-for="col in displayColumns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :fixed="col.fixed"
        :sortable="options.enableSorting && col.sortable !== false"
        :formatter="col.formatter"
        :align="col.align || 'left'"
      >
        <!-- 自定义列内容 -->
        <template v-if="col.customRender" #default="scope">
          <component
            :is="col.customRender"
            :row="scope.row"
            :index="scope.$index"
            :column="col"
          ></component>
        </template>
        
        <!-- 带筛选器的列 -->
        <template v-if="options.enableFiltering && col.filterable" #header>
          <div class="column-header-with-filter">
            <span>{{ col.label }}</span>
            <el-popover
              placement="bottom"
              width="200"
              trigger="click"
              v-model:visible="filterPopoverVisible[col.prop]"
            >
              <template #reference>
                <el-button type="primary" text :icon="Filter" circle size="small"></el-button>
              </template>
              <div>
                <el-input v-model="filterValues[col.prop]" placeholder="过滤值..." clearable></el-input>
                <div style="text-align: right; margin-top: 10px;">
                  <el-button type="primary" size="small" @click="applyFilter(col.prop)">应用</el-button>
                  <el-button size="small" @click="resetFilter(col.prop)">重置</el-button>
                </div>
              </div>
            </el-popover>
          </div>
        </template>
      </el-table-column>
      
      <!-- 操作列 -->
      <el-table-column
        v-if="options.showActionColumn"
        label="操作"
        width="150"
        fixed="right"
      >
        <template #default="scope">
          <div class="table-actions">
            <el-button-group>
              <el-button v-if="options.allowEdit" type="primary" text @click="handleEdit(scope.row, scope.$index)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="options.allowDelete" type="danger" text @click="handleDelete(scope.row, scope.$index)">
                <el-icon><Delete /></el-icon>
              </el-button>
              <el-button v-if="options.allowView" type="info" text @click="handleView(scope.row, scope.$index)">
                <el-icon><View /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="table-pagination" v-if="options.showPagination">
      <el-pagination
        v-model:currentPage="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="totalItems"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      ></el-pagination>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { Search, Filter, Document, Printer, Edit, Delete, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'TableComponent',
  components: {
    Search,
    Filter,
    Document,
    Printer,
    Edit,
    Delete,
    View
  },
  props: {
    tableData: {
      type: Array,
      default: () => []
    },
    tableColumns: {
      type: Array,
      default: () => []
    },
    tableOptions: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['edit', 'delete', 'view', 'row-selection-change', 'export', 'filter-change', 'sort-change', 'page-change'],
  setup(props, { emit }) {
    const tableRef = ref(null)
    const loading = ref(false)
    
    // 表格默认选项
    const defaultOptions = {
      showToolbar: true,
      showSearch: true,
      showColumnSelector: true,
      allowExport: true,
      allowPrint: true,
      showSelectionColumn: false,
      showIndexColumn: true,
      showActionColumn: true,
      allowEdit: true,
      allowDelete: true,
      allowView: true,
      enableSorting: true,
      enableFiltering: true,
      showPagination: true,
      pageSize: 10,
      pageSizes: [10, 20, 50, 100],
      height: 'auto',
      maxHeight: undefined,
      defaultSort: { prop: '', order: '' }
    }
    
    // 合并选项
    const options = computed(() => {
      return { ...defaultOptions, ...props.tableOptions }
    })
    
    // 搜索和过滤
    const searchQuery = ref('')
    const filterValues = reactive({})
    const filterPopoverVisible = reactive({})
    
    // 分页
    const currentPage = ref(1)
    const pageSize = ref(options.value.pageSize)
    const pageSizes = computed(() => options.value.pageSizes)
    const totalItems = computed(() => props.tableData.length)
    
    // 显示/隐藏列
    const visibleColumns = ref([])
    const displayColumns = computed(() => {
      if (visibleColumns.value.length === 0) {
        return props.tableColumns
      } else {
        return props.tableColumns.filter(col => visibleColumns.value.includes(col.prop))
      }
    })
    
    // 默认排序
    const defaultSort = computed(() => {
      if (options.value.defaultSort && options.value.defaultSort.prop) {
        return options.value.defaultSort
      }
      return { prop: '', order: '' }
    })
    
    // 显示工具栏
    const showToolbar = computed(() => {
      return options.value.showToolbar
    })
    
    // 初始化可见列
    const initVisibleColumns = () => {
      visibleColumns.value = props.tableColumns.map(col => col.prop)
    }
    
    // 更新可见列
    const updateVisibleColumns = () => {
      // 这里不需要做什么，因为displayColumns是计算属性，会自动更新
    }
    
    // 过滤数据
    const filteredData = computed(() => {
      let result = [...props.tableData]
      
      // 应用搜索
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(row => {
          return props.tableColumns.some(col => {
            const value = row[col.prop]
            if (value === null || value === undefined) return false
            return String(value).toLowerCase().includes(query)
          })
        })
      }
      
      // 应用过滤器
      Object.keys(filterValues).forEach(prop => {
        const filterValue = filterValues[prop]
        if (filterValue && filterValue.trim()) {
          result = result.filter(row => {
            const value = row[prop]
            if (value === null || value === undefined) return false
            return String(value).toLowerCase().includes(filterValue.toLowerCase())
          })
        }
      })
      
      // 应用分页
      if (options.value.showPagination) {
        const start = (currentPage.value - 1) * pageSize.value
        const end = start + pageSize.value
        return result.slice(start, end)
      }
      
      return result
    })
    
    // 搜索处理
    const handleSearch = () => {
      currentPage.value = 1
    }
    
    // 应用过滤器
    const applyFilter = (prop) => {
      filterPopoverVisible[prop] = false
      currentPage.value = 1
      
      emit('filter-change', {
        prop,
        value: filterValues[prop]
      })
    }
    
    // 重置过滤器
    const resetFilter = (prop) => {
      filterValues[prop] = ''
      filterPopoverVisible[prop] = false
      currentPage.value = 1
      
      emit('filter-change', {
        prop,
        value: ''
      })
    }
    
    // 排序变化处理
    const handleSortChange = (sort) => {
      emit('sort-change', sort)
    }
    
    // 页面大小变化处理
    const handleSizeChange = (size) => {
      pageSize.value = size
      emit('page-change', {
        page: currentPage.value,
        pageSize: size
      })
    }
    
    // 当前页变化处理
    const handleCurrentChange = (page) => {
      currentPage.value = page
      emit('page-change', {
        page,
        pageSize: pageSize.value
      })
    }
    
    // 编辑处理
    const handleEdit = (row, index) => {
      emit('edit', { row, index })
    }
    
    // 删除处理
    const handleDelete = (row, index) => {
      emit('delete', { row, index })
    }
    
    // 查看处理
    const handleView = (row, index) => {
      emit('view', { row, index })
    }
    
    // 导出数据
    const exportData = (type) => {
      loading.value = true
      
      try {
        let content = ''
        let filename = `table-export-${new Date().getTime()}.${type}`
        
        if (type === 'csv') {
          // 获取标题行
          const headers = props.tableColumns.map(col => col.label).join(',')
          
          // 获取数据行
          const rows = props.tableData.map(row => {
            return props.tableColumns.map(col => {
              const value = row[col.prop]
              // 处理包含逗号、引号等特殊字符的情况
              if (value === null || value === undefined) return ''
              const strValue = String(value)
              if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
                return `"${strValue.replace(/"/g, '""')}"`
              }
              return strValue
            }).join(',')
          }).join('\n')
          
          content = `${headers}\n${rows}`
        } else if (type === 'excel') {
          // 为简单起见，这里也生成CSV，实际项目中可以使用专门的Excel库
          ElMessage({
            message: '生成Excel文件，此处简化为CSV',
            type: 'info'
          })
          
          // 获取标题行
          const headers = props.tableColumns.map(col => col.label).join(',')
          
          // 获取数据行
          const rows = props.tableData.map(row => {
            return props.tableColumns.map(col => {
              const value = row[col.prop]
              // 处理包含逗号、引号等特殊字符的情况
              if (value === null || value === undefined) return ''
              const strValue = String(value)
              if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
                return `"${strValue.replace(/"/g, '""')}"`
              }
              return strValue
            }).join(',')
          }).join('\n')
          
          content = `${headers}\n${rows}`
          filename = `table-export-${new Date().getTime()}.csv`
        }
        
        // 创建Blob对象并下载
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        emit('export', { type, data: props.tableData })
        
        ElMessage({
          message: '导出成功',
          type: 'success'
        })
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage({
          message: '导出失败: ' + error.message,
          type: 'error'
        })
      } finally {
        loading.value = false
      }
    }
    
    // 打印表格
    const printTable = () => {
      if (!tableRef.value) return
      
      const printWindow = window.open('', '_blank')
      
      if (!printWindow) {
        ElMessage({
          message: '请允许打开弹出窗口',
          type: 'warning'
        })
        return
      }
      
      // 获取表格内容
      const tableElement = tableRef.value.$el
      
      // 创建打印页面
      printWindow.document.write(`
        <html>
          <head>
            <title>打印表格</title>
            <style>
              body { font-family: Arial, sans-serif; }
              table { border-collapse: collapse; width: 100%; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #f2f2f2; }
            </style>
          </head>
          <body>
            <h1>表格数据</h1>
            <div>${tableElement.outerHTML}</div>
          </body>
        </html>
      `)
      
      printWindow.document.close()
      printWindow.onload = () => {
        printWindow.print()
        printWindow.close()
      }
    }
    
    // 监听表格数据变化
    watch(() => props.tableData, () => {
      // 当数据变化时，保持在当前页，但如果当前页已经超出范围，则回到第一页
      const maxPage = Math.ceil(props.tableData.length / pageSize.value) || 1
      if (currentPage.value > maxPage) {
        currentPage.value = 1
      }
    }, { deep: true })
    
    // 监听表格列变化
    watch(() => props.tableColumns, () => {
      initVisibleColumns()
    }, { deep: true })
    
    // 组件挂载时初始化
    onMounted(() => {
      initVisibleColumns()
    })
    
    return {
      tableRef,
      loading,
      options,
      searchQuery,
      filterValues,
      filterPopoverVisible,
      currentPage,
      pageSize,
      pageSizes,
      totalItems,
      visibleColumns,
      displayColumns,
      defaultSort,
      showToolbar,
      filteredData,
      Filter,
      handleSearch,
      updateVisibleColumns,
      applyFilter,
      resetFilter,
      handleSortChange,
      handleSizeChange,
      handleCurrentChange,
      handleEdit,
      handleDelete,
      handleView,
      exportData,
      printTable
    }
  }
}
</script>

<style scoped>
.table-container {
  width: 100%;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.left-actions,
.right-actions {
  display: flex;
  align-items: center;
}

.right-actions > * {
  margin-left: 8px;
}

.table-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.column-header-with-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-actions {
  display: flex;
  justify-content: center;
}
</style>
