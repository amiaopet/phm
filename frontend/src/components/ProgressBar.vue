<template>
    <div class="progress-bar-container">
      <el-progress
        :percentage="percentage"
        :status="status"
        :stroke-width="strokeWidth"
        :text-inside="textInside"
        :format="format">
      </el-progress>
      <div v-if="message" class="progress-message">{{ message }}</div>
    </div>
  </template>
  
  <script>
  import { computed } from 'vue'
  
  export default {
    name: 'ProgressBar',
    props: {
      percentage: {
        type: Number,
        default: 0
      },
      status: {
        type: String,
        default: '',
        validator: (value) => ['', 'success', 'exception', 'warning'].includes(value)
      },
      message: {
        type: String,
        default: ''
      },
      strokeWidth: {
        type: Number,
        default: 6
      },
      textInside: {
        type: Boolean,
        default: false
      },
      showText: {
        type: Boolean,
        default: true
      }
    },
    setup(props) {
      const format = computed(() => {
        if (!props.showText) {
          return () => ''
        }
        return null // 使用默认格式
      })
      
      return {
        format
      }
    }
  }
  </script>
  
  <style scoped>
  .progress-bar-container {
    margin: 15px 0;
  }
  
  .progress-message {
    margin-top: 8px;
    color: #606266;
    font-size: 14px;
  }
  </style>