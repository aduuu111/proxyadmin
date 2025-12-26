<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>User Management</span>
          <div style="display: flex; gap: 12px; align-items: center;">
            <el-input
              v-model="searchQuery"
              placeholder="Search users..."
              clearable
              style="width: 300px;"
              :prefix-icon="Search"
            />
            <el-button type="primary" :icon="Plus" @click="handleCreateUser">
              Create User
            </el-button>
          </div>
        </div>
      </template>

      <!-- Batch Actions Toolbar -->
      <div v-if="selectedUsers.length > 0" class="batch-actions-toolbar">
        <span>Selected: {{ selectedUsers.length }} users</span>
        <div>
          <el-button type="info" @click="handleShowSelectedInfo">
            View Selected Info
          </el-button>
          <el-button type="success" :icon="DocumentCopy" @click="handleBatchExportClipboard">
            Copy to Clipboard
          </el-button>
          <el-button type="success" :icon="Download" @click="handleBatchExportFile">
            Export to File
          </el-button>
          <el-button type="primary" :icon="DocumentCopy" @click="handleBatchExportSSLinks">
            Copy SS Links
          </el-button>
          <el-button type="warning" @click="handleBatchToggle">
            Batch Enable/Disable
          </el-button>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">
            Batch Delete
          </el-button>
        </div>
      </div>

      <el-table
        :data="filteredUsers"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <!-- Selection Checkbox -->
        <el-table-column type="selection" width="55" />

        <!-- Status Column -->
        <el-table-column label="Status" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)" size="small">
              {{ getStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- Remark -->
        <el-table-column prop="remark" label="Remark" width="150" />

        <!-- Public IP (from outbound) -->
        <el-table-column label="Public IP" width="150">
          <template #default="{ row }">
            {{ getPublicIP(row) }}
          </template>
        </el-table-column>

        <!-- Port -->
        <el-table-column label="Port" width="100">
          <template #default="{ row }">
            {{ row.port }}
          </template>
        </el-table-column>

        <!-- Username -->
        <el-table-column label="Username" width="150">
          <template #default="{ row }">
            {{ row.username }}
          </template>
        </el-table-column>

        <!-- Password -->
        <el-table-column label="Password" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="user-select: text;">{{ row.password }}</span>
          </template>
        </el-table-column>

        <!-- Protocol -->
        <el-table-column prop="protocol" label="Protocol" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.protocol }}</el-tag>
          </template>
        </el-table-column>

        <!-- Upload Traffic -->
        <el-table-column label="Upload Traffic" width="150">
          <template #default="{ row }">
            <div>
              {{ formatBytes(row.up_traffic) }} / {{ row.send_limit > 0 ? (row.send_limit + ' KB/s') : '∞' }}
            </div>
          </template>
        </el-table-column>

        <!-- Download Traffic -->
        <el-table-column label="Download Traffic" width="150">
          <template #default="{ row }">
            <div>
              {{ formatBytes(row.down_traffic) }} / {{ row.receive_limit > 0 ? (row.receive_limit + ' KB/s') : '∞' }}
            </div>
          </template>
        </el-table-column>

        <!-- Expiration -->
        <el-table-column label="Expiration" width="180">
          <template #default="{ row }">
            <div>
              <div>{{ formatDate(row.expire_time) }}</div>
              <div style="font-size: 12px; color: #909399">
                {{ getRemainingDays(row.expire_time) }}
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Outbound -->
        <el-table-column label="Outbound" width="150">
          <template #default="{ row }">
            {{ row.outbound?.name || 'N/A' }}
          </template>
        </el-table-column>

        <!-- Copy -->
        <el-table-column label="Copy" width="100" align="center">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              :icon="DocumentCopy"
              @click="copyUserInfo(row)"
              title="Copy user info"
            >
              Copy
            </el-button>
          </template>
        </el-table-column>

        <!-- Subscription Link (SS only) -->
        <el-table-column label="订阅链接" width="100" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.protocol === 'ss'"
              size="small"
              type="success"
              :icon="DocumentCopy"
              @click="copySSLink(row)"
              title="Copy subscription link"
            >
              Copy
            </el-button>
            <span v-else style="color: #c0c4cc;">-</span>
          </template>
        </el-table-column>

        <!-- Actions -->
        <el-table-column label="Actions" width="320" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" :icon="Edit" @click="handleEdit(row)">
                Edit
              </el-button>
              <el-button size="small" :icon="Refresh" @click="handleResetTraffic(row)">
                Reset
              </el-button>
              <el-button
                size="small"
                :type="row.enable ? 'warning' : 'success'"
                :icon="row.enable ? Close : Check"
                @click="handleToggle(row)"
              >
                {{ row.enable ? 'Disable' : 'Enable' }}
              </el-button>
              <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
                Delete
              </el-button>
            </el-button-group>
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
        <el-form-item label="Remark" prop="remark">
          <el-input v-model="form.remark" placeholder="User description" />
        </el-form-item>

        <el-form-item label="Port" prop="port">
          <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>

        <el-form-item label="Protocol" prop="protocol">
          <el-select v-model="form.protocol" style="width: 100%">
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="Shadowsocks" value="ss" />
          </el-select>
        </el-form-item>

        <!-- Username field for SOCKS5 -->
        <el-form-item v-if="form.protocol === 'socks5'" label="Username" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>

        <!-- Encryption Method for Shadowsocks -->
        <el-form-item v-if="form.protocol === 'ss'" label="Encryption Method" prop="username">
          <el-select v-model="form.username" style="width: 100%">
            <el-option label="AES-128-GCM" value="aes-128-gcm" />
            <el-option label="AES-256-GCM" value="aes-256-gcm" />
            <el-option label="ChaCha20-IETF-Poly1305" value="chacha20-ietf-poly1305" />
          </el-select>
          <span style="font-size: 12px; color: #909399">
            Shadowsocks encryption method
          </span>
        </el-form-item>

        <el-form-item label="Password" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>

        <el-form-item label="Outbound" prop="outbound_id">
          <el-select v-model="form.outbound_id" style="width: 100%">
            <el-option
              v-for="outbound in outbounds"
              :key="outbound.id"
              :label="outbound.name"
              :value="outbound.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Rules" prop="rule_ids">
          <el-select v-model="form.rule_ids" multiple style="width: 100%">
            <el-option
              v-for="rule in rules_list"
              :key="rule.id"
              :label="rule.name"
              :value="rule.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Traffic Limit (GB)" prop="total_traffic">
          <el-input-number
            v-model="trafficGB"
            :min="0"
            :step="1"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Expiration Date" prop="expire_time">
          <el-date-picker
            v-model="form.expire_time"
            type="datetime"
            placeholder="Select date and time"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="Upload Limit (KB/s)" prop="send_limit">
          <el-input-number v-model="form.send_limit" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Download Limit (KB/s)" prop="receive_limit">
          <el-input-number v-model="form.receive_limit" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Max Connections" prop="max_conn_count">
          <el-input-number v-model="form.max_conn_count" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" type="email" />
        </el-form-item>

        <el-form-item label="Enable" prop="enable">
          <el-switch v-model="form.enable" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleSubmit">Confirm</el-button>
      </template>
    </el-dialog>

    <!-- Batch Add Dialog -->
    <el-dialog
      v-model="batchDialogVisible"
      title="Batch Add Users"
      width="700px"
      @close="resetBatchForm"
    >
      <el-form
        ref="batchFormRef"
        :model="batchForm"
        label-width="140px"
      >
        <el-form-item label="Protocol" prop="protocol">
          <el-select v-model="batchForm.protocol" style="width: 100%">
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="Shadowsocks" value="ss" />
          </el-select>
        </el-form-item>

        <el-form-item label="Expiration Days" prop="expiration_days">
          <el-input-number
            v-model="batchForm.expiration_days"
            :min="1"
            :step="1"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399; margin-left: 8px;">Days</span>
        </el-form-item>

        <el-form-item label="Upload Limit (KB/s)" prop="send_limit">
          <el-input-number v-model="batchForm.send_limit" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Download Limit (KB/s)" prop="receive_limit">
          <el-input-number v-model="batchForm.receive_limit" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Max Connections" prop="max_conn_count">
          <el-input-number v-model="batchForm.max_conn_count" :min="0" style="width: 100%" />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Default Outbound" prop="outbound_id">
          <el-select v-model="batchForm.outbound_id" style="width: 100%">
            <el-option
              v-for="outbound in outbounds"
              :key="outbound.id"
              :label="outbound.name"
              :value="outbound.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Default Rules" prop="rule_ids">
          <el-select v-model="batchForm.rule_ids" multiple style="width: 100%">
            <el-option
              v-for="rule in rules_list"
              :key="rule.id"
              :label="rule.name"
              :value="rule.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Batch Data" prop="batch_data">
          <el-input
            v-model="batchForm.batch_data"
            type="textarea"
            :rows="8"
            placeholder="Format: port|username|password|outbound or port|username|password (one per line)"
          />
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            <div><strong>Format:</strong></div>
            <div>1. With outbound: <code>port|username|password|outbound</code></div>
            <div>   Example: <code>12345|abc123|abc321|test1</code></div>
            <div>2. Default outbound: <code>port|username|password</code></div>
            <div>   Example: <code>12345|abc123|abc321</code> (will use default outbound above)</div>
            <div>- One user per line, multiple lines for batch add</div>
            <div>- For SS protocol, username is encryption method (e.g., aes-128-gcm)</div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="batchDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleBatchSubmit">Confirm</el-button>
      </template>
    </el-dialog>

    <!-- Game Selection Dialog -->
    <el-dialog
      v-model="gameSelectionVisible"
      title="Select Game to Play"
      width="600px"
      @close="resetGameSelection"
    >
      <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
        <strong>Choose a game:</strong> Each IP can serve up to 10 users. Same IP cannot be used for the same game twice.
      </el-alert>

      <el-table
        :data="gameInventories"
        v-loading="inventoryLoading"
        stripe
        border
        @row-click="handleGameSelect"
        highlight-current-row
        style="cursor: pointer;"
      >
        <el-table-column label="Game (Rule)" prop="rule_name" width="200" />
        <el-table-column label="Available IPs" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.available_ips > 0 ? 'success' : 'danger'">
              {{ row.available_ips }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Used / Total" width="120" align="center">
          <template #default="{ row }">
            {{ row.used_ips }} / {{ row.total_ips }}
          </template>
        </el-table-column>
        <el-table-column label="Status" align="center">
          <template #default="{ row }">
            <span v-if="row.available_ips > 0" style="color: #67C23A;">
              ✓ Available
            </span>
            <span v-else style="color: #F56C6C;">
              ✗ No slots
            </span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="gameSelectionVisible = false">Cancel</el-button>
      </template>
    </el-dialog>

    <!-- Quick User Creation Dialog -->
    <el-dialog
      v-model="quickCreateVisible"
      :title="quickCreateTitle"
      width="600px"
      @close="resetQuickCreate"
    >
      <el-alert type="success" :closable="false" style="margin-bottom: 16px;">
        <strong>Selected Game:</strong> {{ selectedGameName }}
        <br />
        <strong>Available IPs:</strong> {{ selectedGameAvailableIPs }}
      </el-alert>

      <el-form
        ref="quickCreateFormRef"
        :model="quickCreateForm"
        label-width="150px"
      >
        <!-- Creation Mode -->
        <el-form-item label="Creation Mode">
          <el-radio-group v-model="quickCreateForm.mode">
            <el-radio label="quick">Quick Mode</el-radio>
            <el-radio label="custom">Custom Mode</el-radio>
          </el-radio-group>
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">
            Quick: Auto-generate all settings | Custom: Customize password and bandwidth
          </div>
        </el-form-item>

        <el-form-item label="Number of Users">
          <el-input-number
            v-model="quickCreateForm.count"
            :min="1"
            :max="selectedGameAvailableIPs"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="Protocol">
          <el-select v-model="quickCreateForm.protocol" style="width: 100%">
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="Shadowsocks" value="ss" />
          </el-select>
        </el-form-item>

        <!-- Encryption Method (for Shadowsocks only) -->
        <el-form-item v-if="quickCreateForm.protocol === 'ss'" label="Encryption Method">
          <el-select v-model="quickCreateForm.method" style="width: 100%">
            <el-option label="AES-128-GCM" value="aes-128-gcm" />
            <el-option label="AES-256-GCM" value="aes-256-gcm" />
            <el-option label="ChaCha20-IETF-Poly1305" value="chacha20-ietf-poly1305" />
          </el-select>
        </el-form-item>

        <el-form-item label="Expiration Days">
          <el-input-number
            v-model="quickCreateForm.expiration_days"
            :min="1"
            :max="3650"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399; margin-left: 8px;">Days (Leave blank for system default)</span>
        </el-form-item>

        <!-- Custom Mode Fields -->
        <template v-if="quickCreateForm.mode === 'custom'">
          <el-divider content-position="left">Custom Settings</el-divider>

          <el-form-item label="Custom Password">
            <el-input
              v-model="quickCreateForm.customPassword"
              type="password"
              show-password
              placeholder="Leave blank to auto-generate"
            />
            <span style="font-size: 12px; color: #909399;">
              If specified, all users will use this password
            </span>
          </el-form-item>

          <el-form-item label="Upload Limit">
            <el-input-number
              v-model="quickCreateForm.send_limit"
              :min="0"
              style="width: 100%"
            />
            <span style="font-size: 12px; color: #909399; margin-left: 8px;">KB/s (0 = Unlimited)</span>
          </el-form-item>

          <el-form-item label="Download Limit">
            <el-input-number
              v-model="quickCreateForm.receive_limit"
              :min="0"
              style="width: 100%"
            />
            <span style="font-size: 12px; color: #909399; margin-left: 8px;">KB/s (0 = Unlimited)</span>
          </el-form-item>
        </template>

        <el-alert
          v-if="quickCreateForm.mode === 'quick'"
          type="info"
          :closable="false"
          style="margin-top: 12px;"
        >
          <div><strong>Auto-Generated:</strong></div>
          <div>• Usernames and passwords will be generated automatically</div>
          <div>• Available IPs will be assigned automatically</div>
          <div>• Bandwidth limits will use system defaults</div>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="quickCreateVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleQuickCreateSubmit" :loading="quickCreateLoading">
          Create Users
        </el-button>
      </template>
    </el-dialog>

    <!-- Selected Users Info Dialog -->
    <el-dialog
      v-model="selectedInfoVisible"
      title="Selected Users Information"
      width="800px"
    >
      <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
        <strong>Total Selected:</strong> {{ selectedUsers.length }} users
      </el-alert>

      <el-input
        v-model="selectedUsersText"
        type="textarea"
        :rows="15"
        readonly
        style="font-family: monospace;"
      />

      <template #footer>
        <el-button @click="selectedInfoVisible = false">Close</el-button>
        <el-button type="primary" :icon="DocumentCopy" @click="copySelectedUsersText">
          Copy All
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser, resetTraffic, toggleUser } from '@/api/users'
import { getOutbounds } from '@/api/outbounds'
import { getRules } from '@/api/rules'
import { getAllGameInventories } from '@/api/gameInventory'
import { getSystemSettings, generateTestCredentials } from '@/api/settings'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh, Check, Close, Search, DocumentCopy, Download } from '@element-plus/icons-vue'

