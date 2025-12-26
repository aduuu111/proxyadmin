<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>Admin Settings</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="150px"
        style="max-width: 600px"
      >
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" placeholder="Admin username" />
        </el-form-item>

        <el-form-item label="New Password" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="Leave empty to keep current password"
            show-password
          />
        </el-form-item>

        <el-form-item label="Confirm Password" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="Confirm new password"
            show-password
          />
        </el-form-item>

        <el-form-item label="Avatar URL" prop="avatar">
          <el-input v-model="form.avatar" placeholder="Optional avatar image URL" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            Save Changes
          </el-button>
          <el-button @click="resetForm">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>Core Service Configuration</span>
      </template>

      <el-alert
        v-if="coreConfig.is_configured === false"
        type="warning"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <strong>Core Service not configured.</strong> Please configure the connection settings below.
      </el-alert>

      <el-alert
        v-if="connectionTest.success === true"
        type="success"
        :closable="true"
        style="margin-bottom: 16px"
      >
        {{ connectionTest.message }}
        <div v-if="connectionTest.response_time_ms">
          Response time: {{ connectionTest.response_time_ms }}ms
        </div>
      </el-alert>

      <el-alert
        v-if="connectionTest.success === false"
        type="error"
        :closable="true"
        style="margin-bottom: 16px"
      >
        {{ connectionTest.message }}
      </el-alert>

      <el-form
        ref="coreFormRef"
        :model="coreForm"
        :rules="coreRules"
        label-width="150px"
        style="max-width: 600px"
      >
        <el-form-item label="API URL" prop="api_url">
          <el-input
            v-model="coreForm.api_url"
            placeholder="http://127.0.0.1:51128"
          >
            <template #prepend>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="coreForm.api_key"
            type="password"
            placeholder="Enter your API key"
            show-password
          >
            <template #prepend>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
          <template #extra>
            <span v-if="coreConfig.api_key_masked">
              Current: {{ coreConfig.api_key_masked }}
            </span>
          </template>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleCoreConfigSubmit"
            :loading="coreSaveLoading"
          >
            Save Configuration
          </el-button>
          <el-button
            @click="handleTestConnection"
            :loading="testLoading"
          >
            Test Connection
          </el-button>
          <el-button @click="resetCoreForm">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>Default User Parameters</span>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        These default values will be used when creating new users. You can override them during user creation.
      </el-alert>

      <el-form
        ref="systemSettingsFormRef"
        :model="systemSettingsForm"
        label-width="180px"
        style="max-width: 700px"
      >
        <el-form-item label="Default Protocol">
          <el-select v-model="systemSettingsForm.default_protocol" style="width: 100%">
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="Shadowsocks" value="ss" />
          </el-select>
        </el-form-item>

        <el-form-item label="Default Expiration Days">
          <el-input-number
            v-model="systemSettingsForm.default_expiration_days"
            :min="1"
            :max="3650"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399; margin-left: 8px;">Days</span>
        </el-form-item>

        <el-form-item label="Upload Limit (KB/s)">
          <el-input-number
            v-model="systemSettingsForm.default_send_limit"
            :min="0"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Download Limit (KB/s)">
          <el-input-number
            v-model="systemSettingsForm.default_receive_limit"
            :min="0"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Max Connections">
          <el-input-number
            v-model="systemSettingsForm.default_max_conn_count"
            :min="0"
            style="width: 100%"
          />
          <span style="font-size: 12px; color: #909399">0 = Unlimited</span>
        </el-form-item>

        <el-form-item label="Username Pattern">
          <el-input
            v-model="systemSettingsForm.username_pattern"
            placeholder="e.g., LLL### for abc123"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">
            L=lowercase letter, U=uppercase letter, #=digit
          </div>
        </el-form-item>

        <el-form-item label="Password Pattern">
          <el-input
            v-model="systemSettingsForm.password_pattern"
            placeholder="e.g., LLL### for abc123"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">
            L=lowercase letter, U=uppercase letter, #=digit
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSystemSettingsSubmit"
            :loading="systemSettingsLoading"
          >
            Save Default Settings
          </el-button>
          <el-button @click="handleTestCredentials" :loading="testCredentialsLoading">
            Test Credentials Generation
          </el-button>
        </el-form-item>

        <el-alert
          v-if="testCredentials.username"
          type="success"
          :closable="true"
          style="margin-top: 12px"
        >
          <div><strong>Generated Test Credentials:</strong></div>
          <div>Username: {{ testCredentials.username }}</div>
          <div>Password: {{ testCredentials.password }}</div>
        </el-alert>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>System Information</span>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="Panel Version">
          1.0.0
        </el-descriptions-item>
        <el-descriptions-item label="Backend Framework">
          FastAPI + SQLAlchemy
        </el-descriptions-item>
        <el-descriptions-item label="Frontend Framework">
          Vue 3 + Element Plus
        </el-descriptions-item>
        <el-descriptions-item label="Database">
          SQLite
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>Important Notes</span>
      </template>

      <el-alert type="warning" :closable="false" style="margin-bottom: 12px">
        <p><strong>Security Recommendations:</strong></p>
        <ul style="margin: 8px 0; padding-left: 20px">
          <li>Change the default admin password immediately</li>
          <li>Use strong passwords with at least 12 characters</li>
          <li>Keep your database backups in a secure location</li>
          <li>Regularly update the Core Service API key</li>
          <li>Monitor expired users and traffic usage regularly</li>
        </ul>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getProfile, updateProfile } from '@/api/auth'
