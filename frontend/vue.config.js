const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

module.exports = defineConfig({
  transpileDependencies: true,
  // 禁用 ESLint
  lintOnSave: false,
  // 生产环境不生成 sourceMap
  productionSourceMap: false,
  // 开发服务器配置
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5010',
        changeOrigin: true
      }
    }
  },
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        __VUE_OPTIONS_API__: true,
        __VUE_PROD_DEVTOOLS__: false,
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
      })
    ]
  },
  // 打包输出目录
  outputDir: '../dist/frontend',
  // 静态资源目录
  assetsDir: 'static',
  // 配置方式1: 使用链式操作
  chainWebpack: config => {
    config.plugin('html')
      .tap(args => {
        args[0].title = '飞机监控系统'
        return args
      })
  }
})