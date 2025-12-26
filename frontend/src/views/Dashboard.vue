<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- System Stats Cards -->
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon cpu"><Cpu /></el-icon>
            <div class="stat-info">
              <p class="stat-label">CPU Usage</p>
              <h3 class="stat-value">{{ stats.cpu_usage?.toFixed(2) || 0 }}%</h3>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon memory"><MemoryCard /></el-icon>
            <div class="stat-info">
              <p class="stat-label">Memory Usage</p>
              <h3 class="stat-value">{{ stats.memory_usage?.toFixed(2) || 0 }}%</h3>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon users"><User /></el-icon>
            <div class="stat-info">
              <p class="stat-label">Total Users</p>
              <h3 class="stat-value">{{ stats.total_users || 0 }}</h3>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon active"><CircleCheck /></el-icon>
            <div class="stat-info">
              <p class="stat-label">Active Users</p>
              <h3 class="stat-value">{{ stats.active_users || 0 }}</h3>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Bandwidth Statistics</span>
            </div>
          </template>
          <div class="bandwidth-stats">
            <div class="bandwidth-item">
              <el-icon><Upload /></el-icon>
              <span>Upload: {{ formatBytes(stats.bandwidth_up) }}</span>
            </div>
            <div class="bandwidth-item">
              <el-icon><Download /></el-icon>
              <span>Download: {{ formatBytes(stats.bandwidth_down) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>System Information</span>
            </div>
          </template>
          <div class="system-info">
            <p><strong>Version:</strong> {{ stats.system_version || '1.0.0' }}</p>
            <p><strong>Uptime:</strong> {{ stats.uptime || 'Unknown' }}</p>
            <p><strong>Expired Users:</strong> {{ stats.expired_users || 0 }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Action Buttons -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Quick Actions</span>
            </div>
          </template>
          <div class="action-buttons">
            <el-button type="primary" size="large" :icon="Download" @click="handleBackup">
              Backup Database
            </el-button>
            <el-button type="success" size="large" :icon="Refresh" @click="handleSyncTraffic">
              Sync Traffic
            </el-button>
            <el-button type="warning" size="large" :icon="Clock" @click="handleCheckExpired">
              Check Expired Users
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboardStats, downloadBackup, syncTraffic, checkExpired } from '@/api/system'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Clock } from '@element-plus/icons-vue'

const stats = ref({})
const loading = ref(false)

const loadStats = async () => {
  try {
    stats.value = await getDashboardStats()
  } catch (error) {
    ElMessage.error('Failed to load dashboard statistics')
  }
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleBackup = async () => {
  try {
    const blob = await downloadBackup()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `proxy_admin_backup_${new Date().toISOString().slice(0, 10)}.db`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('Database backup downloaded successfully')
  } catch (error) {
    ElMessage.error('Failed to download backup')
  }
}

const handleSyncTraffic = async () => {
  try {
    const result = await syncTraffic()
    ElMessage.success(result.message || 'Traffic synced successfully')
    await loadStats()
  } catch (error) {
    ElMessage.error('Failed to sync traffic')
  }
}

const handleCheckExpired = async () => {
  try {
    const result = await checkExpired()
    ElMessage.success(result.message || 'Expired users checked successfully')
    await loadStats()
  } catch (error) {
    ElMessage.error('Failed to check expired users')
  }
}

onMounted(() => {
  loadStats()
  // Refresh stats every 30 seconds
  setInterval(loadStats, 30000)
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.stat-card {
  cursor: default;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 48px;
}

.stat-icon.cpu {
  color: #409EFF;
}

.stat-icon.memory {
  color: #67C23A;
}

.stat-icon.users {
  color: #E6A23C;
}

.stat-icon.active {
  color: #67C23A;
}

.stat-info {
  flex: 1;
}

.stat-label {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #909399;
}

.stat-value {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.bandwidth-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bandwidth-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.system-info p {
  margin: 12px 0;
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
</style>