const users = ref([])
const outbounds = ref([])
const rules_list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('Add User')
const formRef = ref(null)
const editingId = ref(null)

// Search and selection state
const searchQuery = ref('')
const selectedUsers = ref([])
const selectedInfoVisible = ref(false)

// Batch add state
const batchDialogVisible = ref(false)
const batchFormRef = ref(null)
const batchForm = reactive({
  protocol: 'socks5',
  expiration_days: 30,
  send_limit: 0,
  receive_limit: 0,
  max_conn_count: 0,
  outbound_id: null,
  rule_ids: [],
  batch_data: ''
})

// Game selection state
const gameSelectionVisible = ref(false)
const gameInventories = ref([])
const inventoryLoading = ref(false)

// Quick create state
const quickCreateVisible = ref(false)
const quickCreateFormRef = ref(null)
const quickCreateLoading = ref(false)
const selectedGameRuleId = ref(null)
const selectedGameName = ref('')
const selectedGameAvailableIPs = ref(0)
const quickCreateForm = reactive({
  mode: 'quick',  // 'quick' or 'custom'
  count: 1,
  protocol: 'socks5',  // Default to socks5
  expiration_days: null,
  method: 'aes-128-gcm',  // Encryption method (for shadowsocks)
  customPassword: '',  // Custom password (only for custom mode)
  send_limit: null,  // Upload limit (only for custom mode)
  receive_limit: null  // Download limit (only for custom mode)
})

