<template>
  <div class="login-view" :class="{ 'has-alert': serverStatus === 'error' }">
    <!-- 服务状态提示 -->
    <div v-if="serverStatus === 'error'" class="server-status-alert">
      <div class="alert-content">
        <exclamation-circle-icon class="alert-icon" size="20" />
        <div class="alert-text">
          <div class="alert-title">服务端连接失败</div>
          <div class="alert-message">{{ serverError }}</div>
        </div>
        <a-button type="link" size="small" @click="checkServerHealth" :loading="healthChecking">
          重试
        </a-button>
      </div>
    </div>

    <!-- 顶部导航：品牌名称 & 操作按钮 -->
    <nav class="login-navbar">
      <div class="navbar-content">
        <div class="brand-container" @click="goHome" style="cursor: pointer">
          <!-- 白色横版 logo（透明底，白校徽 + 中国石油大学（北京）校名），与门户页头同款 -->
          <img src="/cupb-logo.png" alt="中国石油大学（北京）" class="brand-logo" />
        </div>
      </div>
    </nav>

    <!-- 主要内容区：居中卡片 -->
    <main class="login-main">
      <div class="login-card">
        <!-- 左侧图片 -->
        <div class="card-side is-image">
          <img :src="loginBgImage" alt="登录背景" class="login-bg-image" />
        </div>

        <!-- 右侧表单 -->
        <div class="card-side is-form">
          <div class="form-wrapper">
            <header class="form-header">
              <!-- 如果是在初始化，显示特定标题 -->
              <h2 v-if="isFirstRun" class="init-title">系统初始化，请创建超级管理员</h2>
              <p v-else class="welcome-text">{{ isRegistering ? '创建学习账户' : '欢迎登录' }}</p>
            </header>

            <div class="login-content" :class="{ 'is-initializing': isFirstRun }">
              <!-- 初始化管理员表单 -->
              <div v-if="isFirstRun" class="login-form login-form--init">
                <a-form :model="adminForm" @finish="handleInitialize" layout="vertical">
                  <a-form-item
                    label="UID"
                    name="uid"
                    :rules="[
                      { required: true, message: '请输入UID' },
                      {
                        pattern: /^[a-zA-Z0-9_]+$/,
                        message: 'UID只能包含字母、数字和下划线'
                      },
                      {
                        min: 3,
                        max: 20,
                        message: 'UID长度必须在3-20个字符之间'
                      }
                    ]"
                  >
                    <a-input
                      v-model:value="adminForm.uid"
                      placeholder="请输入UID（3-20个字符）"
                      :maxlength="20"
                    />
                  </a-form-item>

                  <a-form-item
                    label="手机号（可选）"
                    name="phone_number"
                    :rules="[
                      {
                        validator: async (rule, value) => {
                          if (!value || value.trim() === '') {
                            return // 空值允许
                          }
                          const phoneRegex = /^1[3-9]\d{9}$/
                          if (!phoneRegex.test(value)) {
                            throw new Error('请输入正确的手机号格式')
                          }
                        }
                      }
                    ]"
                  >
                    <a-input
                      v-model:value="adminForm.phone_number"
                      placeholder="可用于登录，可不填写"
                      :max-length="11"
                    />
                  </a-form-item>

                  <a-form-item
                    label="密码"
                    name="password"
                    :rules="[
                      { required: true, message: '请输入密码' },
                      {
                        min: MIN_PASSWORD_LENGTH,
                        message: `密码至少需要 ${MIN_PASSWORD_LENGTH} 个字符`
                      }
                    ]"
                  >
                    <a-input-password
                      v-model:value="adminForm.password"
                      prefix-icon="lock"
                      :minlength="MIN_PASSWORD_LENGTH"
                    />
                  </a-form-item>

                  <a-form-item
                    label="确认密码"
                    name="confirmPassword"
                    :rules="[
                      { required: true, message: '请确认密码' },
                      { validator: validateConfirmPassword }
                    ]"
                  >
                    <a-input-password
                      v-model:value="adminForm.confirmPassword"
                      prefix-icon="lock"
                    />
                  </a-form-item>

                  <a-form-item v-if="showAgreementConsent" class="agreement-form-item">
                    <div class="agreement-row">
                      <a-checkbox v-model:checked="agreementAccepted">
                        登录即代表同意
                        <a
                          class="agreement-link"
                          :href="userAgreementUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          @click.stop
                          >《用户协议》</a
                        >
                        <a
                          class="agreement-link"
                          :href="privacyPolicyUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          @click.stop
                          >《隐私协议》</a
                        >
                      </a-checkbox>
                    </div>
                  </a-form-item>

                  <a-form-item>
                    <a-button type="primary" html-type="submit" :loading="loading" block
                      >创建管理员账户</a-button
                    >
                  </a-form-item>
                </a-form>
              </div>

              <!-- 登录表单 -->
              <div v-else class="login-form">
                <template v-if="isRegistering">
                  <a-form :model="registrationForm" @finish="handleRegister" layout="vertical">
                    <a-form-item
                      label="用户名"
                      name="username"
                      :rules="[
                        { required: true, message: '请输入用户名' },
                        { min: 2, max: 50, message: '用户名长度必须在2-50个字符之间' }
                      ]"
                    >
                      <a-input v-model:value="registrationForm.username" placeholder="用于展示的姓名或昵称">
                        <template #prefix><user-icon size="18" /></template>
                      </a-input>
                    </a-form-item>

                    <a-form-item label="手机号（可选）" name="phone_number">
                      <a-input
                        v-model:value="registrationForm.phone_number"
                        placeholder="可用于登录和找回账户"
                        :maxlength="11"
                      />
                    </a-form-item>

                    <a-form-item label="身份" name="account_type" :rules="[{ required: true }]">
                      <a-segmented
                        v-model:value="registrationForm.account_type"
                        :options="[
                          { label: '学生', value: 'student' },
                          { label: '教师', value: 'teacher' }
                        ]"
                        block
                      />
                    </a-form-item>

                    <a-form-item
                      label="密码"
                      name="password"
                      :rules="[
                        { required: true, message: '请输入密码' },
                        { min: MIN_PASSWORD_LENGTH, message: `密码至少需要 ${MIN_PASSWORD_LENGTH} 个字符` }
                      ]"
                    >
                      <a-input-password v-model:value="registrationForm.password">
                        <template #prefix><lock-icon size="18" /></template>
                      </a-input-password>
                    </a-form-item>

                    <a-form-item
                      label="确认密码"
                      name="confirmPassword"
                      :rules="[
                        { required: true, message: '请确认密码' },
                        { validator: validateRegistrationConfirmPassword }
                      ]"
                    >
                      <a-input-password v-model:value="registrationForm.confirmPassword">
                        <template #prefix><lock-icon size="18" /></template>
                      </a-input-password>
                    </a-form-item>

                    <a-form-item v-if="showAgreementConsent" class="agreement-form-item">
                      <div class="agreement-row">
                        <a-checkbox v-model:checked="agreementAccepted">
                          注册即代表同意
                          <a
                            class="agreement-link"
                            :href="userAgreementUrl"
                            target="_blank"
                            rel="noopener noreferrer"
                            @click.stop
                            >《用户协议》</a
                          >
                          <a
                            class="agreement-link"
                            :href="privacyPolicyUrl"
                            target="_blank"
                            rel="noopener noreferrer"
                            @click.stop
                            >《隐私协议》</a
                          >
                        </a-checkbox>
                      </div>
                    </a-form-item>

                    <a-form-item>
                      <a-button type="primary" html-type="submit" :loading="loading" block size="large">
                        注册并进入深地智学
                      </a-button>
                    </a-form-item>
                  </a-form>
                  <p class="form-switch">
                    已有账户？<button type="button" @click="switchToLogin">返回登录</button>
                  </p>
                </template>

                <template v-else>
                <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
                  <a-form-item
                    label="登录账号"
                    name="loginId"
                    :rules="[{ required: true, message: '请输入用户名、UID或手机号' }]"
                  >
                    <a-input v-model:value="loginForm.loginId" placeholder="用户名 / UID / 手机号">
                      <template #prefix>
                        <user-icon size="18" />
                      </template>
                    </a-input>
                  </a-form-item>

                  <a-form-item
                    label="密码"
                    name="password"
                    :rules="[{ required: true, message: '请输入密码' }]"
                  >
                    <a-input-password v-model:value="loginForm.password">
                      <template #prefix>
                        <lock-icon size="18" />
                      </template>
                    </a-input-password>
                  </a-form-item>

                  <a-form-item v-if="showAgreementConsent" class="agreement-form-item">
                    <div class="agreement-row">
                      <a-checkbox v-model:checked="agreementAccepted">
                        登录即代表同意
                        <a
                          class="agreement-link"
                          :href="userAgreementUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          @click.stop
                          >《用户协议》</a
                        >
                        <a
                          class="agreement-link"
                          :href="privacyPolicyUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          @click.stop
                          >《隐私协议》</a
                        >
                      </a-checkbox>
                    </div>
                  </a-form-item>

                  <a-form-item>
                    <a-button
                      type="primary"
                      html-type="submit"
                      :loading="loading"
                      :disabled="isLocked"
                      block
                      size="large"
                    >
                      <span v-if="isLocked">账户已锁定 {{ formatTime(lockRemainingTime) }}</span>
                      <span v-else>登录</span>
                    </a-button>
                  </a-form-item>
                </a-form>

                <!-- OIDC 登录选项  -->
                <div v-if="oidcChecking || oidcEnabled" class="third-party-login">
                  <div class="divider">
                    <span>或使用以下方式登录</span>
                  </div>
                  <div class="login-icons">
                    <!-- 检查中显示骨架屏 -->
                    <div v-if="oidcChecking" class="login-skeleton">
                      <a-skeleton-button block size="large" :active="true" />
                    </div>
                    <!-- 检查完成后显示按钮 -->
                    <a-button
                      v-else
                      type="default"
                      size="large"
                      block
                      :loading="oidcLoading"
                      @click="handleOIDCLogin"
                    >
                      <template #icon>
                        <key-icon size="18" />
                      </template>
                      {{ oidcButtonText }}
                    </a-button>
                  </div>
                </div>
                <p class="form-switch">
                  还没有账户？<button type="button" @click="switchToRegistration">立即注册</button>
                </p>
                </template>
              </div>

              <!-- 错误提示 -->
              <div v-if="errorMessage" class="error-message">
                {{ errorMessage }}
                <button v-if="registrationAlreadyExists" type="button" @click="switchToLogin">
                  返回登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="page-footer">
      <div class="copyright">
        &copy; {{ new Date().getFullYear() }} {{ brandName }}. All Rights Reserved.
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { useAgentStore } from '@/stores/agent'
import { message } from 'ant-design-vue'
import { healthApi } from '@/apis/system_api'
import { authApi } from '@/apis/auth_api'
import {
  User as UserIcon,
  Lock as LockIcon,
  Key as KeyIcon,
  AlertCircle as ExclamationCircleIcon
} from '@lucide/vue'
import { tryAutoStartOIDC, sanitizeRedirect } from '@/utils/oidcAutoStart'
import { MIN_PASSWORD_LENGTH } from '@/utils/passwordValidation'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const infoStore = useInfoStore()
const agentStore = useAgentStore()

