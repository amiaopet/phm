<template>
  <div class="chart-container" :style="{ height: `${height}px` }" :id="chartId">
    <!-- 图表容器始终存在，只是覆盖显示loading或error -->
    <div class="chart-body" :id="`${chartId}-body`"></div>
    
    <!-- 使用绝对定位的遮罩层，而不是条件渲染替换图表容器 -->
    <div v-if="loading" class="overlay-container loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>图表加载中...</span>
    </div>
    
    <div v-if="error" class="overlay-container error-container">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed, onBeforeUnmount, getCurrentInstance, nextTick } from 'vue'
import { Loading, WarningFilled } from '@element-plus/icons-vue'

export default {
  name: 'ChartComponent',
  components: {
    Loading,
    WarningFilled
  },
  props: {
    chartType: {
      type: String,
      required: true,
      validator: (value) => {
        return ['line', 'area', 'bar', 'scatter', 'histogram', 'boxplot', 'heatmap', 'radar', 'scatter3d'].includes(value)
      }
    },
    chartData: {
      type: Array,
      default: () => []
    },
    chartOptions: {
      type: Object,
      default: () => ({})
    },
    height: {
      type: Number,
      default: 300
    }
  },
  setup(props, { emit }) {
    // 生成唯一ID
    const chartId = `chart-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    const chartInstance = ref(null);
    const loading = ref(true);
    const error = ref('');
    
    // 获取当前组件实例，用于访问全局属性
    const { proxy } = getCurrentInstance();
    
    // 处理数据
    const processedData = computed(() => {
      if (!props.chartData || props.chartData.length === 0) {
        return {
          xAxis: [],
          series: []
        }
      }
      
      try {
        // 根据图表类型处理数据
        switch (props.chartType) {
          case 'line':
          case 'area':
          case 'bar':
            return processAxisData(props.chartData)
          case 'scatter':
          case 'scatter3d':
            return processScatterData(props.chartData)
          case 'histogram':
            return processHistogramData(props.chartData)
          case 'boxplot':
            return processBoxplotData(props.chartData)
          case 'heatmap':
            return processHeatmapData(props.chartData)
          case 'radar':
            return processRadarData(props.chartData)
          default:
            return { xAxis: [], series: [] }
        }
      } catch (e) {
        error.value = '数据处理错误: ' + e.message
        return { xAxis: [], series: [] }
      }
    })
    
    // 图表配置
    const chartConfig = computed(() => {
      const config = {
        grid: {
          left: '8%',    // 增大左侧边距，为Y轴名称留空间
          right: '4%',
          bottom: '15%', // 增大底部边距，为X轴名称留空间
          top: '10%',    // 调整顶部边距
          containLabel: true
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        ...props.chartOptions
      }
      
      // 根据图表类型设置配置
      switch (props.chartType) {
        case 'line':
          return getLineConfig(config, processedData.value)
        case 'area':
          return getAreaConfig(config, processedData.value)
        case 'bar':
          return getBarConfig(config, processedData.value)
        case 'scatter':
          return getScatterConfig(config, processedData.value)
        case 'histogram':
          return getHistogramConfig(config, processedData.value)
        case 'boxplot':
          return getBoxplotConfig(config, processedData.value)
        case 'heatmap':
          return getHeatmapConfig(config, processedData.value)
        case 'radar':
          return getRadarConfig(config, processedData.value)
        case 'scatter3d':
          return getScatter3DConfig(config, processedData.value)
        default:
          return config
      }
    })
    
    // 使用DOM ID而不是ref来获取容器
    const initChart = () => {
      console.log('开始初始化图表...');
      
      // 先设置加载状态
      loading.value = true;
      error.value = '';
      
      // 使用较长的延迟确保DOM完全渲染
      setTimeout(() => {
        try {
          // 使用ID直接获取DOM元素
          const container = document.getElementById(`${chartId}-body`);
          console.log('检查图表容器:', container);
          
          if (!container) {
            error.value = '图表容器不存在';
            loading.value = false;
            emit('error', '图表容器不存在');
            return;
          }
          
          // 获取容器尺寸
          const width = container.clientWidth;
          const height = container.clientHeight;
          console.log(`图表容器尺寸: ${width}x${height}`);
      
          // 销毁旧实例
      if (chartInstance.value) {
            console.log('销毁旧图表实例');
            chartInstance.value.dispose();
            chartInstance.value = null;
          }
          
          // 判断echarts是否存在
          if (!proxy.$echarts) {
            console.error('ECharts未全局注册');
            error.value = 'ECharts未加载';
            loading.value = false;
            return;
      }
      
          // 创建新的ECharts实例
          console.log('创建新的ECharts实例');
          chartInstance.value = proxy.$echarts.init(container, null, {
            renderer: 'canvas',
            useDirtyRect: false
          });
          
          // 检查数据
          if (!props.chartData || props.chartData.length === 0) {
            console.warn('无数据可显示');
            error.value = '无数据可显示';
            loading.value = false;
            return;
          }
          
          console.log('准备应用图表配置');
          
          // 检查图表配置是否包含必要的系列数据
          if (!chartConfig.value.series || chartConfig.value.series.length === 0) {
            console.error('图表配置中缺少必要的系列数据');
            error.value = '图表配置错误: 缺少系列数据';
            loading.value = false;
            return;
          }
          
          // 检查每个系列是否都有type属性
          const hasError = chartConfig.value.series.some(series => !series.type);
          if (hasError) {
            console.error('图表配置中有系列缺少type属性');
            error.value = '图表配置错误: 系列缺少type属性';
            loading.value = false;
            return;
          }
          
          // 应用图表配置
          try {
            chartInstance.value.setOption(chartConfig.value);
            console.log('图表渲染成功');
          } catch (e) {
            console.error('应用图表配置时出错:', e);
            error.value = `图表配置错误: ${e.message}`;
            emit('error', e.message);
          }
          
          loading.value = false;
      } catch (e) {
          console.error('图表渲染错误:', e);
          error.value = `图表错误: ${e.message}`;
          loading.value = false;
          emit('error', e.message);
      }
      }, 500);
    };
    
    // 轴数据处理（适用于线图、面积图、柱状图）
    const processAxisData = (data) => {
      console.log("处理轴数据，接收数据长度:", data?.length, "数据类型:", typeof data);
      if (!data || data.length === 0) return { xAxis: [], series: [] }
      
      // 提取所有唯一键，除了第一列（用作X轴）
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys, "键数量:", keys.length);
      
      // 确保至少有一个键
      if (keys.length === 0) {
        console.error("数据对象中没有任何属性键");
        return { xAxis: [], series: [] }
      }
      
      // 使用第一列作为X轴
      const xAxisKey = keys[0]
      // 使用剩余列作为系列数据
      const seriesKeys = keys.slice(1)
      
      console.log("使用X轴键:", xAxisKey);
      console.log("使用系列键:", seriesKeys);
      
      // 提取X轴数据
      const xAxis = data.map(item => item[xAxisKey])
      
      // 如果没有足够的系列数据列（至少需要一列），创建一个默认系列
      if (seriesKeys.length === 0) {
        console.warn("没有系列数据列，使用X轴数据创建默认系列");
        return {
          xAxis: xAxis,
          series: [{
            name: xAxisKey,
            data: data.map(item => item[xAxisKey]),
            type: props.chartType === 'area' ? 'line' : props.chartType
          }]
        }
      }
      
      // 处理系列数据
      const series = seriesKeys.map(key => {
        return {
          name: key,
          data: data.map(item => item[key]),
          type: props.chartType === 'area' ? 'line' : props.chartType // area在echarts中是使用areaStyle的line
        }
      })
      
      return { xAxis, series }
    }
    
    // 散点图数据处理
    const processScatterData = (data) => {
      if (!data || data.length === 0) return { series: [] }
      
      // 散点图需要提取两个维度，如果是3D则需要三个维度
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys);
      const is3D = props.chartType === 'scatter3d'
      
      // 确保至少有两个维度(3D需要三个)
      if (keys.length < (is3D ? 3 : 2)) {
        error.value = `散点图需要至少${is3D ? '3' : '2'}个数据维度`
        return { series: [] }
      }
      
      // 提取数据点
      const dimensionKeys = keys.slice(0, is3D ? 3 : 2)
      const scatterData = data.map(item => {
        return dimensionKeys.map(key => item[key])
      })
      
      return {
        series: [{
          type: is3D ? 'scatter3D' : 'scatter',
          data: scatterData
        }]
      }
    }
    
    // 直方图数据处理
    const processHistogramData = (data) => {
      if (!data || data.length === 0) return { series: [] }
      
      // 直方图通常需要单一数值列
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys);
      
      // 使用第一个数值列
      const valueKey = keys.find(key => typeof firstItem[key] === 'number') || keys[0]
      const values = data.map(item => typeof item[valueKey] === 'number' ? item[valueKey] : parseFloat(item[valueKey]) || 0)
      
      return {
        series: [{
          type: 'bar',
          data: values
        }]
      }
    }
    
    // 箱线图数据处理
    const processBoxplotData = (data) => {
      if (!data || data.length === 0) return { series: [] }
      
      // 箱线图需要处理为[min, Q1, median, Q3, max]格式
      // 简化处理，直接使用数据的统计值
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys);
      
      // 提取每列的数据并计算统计值
      const boxplotData = keys.map(key => {
        const values = data.map(item => typeof item[key] === 'number' ? item[key] : parseFloat(item[key]) || 0)
        
        // 排序值
        const sortedValues = [...values].sort((a, b) => a - b)
        const len = sortedValues.length
        
        // 计算统计值
        const min = sortedValues[0]
        const max = sortedValues[len - 1]
        const q1 = sortedValues[Math.floor(len * 0.25)]
        const median = sortedValues[Math.floor(len * 0.5)]
        const q3 = sortedValues[Math.floor(len * 0.75)]
        
        return [min, q1, median, q3, max]
      })
      
      return {
        xAxis: { data: keys },
        series: [{
          type: 'boxplot',
          data: boxplotData
        }]
      }
    }
    
    // 热力图数据处理
    const processHeatmapData = (data) => {
      if (!data || data.length === 0) return { series: [] }
      
      // 热力图需要提取行、列和值
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys);
      
      if (keys.length < 2) {
        error.value = '热力图需要至少2个数据维度'
        return { series: [] }
      }
      
      // 使用前两列作为行列，第三列作为值
      const rowKey = keys[0]
      const colKey = keys[1]
      const valueKey = keys[2] || colKey // 如果没有第三列，使用第二列作为值
      
      // 提取唯一的行和列
      const rows = [...new Set(data.map(item => item[rowKey]))]
      const cols = [...new Set(data.map(item => item[colKey]))]
      
      // 构建热力图数据 [row_index, col_index, value]
      const heatmapData = data.map(item => {
        const rowIndex = rows.indexOf(item[rowKey])
        const colIndex = cols.indexOf(item[colKey])
        const value = typeof item[valueKey] === 'number' ? item[valueKey] : parseFloat(item[valueKey]) || 0
        
        return [rowIndex, colIndex, value]
      })
      
      return {
        xAxis: { data: cols },
        yAxis: { data: rows },
        series: [{
          type: 'heatmap',
          data: heatmapData
        }]
      }
    }
    
    // 雷达图数据处理
    const processRadarData = (data) => {
      if (!data || data.length === 0) return { series: [] }
      
      // 雷达图需要多个维度和系列
      const firstItem = data[0]
      const keys = Object.keys(firstItem);
      console.log("图表数据处理 - 所有数据键:", keys);
      
      if (keys.length < 3) { // 至少需要一个分类列和两个指标列
        error.value = '雷达图需要至少3个数据维度'
        return { series: [] }
      }
      
      // 使用第一列作为分类，其余列作为指标
      const categoryKey = keys[0]
      const indicatorKeys = keys.slice(1)
      
      // 提取分类
      const categories = [...new Set(data.map(item => item[categoryKey]))]
      
      // 提取指标
      const indicators = indicatorKeys.map(key => ({
        name: key,
        max: Math.max(...data.map(item => typeof item[key] === 'number' ? item[key] : parseFloat(item[key]) || 0)) * 1.2
      }))
      
      // 构建雷达图数据
      const radarData = categories.map(category => {
        const categoryData = data.filter(item => item[categoryKey] === category)
        return {
          name: category,
          value: indicatorKeys.map(key => {
            const values = categoryData.map(item => typeof item[key] === 'number' ? item[key] : parseFloat(item[key]) || 0)
            return values.reduce((sum, val) => sum + val, 0) / values.length // 平均值
          })
        }
      })
      
      return {
        radar: { indicator: indicators },
        series: [{
          type: 'radar',
          data: radarData
        }]
      }
    }
    
    // 折线图配置
    const getLineConfig = (baseConfig, { xAxis, series }) => {
      return {
        ...baseConfig,
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: xAxis
        },
        yAxis: {
          type: 'value'
        },
        series
      }
    }
    
    // 面积图配置
    const getAreaConfig = (baseConfig, { xAxis, series }) => {
      // 为每个系列添加areaStyle
      const areaSeriesData = series.map(s => ({
        ...s,
        areaStyle: {}
      }))
      
      return {
        ...baseConfig,
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: xAxis
        },
        yAxis: {
          type: 'value'
        },
        series: areaSeriesData
      }
    }
    
    // 柱状图配置
    const getBarConfig = (baseConfig, { xAxis, series }) => {
      return {
        ...baseConfig,
        xAxis: {
          type: 'category',
          data: xAxis
        },
        yAxis: {
          type: 'value'
        },
        series
      }
    }
    
    // 散点图配置
    const getScatterConfig = (baseConfig, { series }) => {
      return {
        ...baseConfig,
        xAxis: { type: 'value' },
        yAxis: { type: 'value' },
        series
      }
    }
    
    // 直方图配置
    const getHistogramConfig = (baseConfig, { series }) => {
      return {
        ...baseConfig,
        xAxis: { type: 'category' },
        yAxis: { type: 'value' },
        series
      }
    }
    
    // 箱线图配置
    const getBoxplotConfig = (baseConfig, { xAxis, series }) => {
      return {
        ...baseConfig,
        xAxis,
        yAxis: { type: 'value' },
        series
      }
    }
    
    // 热力图配置
    const getHeatmapConfig = (baseConfig, { xAxis, yAxis, series }) => {
      return {
        ...baseConfig,
        xAxis,
        yAxis,
        visualMap: {
          min: 0,
          max: Math.max(...series[0].data.map(item => item[2])),
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '15%'
        },
        series
      }
    }
    
    // 雷达图配置
    const getRadarConfig = (baseConfig, { radar, series }) => {
      return {
        ...baseConfig,
        radar,
        series
      }
    }
    
    // 获取3D散点图配置
    const getScatter3DConfig = (config, data) => {
      // 确保数据是有效的
      if (!data.series || data.series.length === 0) {
        return config;
      }
      
      // 创建3D散点图的基本配置
      const scatter3DConfig = {
        ...config,
        tooltip: {
          ...config.tooltip,
          formatter: (params) => {
            const value = params.value;
            return `(${value[0]}, ${value[1]}, ${value[2]})`;
          }
        },
        xAxis3D: {
          type: 'value',
          name: '维度1'
        },
        yAxis3D: {
          type: 'value',
          name: '维度2'
        },
        zAxis3D: {
          type: 'value',
          name: '维度3'
        },
        grid3D: {
          viewControl: {
            autoRotate: false,
            projection: 'perspective',
            distance: 100
          },
          light: {
            main: {
              intensity: 1.2
            },
            ambient: {
              intensity: 0.3
            }
          }
        },
        series: data.series.map(series => ({
          ...series,
          type: 'scatter3D',
          symbolSize: 5,
          emphasis: {
            itemStyle: {
              color: '#ff0000'
            }
          }
        }))
      };
      
      return scatter3DConfig;
    };
    
    // 图表尺寸调整函数
    const resizeChart = () => {
      if (chartInstance.value) {
        chartInstance.value.resize();
      }
    };
    
    // 修改mounted钩子
    const mounted = () => {
      console.log('Chart组件mounted钩子触发');
      
      // 注册resize事件
      window.addEventListener('resize', resizeChart);
      
      // 延迟初始化，确保DOM已经渲染
      setTimeout(() => {
        console.log('延迟初始化图表，DOM应该已经渲染');
        initChart();
      }, 600);
    };
      
    // 当数据变化时，重新初始化图表
    watch([() => props.chartData, () => props.chartType, () => props.chartOptions, () => props.height], 
      () => {
        console.log('图表属性变化，延迟重新初始化');
        
        // 延迟重新初始化
        setTimeout(() => {
          initChart();
        }, 100);
      }, 
      { deep: true }
    );
    
    // 在组件销毁前，清理资源
    onBeforeUnmount(() => {
      console.log('Chart组件销毁，清理资源');
      
      // 移除事件监听
      window.removeEventListener('resize', resizeChart);
      
      // 销毁图表实例
        if (chartInstance.value) {
        chartInstance.value.dispose();
        chartInstance.value = null;
      }
    });
    
    return { 
      chartId,  // 返回唯一ID
      loading, 
      error,
      mounted
    }
  },
  // 使用传统的mounted生命周期钩子
  mounted() {
    // 调用setup中返回的mounted函数
    this.mounted();
  }
}
</script>

<style scoped>
.chart-container {
  width: 100%;
  min-height: 200px;
  position: relative;
  overflow: hidden;
}

.chart-body {
  width: 100%;
  height: 100%;
  position: relative;
}

.overlay-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.loading-container .el-icon,
.error-container .el-icon {
  font-size: 30px;
  margin-bottom: 10px;
}

.error-container {
  color: #f56c6c;
}
</style>
