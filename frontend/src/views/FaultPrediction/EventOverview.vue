<template>
  <div class="event-overview">
    <h2>事件概览</h2>
    <el-card>
      <div class="content-placeholder">
        <el-empty description="事件概览内容正在开发中"></el-empty>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'EventOverview',
  setup() {
    return {}
  }
}
</script>

<style scoped>
.event-overview {
  padding: 20px;
}

.content-placeholder {
  padding: 40px 0;
  text-align: center;
}
</style>