// 品牌展示数据
const LEGACY_DEFAULT_BG = '/login-bg.jpg'
const loginBgImage = computed(() => {
  // BASE_URL-relative so the request stays inside the /geochat prefix in every environment:
  // the compose build (VITE_BASE_PATH=/geochat/) and the portal's prefix-preserving dev proxy
  // both serve this page under /geochat, where a root-absolute path would escape the prefix and
  // hit the 深地智学 portal instead of this app.
  // The DB still carries organization.login_bg='/login-bg.jpg' from before the campus photo
  // existed; treat that legacy default as unset so the new photo wins.
  // Photo: 校园风光——铁人王进喜塑像与图书馆（中国石油大学（北京）官网新闻图，2026-07），
  // 竖构图与登录卡左栏的纵横比接近，object-fit: cover 裁切损失小。
  const configuredBg = (infoStore.organization?.login_bg || '').trim()
  if (configuredBg && configuredBg !== LEGACY_DEFAULT_BG) return configuredBg
  return `${import.meta.env.BASE_URL}cup-campus.jpg`
})
const brandName = computed(() => infoStore.branding?.name?.trim() || '深地智学')
const userAgreementUrl = computed(() => {
  return infoStore.footer?.user_agreement_url?.trim() || ''
})
const privacyPolicyUrl = computed(() => {
  return infoStore.footer?.privacy_policy_url?.trim() || ''
})
const showAgreementConsent = computed(() => {
  return Boolean(userAgreementUrl.value && privacyPolicyUrl.value)
})
const portalReturnUrl = computed(() => {
  const raw = route.query.portal_return
  const value = Array.isArray(raw) ? raw[0] : raw
  if (typeof value !== 'string' || !value) return ''

  try {
    const target = new URL(value, window.location.origin)
    return target.origin === window.location.origin && !target.pathname.startsWith('/geochat')
      ? target.toString()
      : ''
  } catch {
    return ''
  }
})

