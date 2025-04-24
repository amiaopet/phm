<template>
  <div class="custom-visualization-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <p class="header-description">在此页面创建并配置您的自定义可视化图表、表格和数据分析模块。</p>
          <el-button type="primary" @click="addNewVisualization">
            <el-icon><Plus /></el-icon>添加可视化
          </el-button>
        </div>
      </template>
    </el-card>

    <!-- 可视化工作区 -->
    <div class="visualization-workspace">
      <el-empty v-if="visualizations.length === 0" description="暂无可视化组件，请点击添加"></el-empty>
      
      <div v-else class="visualization-grid">
        <el-card v-for="(item, index) in visualizations" :key="index" class="visualization-card">
          <template #header>
            <div class="visualization-header">
              <span>{{ item.title }}</span>
              <div class="visualization-actions">
                <el-button type="primary" text @click="editVisualization(index)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" text @click="deleteVisualization(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- 图表组件 -->
          <component 
            :is="getComponentType(item.type)" 
            v-if="item.type.startsWith('chart')"
            :chart-type="item.chartType" 
            :chart-data="item.data"
            :chart-options="getChartOptions(item)"
            :height="item.height || 300"
            class="visualization-component"
            @error="handleChartError"
          ></component>
          
          <!-- 表格组件 -->
          <component 
            :is="getComponentType(item.type)" 
            v-else-if="item.type.startsWith('table')"
            :table-data="item.data"
            :table-columns="item.columns"
            :table-options="item.options"
          ></component>
          
          <!-- 数据分析组件 -->
          <component 
            :is="getComponentType(item.type)" 
            v-else-if="item.type.startsWith('analysis')"
            :analysis-type="item.analysisType"
            :analysis-data="item.data"
            :analysis-options="item.options"
          ></component>
        </el-card>
      </div>
    </div>

    <!-- 添加/编辑可视化对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑可视化' : '新增可视化'"
      width="80%"
    >
      <el-form :model="currentVisualization" label-width="120px">
        <el-form-item label="标题">
          <el-input v-model="currentVisualization.title" placeholder="请输入可视化标题"></el-input>
        </el-form-item>
        
        <el-form-item label="组件类型">
          <el-select v-model="currentVisualization.type" placeholder="请选择组件类型" @change="handleTypeChange">
            <el-option-group label="图表">
              <el-option label="图表" value="chart"></el-option>
            </el-option-group>
            <el-option-group label="表格">
              <el-option label="高级表格" value="table"></el-option>
            </el-option-group>
            <el-option-group label="数据分析">
              <el-option label="数据分析" value="analysis"></el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <!-- 图表特有配置 -->
        <template v-if="currentVisualization.type === 'chart'">
          <el-form-item label="图表类型">
            <el-select v-model="currentVisualization.chartType" placeholder="请选择图表类型">
              <el-option label="折线图" value="line"></el-option>
              <el-option label="区域图" value="area"></el-option>
              <el-option label="柱状图" value="bar"></el-option>
              <el-option label="散点图" value="scatter"></el-option>
              <el-option label="直方图" value="histogram"></el-option>
              <el-option label="箱线图" value="boxplot"></el-option>
              <el-option label="热力图" value="heatmap"></el-option>
              <el-option label="雷达图" value="radar"></el-option>
              <el-option label="3D散点图" value="scatter3d"></el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="图表高度">
            <el-slider v-model="currentVisualization.height" :min="200" :max="600" :step="50"></el-slider>
          </el-form-item>
        </template>
        
        <!-- 表格特有配置 -->
        <template v-if="currentVisualization.type === 'table'">
          <el-form-item label="表格功能">
            <el-checkbox-group v-model="currentVisualization.tableFeatures">
              <el-checkbox label="排序" name="sort"></el-checkbox>
              <el-checkbox label="过滤" name="filter"></el-checkbox>
              <el-checkbox label="分页" name="pagination"></el-checkbox>
              <el-checkbox label="导出" name="export"></el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </template>
        
        <!-- 数据分析特有配置 -->
        <template v-if="currentVisualization.type === 'analysis'">
          <el-form-item label="分析类型">
            <el-select v-model="currentVisualization.analysisType" placeholder="请选择分析类型">
              <el-option label="基础统计" value="basic"></el-option>
              <el-option label="相关性分析" value="correlation"></el-option>
              <el-option label="趋势分析" value="trend"></el-option>
              <el-option label="异常检测" value="anomaly"></el-option>
              <el-option label="频谱分析" value="spectrum"></el-option>
            </el-select>
          </el-form-item>
        </template>
        
        <!-- 数据源配置 -->
        <el-form-item label="数据源">
          <el-select v-model="currentVisualization.dataSource" placeholder="请选择数据源类型" @change="handleDataSourceChange">
            <el-option label="本地文件" value="local"></el-option>
            <el-option label="数据库" value="database"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 本地文件上传 -->
        <template v-if="currentVisualization.dataSource === 'local'">
          <el-form-item v-if="currentVisualization.file && parsedColumns.length > 0" label="选择数据列">
            <div class="column-usage-tips">
              <h4>数据列使用说明</h4>
              <ul>
                <li><b>折线图/面积图/柱状图</b>: 第一列作为X轴类别数据，其余列作为数据系列</li>
                <li><b>散点图</b>: 使用前两列作为X轴和Y轴坐标</li>
                <li><b>3D散点图</b>: 使用前三列作为X、Y、Z坐标</li>
                <li><b>数据分析</b>: 使用所有选中列进行分析</li>
              </ul>
            </div>
            
            <div class="column-selection-table">
              <el-table 
                ref="columnTableRef"
                :data="columnSelectionData" 
                style="width: 100%" 
                border 
                :max-height="400"
                @selection-change="handleColumnsSelectionChange"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column prop="columnName" label="列名" min-width="150" />
                <el-table-column prop="dataType" label="数据类型" min-width="100" />
                <el-table-column prop="sampleData" label="示例数据" min-width="250">
                  <template #default="scope">
                    <div class="sample-data-cell">
                      <span v-for="(item, index) in scope.row.sampleData" :key="index" class="sample-data-item">
                        {{ item }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <div class="column-selection-actions">
                <el-button type="primary" link @click="selectAllColumns">全选</el-button>
                <el-button type="danger" link @click="deselectAllColumns">取消全选</el-button>
              </div>
            </div>
          </el-form-item>
          
          <el-form-item label="上传文件">
          <el-upload
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
              accept=".csv,.json,.xlsx,.xls"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持上传CSV、JSON、Excel文件</div>
            </template>
          </el-upload>
        </el-form-item>
        </template>
        
        <!-- 数据库配置 -->
        <template v-if="currentVisualization.dataSource === 'database'">
          <el-form-item label="数据库类型">
            <el-select v-model="currentVisualization.dbType" placeholder="请选择数据库类型">
              <el-option label="MySQL" value="mysql"></el-option>
              <el-option label="PostgreSQL" value="postgresql"></el-option>
              <el-option label="腾讯云CDB" value="tccloud"></el-option>
              <el-option label="阿里云RDS" value="aliyun"></el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="连接参数">
            <el-input v-model="currentVisualization.connectionString" placeholder="请输入连接字符串或选择已保存的连接"></el-input>
          </el-form-item>
          
          <el-form-item label="查询语句">
            <el-input
              type="textarea"
              v-model="currentVisualization.query"
              placeholder="请输入SQL查询语句"
              :rows="3"
            ></el-input>
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveVisualization" :disabled="!canSave">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import Chart from '@/components/Chart.vue'
import Table from '@/components/Table.vue'
import DataAnalysis from '@/components/DataAnalysis.vue'
import { parseFile, getColumnOptions } from '@/utils/fileUtils'
import { debounce } from 'lodash'

export default {
  name: 'CustomVisualization',
  components: {
    Chart,
    Table,
    DataAnalysis,
    Plus,
    Edit,
    Delete
  },
  setup() {
    // 可视化组件列表
    const visualizations = ref([]);
    
    // 对话框控制
    const dialogVisible = ref(false);
    const isEditing = ref(false);
    const editIndex = ref(-1);
    
    // 当前编辑的可视化配置
    const currentVisualization = reactive({
      title: '',
      type: '',
      dataSource: '',
      data: null,
      options: {},
      // 图表特有
      chartType: '',
      height: 300,
      // 表格特有
      columns: [],
      tableFeatures: [],
      // 数据分析特有
      analysisType: '',
      // 数据库特有
      dbType: '',
      connectionString: '',
      query: '',
      // 本地文件特有
      file: null
    });
    
    // 解析数据
    const parsedData = ref([]);
    const parsedColumns = ref([]);
    const selectedColumns = ref([]);
    const columnOptions = ref([]);
    const loading = ref(false);
    
    // 表格选择数据列
    const columnSelectionData = computed(() => {
      if (!parsedData.value || parsedData.value.length === 0 || !parsedColumns.value) {
        return [];
      }
      
      return parsedColumns.value.map(column => {
        // 获取示例数据
        const sampleValues = parsedData.value.slice(0, 3).map(row => row[column]);
        
        // 推断数据类型
        const dataType = inferDataType(sampleValues);
        
        return {
          columnName: column,
          dataType: dataType,
          sampleData: sampleValues
        };
      });
    });
    
    // 推断数据类型
    const inferDataType = (values) => {
      if (!values || values.length === 0) return '未知';
      
      // 检查第一个非空值
      const sample = values.find(v => v !== null && v !== undefined);
      if (sample === undefined) return '空';
      
      if (!isNaN(Number(sample))) {
        if (String(sample).includes('.')) {
          return '数值 (小数)';
        }
        return '数值 (整数)';
      } else if (typeof sample === 'string') {
        if (/^\d{4}[-\/]\d{1,2}[-\/]\d{1,2}/.test(sample)) {
          return '日期';
        }
        if (/^\d{1,2}:\d{1,2}(:\d{1,2})?/.test(sample)) {
          return '时间';
        }
        return '文本';
      } else if (typeof sample === 'boolean') {
        return '布尔值';
      }
      
      return '未知';
    };
    
    // 添加表格引用和选择方法
    const columnTableRef = ref(null);
    
    // 添加防抖的列选择方法
    const debouncedToggleSelection = debounce((rows, selected) => {
      if (columnTableRef.value) {
        rows.forEach(row => {
          columnTableRef.value.toggleRowSelection(row, selected);
        });
      }
    }, 50);
    
    // 优化全选方法，防止ResizeObserver错误
    const selectAllColumns = () => {
      // 直接更新数据
      selectedColumns.value = parsedColumns.value;
      
      // 取消表格的原生选择，改用我们自己的数据来管理选择状态
      if (columnTableRef.value) {
        columnTableRef.value.clearSelection();
      }

      // 手动强制表格更新已选中的行
      nextTick(() => {
        if (columnTableRef.value) {
          selectedColumns.value.forEach(columnName => {
            const row = columnSelectionData.value.find(item => item.columnName === columnName);
            if (row) {
              columnTableRef.value.toggleRowSelection(row, true, false); // 第三个参数防止触发selectionChange
            }
          });
        }
      });
    };
    
    // 优化取消全选方法
    const deselectAllColumns = () => {
      selectedColumns.value = [];
      if (columnTableRef.value) {
        columnTableRef.value.clearSelection();
      }
    };
    
    // 修改处理列选择变化的方法
    const handleColumnsSelectionChange = (selection) => {
      // 不使用debounce，直接更新
      selectedColumns.value = selection.map(item => item.columnName);
      console.log('列选择已更新，当前选择的列:', selectedColumns.value);
    };
    
    // 使用nextTick替代setTimeout
    const initColumnSelection = () => {
      nextTick(() => {
        if (columnTableRef.value && columnSelectionData.value.length > 0) {
          columnTableRef.value.clearSelection();
          
          // 使用nextTick确保DOM已更新
          nextTick(() => {
            // 分批处理，但使用nextTick代替setTimeout
            const chunks = [];
            const chunkSize = 10;
            
            for (let i = 0; i < columnSelectionData.value.length; i += chunkSize) {
              chunks.push(columnSelectionData.value.slice(i, i + chunkSize));
            }
            
            let processedChunks = 0;
            
            const processNextChunk = () => {
              if (processedChunks < chunks.length) {
                const chunk = chunks[processedChunks];
                chunk.forEach(row => {
                  columnTableRef.value?.toggleRowSelection(row, true, false); // 最后一个参数阻止触发selectionChange
                });
                processedChunks++;
                nextTick(processNextChunk);
              }
            };
            
            processNextChunk();
          });
        }
      });
    };
    
    // 根据组件类型获取对应的组件
    const getComponentType = (type) => {
      if (type.startsWith('chart')) return Chart;
      if (type.startsWith('table')) return Table;
      if (type.startsWith('analysis')) return DataAnalysis;
      return null;
    };
    
    // 是否可以保存数据
    const canSave = computed(() => {
      if (!currentVisualization.title) return false;
      if (!currentVisualization.type) return false;
      if (!currentVisualization.dataSource) return false;
      
      // 根据数据源类型检查
      if (currentVisualization.dataSource === 'local' && 
          (!currentVisualization.file || selectedColumns.value.length === 0)) {
        return false;
      }
      
      if (currentVisualization.dataSource === 'database' && 
          (!currentVisualization.dbType || !currentVisualization.connectionString || !currentVisualization.query)) {
        return false;
      }
      
      // 根据组件类型检查
      if (currentVisualization.type === 'chart' && !currentVisualization.chartType) {
        return false;
      }
      
      if (currentVisualization.type === 'analysis' && !currentVisualization.analysisType) {
      return false;
      }
      
      return true;
    });
    
    // 添加新的可视化
    const addNewVisualization = () => {
      // 重置当前可视化配置
      Object.keys(currentVisualization).forEach(key => {
        if (Array.isArray(currentVisualization[key])) {
          currentVisualization[key] = [];
        } else if (typeof currentVisualization[key] === 'object' && currentVisualization[key] !== null) {
          currentVisualization[key] = {};
        } else {
          currentVisualization[key] = '';
        }
      });
      currentVisualization.height = 300;
      
      isEditing.value = false;
      dialogVisible.value = true;
    };
    
    // 编辑可视化
    const editVisualization = (index) => {
      const item = visualizations.value[index];
      
      // 复制配置到当前可视化
      Object.keys(currentVisualization).forEach(key => {
        if (item[key] !== undefined) {
          if (Array.isArray(item[key])) {
            currentVisualization[key] = [...item[key]];
          } else if (typeof item[key] === 'object' && item[key] !== null) {
            currentVisualization[key] = { ...item[key] };
          } else {
            currentVisualization[key] = item[key];
          }
        }
      });
      
      isEditing.value = true;
      editIndex.value = index;
      dialogVisible.value = true;
    };
    
    // 删除可视化
    const deleteVisualization = (index) => {
      visualizations.value.splice(index, 1);
    };
    
    // 处理组件类型变更
    const handleTypeChange = () => {
      // 重置相关属性
      if (currentVisualization.type === 'chart') {
        currentVisualization.chartType = '';
      } else if (currentVisualization.type === 'table') {
        currentVisualization.tableFeatures = [];
      } else if (currentVisualization.type === 'analysis') {
        currentVisualization.analysisType = '';
      }
    };
    
    // 处理数据源变更
    const handleDataSourceChange = () => {
      // 重置相关属性
      currentVisualization.data = null;
      
      if (currentVisualization.dataSource === 'database') {
        currentVisualization.dbType = '';
        currentVisualization.connectionString = '';
        currentVisualization.query = '';
      } else if (currentVisualization.dataSource === 'local') {
        currentVisualization.file = null;
      }
    };
    
    // 处理文件上传
    const handleFileChange = (file) => {
      if (!file || !file.raw) {
        ElMessage.error('文件上传失败');
        return;
      }

      currentVisualization.file = file.raw;
      
      // 自动执行文件解析
      parseUploadedFile(file.raw);
    };
    
    // 解析上传的文件
    const parseUploadedFile = async (fileObj) => {
      if (!fileObj) return;
      
      try {
        loading.value = true;
        const result = await parseFile(fileObj);
        
        // 保存解析的数据和列信息
        parsedData.value = result.data;
        parsedColumns.value = result.columns;
        
        // 默认选择所有列
        selectedColumns.value = [...result.columns];
        console.log('文件解析完成，默认选择的列:', selectedColumns.value);
        
        // 更新列选择器选项
        columnOptions.value = getColumnOptions(result.columns);
        
        // 初始化列选择表格
        initColumnSelection();
        
        ElMessage.success(`文件解析成功，共 ${result.total} 条数据`);
      } catch (error) {
        ElMessage.error(error.message || '文件解析失败');
        console.error('文件解析错误:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 预览数据
    const loadPreviewData = () => {
      if (currentVisualization.dataSource === 'local') {
        if (parsedData.value.length > 0) {
          updatePreviewData();
        } else if (currentVisualization.file) {
          parseUploadedFile(currentVisualization.file);
        } else {
          ElMessage.warning('请先选择文件');
        }
      } else if (currentVisualization.dataSource === 'database') {
        // 模拟数据库查询，这里简单模拟
        ElMessage({
          message: '数据库查询已执行，请查看预览',
          type: 'success'
        });
        previewData.value = [
          { 'id': 1, 'name': '数据1', 'value': 100 },
          { 'id': 2, 'name': '数据2', 'value': 200 },
          { 'id': 3, 'name': '数据3', 'value': 300 }
        ];
        previewColumns.value = ['id', 'name', 'value'];
        previewVisible.value = true;
      }
    };
    
    // 添加图表错误处理
    const handleChartError = (error) => {
      console.error('图表渲染错误:', error);
      ElMessage.error(`图表渲染失败: ${error}`);
    };
    
    // 获取图表配置，确保数据格式正确
    const getChartOptions = (item) => {
      console.log('生成图表配置, 类型:', item.chartType, '数据长度:', item.data?.length, '列:', item.columns);
      
      // 检查数据中实际包含的键（应该与选择的列一致）
      const dataKeys = (item.data && item.data.length > 0) ? Object.keys(item.data[0]) : [];
      console.log('数据对象中的实际键:', dataKeys);
      console.log('期望的列:', item.columns);
      
      // 基础配置
      const options = {
        backgroundColor: '#fff',
        animation: false, // 禁用动画，减少性能问题
        ...item.options
      };

      // 确保数据存在
      if (!item.data || item.data.length === 0 || !item.columns || item.columns.length === 0) {
        console.warn('没有数据或列定义');
        return options;
      }

      // 根据图表类型优化配置
      if (item.chartType === 'line' || item.chartType === 'area' || item.chartType === 'bar') {
        // 确保有X轴数据
        const xAxisKey = item.columns[0]; // 使用第一列作为X轴
        // 定义系列键
        const seriesKeys = item.columns.slice(1); // 除第一列外的所有列作为系列
        
        options.xAxis = options.xAxis || {
          type: 'category',
          data: item.data.map(row => row[xAxisKey]),
          name: xAxisKey,
          nameLocation: 'middle',
          nameGap: 30,
          axisLabel: { 
            rotate: item.data.length > 10 ? 45 : 0,
            interval: 'auto',
            showMaxLabel: true,
            hideOverlap: true
          }
        };
        
        options.yAxis = options.yAxis || { 
          type: 'value',
          name: seriesKeys.length > 0 ? seriesKeys[0] : '', // 添加Y轴名称（使用第一个系列名）
          nameLocation: 'middle',
          nameGap: 50,
          nameRotate: 90
        };
        
        // 构建系列数据
        if (seriesKeys.length === 0) {
          console.warn('没有足够的数据列来创建图表系列，将使用X轴数据作为唯一系列');
          // 使用X轴数据创建一个默认系列
          options.series = [{
            name: item.columns[0],
            type: item.chartType === 'area' ? 'line' : item.chartType,
            data: item.data.map(row => row[item.columns[0]]),
            ...(item.chartType === 'area' ? { areaStyle: {} } : {})
          }];
          return options;
        }
        
        options.series = seriesKeys.map(key => ({
          name: key,
          type: item.chartType === 'area' ? 'line' : item.chartType,
          data: item.data.map(row => row[key]),
          ...(item.chartType === 'area' ? { areaStyle: {} } : {})
        }));
      } else if (item.chartType === 'scatter' || item.chartType === 'scatter3d') {
        // 散点图特殊处理
        const is3D = item.chartType === 'scatter3d';
        
        // 确保至少有2个维度(3D需要3个)
        if (item.columns.length < (is3D ? 3 : 2)) {
          console.warn(`${is3D ? '3D散点图' : '散点图'}需要至少${is3D ? 3 : 2}个数据维度`);
          return options;
        }
        
        // 定义维度列（前2或3列）
        const dims = item.columns.slice(0, is3D ? 3 : 2);
        
        if (is3D) {
          options.xAxis3D = options.xAxis3D || { 
            type: 'value', 
            name: dims[0],
            nameTextStyle: { fontSize: 12 }
          };
          options.yAxis3D = options.yAxis3D || { 
            type: 'value', 
            name: dims[1],
            nameTextStyle: { fontSize: 12 }
          };
          options.zAxis3D = options.zAxis3D || { 
            type: 'value', 
            name: dims[2],
            nameTextStyle: { fontSize: 12 }
          };
          options.grid3D = options.grid3D || {
            viewControl: {
              autoRotate: false,
              projection: 'perspective'
            }
          };
        } else {
          options.xAxis = options.xAxis || { 
            type: 'value', 
            name: dims[0],
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: { fontSize: 12 }
          };
          options.yAxis = options.yAxis || { 
            type: 'value', 
            name: dims[1],
            nameLocation: 'middle',
            nameGap: 50,
            nameRotate: 90,
            nameTextStyle: { fontSize: 12 }
          };
        }
        
        options.series = [{
          type: is3D ? 'scatter3D' : 'scatter',
          data: item.data.map(row => dims.map(key => row[key])),
          symbolSize: 10,
          itemStyle: {
            opacity: 0.8
          }
        }];
        
        console.log(`已生成${is3D ? '3D' : ''}散点图配置`);
      }

      return options;
    };
    
    // 添加图表组件Mount完成的回调
    const handleChartMounted = () => {
      console.log('图表组件挂载完成');
    };
    
    // 修改保存可视化函数
    const saveVisualization = () => {
      // 准备保存的数据
      const visualization = {
        title: currentVisualization.title,
        type: currentVisualization.type,
        dataSource: currentVisualization.dataSource,
        options: {}
      };
      
      // 根据组件类型添加特有属性
      if (currentVisualization.type === 'chart') {
        visualization.chartType = currentVisualization.chartType;
        visualization.height = currentVisualization.height;
        
        // 添加特定图表类型的默认配置
        switch (currentVisualization.chartType) {
          case 'line':
          case 'area':
          case 'bar':
            visualization.options = {
              legend: { 
                show: true,
                top: '5px', // 将图例放在顶部
                type: 'scroll', // 可滚动图例
                padding: [5, 10], // 填充
                textStyle: {
                  fontSize: 12 // 调整文字大小
                }
              },
              tooltip: { trigger: 'axis' },
              grid: { left: '8%', right: '4%', bottom: '15%', top: '10%', containLabel: true }
            };
            break;
          case 'scatter':
          case 'scatter3d':
            visualization.options = {
              visualMap: {
                show: false,
                dimension: 2,
                min: 0,
                max: 100
              }
            };
            break;
        }
      } else if (currentVisualization.type === 'table') {
        visualization.tableFeatures = [...currentVisualization.tableFeatures];
      } else if (currentVisualization.type === 'analysis') {
        visualization.analysisType = currentVisualization.analysisType;
      }
      
      // 处理数据源
          // 图表类型特殊检查
          if (currentVisualization.type === 'chart') {
            // 确保至少选择了一列数据
            if (selectedColumns.value.length < 1) {
              ElMessage.warning('请至少选择一列数据');
              return;
            }
            
            // 散点图需要额外检查
            if ((currentVisualization.chartType === 'scatter' && selectedColumns.value.length < 2) ||
                (currentVisualization.chartType === 'scatter3d' && selectedColumns.value.length < 3)) {
              ElMessage.warning(`${currentVisualization.chartType === 'scatter3d' ? '3D散点图' : '散点图'}至少需要${currentVisualization.chartType === 'scatter3d' ? '3' : '2'}列数据`);
              return;
            }
          }
          
      if (currentVisualization.dataSource === 'database') {
        // 数据库数据无需过滤，已经通过SQL选择了列
        visualization.dbType = currentVisualization.dbType;
        visualization.connectionString = currentVisualization.connectionString;
        visualization.query = currentVisualization.query;
        visualization.data = [];  // 会通过API获取
        visualization.columns = [];
      } else if (currentVisualization.dataSource === 'local') {
        // 使用已解析的数据
        if (parsedData.value.length > 0 && selectedColumns.value.length > 0) {
          try {
            // 只保留用户选择的列
            const filteredData = parsedData.value.map(item => {
              const filtered = {};
              // 只处理选择的列
              selectedColumns.value.forEach(col => {
                // 尝试转换数值类型
                if (typeof item[col] === 'string' && !isNaN(Number(item[col]))) {
                  filtered[col] = Number(item[col]);
                } else {
                  filtered[col] = item[col];
                }
              });
              return filtered;
            });
            
            // 确保每个数据对象只包含选择的列
            console.log('筛选前数据示例 - 属性数:', Object.keys(parsedData.value[0]).length);
            console.log('筛选后数据示例 - 属性数:', Object.keys(filteredData[0]).length);
            console.log('选择的列数:', selectedColumns.value.length);
            
            visualization.data = filteredData;
            visualization.columns = [...selectedColumns.value];
            visualization.file = currentVisualization.file ? currentVisualization.file.name : null;
            
            console.log('使用本地文件数据:', visualization.data);
            console.log('选择的列:', visualization.columns);
          } catch (error) {
            console.error('数据处理错误:', error);
            ElMessage.warning('数据处理出错，请检查格式');
            return;
          }
        } else {
          ElMessage.warning('没有可用数据或未选择数据列，请先上传并解析文件并选择数据列');
          return;
        }
      }
      
      // 保存或更新
      if (isEditing.value) {
        visualizations.value[editIndex.value] = visualization;
      } else {
        visualizations.value.push(visualization);
      }
      
      // 关闭对话框
      dialogVisible.value = false;
      
      // 使用更长的延迟确保DOM完全更新
      nextTick(() => {
        setTimeout(() => {
          console.log('可视化已添加，等待图表初始化...');
        }, 300);
      });
      
      ElMessage({
        message: isEditing.value ? '可视化已更新' : '可视化已创建',
        type: 'success'
      });
    };
    
    return {
      visualizations,
      dialogVisible,
      isEditing,
      currentVisualization,
      canSave,
      getComponentType,
      addNewVisualization,
      editVisualization,
      deleteVisualization,
      handleTypeChange,
      handleDataSourceChange,
      handleFileChange,
      saveVisualization,
      parsedData,
      parsedColumns,
      selectedColumns,
      columnOptions,
      loading,
      parseUploadedFile,
      columnTableRef,
      selectAllColumns,
      deselectAllColumns,
      handleChartError,
      getChartOptions,
      columnSelectionData,
      handleColumnsSelectionChange,
      handleChartMounted
    };
  }
}
</script>

<style scoped>
.custom-visualization-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-description {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.header-card {
  margin-bottom: 20px;
}

.visualization-workspace {
  margin-top: 20px;
}

.visualization-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 20px;
}

.visualization-card {
  margin-bottom: 20px;
}

.visualization-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.visualization-actions {
  display: flex;
  gap: 5px;
}

.data-preview {
  margin-top: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.column-selection-table {
  margin-bottom: 20px;
  width: 100%;
}

.sample-data-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 100%;
  overflow: hidden;
}

.sample-data-item {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.column-selection-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

/* 增加表格内部间距 */
:deep(.el-table td) {
  padding: 8px 0;
}

:deep(.el-table th) {
  padding: 10px 0;
  font-weight: bold;
}

:deep(.el-form-item__content) {
  width: 100%;
}

/* 添加数据列使用说明样式 */
.column-usage-tips {
  margin-bottom: 15px;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.column-usage-tips h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #409eff;
}

.column-usage-tips ul {
  margin: 0;
  padding-left: 20px;
}

.column-usage-tips li {
  margin-bottom: 5px;
  font-size: 13px;
  color: #606266;
}

/* 解决表格在某些浏览器中的样式问题 */
:deep(.el-table__inner-wrapper) {
  overflow: hidden;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
}

/* 优化可视化组件显示 */
.visualization-component {
  width: 100%;
  overflow: hidden;
}

.visualization-card {
  margin-bottom: 20px;
  overflow: hidden;
}

/* 确保图表容器有足够的空间 */
.visualization-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

/* 解决某些浏览器中表格布局问题 */
:deep(.el-card__body) {
  overflow: hidden;
  padding: 10px;
}
</style> 