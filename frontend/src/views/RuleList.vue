<template>
  <div class="rule-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Rule Management</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">
            Add Rule
          </el-button>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading" stripe border>
        <el-table-column prop="name" label="Name" width="200" />

        <el-table-column prop="priority" label="Priority" width="100" sortable />

        <el-table-column label="Content" min-width="300">
          <template #default="{ row }">
            <el-text type="info" size="small" style="font-family: monospace">
              {{ row.content }}
            </el-text>
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="Remark" width="200" />

        <el-table-column label="Created At" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

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

    <!-- Rule Examples Card -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>Rule Examples</span>
      </template>
      <div class="rule-examples">
        <el-alert type="info" :closable="false" style="margin-bottom: 12px">
          <p><strong>Rule Format:</strong></p>
          <ul style="margin: 8px 0; padding-left: 20px">
            <li><code>* = allow</code> - Allow all traffic (no restrictions)</li>
            <li><code>*.google.com:* = allow</code> - Allow access to Google domains on all ports</li>
            <li><code>baidu?.com:* = allow</code> - Match with wildcard (? = any single character)</li>
            <li><code>192.168.1.0/24:* = block</code> - Block local network</li>
            <li><code>*:443 = allow</code> - Allow HTTPS only</li>
          </ul>
        </el-alert>
      </div>
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
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Unique rule name" />
        </el-form-item>

        <el-form-item label="Content" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="e.g., * = allow"
          />
          <span style="font-size: 12px; color: #909399">
            Define traffic rules (domain/IP patterns and actions)
          </span>
        </el-form-item>

        <el-form-item label="Priority" prop="priority">
          <el-input-number v-model="form.priority" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">
            Higher priority rules are evaluated first
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
import { ref, reactive, onMounted } from 'vue'
import { getRules, createRule, updateRule, deleteRule } from '@/api/rules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const rules = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('Add Rule')
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  content: '',
  priority: 0,
  remark: ''
})

const formRules = {
  name: [{ required: true, message: 'Please enter rule name', trigger: 'blur' }],
  content: [{ required: true, message: 'Please enter rule content', trigger: 'blur' }]
}

const loadRules = async () => {
  loading.value = true
  try {
    rules.value = await getRules()
  } catch (error) {
    ElMessage.error('Failed to load rules')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const handleAdd = () => {
  dialogTitle.value = 'Add Rule'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = 'Edit Rule'
  editingId.value = row.id

  form.name = row.name
  form.content = row.content
  form.priority = row.priority
  form.remark = row.remark || ''

  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (editingId.value) {
        await updateRule(editingId.value, form)
        ElMessage.success('Rule updated successfully')
      } else {
        await createRule(form)
        ElMessage.success('Rule created successfully')
      }

      dialogVisible.value = false
      await loadRules()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || 'Operation failed')
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `Are you sure you want to delete rule "${row.name}"?`,
    'Confirm Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteRule(row.id)
      ElMessage.success('Rule deleted successfully')
      await loadRules()
    } catch (error) {
      ElMessage.error('Failed to delete rule')
    }
  })
}

const resetForm = () => {
  form.name = ''
  form.content = ''
  form.priority = 0
  form.remark = ''

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.rule-list {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rule-examples code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  color: #e6a23c;
}

.rule-examples ul {
  line-height: 1.8;
}
</style>