import { getCoreConfig, updateCoreConfig, testCoreConnection } from '@/api/coreConfig'
import { getSystemSettings, updateSystemSettings, generateTestCredentials } from '@/api/settings'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { Link, Key } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const formRef = ref(null)
const coreFormRef = ref(null)
const systemSettingsFormRef = ref(null)
const loading = ref(false)
const coreSaveLoading = ref(false)
const testLoading = ref(false)
const systemSettingsLoading = ref(false)
const testCredentialsLoading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  avatar: ''
})

const coreForm = reactive({
  api_url: '',
  api_key: ''
})

const coreConfig = reactive({
  api_url: '',
  api_key_masked: '',
  is_configured: false
})

const connectionTest = reactive({
  success: null,
  message: '',
  response_time_ms: null
})

const systemSettingsForm = reactive({
  default_protocol: 'socks5',
  default_expiration_days: 30,
  default_max_send_byte: 0,
  default_max_receive_byte: 0,
  default_send_limit: 0,
  default_receive_limit: 0,
  default_max_conn_count: 0,
  username_pattern: 'LLL###',
  password_pattern: 'LLL###'
})

const testCredentials = reactive({
  username: '',
  password: ''
})

const validatePassword = (rule, value, callback) => {
  if (value && value.length < 6) {
    callback(new Error('Password must be at least 6 characters'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule, value, callback) => {
  if (form.password && value !== form.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, max: 50, message: 'Username must be 3-50 characters', trigger: 'blur' }
  ],
  password: [
    { validator: validatePassword, trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const coreRules = {
  api_url: [
    { required: true, message: 'Please enter Core Service API URL', trigger: 'blur' },
    { type: 'url', message: 'Please enter a valid URL', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: 'Please enter API Key', trigger: 'blur' },
    { min: 3, message: 'API Key must be at least 3 characters', trigger: 'blur' }
  ]
}

const loadProfile = async () => {
  try {
    const profile = await getProfile()
    form.username = profile.username
    form.avatar = profile.avatar || ''
  } catch (error) {
    ElMessage.error('Failed to load profile')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true

    try {
      const updateData = {
        username: form.username,
        avatar: form.avatar || null
      }

      // Only include password if it's being changed
      if (form.password) {
        updateData.password = form.password
      }

      await updateProfile(updateData)

      // Update stored username if changed
      if (form.username !== authStore.username) {
        authStore.username = form.username
        localStorage.setItem('username', form.username)
      }

      ElMessage.success('Profile updated successfully')

      // Clear password fields
      form.password = ''
      form.confirmPassword = ''
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      loading.value = false
    }
  })
}

const resetForm = () => {
  loadProfile()
  form.password = ''
  form.confirmPassword = ''

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

const loadCoreConfig = async () => {
  try {
    const config = await getCoreConfig()
    coreConfig.api_url = config.api_url
    coreConfig.api_key_masked = config.api_key_masked
    coreConfig.is_configured = config.is_configured

    coreForm.api_url = config.api_url
    // Don't pre-fill the API key for security
  } catch (error) {
    ElMessage.error('Failed to load Core Service configuration')
  }
}

const handleCoreConfigSubmit = async () => {
  if (!coreFormRef.value) return

  await coreFormRef.value.validate(async (valid) => {
    if (!valid) return

    coreSaveLoading.value = true

    try {
      const result = await updateCoreConfig({
        api_url: coreForm.api_url,
        api_key: coreForm.api_key
      })

      ElMessage.success(result.message || 'Configuration saved successfully')

      // Reload config to get masked key
      await loadCoreConfig()

      // Clear the password field
      coreForm.api_key = ''

      // Clear connection test result
      connectionTest.success = null
      connectionTest.message = ''
      connectionTest.response_time_ms = null
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || 'Failed to save configuration')
    } finally {
      coreSaveLoading.value = false
    }
  })
}

const handleTestConnection = async () => {
  testLoading.value = true

  try {
    // If form has values, test with those; otherwise test with current config
    const testData = (coreForm.api_url && coreForm.api_key)
      ? { api_url: coreForm.api_url, api_key: coreForm.api_key }
      : null

    const result = await testCoreConnection(testData)

    connectionTest.success = result.success
    connectionTest.message = result.message
    connectionTest.response_time_ms = result.response_time_ms || null

    if (result.success) {
      ElMessage.success('Connection test successful!')
    } else {
      ElMessage.error('Connection test failed')
    }
  } catch (error) {
    connectionTest.success = false
    connectionTest.message = error.response?.data?.detail || 'Failed to test connection'
    connectionTest.response_time_ms = null
    ElMessage.error('Failed to test connection')
  } finally {
    testLoading.value = false
  }
}

const resetCoreForm = () => {
  loadCoreConfig()
  coreForm.api_key = ''
  connectionTest.success = null
  connectionTest.message = ''
  connectionTest.response_time_ms = null

  if (coreFormRef.value) {
    coreFormRef.value.clearValidate()
  }
}

const loadSystemSettings = async () => {
  try {
    const settings = await getSystemSettings()
    systemSettingsForm.default_protocol = settings.default_protocol
    systemSettingsForm.default_expiration_days = settings.default_expiration_days
    systemSettingsForm.default_max_send_byte = settings.default_max_send_byte
    systemSettingsForm.default_max_receive_byte = settings.default_max_receive_byte
    systemSettingsForm.default_send_limit = settings.default_send_limit
    systemSettingsForm.default_receive_limit = settings.default_receive_limit
    systemSettingsForm.default_max_conn_count = settings.default_max_conn_count
    systemSettingsForm.username_pattern = settings.username_pattern
    systemSettingsForm.password_pattern = settings.password_pattern
  } catch (error) {
    ElMessage.error('Failed to load system settings')
  }
}

const handleSystemSettingsSubmit = async () => {
  systemSettingsLoading.value = true

  try {
    await updateSystemSettings(systemSettingsForm)
    ElMessage.success('Default settings saved successfully')
    // Clear test credentials after saving
    testCredentials.username = ''
    testCredentials.password = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Failed to save settings')
  } finally {
    systemSettingsLoading.value = false
  }
}

const handleTestCredentials = async () => {
  testCredentialsLoading.value = true

  try {
    const result = await generateTestCredentials()
    testCredentials.username = result.username
    testCredentials.password = result.password
    ElMessage.success('Test credentials generated')
  } catch (error) {
    ElMessage.error('Failed to generate test credentials')
  } finally {
    testCredentialsLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadCoreConfig()
  loadSystemSettings()
})
</script>

<style scoped>
.settings {
  width: 100%;
}

ul {
  line-height: 1.8;
}
</style>
