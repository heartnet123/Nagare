<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useApiProfile, type ProfileData } from '~/composables/useApi/profile'
import {
  Pencil,
  Mail,
  MapPin,
  Clock,
  Building2,
  User,
  SlidersHorizontal,
  Bell,
  Lock,
  Link2,
  Plus,
  MoreHorizontal,
  ChevronRight,
  Copy,
  CheckCircle2,
  Circle,
  Database,
  Search,
  Check,
  X,
  Laptop,
  History,
  ShieldCheck,
  Smartphone
} from '@lucide/vue'

definePageMeta({ layout: 'default' })

const api = useApiProfile()

const profile = ref<ProfileData | null>(null)
const loading = ref(true)
const saving = ref(false)
const copied = ref(false)
const toastMessage = ref<string | null>(null)

// Edit Modals
const showEditPersonal = ref(false)
const showEditWork = ref(false)
const showAddAccount = ref(false)
const showSecurityModal = ref(false)

// Edit Forms
const personalForm = reactive({
  full_name: '',
  email: '',
  phone: '',
  location: '',
  company: '',
  bio: '',
  avatar_url: ''
})

const workForm = reactive({
  role: '',
  default_workspace: '',
  preferred_language: '',
  timezone: '',
  working_hours: ''
})

const newAccount = reactive({
  provider: 'figma',
  account_name: ''
})

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = null
  }, 3000)
}

async function loadProfile() {
  loading.value = true
  try {
    const data = await api.getProfile()
    profile.value = data
    syncPersonalForm(data)
    syncWorkForm(data)
  } catch (err) {
    console.error('Failed to load profile', err)
    showToast('Failed to load profile data')
  } finally {
    loading.value = false
  }
}

function syncPersonalForm(data: ProfileData) {
  personalForm.full_name = data.full_name
  personalForm.email = data.email
  personalForm.phone = data.phone
  personalForm.location = data.location
  personalForm.company = data.company
  personalForm.bio = data.bio
  personalForm.avatar_url = data.avatar_url
}

function syncWorkForm(data: ProfileData) {
  workForm.role = data.role
  workForm.default_workspace = data.default_workspace
  workForm.preferred_language = data.preferred_language
  workForm.timezone = data.timezone
  workForm.working_hours = data.working_hours
}

function openPersonalModal() {
  if (!profile.value) return
  syncPersonalForm(profile.value)
  showEditPersonal.value = true
}

function openWorkModal() {
  if (!profile.value) return
  syncWorkForm(profile.value)
  showEditWork.value = true
}

async function savePersonalInfo() {
  saving.value = true
  try {
    const updated = await api.updateProfile(personalForm)
    profile.value = updated
    showEditPersonal.value = false
    showToast('Profile updated successfully')
  } catch (err) {
    console.error('Update failed', err)
    showToast('Failed to update profile')
  } finally {
    saving.value = false
  }
}

async function saveWorkPreferences() {
  saving.value = true
  try {
    const updated = await api.updateProfile(workForm)
    profile.value = updated
    showEditWork.value = false
    showToast('Work preferences saved')
  } catch (err) {
    console.error('Update failed', err)
    showToast('Failed to save preferences')
  } finally {
    saving.value = false
  }
}

async function toggleNotification(key: 'email_notifications' | 'task_updates' | 'approval_requests' | 'weekly_digest') {
  if (!profile.value) return
  const currentVal = profile.value[key]
  const newVal = !currentVal
  profile.value[key] = newVal

  try {
    const updated = await api.updateNotifications({ [key]: newVal })
    profile.value = updated
    showToast('Notification settings updated')
  } catch (err) {
    // Revert on error
    profile.value[key] = currentVal
    console.error('Notification update failed', err)
    showToast('Failed to update notification setting')
  }
}

async function handleToggleChecklist(itemId: string) {
  try {
    const updated = await api.toggleChecklist(itemId)
    profile.value = updated
  } catch (err) {
    console.error('Checklist toggle failed', err)
    showToast('Failed to update checklist')
  }
}

async function handleAddAccount() {
  if (!newAccount.account_name.trim()) return
  saving.value = true
  try {
    const updated = await api.addConnectedAccount({
      provider: newAccount.provider,
      account_name: newAccount.account_name.trim()
    })
    profile.value = updated
    newAccount.account_name = ''
    showAddAccount.value = false
    showToast('Connected account added')
  } catch (err) {
    console.error('Add account failed', err)
    showToast('Failed to connect account')
  } finally {
    saving.value = false
  }
}

