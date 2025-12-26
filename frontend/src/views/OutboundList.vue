<template>
  <div class="outbound-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Outbound Management</span>
          <div class="header-actions">
            <el-button type="success" :icon="Search" @click="handleScan">
              Scan Local IPs
            </el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">
              Add Outbound
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="outbounds" v-loading="loading" stripe border>
        <el-table-column prop="name" label="Name" width="200" />

        <el-table-column label="Type" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_auto_generated ? 'success' : 'primary'" size="small">
              {{ row.is_auto_generated ? 'Auto (Direct)' : row.protocol }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="local_interface_ip" label="Local IP" width="150" />

        <el-table-column label="Proxy URL" min-width="250">
          <template #default="{ row }">
            {{ row.config?.proxyUrl || 'Direct (No proxy)' }}
          </template>
        </el-table-column>

        <el-table-column label="Public IP" width="150">
          <template #default="{ row }">
            {{ row.config?.publicIp || 'N/A' }}
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="Remark" width="200" />

        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="handleEdit(row)">
              Edit
            </el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
              Delete
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
      >
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Unique outbound name" />
        </el-form-item>

        <el-form-item label="Protocol" prop="protocol">
          <el-select v-model="form.protocol" style="width: 100%" @change="handleProtocolChange">
            <el-option label="Direct" value="direct" />
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="HTTP" value="http" />
            <el-option label="Shadowsocks" value="ss" />
          </el-select>
        </el-form-item>

        <el-form-item label="Local Interface IP" prop="local_interface_ip">
          <el-input v-model="form.local_interface_ip" placeholder="e.g., 192.168.1.1" />
          <span style="font-size: 12px; color: #909399">
            The network interface to use for outbound connections (Internal IP)
          </span>
        </el-form-item>

        <el-form-item label="Public IP" prop="publicIp">
          <el-input v-model="form.publicIp" placeholder="e.g., 8.8.8.8" />
          <span style="font-size: 12px; color: #909399">
            The public IP address for this outbound (External IP)
          </span>
        </el-form-item>

        <el-form-item
          v-if="form.protocol !== 'direct'"
          label="Proxy URL"
          prop="proxyUrl"
        >
          <el-input v-model="proxyUrl" placeholder="e.g., socks5://user:pass@ip:port" />
          <span style="font-size: 12px; color: #909399">
            Format: {{ getProxyUrlFormat() }}
          </span>
        </el-form-item>

        <el-form-item label="Remark" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="Description" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleSubmit">Confirm</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onMounted } from 'vue'
import { getOutbounds, createOutbound, updateOutbound, deleteOutbound, scanInterfaces } from '@/api/outbounds'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'

const outbounds = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('Add Outbound')
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  protocol: 'direct',
  local_interface_ip: '',
  publicIp: '',
  remark: '',
  config: {}
})

const proxyUrl = ref('')

const rules = {
  name: [{ required: true, message: 'Please enter name', trigger: 'blur' }],
  protocol: [{ required: true, message: 'Please select protocol', trigger: 'change' }],
  local_interface_ip: [{ required: true, message: 'Please enter local interface IP', trigger: 'blur' }]
}

const loadOutbounds = async () => {
  loading.value = true
  try {
    outbounds.value = await getOutbounds()
  } catch (error) {
    ElMessage.error('Failed to load outbounds')
  } finally {
    loading.value = false
  }
}

const getProxyUrlFormat = () => {
  const formats = {
    socks5: 'socks5://[user:pass@]ip:port',
    http: 'http://[user:pass@]ip:port',
    ss: 'ss://method:password@ip:port'
  }
  return formats[form.protocol] || ''
}

const handleProtocolChange = () => {
  proxyUrl.value = ''
}

const handleAdd = () => {
  dialogTitle.value = 'Add Outbound'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = 'Edit Outbound'
  editingId.value = row.id

  form.name = row.name
  form.protocol = row.protocol
  form.local_interface_ip = row.local_interface_ip || ''
  form.publicIp = row.config?.publicIp || ''
  form.remark = row.remark || ''
  proxyUrl.value = row.config?.proxyUrl || ''

  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const submitData = {
        name: form.name,
        protocol: form.protocol,
        local_interface_ip: form.local_interface_ip,
        remark: form.remark,
        config: {
          eh: form.local_interface_ip,
          publicIp: form.publicIp || '',
          proxyUrl: proxyUrl.value || ''
        }
      }

      if (editingId.value) {
        await updateOutbound(editingId.value, submitData)
        ElMessage.success('Outbound updated successfully')
      } else {
        await createOutbound(submitData)
        ElMessage.success('Outbound created successfully')
      }

      dialogVisible.value = false
      await loadOutbounds()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || 'Operation failed')
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `Are you sure you want to delete outbound "${row.name}"?`,
    'Confirm Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteOutbound(row.id)
      ElMessage.success('Outbound deleted successfully')
      await loadOutbounds()
    } catch (error) {
      ElMessage.error('Failed to delete outbound')
    }
  })
}

const handleScan = async () => {
  ElMessageBox.confirm(
    'This will scan all local network interfaces and create direct outbounds. Continue?',
    'Scan Local IPs',
    {
      confirmButtonText: 'Scan',
      cancelButtonText: 'Cancel',
      type: 'info'
    }
  ).then(async () => {
    loading.value = true
    try {
      const result = await scanInterfaces()
      ElMessage.success(result.message || 'Scan completed successfully')
      await loadOutbounds()
    } catch (error) {
      ElMessage.error('Failed to scan interfaces')
    } finally {
      loading.value = false
    }
  })
}

const resetForm = () => {
  form.name = ''
  form.protocol = 'direct'
  form.local_interface_ip = ''
  form.publicIp = ''
  form.remark = ''
  proxyUrl.value = ''

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

onMounted(() => {
  loadOutbounds()
})
</script>

<style scoped>
.outbound-list {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