const quickCreateTitle = computed(() => {
  return `Create Users for ${selectedGameName.value}`
})

// Filtered users based on search query
const filteredUsers = computed(() => {
  if (!searchQuery.value) {
    return users.value
  }

  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => {
    return (
      user.remark?.toLowerCase().includes(query) ||
      user.username?.toLowerCase().includes(query) ||
      user.port?.toString().includes(query) ||
      user.outbound?.name?.toLowerCase().includes(query) ||
      getPublicIP(user).toLowerCase().includes(query)
    )
  })
})

// Selected users formatted text
const selectedUsersText = computed(() => {
  return selectedUsers.value
    .map(user => formatUserInfo(user))
    .join('\n')
})

const form = reactive({
  remark: '',
  port: 1080,
  username: '',
  password: '',
  protocol: 'socks5',
  outbound_id: null,
  rule_ids: [],
  total_traffic: 0,
  expire_time: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
  send_limit: 0,
  receive_limit: 0,
  max_conn_count: 0,
  email: '',
  enable: true
})

// Traffic in GB for easier input
const trafficGB = computed({
  get: () => form.total_traffic / (1024 * 1024 * 1024),
  set: (val) => {
    form.total_traffic = val * 1024 * 1024 * 1024
  }
})

const rules = {
  port: [{ required: true, message: 'Please enter port', trigger: 'blur' }],
  username: [{ required: true, message: 'Please enter username', trigger: 'blur' }],
  password: [{ required: true, message: 'Please enter password', trigger: 'blur' }],
  outbound_id: [{ required: true, message: 'Please select outbound', trigger: 'change' }],
  expire_time: [{ required: true, message: 'Please select expiration date', trigger: 'change' }]
}

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (error) {
    ElMessage.error('Failed to load users')
  } finally {
    loading.value = false
  }
}