async function handleDisconnectAccount(provider: string) {
  if (!confirm(`Are you sure you want to disconnect ${provider.toUpperCase()}?`)) return
  try {
    const updated = await api.deleteConnectedAccount(provider)
    profile.value = updated
    showToast(`${provider.toUpperCase()} disconnected`)
  } catch (err) {
    console.error('Disconnect failed', err)
    showToast('Failed to disconnect account')
  }
}

function copyAccountId() {
  if (!profile.value) return
  navigator.clipboard.writeText(profile.value.account_id)
  copied.value = true
  showToast('Account ID copied to clipboard')
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

function getActivityIcon(type: string) {
  switch (type.toLowerCase()) {
    case 'notion':
      return Link2
    case 'settings':
      return Bell
    case 'security':
      return Laptop
    default:
      return User
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="flex-1 overflow-y-auto bg-[#f8fafc] dark:bg-stone-950 text-slate-800 dark:text-stone-200">
    <div class="max-w-7xl mx-auto p-6 md:p-8 space-y-6">
      <!-- Top Bar: Title & Search -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Your profile
          </h1>
          <p class="text-sm text-slate-500 dark:text-stone-400 mt-1">
            Manage your account, identity, and preferences.
          </p>
        </div>

        <div class="flex items-center gap-3 self-end sm:self-auto">
          <!-- Search box -->
          <div class="relative flex items-center">
            <Search
              :size="15"
              class="absolute left-3 text-slate-400 pointer-events-none"
            />
            <input
              type="text"
              placeholder="Search anything..."
              class="w-48 sm:w-64 pl-9 pr-12 py-1.5 text-xs bg-white dark:bg-stone-900 border border-slate-200/80 dark:border-stone-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 dark:text-stone-200 shadow-2xs"
            >
            <span class="absolute right-2.5 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 bg-slate-100 dark:bg-stone-800 rounded border border-slate-200/60 dark:border-stone-700">
              ⌘ K
            </span>
          </div>

          <!-- Notification Bell -->
          <button
            aria-label="Notifications"
            class="p-2 rounded-xl bg-white dark:bg-stone-900 border border-slate-200/80 dark:border-stone-800 text-slate-500 hover:text-slate-800 dark:hover:text-stone-200 shadow-2xs transition-colors"
          >
            <Bell :size="16" />
          </button>
        </div>
      </div>

      <!-- Loading skeleton or Main Grid -->
      <div
        v-if="loading && !profile"
        class="flex items-center justify-center py-20"
      >
        <div class="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>

      <div
        v-else-if="profile"
        class="grid grid-cols-1 lg:grid-cols-12 gap-6"
      >
        <!-- LEFT COLUMN (Span 8) -->
        <div class="lg:col-span-8 space-y-6">
          <!-- 1. Header Banner Card -->
          <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
              <div class="flex items-center gap-5">
                <img
                  :src="profile.avatar_url"
                  :alt="profile.full_name"
                  class="w-20 h-20 rounded-full object-cover ring-4 ring-slate-100 dark:ring-stone-800 shrink-0"
                >
                <div>
                  <h2 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    {{ profile.full_name }}
                  </h2>
                  <p class="text-sm font-medium text-slate-500 dark:text-stone-400 mt-0.5">
                    {{ profile.role }}
                  </p>
                </div>
              </div>

              <button
                class="self-start sm:self-auto bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl flex items-center gap-2 shadow-sm transition-all"
                @click="openPersonalModal"
              >
                <Pencil :size="14" />
                Edit profile
              </button>
            </div>

            <!-- Profile Info Metadata Rows -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-y-2.5 gap-x-6 mt-6 pt-5 border-t border-slate-100 dark:border-stone-800 text-xs text-slate-600 dark:text-stone-300">
              <div class="flex items-center gap-2.5">
                <Mail
                  :size="15"
                  class="text-slate-400 shrink-0"
                />
                <span class="truncate">{{ profile.email }}</span>
              </div>
              <div class="flex items-center gap-2.5">
                <Clock
                  :size="15"
                  class="text-slate-400 shrink-0"
                />
                <span>{{ profile.timezone }}</span>
              </div>
              <div class="flex items-center gap-2.5">
                <MapPin
                  :size="15"
                  class="text-slate-400 shrink-0"
                />
                <span>{{ profile.location }}</span>
              </div>
              <div class="flex items-center gap-2.5">
                <Building2
                  :size="15"
                  class="text-slate-400 shrink-0"
                />
                <span>{{ profile.company }}</span>
              </div>
            </div>
          </div>

          <!-- 2 & 3. Personal Information & Work Preferences (2 Cols Grid) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- 2. Personal Information Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-stone-800">
                  <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                    <User
                      :size="16"
                      class="text-blue-600"
                    />
                    <span>Personal information</span>
                  </div>
                  <button
                    class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-stone-700 text-xs font-medium text-slate-600 dark:text-stone-300 hover:bg-slate-50 dark:hover:bg-stone-800 transition-colors"
                    @click="openPersonalModal"
                  >
                    Edit
                  </button>
                </div>

                <div class="divide-y divide-slate-100 dark:divide-stone-800/80 text-xs">
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Full name</span>
                    <span class="col-span-8 text-slate-800 dark:text-stone-200 font-medium">{{ profile.full_name }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Email</span>
                    <span class="col-span-8 text-slate-800 dark:text-stone-200 font-medium truncate">{{ profile.email }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Phone</span>
                    <span class="col-span-8 text-slate-800 dark:text-stone-200 font-medium">{{ profile.phone }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Location</span>
                    <span class="col-span-8 text-slate-800 dark:text-stone-200 font-medium">{{ profile.location }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Company</span>
                    <span class="col-span-8 text-slate-800 dark:text-stone-200 font-medium">{{ profile.company }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-4 text-slate-400 font-medium">Bio</span>
                    <span class="col-span-8 text-slate-700 dark:text-stone-300 leading-relaxed">{{ profile.bio }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Work Preferences Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-stone-800">
                  <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                    <SlidersHorizontal
                      :size="16"
                      class="text-blue-600"
                    />
                    <span>Work preferences</span>
                  </div>
                  <button
                    class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-stone-700 text-xs font-medium text-slate-600 dark:text-stone-300 hover:bg-slate-50 dark:hover:bg-stone-800 transition-colors"
                    @click="openWorkModal"
                  >
                    Edit
                  </button>
                </div>

                <div class="divide-y divide-slate-100 dark:divide-stone-800/80 text-xs">
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-5 text-slate-400 font-medium">Role</span>
                    <span class="col-span-7 text-slate-800 dark:text-stone-200 font-medium">{{ profile.role }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-5 text-slate-400 font-medium">Default workspace</span>
                    <span class="col-span-7 text-slate-800 dark:text-stone-200 font-medium">{{ profile.default_workspace }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-5 text-slate-400 font-medium">Preferred language</span>
                    <span class="col-span-7 text-slate-800 dark:text-stone-200 font-medium">{{ profile.preferred_language }}</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-5 text-slate-400 font-medium">Time zone</span>
                    <span class="col-span-7 text-slate-800 dark:text-stone-200 font-medium">{{ profile.timezone }} ({{ profile.timezone_utc }})</span>
                  </div>
                  <div class="grid grid-cols-12 py-3">
                    <span class="col-span-5 text-slate-400 font-medium">Working hours</span>
                    <div class="col-span-7 text-slate-800 dark:text-stone-200 font-medium leading-relaxed">
                      <div>9:00 AM – 6:00 PM</div>
                      <div class="text-slate-400 dark:text-stone-500 font-normal">
                        Mon – Fri
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 4 & 5. Notifications & Security (2 Cols Grid) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- 4. Notifications Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-stone-800">
                <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                  <Bell
                    :size="16"
                    class="text-blue-600"
                  />
                  <span>Notifications</span>
                </div>
                <button
                  class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-stone-700 text-xs font-medium text-slate-600 dark:text-stone-300 hover:bg-slate-50 dark:hover:bg-stone-800 transition-colors"
                  @click="showToast('Toggle items directly using switches below')"
                >
                  Edit
                </button>
              </div>

              <div class="space-y-4 pt-3">
                <!-- Toggle 1 -->
                <div class="flex items-center justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="text-xs font-semibold text-slate-800 dark:text-stone-200">
                      Email notifications
                    </div>
                    <div class="text-[11px] text-slate-400 dark:text-stone-500">
                      Product updates, mentions, and important alerts
                    </div>
                  </div>
                  <button
                    role="switch"
                    :aria-checked="profile.email_notifications"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="profile.email_notifications ? 'bg-blue-600' : 'bg-slate-200 dark:bg-stone-700'"
                    @click="toggleNotification('email_notifications')"
                  >
                    <span
                      class="pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out mt-[3px] ml-[3px]"
                      :class="profile.email_notifications ? 'translate-x-4' : 'translate-x-0'"
                    />
                  </button>
                </div>

                <!-- Toggle 2 -->
                <div class="flex items-center justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="text-xs font-semibold text-slate-800 dark:text-stone-200">
                      Task updates
                    </div>
                    <div class="text-[11px] text-slate-400 dark:text-stone-500">
                      Changes to tasks you're involved in
                    </div>
                  </div>
                  <button
                    role="switch"
                    :aria-checked="profile.task_updates"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="profile.task_updates ? 'bg-blue-600' : 'bg-slate-200 dark:bg-stone-700'"
                    @click="toggleNotification('task_updates')"
                  >
                    <span
                      class="pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out mt-[3px] ml-[3px]"
                      :class="profile.task_updates ? 'translate-x-4' : 'translate-x-0'"
                    />
                  </button>
                </div>

                <!-- Toggle 3 -->
                <div class="flex items-center justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="text-xs font-semibold text-slate-800 dark:text-stone-200">
                      Approval requests
                    </div>
                    <div class="text-[11px] text-slate-400 dark:text-stone-500">
                      Requests for your review and approval
                    </div>
                  </div>
                  <button
                    role="switch"
                    :aria-checked="profile.approval_requests"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="profile.approval_requests ? 'bg-blue-600' : 'bg-slate-200 dark:bg-stone-700'"
                    @click="toggleNotification('approval_requests')"
                  >
                    <span
                      class="pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out mt-[3px] ml-[3px]"
                      :class="profile.approval_requests ? 'translate-x-4' : 'translate-x-0'"
                    />
                  </button>
                </div>

                <!-- Toggle 4 -->
                <div class="flex items-center justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="text-xs font-semibold text-slate-800 dark:text-stone-200">
                      Weekly digest
                    </div>
                    <div class="text-[11px] text-slate-400 dark:text-stone-500">
                      A summary of your activity every Monday
                    </div>
                  </div>
                  <button
                    role="switch"
                    :aria-checked="profile.weekly_digest"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="profile.weekly_digest ? 'bg-blue-600' : 'bg-slate-200 dark:bg-stone-700'"
                    @click="toggleNotification('weekly_digest')"
                  >
                    <span
                      class="pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out mt-[3px] ml-[3px]"
                      :class="profile.weekly_digest ? 'translate-x-4' : 'translate-x-0'"
                    />
                  </button>
                </div>
              </div>
            </div>

            <!-- 5. Security Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-stone-800">
                <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                  <Lock
                    :size="16"
                    class="text-blue-600"
                  />
                  <span>Security</span>
                </div>
                <button
                  class="text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors"
                  @click="showSecurityModal = true"
                >
                  Manage security
                </button>
              </div>

              <div class="divide-y divide-slate-100 dark:divide-stone-800/80 text-xs">
                <!-- Password row -->
                <div
                  class="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50/60 dark:hover:bg-stone-800/40 px-1 rounded-lg transition-colors"
                  @click="showSecurityModal = true"
                >
                  <div class="space-y-0.5">
                    <div class="font-semibold text-slate-800 dark:text-stone-200">
                      Password
                    </div>
                    <div class="text-[11px] text-slate-400">
                      {{ profile.password_last_changed }}
                    </div>
                  </div>
                  <div class="flex items-center gap-2 text-slate-500">
                    <span class="tracking-widest text-slate-600 dark:text-stone-400">••••••••</span>
                    <ChevronRight
                      :size="14"
                      class="text-slate-400"
                    />
                  </div>
                </div>

                <!-- 2FA row -->
                <div
                  class="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50/60 dark:hover:bg-stone-800/40 px-1 rounded-lg transition-colors"
                  @click="showSecurityModal = true"
                >
                  <div class="font-semibold text-slate-800 dark:text-stone-200">
                    Two-factor authentication
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-[11px] font-medium bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 rounded-md">
                      Enabled
                    </span>
                    <ChevronRight
                      :size="14"
                      class="text-slate-400"
                    />
                  </div>
                </div>

                <!-- Active Sessions row -->
                <div
                  class="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50/60 dark:hover:bg-stone-800/40 px-1 rounded-lg transition-colors"
                  @click="showSecurityModal = true"
                >
                  <div class="font-semibold text-slate-800 dark:text-stone-200">
                    Active sessions
                  </div>
                  <div class="flex items-center gap-2 text-slate-600 dark:text-stone-300">
                    <span>{{ profile.active_sessions }} devices</span>
                    <ChevronRight
                      :size="14"
                      class="text-slate-400"
                    />
                  </div>
                </div>

                <!-- Recent login row -->
                <div
                  class="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50/60 dark:hover:bg-stone-800/40 px-1 rounded-lg transition-colors"
                  @click="showSecurityModal = true"
                >
                  <div class="font-semibold text-slate-800 dark:text-stone-200">
                    Recent login
                  </div>
                  <div class="flex items-center gap-2 text-right text-[11px] text-slate-500 dark:text-stone-400">
                    <div>
                      <div>Apr 27, 2025, 11:24 AM</div>
                      <div>San Francisco, CA</div>
                    </div>
                    <ChevronRight
                      :size="14"
                      class="text-slate-400 shrink-0"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 6. Connected Accounts Card (Full Width in Left Column) -->
          <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-stone-800">
              <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                <Link2
                  :size="16"
                  class="text-blue-600"
                />
                <span>Connected accounts</span>
              </div>
              <button
                class="px-3 py-1 rounded-lg border border-slate-200 dark:border-stone-700 text-xs font-medium text-slate-700 dark:text-stone-300 hover:bg-slate-50 dark:hover:bg-stone-800 flex items-center gap-1.5 transition-colors"
                @click="showAddAccount = true"
              >
                <Plus :size="13" />
                Add account
              </button>
            </div>

            <!-- Connected Accounts Grid (4 items) -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <div
                v-for="acc in profile.connected_accounts"
                :key="acc.provider"
                class="border border-slate-200/80 dark:border-stone-800 rounded-xl p-3.5 bg-white dark:bg-stone-900/90 flex flex-col justify-between hover:border-slate-300 dark:hover:border-stone-700 transition-colors group"
              >
                <div>
                  <div class="flex items-center justify-between">
                    <!-- Provider Logo -->
                    <div class="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs">
                      <!-- Google Logo SVG -->
                      <svg
                        v-if="acc.provider === 'google'"
                        class="w-5 h-5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          fill="#4285F4"
                          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        />
                        <path
                          fill="#34A853"
                          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        />
                        <path
                          fill="#FBBC05"
                          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                        />
                        <path
                          fill="#EA4335"
                          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                        />
                      </svg>
                      <!-- Slack Logo SVG -->
                      <svg
                        v-else-if="acc.provider === 'slack'"
                        class="w-5 h-5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          fill="#E01E5A"
                          d="M6 15a2 2 0 0 1-2-2 2 2 0 0 1 2-2h2v2a2 2 0 0 1-2 2zm1 0a2 2 0 0 1 2-2 2 2 0 0 1 2 2v5a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-5z"
                        />
                        <path
                          fill="#36C5F0"
                          d="M9 6a2 2 0 0 1 2-2 2 2 0 0 1 2 2v2H9V6zm0 1a2 2 0 0 1 2 2 2 2 0 0 1-2 2H4a2 2 0 0 1-2-2 2 2 0 0 1 2-2h5z"
                        />
                        <path
                          fill="#2EB67D"
                          d="M18 9a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-2V9h2zm-1 0a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2 2 2 0 0 1 2 2v5z"
                        />
                        <path
                          fill="#ECB22E"
                          d="M15 18a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-2h2v2zm0-1a2 2 0 0 1-2-2 2 2 0 0 1 2-2h5a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-5z"
                        />
                      </svg>
                      <!-- GitHub Logo SVG -->
                      <svg
                        v-else-if="acc.provider === 'github'"
                        class="w-5 h-5 fill-slate-900 dark:fill-white"
                        viewBox="0 0 24 24"
                      >
                        <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z" />
                      </svg>
                      <!-- Notion Logo SVG -->
                      <svg
                        v-else-if="acc.provider === 'notion'"
                        class="w-5 h-5 fill-slate-900 dark:fill-white"
                        viewBox="0 0 24 24"
                      >
                        <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.768c-.42-.326-.98-.7-2.053-.607L3.107 2.28c-.466.046-.56.28-.373.466zm.84 3.732v13.578c0 .513.28.7.793.746l14.475.84c.513 0 .746-.233.746-.746V8.125c0-.513-.233-.746-.746-.746l-14.475-.84c-.56 0-.793.28-.793.793zm13.122 1.493c.093.42 0 .84-.42.887l-.746.14v9.61c-.513.28-.98.42-1.447.42-.746 0-1.073-.233-1.726-1.026l-4.993-7.886v7.466l1.213.28c.093.42 0 .84-.42.887l-3.36.233c-.093-.42 0-.84.42-.887l.84-.187V10.224l-1.12-.093c-.093-.42 0-.84.42-.887l3.453-.233 5.367 8.213V10.27l-1.027-.093c-.093-.42 0-.84.42-.887z" />
                      </svg>
                      <!-- Default Fallback -->
                      <div
                        v-else
                        class="w-5 h-5 rounded bg-blue-100 text-blue-700 flex items-center justify-center font-bold"
                      >
                        {{ acc.provider.charAt(0).toUpperCase() }}
                      </div>
                    </div>

                    <!-- Options / Disconnect button -->
                    <button
                      class="text-slate-400 hover:text-slate-700 dark:hover:text-stone-200 p-1 rounded-md"
                      title="Disconnect account"
                      @click="handleDisconnectAccount(acc.provider)"
                    >
                      <MoreHorizontal :size="14" />
                    </button>
                  </div>

                  <div class="mt-3">
                    <div class="text-xs font-semibold text-slate-800 dark:text-stone-200 capitalize">
                      {{ acc.provider }}
                    </div>
                    <div class="text-[11px] text-slate-400 truncate mt-0.5">
                      {{ acc.account_name }}
                    </div>
                  </div>
                </div>

                <div class="flex items-center gap-1.5 mt-3 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Connected</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN (Span 4) -->
        <div class="lg:col-span-4 space-y-6">
          <!-- 7. Profile Completion Card -->
          <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-slate-900 dark:text-white">Profile completion</span>
              <span class="text-sm font-semibold text-slate-700 dark:text-stone-300">{{ profile.completion_percentage }}%</span>
            </div>

            <!-- Progress bar -->
            <div class="w-full bg-slate-100 dark:bg-stone-800 h-2 rounded-full overflow-hidden mt-3">
              <div
                class="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
                :style="{ width: `${profile.completion_percentage}%` }"
              />
            </div>

            <p class="text-xs text-slate-500 dark:text-stone-400 mt-3 leading-relaxed">
              Complete your profile to get the most out of NagareOS.
            </p>

            <!-- Checklist -->
            <div class="mt-4 space-y-2.5">
              <div
                v-for="item in profile.completion_items"
                :key="item.id"
                class="flex items-center gap-2.5 text-xs text-slate-700 dark:text-stone-300 cursor-pointer select-none group"
                @click="handleToggleChecklist(item.id)"
              >
                <CheckCircle2
                  v-if="item.completed"
                  :size="16"
                  class="text-emerald-500 shrink-0"
                />
                <Circle
                  v-else
                  :size="16"
                  class="text-slate-300 dark:text-stone-600 group-hover:text-slate-400 shrink-0"
                />
                <span :class="item.completed ? 'text-slate-800 dark:text-stone-200' : 'text-slate-500 dark:text-stone-400'">
                  {{ item.label }}
                </span>
              </div>
            </div>
          </div>

          <!-- 8. Recent Activity Card -->
          <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-stone-800">
              <div class="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
                <History
                  :size="16"
                  class="text-slate-600 dark:text-stone-300"
                />
                <span>Recent activity</span>
              </div>
              <button
                class="text-xs font-medium text-blue-600 hover:underline"
                @click="showToast('Showing latest activities')"
              >
                View all
              </button>
            </div>

            <div class="mt-3 divide-y divide-slate-100 dark:divide-stone-800/60">
              <div
                v-for="act in profile.recent_activity"
                :key="act.id"
                class="flex items-start gap-3 py-3"
              >
                <div class="w-7 h-7 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
                  <component
                    :is="getActivityIcon(act.type)"
                    :size="14"
                  />
                </div>
                <div class="space-y-0.5">
                  <div class="text-xs font-medium text-slate-800 dark:text-stone-200">
                    {{ act.title }}
                  </div>
                  <div class="text-[11px] text-slate-400">
                    {{ act.time_ago }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 9. Account Card -->
          <div class="bg-white dark:bg-stone-900 rounded-2xl p-6 border border-slate-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-stone-800 text-slate-900 dark:text-white font-semibold text-sm">
              <Database
                :size="16"
                class="text-blue-600"
              />
              <span>Account</span>
            </div>

            <div class="divide-y divide-slate-100 dark:divide-stone-800/80 text-xs">
              <div class="flex items-center justify-between py-3">
                <span class="text-slate-500 font-medium">Plan</span>
                <div class="flex items-center gap-1 font-semibold text-slate-800 dark:text-stone-200 cursor-pointer hover:text-blue-600">
                  <span>{{ profile.plan }}</span>
                  <ChevronRight :size="13" />
                </div>
              </div>

              <div class="flex items-center justify-between py-3">
                <span class="text-slate-500 font-medium">Member since</span>
                <span class="text-slate-700 dark:text-stone-300 font-medium">{{ profile.member_since }}</span>
              </div>

              <div class="flex items-center justify-between py-3">
                <span class="text-slate-500 font-medium">Account ID</span>
                <button
                  class="flex items-center gap-1.5 px-2 py-1 bg-slate-50 dark:bg-stone-800/80 border border-slate-200/60 dark:border-stone-700 rounded font-mono text-[11px] text-slate-600 dark:text-stone-300 hover:bg-slate-100 dark:hover:bg-stone-700 transition-colors"
                  title="Click to copy"
                  @click="copyAccountId"
                >
                  <span>{{ profile.account_id }}</span>
                  <Check
                    v-if="copied"
                    :size="12"
                    class="text-emerald-600"
                  />
                  <Copy
                    v-else
                    :size="12"
                    class="text-slate-400"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 1: Edit Personal Information -->
    <Transition name="fade">
      <div
        v-if="showEditPersonal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
        @click.self="showEditPersonal = false"
      >
        <div class="bg-white dark:bg-stone-900 rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 dark:border-stone-800 space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-stone-800">
            <h3 class="font-bold text-base text-slate-900 dark:text-white">
              Edit personal information
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600"
              @click="showEditPersonal = false"
            >
              <X :size="18" />
            </button>
          </div>

          <form
            class="space-y-3 text-xs"
            @submit.prevent="savePersonalInfo"
          >
            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Full name</label>
              <input
                v-model="personalForm.full_name"
                type="text"
                required
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Email</label>
              <input
                v-model="personalForm.email"
                type="email"
                required
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Phone</label>
              <input
                v-model="personalForm.phone"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Location</label>
              <input
                v-model="personalForm.location"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Company</label>
              <input
                v-model="personalForm.company"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Bio</label>
              <textarea
                v-model="personalForm.bio"
                rows="2"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Avatar Image URL</label>
              <input
                v-model="personalForm.avatar_url"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-slate-200 dark:border-stone-700 hover:bg-slate-50 dark:hover:bg-stone-800"
                @click="showEditPersonal = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium flex items-center gap-1.5"
              >
                <span
                  v-if="saving"
                  class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
                />
                Save changes
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- MODAL 2: Edit Work Preferences -->
    <Transition name="fade">
      <div
        v-if="showEditWork"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
        @click.self="showEditWork = false"
      >
        <div class="bg-white dark:bg-stone-900 rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 dark:border-stone-800 space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-stone-800">
            <h3 class="font-bold text-base text-slate-900 dark:text-white">
              Edit work preferences
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600"
              @click="showEditWork = false"
            >
              <X :size="18" />
            </button>
          </div>

          <form
            class="space-y-3 text-xs"
            @submit.prevent="saveWorkPreferences"
          >
            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Role</label>
              <input
                v-model="workForm.role"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Default workspace</label>
              <input
                v-model="workForm.default_workspace"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Preferred language</label>
              <input
                v-model="workForm.preferred_language"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Timezone</label>
              <input
                v-model="workForm.timezone"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Working hours</label>
              <input
                v-model="workForm.working_hours"
                type="text"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-slate-200 dark:border-stone-700 hover:bg-slate-50 dark:hover:bg-stone-800"
                @click="showEditWork = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium flex items-center gap-1.5"
              >
                <span
                  v-if="saving"
                  class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
                />
                Save preferences
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- MODAL 3: Add Connected Account -->
    <Transition name="fade">
      <div
        v-if="showAddAccount"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
        @click.self="showAddAccount = false"
      >
        <div class="bg-white dark:bg-stone-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-stone-800 space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-stone-800">
            <h3 class="font-bold text-base text-slate-900 dark:text-white">
              Connect an account
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600"
              @click="showAddAccount = false"
            >
              <X :size="18" />
            </button>
          </div>

          <form
            class="space-y-3 text-xs"
            @submit.prevent="handleAddAccount"
          >
            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Service</label>
              <select
                v-model="newAccount.provider"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="figma">
                  Figma
                </option>
                <option value="discord">
                  Discord
                </option>
                <option value="linear">
                  Linear
                </option>
                <option value="zoom">
                  Zoom
                </option>
                <option value="google">
                  Google
                </option>
                <option value="slack">
                  Slack
                </option>
                <option value="github">
                  GitHub
                </option>
                <option value="notion">
                  Notion
                </option>
              </select>
            </div>

            <div>
              <label class="block font-medium text-slate-700 dark:text-stone-300 mb-1">Account username or email</label>
              <input
                v-model="newAccount.account_name"
                type="text"
                placeholder="e.g. alex@nagareos.com"
                required
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-stone-700 bg-white dark:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-slate-200 dark:border-stone-700 hover:bg-slate-50 dark:hover:bg-stone-800"
                @click="showAddAccount = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium flex items-center gap-1.5"
              >
                <span
                  v-if="saving"
                  class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
                />
                Connect
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- MODAL 4: Manage Security -->
    <Transition name="fade">
      <div
        v-if="showSecurityModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
        @click.self="showSecurityModal = false"
      >
        <div class="bg-white dark:bg-stone-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-stone-800 space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-stone-800">
            <h3 class="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck class="text-blue-600" />
              Security settings
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600"
              @click="showSecurityModal = false"
            >
              <X :size="18" />
            </button>
          </div>

          <div class="space-y-4 text-xs">
            <div class="p-3.5 bg-slate-50 dark:bg-stone-800/60 rounded-xl space-y-1">
              <div class="font-semibold text-slate-800 dark:text-stone-200">
                Two-Factor Authentication
              </div>
              <div class="text-slate-500">
                Your account is currently protected with authenticator app 2FA.
              </div>
              <div class="pt-2">
                <span class="px-2 py-0.5 text-[11px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 rounded">
                  Status: Enabled
                </span>
              </div>
            </div>

            <div class="p-3.5 bg-slate-50 dark:bg-stone-800/60 rounded-xl space-y-2">
              <div class="font-semibold text-slate-800 dark:text-stone-200">
                Active Sessions (3)
              </div>
              <div class="space-y-1.5 text-[11px] text-slate-600 dark:text-stone-400">
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <Laptop :size="13" /> macOS Chrome (Current)
                  </span>
                  <span class="text-emerald-600 font-medium">Active now</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <Smartphone :size="13" /> iPhone Safari
                  </span>
                  <span>1 day ago</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <Laptop :size="13" /> Windows Edge
                  </span>
                  <span>3 days ago</span>
                </div>
              </div>
            </div>

            <div class="flex justify-end pt-2">
              <button
                class="px-4 py-2 rounded-xl bg-blue-600 text-white font-medium"
                @click="showSecurityModal = false"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast Notification -->
    <Transition name="fade">
      <div
        v-if="toastMessage"
        class="fixed bottom-5 right-5 z-50 px-4 py-2.5 bg-slate-900 text-white text-xs font-medium rounded-xl shadow-lg flex items-center gap-2 border border-slate-700"
      >
        <CheckCircle2
          :size="15"
          class="text-emerald-400"
        />
        <span>{{ toastMessage }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