// 状态
const isFirstRun = ref(false)
const isRegistering = ref(route.query.mode === 'register')
const loading = ref(false)
const errorMessage = ref('')
const registrationAlreadyExists = ref(false)
const agreementAccepted = ref(false)
const serverStatus = ref('loading')
const serverError = ref('')
const healthChecking = ref(false)

// OIDC 相关状态
const oidcEnabled = ref(false)
const oidcLoading = ref(false)
const oidcChecking = ref(true)
const oidcButtonText = ref('OIDC 登录')

// 登录锁定相关状态
const isLocked = ref(false)
const lockRemainingTime = ref(0)
const lockCountdown = ref(null)

// 登录表单
const loginForm = reactive({
  loginId: '', // 支持uid或phone_number登录
  password: ''
})

const registrationForm = reactive({
  username: '',
  phone_number: '',
  account_type: 'student',
  password: '',
  confirmPassword: ''
})

// 管理员初始化表单
const adminForm = reactive({
  uid: '', // 改为直接输入uid
  password: '',
  confirmPassword: '',
  phone_number: '' // 手机号字段（可选）
})

const goHome = () => {
  router.push('/')
}

const completeLogin = async (redirectPath = '/') => {
  if (portalReturnUrl.value) {
    window.location.replace(portalReturnUrl.value)
    return
  }

  if (redirectPath === '/') {
    try {
      await agentStore.initialize()
    } catch (error) {
      console.error('获取智能体信息失败:', error)
    }
    router.push('/agent')
    return
  }

  router.push(redirectPath)
}