const loadOutbounds = async () => {
  try {
    outbounds.value = await getOutbounds()
  } catch (error) {
    ElMessage.error('Failed to load outbounds')
  }
}

const loadRules = async () => {
  try {
    rules_list.value = await getRules()
  } catch (error) {
    ElMessage.error('Failed to load rules')
  }
}

const getStatusType = (row) => {
  if (row.status === 'expired') return 'danger'
  if (row.status === 'disabled' || !row.enable) return 'info'
  return 'success'
}

const getStatusText = (row) => {
  if (row.status === 'expired') return 'Expired'
  if (!row.enable) return 'Disabled'
  return 'Active'
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const getRemainingDays = (expireTime) => {
  const now = new Date()
  const expire = new Date(expireTime)
  const diff = expire - now
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days < 0) return 'Expired'
  if (days === 0) return 'Expires today'
  return `${days} days remaining`
}

const getTrafficPercentage = (row) => {
  if (row.total_traffic === 0) return 0
  const used = row.up_traffic + row.down_traffic
  return Math.min(100, (used / row.total_traffic) * 100)
}

const handleAdd = () => {
  dialogTitle.value = 'Add User'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = 'Edit User'
  editingId.value = row.id

  // Populate form
  Object.keys(form).forEach(key => {
    if (key === 'expire_time') {
      form[key] = new Date(row[key])
    } else if (key === 'rule_ids') {
      form[key] = row.rules?.map(r => r.id) || []
    } else {
      form[key] = row[key]
    }
  })

  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const submitData = { ...form }

      if (editingId.value) {
        await updateUser(editingId.value, submitData)
        ElMessage.success('User updated successfully')
      } else {
        await createUser(submitData)
        ElMessage.success('User created successfully')
      }

      dialogVisible.value = false
      await loadUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || 'Operation failed')
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `Are you sure you want to delete user on port ${row.port}?`,
    'Confirm Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteUser(row.id)
      ElMessage.success('User deleted successfully')
      await loadUsers()
    } catch (error) {
      ElMessage.error('Failed to delete user')
    }
  })
}

