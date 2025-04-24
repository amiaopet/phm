<template>
  <div class="data-analysis-container">
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>数据分析中...</span>
    </div>
    <div v-else-if="error" class="error-container">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>
    <div v-else>
      <!-- 基础统计分析 -->
      <div v-if="analysisType === 'basic'" class="basic-statistics">
        <h3>基础统计分析</h3>
        <el-descriptions :column="3" border>
          <el-descriptions-item v-for="(value, key) in basicStats" :key="key" :label="key">
            {{ formatValue(value) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="histogramData.labels.length > 0" class="histogram-container">
          <h4>数据分布</h4>
          <div ref="histogramRef" class="histogram-chart"></div>
        </div>
      </div>
      
      <!-- 相关性分析 -->
      <div v-else-if="analysisType === 'correlation'" class="correlation-analysis">
        <h3>相关性分析</h3>
        <div ref="correlationRef" class="correlation-chart"></div>
        <div class="correlation-table-container">
          <el-table :data="correlationTableData" border style="width: 100%">
            <el-table-column
              v-for="column in correlationColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :min-width="column.minWidth || 100"
            ></el-table-column>
          </el-table>
        </div>
      </div>
      
      <!-- 趋势分析 -->
      <div v-else-if="analysisType === 'trend'" class="trend-analysis">
        <h3>趋势分析</h3>
        <div ref="trendRef" class="trend-chart"></div>
        <div class="trend-analysis-metrics">
          <el-descriptions :column="4" border>
            <el-descriptions-item label="趋势系数">{{ trendMetrics.coefficient || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="R²值">{{ trendMetrics.rSquared || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="P值">{{ trendMetrics.pValue || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="预测趋势">
              <el-tag :type="getTrendTagType(trendMetrics.trend)">{{ trendMetrics.trend || 'N/A' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <!-- 异常检测 -->
      <div v-else-if="analysisType === 'anomaly'" class="anomaly-detection">
        <h3>异常检测</h3>
        <div ref="anomalyRef" class="anomaly-chart"></div>
        <div class="anomaly-metrics">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="异常点数量">{{ anomalyMetrics.anomalyCount || 0 }}</el-descriptions-item>
            <el-descriptions-item label="异常率">{{ anomalyMetrics.anomalyRate || '0%' }}</el-descriptions-item>
            <el-descriptions-item label="检测阈值">{{ anomalyMetrics.threshold || 'N/A' }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div v-if="anomalyTableData.length > 0" class="anomaly-table-container">
          <h4>异常数据点</h4>
          <el-table :data="anomalyTableData" border style="width: 100%" max-height="200">
            <el-table-column
              v-for="column in anomalyColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
            ></el-table-column>
          </el-table>
        </div>
      </div>
      
      <!-- 频谱分析 -->
      <div v-else-if="analysisType === 'spectrum'" class="spectrum-analysis">
        <h3>频谱分析</h3>
        <div ref="spectrumRef" class="spectrum-chart"></div>
        <div class="spectrum-metrics">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="主频">{{ spectrumMetrics.mainFrequency || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="最大幅值">{{ spectrumMetrics.maxAmplitude || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="信噪比">{{ spectrumMetrics.snr || 'N/A' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <!-- 未支持的分析类型 -->
      <el-empty v-else description="暂不支持该分析类型"></el-empty>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

export default {
  name: 'DataAnalysisComponent',
  components: {
    Loading,
    WarningFilled
  },
  props: {
    analysisType: {
      type: String,
      required: true,
      validator: (value) => {
        return ['basic', 'correlation', 'trend', 'anomaly', 'spectrum'].includes(value)
      }
    },
    analysisData: {
      type: Array,
      default: () => []
    },
    analysisOptions: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    // 状态管理
    const loading = ref(true)
    const error = ref('')
    
    // 图表容器引用
    const histogramRef = ref(null)
    const correlationRef = ref(null)
    const trendRef = ref(null)
    const anomalyRef = ref(null)
    const spectrumRef = ref(null)
    
    // 基础统计分析数据
    const basicStats = ref({})
    const histogramData = ref({ labels: [], values: [] })
    
    // 相关性分析数据
    const correlationTableData = ref([])
    const correlationColumns = ref([])
    
    // 趋势分析数据
    const trendMetrics = ref({
      coefficient: null,
      rSquared: null,
      pValue: null,
      trend: null
    })
    
    // 异常检测数据
    const anomalyMetrics = ref({
      anomalyCount: 0,
      anomalyRate: '0%',
      threshold: null
    })
    const anomalyTableData = ref([])
    const anomalyColumns = ref([])
    
    // 频谱分析数据
    const spectrumMetrics = ref({
      mainFrequency: null,
      maxAmplitude: null,
      snr: null
    })
    
    // 各类图表实例
    const chartInstances = {
      histogram: null,
      correlation: null,
      trend: null,
      anomaly: null,
      spectrum: null
    }
    
    // 值格式化
    const formatValue = (value) => {
      if (value === null || value === undefined) return 'N/A'
      if (typeof value === 'number') {
        // 如果是小数，保留两位小数
        return Number.isInteger(value) ? value : value.toFixed(2)
      }
      return value
    }
    
    // 获取趋势标签类型
    const getTrendTagType = (trend) => {
      if (!trend) return 'info'
      switch (trend.toLowerCase()) {
        case '上升':
        case '增长':
        case 'increase':
          return 'success'
        case '下降':
        case 'decrease':
          return 'danger'
        case '稳定':
        case 'stable':
          return 'info'
        default:
          return 'info'
      }
    }
    
    // 分析数据处理函数
    const analyzeData = () => {
      loading.value = true
      error.value = ''
      
      try {
        if (!props.analysisData || props.analysisData.length === 0) {
          error.value = '无可分析数据'
          return
        }
        
        // 根据分析类型调用不同的分析方法
        switch (props.analysisType) {
          case 'basic':
            performBasicAnalysis()
            break
          case 'correlation':
            performCorrelationAnalysis()
            break
          case 'trend':
            performTrendAnalysis()
            break
          case 'anomaly':
            performAnomalyDetection()
            break
          case 'spectrum':
            performSpectrumAnalysis()
            break
          default:
            error.value = '不支持的分析类型'
        }
      } catch (e) {
        error.value = '分析过程中出错: ' + e.message
        console.error('数据分析错误:', e)
      } finally {
        loading.value = false
      }
    }
    
    // 基础统计分析
    const performBasicAnalysis = () => {
      const data = props.analysisData
      const firstItem = data[0]
      const stats = {}
      
      // 处理每一列数据
      for (const key of Object.keys(firstItem)) {
        // 跳过非数值列
        if (typeof firstItem[key] !== 'number' && isNaN(parseFloat(firstItem[key]))) {
          continue
        }
        
        // 收集该列的所有数值
        const values = data.map(item => {
          const value = item[key]
          return typeof value === 'number' ? value : parseFloat(value) || 0
        })
        
        // 计算统计指标
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length
        const sortedValues = [...values].sort((a, b) => a - b)
        const min = sortedValues[0]
        const max = sortedValues[sortedValues.length - 1]
        const median = sortedValues[Math.floor(sortedValues.length / 2)]
        
        // 计算标准差
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
        const stdDev = Math.sqrt(variance)
        
        // 存储该列的统计结果
        stats[`${key} (平均值)`] = mean
        stats[`${key} (中位数)`] = median
        stats[`${key} (最小值)`] = min
        stats[`${key} (最大值)`] = max
        stats[`${key} (标准差)`] = stdDev
      }
      
      // 更新统计结果
      basicStats.value = stats
      
      // 生成直方图数据（使用第一个数值列）
      const firstNumericKey = Object.keys(firstItem).find(key => 
        typeof firstItem[key] === 'number' || !isNaN(parseFloat(firstItem[key]))
      )
      
      if (firstNumericKey) {
        const values = data.map(item => {
          const value = item[firstNumericKey]
          return typeof value === 'number' ? value : parseFloat(value) || 0
        })
        
        // 生成直方图所需的bins
        const min = Math.min(...values)
        const max = Math.max(...values)
        const binCount = Math.min(10, Math.ceil(Math.sqrt(values.length)))
        const binWidth = (max - min) / binCount
        
        const bins = Array(binCount).fill(0)
        const binLabels = []
        
        // 生成bin标签
        for (let i = 0; i < binCount; i++) {
          const binStart = min + i * binWidth
          const binEnd = binStart + binWidth
          binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`)
        }
        
        // 统计每个bin中的数据点数量
        values.forEach(value => {
          if (value === max) {
            // 处理最大值的特殊情况
            bins[binCount - 1]++
          } else {
            const binIndex = Math.floor((value - min) / binWidth)
            bins[binIndex]++
          }
        })
        
        // 更新直方图数据
        histogramData.value = {
          labels: binLabels,
          values: bins
        }
        
        // 创建直方图
        setTimeout(() => {
          createHistogram(histogramData.value)
        }, 100)
      }
    }
    
    // 创建直方图
    const createHistogram = (data) => {
      if (!histogramRef.value) return
      
      // 销毁旧的图表实例
      if (chartInstances.histogram) {
        chartInstances.histogram.dispose()
      }
      
      // 创建新的图表实例
      chartInstances.histogram = echarts.init(histogramRef.value)
      
      // 设置图表配置
      chartInstances.histogram.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.labels,
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: '频率',
          type: 'bar',
          data: data.values,
          itemStyle: {
            color: '#5470c6'
          }
        }]
      })
    }
    
    // 相关性分析
    const performCorrelationAnalysis = () => {
      const data = props.analysisData
      const firstItem = data[0]
      
      // 提取所有数值列
      const numericColumns = Object.keys(firstItem).filter(key => 
        typeof firstItem[key] === 'number' || !isNaN(parseFloat(firstItem[key]))
      )
      
      if (numericColumns.length < 2) {
        error.value = '需要至少两个数值列进行相关性分析'
        return
      }
      
      // 提取每列的数值
      const columnValues = {}
      numericColumns.forEach(col => {
        columnValues[col] = data.map(item => {
          const value = item[col]
          return typeof value === 'number' ? value : parseFloat(value) || 0
        })
      })
      
      // 计算相关系数矩阵
      const correlationMatrix = {}
      numericColumns.forEach(col1 => {
        correlationMatrix[col1] = {}
        numericColumns.forEach(col2 => {
          // 计算Pearson相关系数
          correlationMatrix[col1][col2] = calculateCorrelation(columnValues[col1], columnValues[col2])
        })
      })
      
      // 转换为表格数据格式
      correlationColumns.value = [
        { prop: 'feature', label: '特征', width: 150 },
        ...numericColumns.map(col => ({ prop: col, label: col }))
      ]
      
      correlationTableData.value = numericColumns.map(col => {
        const row = { feature: col }
        numericColumns.forEach(otherCol => {
          row[otherCol] = formatValue(correlationMatrix[col][otherCol])
        })
        return row
      })
      
      // 创建热力图
      setTimeout(() => {
        createCorrelationHeatmap(correlationMatrix, numericColumns)
      }, 100)
    }
    
    // 计算Pearson相关系数
    const calculateCorrelation = (x, y) => {
      const n = x.length
      
      // 计算均值
      const xMean = x.reduce((sum, val) => sum + val, 0) / n
      const yMean = y.reduce((sum, val) => sum + val, 0) / n
      
      // 计算分子（协方差）
      let numerator = 0
      for (let i = 0; i < n; i++) {
        numerator += (x[i] - xMean) * (y[i] - yMean)
      }
      
      // 计算分母（标准差乘积）
      let xSumSquares = 0
      let ySumSquares = 0
      for (let i = 0; i < n; i++) {
        xSumSquares += Math.pow(x[i] - xMean, 2)
        ySumSquares += Math.pow(y[i] - yMean, 2)
      }
      
      const denominator = Math.sqrt(xSumSquares * ySumSquares)
      
      // 处理分母为0的情况
      if (denominator === 0) return 0
      
      return numerator / denominator
    }
    
    // 创建相关性热力图
    const createCorrelationHeatmap = (correlationMatrix, features) => {
      if (!correlationRef.value) return
      
      // 销毁旧的图表实例
      if (chartInstances.correlation) {
        chartInstances.correlation.dispose()
      }
      
      // 创建新的图表实例
      chartInstances.correlation = echarts.init(correlationRef.value)
      
      // 准备热力图数据
      const data = []
      features.forEach((col1, i) => {
        features.forEach((col2, j) => {
          const value = correlationMatrix[col1][col2]
          data.push([i, j, parseFloat(value.toFixed(2))])
        })
      })
      
      // 设置图表配置
      chartInstances.correlation.setOption({
        tooltip: {
          position: 'top',
          formatter: function (params) {
            const x = features[params.data[0]]
            const y = features[params.data[1]]
            return `${x} 和 ${y} 的相关系数: ${params.data[2]}`
          }
        },
        grid: {
          left: '3%',
          right: '7%',
          bottom: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: features,
          axisLabel: {
            interval: 0,
            rotate: 45
          }
        },
        yAxis: {
          type: 'category',
          data: features
        },
        visualMap: {
          min: -1,
          max: 1,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '0%',
          inRange: {
            color: ['#d94e5d', '#eac736', '#50a3ba']
          }
        },
        series: [{
          name: '相关系数',
          type: 'heatmap',
          data: data,
          label: {
            show: true,
            formatter: function (params) {
              return params.data[2].toFixed(2)
            }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      })
    }
    
    // 趋势分析
    const performTrendAnalysis = () => {
      const data = props.analysisData
      const firstItem = data[0]
      
      // 需要一个时间列和一个数值列
      const timeKey = Object.keys(firstItem).find(key => {
        const value = firstItem[key]
        return typeof value === 'string' && (
          !isNaN(Date.parse(value)) || 
          /^\d{2}:\d{2}(:\d{2})?$/.test(value) ||
          /^\d{4}-\d{2}-\d{2}/.test(value)
        )
      })
      
      const valueKey = Object.keys(firstItem).find(key => 
        key !== timeKey && (typeof firstItem[key] === 'number' || !isNaN(parseFloat(firstItem[key])))
      )
      
      if (!timeKey || !valueKey) {
        error.value = '趋势分析需要一个时间列和一个数值列'
        return
      }
      
      // 提取并排序数据
      const timePoints = data.map(item => item[timeKey])
      const values = data.map(item => {
        const value = item[valueKey]
        return typeof value === 'number' ? value : parseFloat(value) || 0
      })
      
      // 简单线性回归
      const n = values.length
      const indices = Array.from({ length: n }, (_, i) => i + 1)
      
      // 计算平均值
      const xMean = indices.reduce((sum, val) => sum + val, 0) / n
      const yMean = values.reduce((sum, val) => sum + val, 0) / n
      
      // 计算斜率和截距
      let numerator = 0
      let denominator = 0
      for (let i = 0; i < n; i++) {
        numerator += (indices[i] - xMean) * (values[i] - yMean)
        denominator += Math.pow(indices[i] - xMean, 2)
      }
      
      const slope = denominator !== 0 ? numerator / denominator : 0
      const intercept = yMean - slope * xMean
      
      // 计算预测值和R²
      const predictions = indices.map(x => slope * x + intercept)
      const ssr = predictions.reduce((sum, pred, i) => sum + Math.pow(pred - yMean, 2), 0)
      const sst = values.reduce((sum, val) => sum + Math.pow(val - yMean, 2), 0)
      const rSquared = sst !== 0 ? ssr / sst : 0
      
      // 确定趋势
      let trend
      if (Math.abs(slope) < 0.001) {
        trend = '稳定'
      } else if (slope > 0) {
        trend = '上升'
      } else {
        trend = '下降'
      }
      
      // 更新趋势指标
      trendMetrics.value = {
        coefficient: slope.toFixed(4),
        rSquared: rSquared.toFixed(4),
        pValue: 'N/A', // 简化版不计算p值
        trend: trend
      }
      
      // 创建趋势图
      setTimeout(() => {
        createTrendChart(timePoints, values, predictions)
      }, 100)
    }
    
    // 创建趋势图
    const createTrendChart = (timePoints, values, predictions) => {
      if (!trendRef.value) return
      
      // 销毁旧的图表实例
      if (chartInstances.trend) {
        chartInstances.trend.dispose()
      }
      
      // 创建新的图表实例
      chartInstances.trend = echarts.init(trendRef.value)
      
      // 设置图表配置
      chartInstances.trend.setOption({
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['实际值', '趋势线']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: timePoints,
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '实际值',
            type: 'scatter',
            data: values,
            symbolSize: 8,
            itemStyle: {
              color: '#5470c6'
            }
          },
          {
            name: '趋势线',
            type: 'line',
            data: predictions,
            smooth: true,
            showSymbol: false,
            itemStyle: {
              color: '#ee6666'
            }
          }
        ]
      })
    }
    
    // 异常检测
    const performAnomalyDetection = () => {
      const data = props.analysisData
      const firstItem = data[0]
      
      // 需要一个时间列和一个数值列
      const timeKey = Object.keys(firstItem).find(key => {
        const value = firstItem[key]
        return typeof value === 'string' && (
          !isNaN(Date.parse(value)) || 
          /^\d{2}:\d{2}(:\d{2})?$/.test(value) ||
          /^\d{4}-\d{2}-\d{2}/.test(value)
        )
      })
      
      const valueKey = Object.keys(firstItem).find(key => 
        key !== timeKey && (typeof firstItem[key] === 'number' || !isNaN(parseFloat(firstItem[key])))
      )
      
      if (!timeKey || !valueKey) {
        error.value = '异常检测需要一个时间列和一个数值列'
        return
      }
      
      // 提取数据
      const timePoints = data.map(item => item[timeKey])
      const values = data.map(item => {
        const value = item[valueKey]
        return typeof value === 'number' ? value : parseFloat(value) || 0
      })
      
      // 简单异常检测：使用Z-Score方法
      // 计算均值和标准差
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
      const stdDev = Math.sqrt(variance)
      
      // 设定阈值
      const threshold = 2.0 // Z-Score阈值
      
      // 检测异常
      const anomalies = []
      const anomalyIndices = []
      
      values.forEach((value, index) => {
        const zScore = Math.abs((value - mean) / stdDev)
        if (zScore > threshold) {
          anomalies.push({
            time: timePoints[index],
            value: value,
            zScore: zScore.toFixed(2)
          })
          anomalyIndices.push(index)
        }
      })
      
      // 更新异常检测指标
      anomalyMetrics.value = {
        anomalyCount: anomalies.length,
        anomalyRate: ((anomalies.length / values.length) * 100).toFixed(2) + '%',
        threshold: `Z-Score > ${threshold}`
      }
      
      // 设置异常表格列
      anomalyColumns.value = [
        { prop: 'time', label: '时间点' },
        { prop: 'value', label: '值' },
        { prop: 'zScore', label: 'Z-Score' }
      ]
      
      // 更新异常表格数据
      anomalyTableData.value = anomalies
      
      // 创建异常检测图
      setTimeout(() => {
        createAnomalyChart(timePoints, values, anomalyIndices)
      }, 100)
    }
    
    // 创建异常检测图
    const createAnomalyChart = (timePoints, values, anomalyIndices) => {
      if (!anomalyRef.value) return
      
      // 销毁旧的图表实例
      if (chartInstances.anomaly) {
        chartInstances.anomaly.dispose()
      }
      
      // 创建新的图表实例
      chartInstances.anomaly = echarts.init(anomalyRef.value)
      
      // 准备异常点数据
      const anomalyData = anomalyIndices.map(index => ({
        name: timePoints[index],
        value: [timePoints[index], values[index]],
        itemStyle: {
          color: '#ee6666'
        }
      }))
      
      // 设置图表配置
      chartInstances.anomaly.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            if (params.length > 0) {
              const isAnomaly = anomalyIndices.includes(params[0].dataIndex)
              return `${params[0].name}<br/>${params[0].seriesName}: ${params[0].value}${isAnomaly ? '<br/><span style="color:#ee6666">异常点</span>' : ''}`
            }
            return ''
          }
        },
        legend: {
          data: ['数据序列', '异常点']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: timePoints,
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '数据序列',
            type: 'line',
            data: values,
            smooth: true,
            markPoint: {
              data: anomalyData
            }
          },
          {
            name: '异常点',
            type: 'scatter',
            symbolSize: 10,
            data: anomalyIndices.map(index => [timePoints[index], values[index]]),
            itemStyle: {
              color: '#ee6666'
            }
          }
        ]
      })
    }
    
    // 频谱分析（简化版）
    const performSpectrumAnalysis = () => {
      const data = props.analysisData
      const firstItem = data[0]
      
      // 需要一个数值列
      const valueKey = Object.keys(firstItem).find(key => 
        typeof firstItem[key] === 'number' || !isNaN(parseFloat(firstItem[key]))
      )
      
      if (!valueKey) {
        error.value = '频谱分析需要一个数值列'
        return
      }
      
      // 提取数据
      const values = data.map(item => {
        const value = item[valueKey]
        return typeof value === 'number' ? value : parseFloat(value) || 0
      })
      
      // 简化的频谱分析（因为浏览器中没有FFT库，这里模拟一个简单的频谱）
      // 生成一些频率点
      const frequencies = []
      const amplitudes = []
      
      // 模拟简单的频谱
      for (let i = 1; i <= 20; i++) {
        const freq = i / 2 // 模拟频率点
        const amp = Math.abs(
          Math.sin(i * 0.4) * 3 + 
          Math.random() * 0.5
        ) // 模拟振幅
        
        frequencies.push(freq)
        amplitudes.push(amp)
      }
      
      // 找出主频（最大振幅对应的频率）
      let maxAmpIndex = 0
      for (let i = 1; i < amplitudes.length; i++) {
        if (amplitudes[i] > amplitudes[maxAmpIndex]) {
          maxAmpIndex = i
        }
      }
      
      // 更新频谱分析指标
      spectrumMetrics.value = {
        mainFrequency: frequencies[maxAmpIndex].toFixed(2) + ' Hz',
        maxAmplitude: amplitudes[maxAmpIndex].toFixed(2),
        snr: (20 * Math.log10(amplitudes[maxAmpIndex] / (amplitudes.reduce((sum, amp) => sum + amp, 0) / amplitudes.length))).toFixed(2) + ' dB'
      }
      
      // 创建频谱图
      setTimeout(() => {
        createSpectrumChart(frequencies, amplitudes, maxAmpIndex)
      }, 100)
    }
    
    // 创建频谱图
    const createSpectrumChart = (frequencies, amplitudes, maxAmpIndex) => {
      if (!spectrumRef.value) return
      
      // 销毁旧的图表实例
      if (chartInstances.spectrum) {
        chartInstances.spectrum.dispose()
      }
      
      // 创建新的图表实例
      chartInstances.spectrum = echarts.init(spectrumRef.value)
      
      // 设置图表配置
      chartInstances.spectrum.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            return `频率: ${params[0].name} Hz<br/>振幅: ${params[0].value}`
          }
        },
        legend: {
          data: ['频谱']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          name: '频率 (Hz)',
          data: frequencies.map(f => f.toFixed(1))
        },
        yAxis: {
          type: 'value',
          name: '振幅'
        },
        series: [
          {
            name: '频谱',
            type: 'bar',
            data: amplitudes.map((amp, index) => {
              return {
                value: amp,
                itemStyle: {
                  color: index === maxAmpIndex ? '#ee6666' : '#5470c6'
                }
              }
            }),
            markPoint: {
              data: [
                { 
                  name: '主频', 
                  coord: [frequencies[maxAmpIndex].toFixed(1), amplitudes[maxAmpIndex]],
                  value: '主频'
                }
              ]
            }
          }
        ]
      })
    }
    
    // 组件挂载后执行分析
    onMounted(() => {
      analyzeData()
    })
    
    // 当分析类型或数据变化时重新分析
    watch([() => props.analysisType, () => props.analysisData, () => props.analysisOptions], () => {
      analyzeData()
    }, { deep: true })
    
    // 监听窗口大小变化
    const handleResize = () => {
      Object.values(chartInstances).forEach(chart => {
        if (chart) chart.resize()
      })
    }
    
    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })
    
    return {
      loading,
      error,
      histogramRef,
      correlationRef,
      trendRef,
      anomalyRef,
      spectrumRef,
      basicStats,
      histogramData,
      correlationTableData,
      correlationColumns,
      trendMetrics,
      anomalyMetrics,
      anomalyTableData,
      anomalyColumns,
      spectrumMetrics,
      formatValue,
      getTrendTagType
    }
  }
}
</script>

<style scoped>
.data-analysis-container {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.loading-container .el-icon,
.error-container .el-icon {
  font-size: 30px;
  margin-bottom: 10px;
}

.error-container {
  color: #f56c6c;
}

.histogram-container,
.correlation-chart,
.trend-chart,
.anomaly-chart,
.spectrum-chart {
  height: 300px;
  margin: 16px 0;
}

.anomaly-table-container,
.correlation-table-container {
  margin-top: 16px;
}
</style>