// 清理倒计时器
const clearLockCountdown = () => {
  if (lockCountdown.value) {
    clearInterval(lockCountdown.value)
    lockCountdown.value = null
  }
}

// 启动锁定倒计时
const startLockCountdown = (remainingSeconds) => {
  clearLockCountdown()
  isLocked.value = true
  lockRemainingTime.value = remainingSeconds

  lockCountdown.value = setInterval(() => {
    lockRemainingTime.value--
    if (lockRemainingTime.value <= 0) {
      clearLockCountdown()
      isLocked.value = false
      errorMessage.value = ''
    }
  }, 1000)
}

// 格式化时间显示
const formatTime = (seconds) => {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds}秒`
  } else if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  } else {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    return `${days}天${hours}小时`
  }
}

// 密码确认验证
const validateConfirmPassword = async (rule, value) => {
  if (value === '') {
    throw new Error('请确认密码')
  }
  if (value !== adminForm.password) {
    throw new Error('两次输入的密码不一致')
  }
}

const validateRegistrationConfirmPassword = async (rule, value) => {
  if (value === '') {
    throw new Error('请确认密码')
  }
  if (value !== registrationForm.password) {
    throw new Error('两次输入的密码不一致')
  }
}

const switchToRegistration = () => {
  isRegistering.value = true
  errorMessage.value = ''
  registrationAlreadyExists.value = false
}

const switchToLogin = () => {
  isRegistering.value = false
  errorMessage.value = ''
  registrationAlreadyExists.value = false
}

const ensureAgreementAccepted = () => {
  if (!showAgreementConsent.value || agreementAccepted.value) {
    return true
  }

  const warningMessage = '请先阅读并同意《用户协议》《隐私协议》'
  message.warning(warningMessage)
  return false
}

// 处理登录
const handleLogin = async () => {
  // 如果当前被锁定，不允许登录
  if (isLocked.value) {
    message.warning(`账户被锁定，请等待 ${formatTime(lockRemainingTime.value)}`)
    return
  }

  if (!ensureAgreementAccepted()) {
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''
    clearLockCountdown()

    await userStore.login({
      loginId: loginForm.loginId,
      password: loginForm.password
    })

    message.success('登录成功')

    // 获取重定向路径
    const redirectPath = sessionStorage.getItem('redirect') || '/'
    sessionStorage.removeItem('redirect') // 清除重定向信息

    await completeLogin(redirectPath)
  } catch (error) {
    // 检查是否是锁定错误（HTTP 423）
    if (error.status === 423) {
      // 尝试从响应头中获取剩余时间
      let remainingTime = 0
      if (error.headers && error.headers.get) {
        const lockRemainingHeader = error.headers.get('X-Lock-Remaining')
        if (lockRemainingHeader) {
          remainingTime = parseInt(lockRemainingHeader)
        }
      }

      // 如果没有从头中获取到，尝试从错误消息中解析
      if (remainingTime === 0) {
        const lockTimeMatch = error.message.match(/(\d+)\s*秒/)
        if (lockTimeMatch) {
          remainingTime = parseInt(lockTimeMatch[1])
        }
      }

      if (remainingTime > 0) {
        startLockCountdown(remainingTime)
        errorMessage.value = `由于多次登录失败，账户已被锁定 ${formatTime(remainingTime)}`
      } else {
        errorMessage.value = error.message || '账户被锁定，请稍后再试'
      }
    } else if (error.kind === 'credentials' || error.status === 401) {
      errorMessage.value = '账号或密码错误'
    } else if (error.kind === 'service_unavailable' || (error.status >= 500 && error.status <= 599)) {
      errorMessage.value = '认证服务暂不可用，请稍后重试'
      console.error('认证服务不可用:', { status: error.status, kind: error.kind })
    } else if (error.kind === 'network') {
      errorMessage.value = '无法连接认证服务，请检查服务状态或网络连接'
      console.error('认证服务连接失败:', { kind: error.kind })
    } else {
      errorMessage.value = error.message || '登录失败，请稍后重试'
      console.error('登录请求失败:', { status: error.status ?? null, kind: error.kind || 'unknown' })
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!ensureAgreementAccepted()) {
    return
  }

  if (registrationForm.password !== registrationForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''
    registrationAlreadyExists.value = false
    await userStore.register({
      username: registrationForm.username.trim(),
      password: registrationForm.password,
      phone_number: registrationForm.phone_number.trim() || null,
      account_type: registrationForm.account_type
    })
    message.success('注册成功')
    await completeLogin()
  } catch (error) {
    if (error.kind === 'already_registered' || error.status === 409) {
      registrationAlreadyExists.value = true
      loginForm.loginId = registrationForm.phone_number.trim() || registrationForm.username.trim()
      errorMessage.value = error.message || '该账户已注册，请直接登录'
    } else {
      console.error('注册失败:', { status: error.status ?? null, kind: error.kind || 'unknown' })
      errorMessage.value = error.message || '注册失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

// 处理 OIDC 登录
const handleOIDCLogin = async () => {
  if (!ensureAgreementAccepted()) {
    return
  }

  try {
    oidcLoading.value = true
    errorMessage.value = ''

    // 获取 OIDC 登录 URL
    const response = await authApi.getOIDCLoginUrl()
    if (response.login_url) {
      // 保存当前路径，以便登录后返回
      const redirectPath =
        sessionStorage.getItem('redirect') || router.currentRoute.value.query.redirect || '/'
      sessionStorage.setItem('oidc_redirect', redirectPath)
      if (portalReturnUrl.value) sessionStorage.setItem('portal_return', portalReturnUrl.value)

      // 跳转到 OIDC Provider
      window.location.href = response.login_url
    } else {
      errorMessage.value = '获取 OIDC 登录地址失败'
    }
  } catch (error) {
    console.error('OIDC 登录失败:', error)
    errorMessage.value = error.message || 'OIDC 登录失败，请重试'
  } finally {
    oidcLoading.value = false
  }
}

// 检查 OIDC 配置
const checkOIDCConfig = async () => {
  oidcChecking.value = true
  try {
    const config = await authApi.getOIDCConfig()
    oidcEnabled.value = config.enabled
    if (config.provider_name) {
      oidcButtonText.value = config.provider_name
    }
    return config
  } catch (error) {
    console.error('检查 OIDC 配置失败:', error)
    oidcEnabled.value = false
    return null
  } finally {
    oidcChecking.value = false
  }
}

// 处理初始化管理员
const handleInitialize = async () => {
  if (!ensureAgreementAccepted()) {
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''

    if (adminForm.password !== adminForm.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }

    await userStore.initialize({
      uid: adminForm.uid,
      password: adminForm.password,
      phone_number: adminForm.phone_number || null // 空字符串转为null
    })

    message.success('管理员账户创建成功')
    await completeLogin()
  } catch (error) {
    console.error('初始化失败:', error)
    errorMessage.value = error.message || '初始化失败，请重试'
  } finally {
    loading.value = false
  }
}

// 检查是否是首次运行
const checkFirstRunStatus = async () => {
  try {
    loading.value = true
    const isFirst = await userStore.checkFirstRun()
    isFirstRun.value = isFirst
  } catch (error) {
    console.error('检查首次运行状态失败:', error)
    errorMessage.value = '系统出错，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 检查服务器健康状态
const checkServerHealth = async () => {
  try {
    healthChecking.value = true
    const response = await healthApi.checkHealth()
    if (response.status === 'ok') {
      serverStatus.value = 'ok'
    } else {
      serverStatus.value = 'error'
      serverError.value = response.message || '服务端状态异常'
    }
  } catch (error) {
    console.error('检查服务器健康状态失败:', error)
    serverStatus.value = 'error'
    serverError.value = error.message || '无法连接到服务端，请检查网络连接'
  } finally {
    healthChecking.value = false
  }
}

// 组件挂载时
onMounted(async () => {
  // 如果已登录，按 redirect 参数跳转（不固定跳首页）
  if (userStore.isLoggedIn) {
    await completeLogin(sanitizeRedirect(route.query.redirect))
    return
  }

  // 显示 OIDC 认证失败的错误信息（由后端重定向携带）
  if (route.query.oidc_error) {
    errorMessage.value = String(route.query.oidc_error)
  }

  // 首先检查服务器健康状态
  await checkServerHealth()

  // 检查是否是首次运行
  await checkFirstRunStatus()

  // 如果处于首次运行状态，不需要 OIDC 自动登录
  if (isFirstRun.value) {
    return
  }

  // 检查 OIDC 配置完成后，尝试自动触发 OIDC 登录（跨系统跳转场景）
  const config = await checkOIDCConfig()
  if (config && config.enabled) {
    const autoStarted = await tryAutoStartOIDC(async () => await authApi.getOIDCLoginUrl(), config)
    // 如果已发起 OIDC 跳转，页面会被重定向，不需要继续
    if (autoStarted) return
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  clearLockCountdown()
})
</script>

<style lang="less" scoped>
.login-view {
  min-height: 100vh;
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  isolation: isolate;

  /* 品牌深蓝整页背景：与门户 hero 同族的渐变打底，加一点柔光和同心圆装饰，
     白色登录卡浮于其上。替换掉原先单调的灰色波点底。 */
  color: #142d45;
  background:
    radial-gradient(ellipse at 88% 118%, rgba(103, 189, 242, 0.28), transparent 55%),
    radial-gradient(ellipse at 8% -12%, rgba(214, 238, 255, 0.16), transparent 52%),
    linear-gradient(150deg, #03294e 0%, #06508f 46%, #0a74b8 100%);

  /* 右下同心圆装饰（呼应统一登录入口页的 strata 母题） */
  &::before {
    content: '';
    position: absolute;
    right: -16vw;
    bottom: -34vw;
    width: 58vw;
    height: 58vw;
    border: 1px solid rgba(150, 205, 248, 0.22);
    border-radius: 50%;
    box-shadow:
      0 0 0 70px rgba(150, 205, 248, 0.06),
      0 0 0 170px rgba(150, 205, 248, 0.05);
    z-index: -1;
  }

  /* 左上淡圆环，平衡构图 */
  &::after {
    content: '';
    position: absolute;
    top: -18vw;
    left: -14vw;
    width: 40vw;
    height: 40vw;
    border: 1px solid rgba(150, 205, 248, 0.16);
    border-radius: 50%;
    z-index: -1;
  }

  &.has-alert {
    padding-top: 60px;
  }
}

/* Unified Navbar */
.login-navbar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 32px 0;
  z-index: 10;

  .navbar-content {
    max-width: 1500px; /* Constraint the width */
    margin: 0 auto;
    padding: 0 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    .brand-container {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
}

/* 白色横版 logo：透明底，白校徽 + 校名，深蓝背景上直接展示（门户页头同款素材） */
.brand-logo {
  height: 44px;
  width: auto;
}

.top-logo {
  height: 32px;
  width: auto;
  object-fit: contain;
}

.back-home-btn {
  color: var(--gray-600);
  font-size: 14px;
  &:hover {
    color: var(--main-color);
    background-color: transparent;
  }
}

/* Main Content: Card Layout */
.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  padding-top: 80px; /* Add space for navbar */
}

.login-card {
  width: 900px;
  max-width: 95vw;
  /* min-height instead of fixed height: the register form (username + phone + password +
     confirm + agreement + button) is taller than 560px, and the fixed height was clipping
     the header at the top and the form-switch at the bottom. The card now grows with the
     form; the image side stretches with it. */
  min-height: 560px;
  background: var(--gray-0);
  border-radius: 16px;
  box-shadow: 0 0px 40px var(--shadow-1);
  display: flex;
  overflow: hidden;
}

.card-side {
  position: relative;
}

/* Image Side */
.card-side.is-image {
  flex: 1.4;
  background-color: var(--main-10);
  overflow: hidden;

  .login-bg-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
  }
}

/* Form Side */
.card-side.is-form {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-wrapper {
  width: 100%;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-header {
  text-align: left;
  .welcome-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--gray-500);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .init-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--main-color);
    margin: 0;
    line-height: 1.4;
  }
}

.login-form {
  :deep(.ant-input-affix-wrapper) {
    padding: 10px 12px;
    border-radius: 8px;
  }
  :deep(.ant-btn) {
    height: 44px;
    font-size: 16px;
    border-radius: 8px;
  }
  :deep(.ant-input-prefix) {
    margin-right: 8px;
    color: var(--gray-500);
  }
}

.login-form.login-form--init :deep(.ant-form-item) {
  margin-bottom: 14px;
}

.third-party-login {
  margin-top: 16px;
  .divider {
    position: relative;
    text-align: center;
    margin: 24px 0 16px;
    &::before,
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      width: 30%;
      height: 1px;
      background-color: var(--gray-200);
    }
    &::before {
      left: 0;
    }
    &::after {
      right: 0;
    }
    span {
      display: inline-block;
      padding: 0 8px;
      background-color: var(--gray-0);
      color: var(--gray-400);
      font-size: 12px;
    }
  }

  .login-icons {
    :deep(.ant-btn) {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border-color: var(--gray-300);
      color: var(--gray-700);

      &:hover {
        border-color: var(--main-color);
        color: var(--main-color);
        background-color: var(--main-10);
      }

      .anticon,
      svg {
        color: var(--main-color);
      }
    }
  }

  /* 修复：添加骨架屏样式 */
  .login-skeleton {
    :deep(.ant-skeleton-button) {
      width: 100% !important;
      height: 44px;
      border-radius: 8px;
    }
  }
}

.agreement-form-item {
  margin-bottom: 12px;
}

.agreement-row {
  font-size: 13px;
  color: var(--gray-600);
  line-height: 1.6;

  :deep(.ant-checkbox-wrapper) {
    display: inline-flex;
    align-items: flex-start;
  }

  :deep(.ant-checkbox + span) {
    padding-inline-start: 8px;
  }
}

.agreement-link {
  color: var(--main-color);

  &:hover {
    text-decoration: underline;
  }
}

.form-switch {
  margin: 4px 0 0;
  color: var(--gray-600);
  font-size: 13px;
  text-align: center;

  button {
    padding: 0;
    color: var(--main-color);
    background: transparent;
    border: 0;
    cursor: pointer;
    font-size: inherit;

    &:hover {
      text-decoration: underline;
    }
  }
}

.error-message {
  margin-top: 16px;
  padding: 10px 12px;
  background-color: var(--color-error-50);
  border: 1px solid color-mix(in srgb, var(--color-error-500) 25%, transparent);
  border-radius: 6px;
  color: var(--color-error-700);
  font-size: 13px;
  text-align: center;

  button {
    margin-left: 8px;
    padding: 0;
    color: currentColor;
    background: transparent;
    border: 0;
    font-weight: 700;
    text-decoration: underline;
    cursor: pointer;
  }
}

/* Page Footer */
.page-footer {
  padding: 24px;
  text-align: center;
}

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;

  a {
    color: var(--gray-500);
    font-size: 13px;
    &:hover {
      color: var(--main-color);
    }
  }

  .divider {
    color: var(--gray-300);
    font-size: 12px;
  }
}

.copyright {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

/* Server Status Alert */
.server-status-alert {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 12px 20px;
  background: var(--color-error-500);
  color: var(--gray-0);
  z-index: 1000;

  .alert-content {
    display: flex;
    align-items: center;
    max-width: 1500px;
    margin: 0 auto;

    .alert-icon {
      font-size: 20px;
      margin-right: 12px;
      color: var(--gray-0);
    }

    .alert-text {
      flex: 1;

      .alert-title {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 2px;
      }

      .alert-message {
        font-size: 14px;
        opacity: 0.9;
      }
    }

    :deep(.ant-btn-link) {
      color: var(--gray-0);
      border-color: var(--gray-0);

      &:hover {
        color: var(--gray-0);
        background-color: color-mix(in srgb, var(--gray-0) 10%, transparent);
      }
    }
  }
}

/* Responsive */
@media (max-width: 1280px) {
  .login-navbar .navbar-content {
    padding: 0 40px;
  }
}

@media (max-width: 768px) {
  .login-navbar .navbar-content {
    padding: 0 20px;
  }

  .brand-logo {
    height: 40px;
  }

  .login-card {
    flex-direction: column;
    height: auto;
    max-height: none;
    width: 100%;
    margin-top: 20px;
  }

  .card-side.is-image {
    display: none;
  }

  .card-side.is-form {
    padding: 40px 20px;
  }
}
</style>