const handleResetTraffic = (row) => {
  ElMessageBox.confirm(
    `Reset traffic counters for user on port ${row.port}?`,
    'Confirm Reset',
    {
      confirmButtonText: 'Reset',
      cancelButtonText: 'Cancel',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await resetTraffic(row.id)
      ElMessage.success('Traffic reset successfully')
      await loadUsers()
    } catch (error) {
      ElMessage.error('Failed to reset traffic')
    }
  })
}

const handleToggle = async (row) => {
  try {
    await toggleUser(row.id)
    ElMessage.success(`User ${row.enable ? 'disabled' : 'enabled'} successfully`)
    await loadUsers()
  } catch (error) {
    ElMessage.error('Failed to toggle user status')
  }
}

const resetForm = () => {
  form.remark = ''
  form.port = 1080
  form.username = ''
  form.password = ''
  form.protocol = 'socks5'
  form.outbound_id = null
  form.rule_ids = []
  form.total_traffic = 0
  form.expire_time = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
  form.send_limit = 0
  form.receive_limit = 0
  form.max_conn_count = 0
  form.email = ''
  form.enable = true

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

const handleBatchAdd = () => {
  batchDialogVisible.value = true
}

const resetBatchForm = () => {
  batchForm.protocol = 'socks5'
  batchForm.expiration_days = 30
  batchForm.send_limit = 0
  batchForm.receive_limit = 0
  batchForm.max_conn_count = 0
  batchForm.outbound_id = null
  batchForm.rule_ids = []
  batchForm.batch_data = ''

  if (batchFormRef.value) {
    batchFormRef.value.clearValidate()
  }
}

const handleBatchSubmit = async () => {
  if (!batchForm.batch_data.trim()) {
    ElMessage.warning('Please enter batch data')
    return
  }

  if (!batchForm.outbound_id) {
    ElMessage.warning('Please select default outbound')
    return
  }

  try {
    const lines = batchForm.batch_data.trim().split('\n')
    const expireTime = new Date(Date.now() + batchForm.expiration_days * 24 * 60 * 60 * 1000)

    let successCount = 0
    let failCount = 0
    const errors = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue

      const parts = line.split('|')
      if (parts.length < 3) {
        errors.push(`Line ${i + 1}: Invalid format (need at least 3 parts)`)
        failCount++
        continue
      }

      const port = parseInt(parts[0])
      const username = parts[1]
      const password = parts[2]
      const outboundName = parts[3] ? parts[3] : null

      if (isNaN(port)) {
        errors.push(`Line ${i + 1}: Invalid port number`)
        failCount++
        continue
      }

      // Find outbound ID
      let outboundId = batchForm.outbound_id
      if (outboundName) {
        const foundOutbound = outbounds.value.find(o => o.name === outboundName)
        if (foundOutbound) {
          outboundId = foundOutbound.id
        } else {
          errors.push(`Line ${i + 1}: Outbound "${outboundName}" not found, using default`)
        }
      }

      try {
        await createUser({
          port,
          username,
          password,
          protocol: batchForm.protocol,
          outbound_id: outboundId,
          rule_ids: batchForm.rule_ids,
          total_traffic: 0,
          expire_time: expireTime,
          send_limit: batchForm.send_limit,
          receive_limit: batchForm.receive_limit,
          max_conn_count: batchForm.max_conn_count,
          enable: true,
          remark: `Batch imported - Port ${port}`,
          email: ''
        })
        successCount++
      } catch (error) {
        errors.push(`Line ${i + 1} (Port ${port}): ${error.response?.data?.detail || error.message}`)
        failCount++
      }
    }

    // Show result
    let message = `Batch add completed: ${successCount} succeeded`
    if (failCount > 0) {
      message += `, ${failCount} failed`
      if (errors.length > 0) {
        console.error('Batch add errors:', errors)
        ElMessage.warning({
          message: message + '. Check console for details.',
          duration: 5000
        })
      }
    } else {
      ElMessage.success(message)
    }

    batchDialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error('Batch add failed: ' + (error.message || 'Unknown error'))
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('Copied to clipboard')
  } catch (error) {
    ElMessage.error('Failed to copy')
  }
}

const getPublicIP = (row) => {
  if (!row.outbound) return 'N/A'

  // Try to get Public IP from outbound config
  if (row.outbound.config) {
    try {
      const config = typeof row.outbound.config === 'string'
        ? JSON.parse(row.outbound.config)
        : row.outbound.config

      // Use publicIp field for public IP
      if (config.publicIp) {
        return config.publicIp
      }
    } catch (error) {
      console.warn('Failed to parse outbound config:', error)
    }
  }

  // Fallback to N/A if no public IP available
  return 'N/A'
}

const formatUserInfo = (row) => {
  const ip = getPublicIP(row)
  const port = row.port
  const username = row.username
  const password = row.password
  const expiry = row.expire_time ? formatDate(row.expire_time) : 'N/A'

  return `${ip}|${port}|${username}|${password}|${expiry}`
}

const copyUserInfo = async (row) => {
  const info = formatUserInfo(row)
  await copyToClipboard(info)
}

// Generate Shadowsocks subscription link
const generateSSLink = (row) => {
  if (row.protocol !== 'ss') {
    return 'N/A'
  }

  const ip = getPublicIP(row)
  const port = row.port
  const method = row.username  // For SS, username field stores the encryption method
  const password = row.password

  // Format: method:password@ip:port
  const ssInfo = `${method}:${password}@${ip}:${port}`

  // Encode to base64
  const base64Encoded = btoa(ssInfo)

  // Return ss:// link
  return `ss://${base64Encoded}`
}

// Copy SS subscription link
const copySSLink = async (row) => {
  const link = generateSSLink(row)
  if (link === 'N/A') {
    ElMessage.warning('Only available for Shadowsocks protocol')
    return
  }
  await copyToClipboard(link)
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const handleBatchExportClipboard = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  const exportData = selectedUsers.value
    .map(user => formatUserInfo(user))
    .join('\n')

  await copyToClipboard(exportData)
  ElMessage.success(`Exported ${selectedUsers.value.length} users to clipboard`)
}

const handleBatchExportFile = () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  const exportData = selectedUsers.value
    .map(user => formatUserInfo(user))
    .join('\n')

  // Create blob and download
  const blob = new Blob([exportData], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `users_export_${new Date().getTime()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success(`Exported ${selectedUsers.value.length} users to file`)
}

const handleBatchToggle = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  try {
    // Determine action based on majority status
    const enabledCount = selectedUsers.value.filter(u => u.enable).length
    const shouldEnable = enabledCount < selectedUsers.value.length / 2

    let successCount = 0
    let failCount = 0

    for (const user of selectedUsers.value) {
      // Only toggle if current state is different from target state
      if (user.enable !== shouldEnable) {
        try {
          await toggleUser(user.id)
          successCount++
        } catch (error) {
          failCount++
          console.error(`Failed to toggle user ${user.id}:`, error)
        }
      }
    }

    if (failCount === 0) {
      ElMessage.success(`${shouldEnable ? 'Enabled' : 'Disabled'} ${successCount} users successfully`)
    } else {
      ElMessage.warning(`${successCount} succeeded, ${failCount} failed`)
    }

    await loadUsers()
  } catch (error) {
    ElMessage.error('Batch toggle failed')
  }
}

const handleBatchExportSSLinks = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  // Filter only Shadowsocks users
  const ssUsers = selectedUsers.value.filter(user => user.protocol === 'ss')

  if (ssUsers.length === 0) {
    ElMessage.warning('No Shadowsocks users selected')
    return
  }

  // Generate SS links
  const ssLinks = ssUsers
    .map(user => generateSSLink(user))
    .filter(link => link !== 'N/A')
    .join('\n')

  // Copy to clipboard
  await copyToClipboard(ssLinks)
  ElMessage.success(`Copied ${ssUsers.length} Shadowsocks links to clipboard`)
}

const handleBatchDelete = () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  ElMessageBox.confirm(
    `Are you sure you want to delete ${selectedUsers.value.length} selected user(s)? This action cannot be undone.`,
    'Confirm Batch Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
      dangerouslyUseHTMLString: true
    }
  ).then(async () => {
    try {
      let successCount = 0
      let failCount = 0

      for (const user of selectedUsers.value) {
        try {
          await deleteUser(user.id)
          successCount++
        } catch (error) {
          failCount++
          console.error(`Failed to delete user ${user.id}:`, error)
        }
      }

      if (failCount === 0) {
        ElMessage.success(`Deleted ${successCount} users successfully`)
      } else {
        ElMessage.warning(`${successCount} succeeded, ${failCount} failed`)
      }

      await loadUsers()
    } catch (error) {
      ElMessage.error('Batch delete failed')
    }
  }).catch(() => {
    // User cancelled
  })
}

const handleShowSelectedInfo = () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('No users selected')
    return
  }

  selectedInfoVisible.value = true
}

const copySelectedUsersText = async () => {
  await copyToClipboard(selectedUsersText.value)
}

const loadGameInventories = async () => {
  inventoryLoading.value = true
  try {
    const result = await getAllGameInventories()
    gameInventories.value = result.games
  } catch (error) {
    ElMessage.error('Failed to load game inventories')
  } finally {
    inventoryLoading.value = false
  }
}

const handleCreateUser = async () => {
  // Load game inventories and show selection dialog
  gameSelectionVisible.value = true
  await loadGameInventories()
}

const handleGameSelect = (row) => {
  if (row.available_ips <= 0) {
    ElMessage.warning(`No available IPs for game "${row.rule_name}"`)
    return
  }

  // Store selected game info
  selectedGameRuleId.value = row.rule_id
  selectedGameName.value = row.rule_name
  selectedGameAvailableIPs.value = row.available_ips

  // Reset quick create form
  quickCreateForm.count = 1
  quickCreateForm.protocol = null
  quickCreateForm.expiration_days = null

  // Close game selection and show quick create dialog
  gameSelectionVisible.value = false
  quickCreateVisible.value = true
}

const resetGameSelection = () => {
  gameInventories.value = []
}

const resetQuickCreate = () => {
  selectedGameRuleId.value = null
  selectedGameName.value = ''
  selectedGameAvailableIPs.value = 0
  quickCreateForm.mode = 'quick'
  quickCreateForm.count = 1
  quickCreateForm.protocol = 'socks5'
  quickCreateForm.expiration_days = null
  quickCreateForm.method = 'aes-128-gcm'
  quickCreateForm.customPassword = ''
  quickCreateForm.send_limit = null
  quickCreateForm.receive_limit = null
}

const handleQuickCreateSubmit = async () => {
  if (!selectedGameRuleId.value) {
    ElMessage.error('No game selected')
    return
  }

  if (quickCreateForm.count > selectedGameAvailableIPs.value) {
    ElMessage.error(`Cannot create ${quickCreateForm.count} users. Only ${selectedGameAvailableIPs.value} IPs available.`)
    return
  }

  quickCreateLoading.value = true

  try {
    // Get system settings for defaults
    const settings = await getSystemSettings()

    // Determine protocol and expiration
    const protocol = quickCreateForm.protocol || settings.default_protocol
    const expirationDays = quickCreateForm.expiration_days || settings.default_expiration_days
    const expireTime = new Date(Date.now() + expirationDays * 24 * 60 * 60 * 1000)

    let successCount = 0
    let failCount = 0
    const errors = []

    // Find available outbounds for this game
    // This is a simplified approach - we should call a backend endpoint to get available IPs
    // For now, we'll create users and let the backend handle IP assignment

    for (let i = 0; i < quickCreateForm.count; i++) {
      try {
        let username, password

        // Determine credentials based on mode
        if (quickCreateForm.mode === 'custom') {
          // Custom mode
          if (protocol === 'ss') {
            // For shadowsocks in custom mode, use selected encryption method
            username = quickCreateForm.method
            // Generate or use custom password
            if (quickCreateForm.customPassword) {
              password = quickCreateForm.customPassword
            } else {
              const credentials = await generateTestCredentials(protocol)
              password = credentials.password
            }
          } else {
            // For socks5/http in custom mode
            const credentials = await generateTestCredentials(protocol)
            username = credentials.username
            password = quickCreateForm.customPassword || credentials.password
          }
        } else {
          // Quick mode
          if (protocol === 'ss') {
            // For shadowsocks in quick mode, use selected encryption method
            username = quickCreateForm.method
            const credentials = await generateTestCredentials(protocol)
            password = credentials.password
          } else {
            // For socks5/http in quick mode - auto-generate everything
            const credentials = await generateTestCredentials(protocol)
            username = credentials.username
            password = credentials.password
          }
        }

        // Find an available port (simple incrementing)
        const basePort = 10000 + Math.floor(Math.random() * 10000)
        const port = basePort + i

        // Determine bandwidth limits based on mode
        let sendLimit, receiveLimit
        if (quickCreateForm.mode === 'custom') {
          // Custom mode - use custom values or 0 if null
          sendLimit = quickCreateForm.send_limit !== null ? quickCreateForm.send_limit : 0
          receiveLimit = quickCreateForm.receive_limit !== null ? quickCreateForm.receive_limit : 0
        } else {
          // Quick mode - use system defaults
          sendLimit = settings.default_send_limit
          receiveLimit = settings.default_receive_limit
        }

        // Create user
        await createUser({
          port,
          username,
          password,
          protocol,
          outbound_id: outbounds.value[0]?.id, // TODO: Should get available outbound from backend
          rule_ids: [selectedGameRuleId.value],
          total_traffic: settings.default_max_send_byte || 0,
          expire_time: expireTime,
          send_limit: sendLimit,
          receive_limit: receiveLimit,
          max_conn_count: settings.default_max_conn_count,
          enable: true,
          remark: `${selectedGameName.value} - User ${i + 1}`,
          email: ''
        })

        successCount++
      } catch (error) {
        errors.push(`User ${i + 1}: ${error.response?.data?.detail || error.message}`)
        failCount++
      }
    }

    // Show results
    let message = `Created ${successCount} users successfully`
    if (failCount > 0) {
      message += `, ${failCount} failed`
      if (errors.length > 0) {
        console.error('Creation errors:', errors)
        ElMessage.warning({
          message: message + '. Check console for details.',
          duration: 5000
        })
      }
    } else {
      ElMessage.success(message)
    }

    quickCreateVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error('Failed to create users: ' + (error.message || 'Unknown error'))
  } finally {
    quickCreateLoading.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadOutbounds()
  loadRules()
})
</script>

<style scoped>
.user-list {
  width: 100%;
  padding: 20px;
  background: #f5f5f7;
  min-height: 100vh;
}

/* Card styling - Apple style */
:deep(.el-card) {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s ease;
}

:deep(.el-card:hover) {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 20px 24px;
  background: #ffffff;
}

:deep(.el-card__body) {
  padding: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 18px;
  color: #1d1d1f;
}

/* Search input - Apple style */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #d2d2d7;
  transition: all 0.2s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #0071e3;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #0071e3;
  box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1);
}

/* Buttons - Apple style */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: none;
  padding: 8px 16px;
}

:deep(.el-button--primary) {
  background: #0071e3;
  color: #ffffff;
}

:deep(.el-button--primary:hover) {
  background: #0077ed;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
}

:deep(.el-button--success) {
  background: #34c759;
  color: #ffffff;
}

:deep(.el-button--success:hover) {
  background: #30d158;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
}

:deep(.el-button--danger) {
  background: #ff3b30;
  color: #ffffff;
}

:deep(.el-button--danger:hover) {
  background: #ff453a;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 59, 48, 0.3);
}

:deep(.el-button--warning) {
  background: #ff9500;
  color: #ffffff;
}

:deep(.el-button--warning:hover) {
  background: #ff9f0a;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3);
}

:deep(.el-button--info) {
  background: #8e8e93;
  color: #ffffff;
}

:deep(.el-button--info:hover) {
  background: #98989d;
  transform: translateY(-1px);
}

:deep(.el-button.is-disabled) {
  opacity: 0.4;
  transform: none !important;
}

/* Table - Apple style */
:deep(.el-table) {
  border-radius: 10px;
  overflow: hidden;
  font-size: 14px;
  color: #1d1d1f;
}

:deep(.el-table thead) {
  background: #fafafa;
}

:deep(.el-table th.el-table__cell) {
  background: #fafafa;
  color: #86868b;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #e5e5e5;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-table__body tr:hover > td) {
  background: #f9f9f9 !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafafa;
}

/* Tags - Apple style */
:deep(.el-tag) {
  border-radius: 6px;
  border: none;
  padding: 4px 12px;
  font-weight: 500;
  font-size: 12px;
}

:deep(.el-tag--success) {
  background: #d1f2dd;
  color: #248a3d;
}

:deep(.el-tag--warning) {
  background: #fff3cd;
  color: #bf8700;
}

:deep(.el-tag--danger) {
  background: #ffe5e5;
  color: #c1121f;
}

:deep(.el-tag--info) {
  background: #e5e5e7;
  color: #6e6e73;
}

/* Batch actions toolbar - Apple style */
.batch-actions-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  margin-bottom: 20px;
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.batch-actions-toolbar > div {
  display: flex;
  gap: 10px;
}

/* Dialog - Apple style */
:deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
  border-top: 1px solid #f0f0f0;
}

/* Form - Apple style */
:deep(.el-form-item__label) {
  color: #1d1d1f;
  font-weight: 500;
  font-size: 14px;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px;
}

/* Loading - Apple style */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

/* Smooth transitions */
* {
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
</style>
