<script setup>
import { ElUpload, ElIcon, ElMessage, ElRadioGroup, ElRadioButton, ElInput, ElInputNumber, ElCollapse, ElCollapseItem, ElTooltip, ElButton } from 'element-plus'
import { UploadFilled, VideoCamera, Promotion, RefreshRight, Loading, Setting, Link } from '@element-plus/icons-vue'
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import RemarksInput from '../common/RemarksInput.vue'

const { t } = useI18n()

const props = defineProps({
  ffmpegLoading: {
    type: Boolean,
    default: false
  },
  isProcessing: {
    type: Boolean,
    default: false
  },
  acceptHint: {
    type: String,
    default: ''
  },
  file: Object,
  fileName: String,
  fileSize: Number,
  fileMd5: String,
  style: String,
  showStyleSelector: Boolean,
  disabled: Boolean,
  md5Calculating: {
    type: Boolean,
    default: false
  },
  remarks: {
    type: String,
    default: ''
  },
  timeout: {
    type: Number,
    default: 120
  },
  maxTokens: {
    type: Number,
    default: 8192
  },
  linkUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['file-selected', 'link-submitted', 'update:style', 'update:remarks', 'update:timeout', 'update:maxTokens', 'start-process', 'reset'])

const hasSource = computed(() => !!props.file || !!props.linkUrl)
const linkInput = ref('')

const handleLinkSubmit = () => {
  const url = linkInput.value.trim()
  if (!/^https?:\/\//i.test(url)) {
    ElMessage.error(t('upload.invalidLink'))
    return
  }
  emit('link-submitted', url)
}

const allowedTypes = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
  'video/webm',
  'audio/mpeg'
]

// 获取本地设置的最大上传文件大小（单位MB），默认200
function getLocalMaxUploadSize() {
  try {
    const v = localStorage.getItem('maxUploadSize')
    if (v) {
      const n = parseInt(v)
      if (!isNaN(n) && n >= 10) return n
    }
  } catch { }
  return 200
}

const handleFileChange = (file) => {
  const isAllowedType = allowedTypes.includes(file.raw.type) ||
    file.raw.name.toLowerCase().endsWith('.mp3');
  if (!isAllowedType) {
    ElMessage.error(t('upload.unsupportedType'))
    return false
  }
  const maxSize = getLocalMaxUploadSize() * 1024 * 1024
  if (file.raw.size > maxSize) {
    ElMessage.error(t('upload.tooLarge', { size: getLocalMaxUploadSize() }))
    return false
  }
  emit('file-selected', file.raw)
}

// 支持风格类型及图标
const styleList = [
  { label: 'note', name: 'styles.note', icon: new URL('../../assets/笔记.svg', import.meta.url).href },
  { label: 'xiaohongshu', name: 'styles.xiaohongshu', icon: new URL('../../assets/小红书.svg', import.meta.url).href },
  { label: 'wechat', name: 'styles.wechat', icon: new URL('../../assets/微信公众号.svg', import.meta.url).href },
  { label: 'summary', name: 'styles.summary', icon: new URL('../../assets/汇总.svg', import.meta.url).href },
  { label: 'mind', name: 'styles.mind', icon: new URL('../../assets/思维导图.svg', import.meta.url).href },
  { label: 'cc', name: 'styles.cc', icon: new URL('../../assets/字幕.svg', import.meta.url).href },
]

const localStyle = ref(props.style || '')
watch(() => props.style, v => { localStyle.value = v })
const handleStyleChange = (val) => {
  emit('update:style', val)
}
const handleStart = () => {
  emit('start-process')
}
const handleReset = () => {
  emit('reset')
}

const localRemarks = ref(props.remarks || '')
const localTimeout = ref(props.timeout)
const localMaxTokens = ref(props.maxTokens)

watch(() => props.remarks, v => { localRemarks.value = v })
watch(() => props.timeout, v => { localTimeout.value = v })
watch(() => props.maxTokens, v => { localMaxTokens.value = v })

const handleRemarksChange = (val) => {
  emit('update:remarks', val)
}

const handleTimeoutChange = (val) => {
  emit('update:timeout', val)
}

const handleMaxTokensChange = (val) => {
  emit('update:maxTokens', val)
}
</script>

<template>
  <div class="upload-section-outer">
    <div class="upload-section" :class="{ 'loading-state': ffmpegLoading }">
      <div class="welcome">
        <div class="welcome-title">{{ t('upload.greeting', { name: '' }) }}<span class="ai-highlight">{{ t('upload.aiName') }}</span></div>
        <div class="welcome-desc">{{ t('upload.description') }}</div>
      </div>
      <!-- 仅在未选择来源时显示风格支持列表和apacceptHint -->
      <div v-if="!hasSource">
        <div class="style-support-list">
          <div class="style-support-item" v-for="item in styleList" :key="item.label">
            <img :src="item.icon" :alt="t(item.name)" class="style-support-icon" />
            <span class="style-support-name">{{ t(item.name) }}</span>
          </div>
        </div>
        <h3 class="section-title">
          <el-icon>
            <VideoCamera />
          </el-icon>
          {{ acceptHint || t('upload.acceptHint') }}
        </h3>
      </div>
      <!-- 上传区域：仅在未选择来源时显示 -->
      <el-upload v-if="!hasSource" class="uploader" drag action="" :auto-upload="false" :on-change="handleFileChange"
        :disabled="ffmpegLoading || isProcessing" :accept="allowedTypes.join(',') + ',.mp3'">
        <div class="upload-content">
          <div class="upload-icon-wrapper">
            <el-icon class="upload-icon">
              <UploadFilled />
            </el-icon>
          </div>
          <h3 class="upload-title">
            {{ ffmpegLoading ? t('upload.ffmpegLoading') : t('upload.start') }}
          </h3>
          <p class="upload-desc" v-if="!ffmpegLoading">
            {{ t('upload.dropHint') }}<br>
            <span class="upload-formats">{{ t('upload.formats', { size: getLocalMaxUploadSize() }) }}</span>
            <el-tooltip :content="t('upload.sizeTip')" placement="top" effect="dark">
              <span class="size-tip-hint">?</span>
            </el-tooltip>
          </p>
        </div>
      </el-upload>
      <!-- 视频链接输入：仅在未选择来源时显示 -->
      <div v-if="!hasSource" class="link-input-section">
        <div class="link-input-divider"><span>{{ t('upload.orPasteLink') }}</span></div>
        <div class="link-input-row">
          <el-input v-model="linkInput" :disabled="isProcessing" clearable
            :placeholder="t('upload.linkPlaceholder')" @keyup.enter="handleLinkSubmit">
            <template #prefix>
              <el-icon>
                <Link />
              </el-icon>
            </template>
          </el-input>
          <el-button type="primary" :disabled="isProcessing || !linkInput" @click="handleLinkSubmit">{{ t('upload.parseLink') }}</el-button>
        </div>
        <p class="link-input-tip">{{ t('upload.linkTip') }}</p>
      </div>
      <!-- 文件信息和风格选择：上传后显示 -->
      <div v-else class="file-info-section">
        <div class="file-info-card">
          <div v-if="props.linkUrl" class="file-info-row">
            <span class="file-info-label">{{ t('upload.videoLink') }}</span>
            <span class="file-info-value">{{ props.linkUrl }}</span>
          </div>
          <template v-else>
            <div class="file-info-row">
              <span class="file-info-label">{{ t('upload.fileName') }}</span>
              <span class="file-info-value">{{ props.fileName }}</span>
            </div>
            <div class="file-info-row">
              <span class="file-info-label">{{ t('upload.fileSize') }}</span>
              <span class="file-info-value">{{ (props.fileSize / 1024 / 1024).toFixed(2) }} MB</span>
            </div>
            <div class="file-info-row">
              <span class="file-info-label">{{ t('upload.fileMd5') }}</span>
              <span class="file-info-value file-info-md5">
                <template v-if="props.md5Calculating">
                  <el-icon class="md5-loading-icon">
                    <Loading />
                  </el-icon>
                  {{ t('upload.calculatingMd5') }}
                  <span class="md5-loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </span>
                </template>
                <template v-else>
                  {{ props.fileMd5 }}
                </template>
              </span>
            </div>
          </template>
        </div>
        <div class="file-info-main">
          <div class="style-selector-wrapper style-selector-flex">
            <el-radio-group v-model="localStyle" :disabled="isProcessing" @change="handleStyleChange" size="large"
              class="style-radio-group-flex">
              <el-radio-button v-for="item in styleList" :key="item.label" :value="item.label"
                class="style-radio-btn-flex" :disabled="item.label === 'cc'">
                <img :src="item.icon" :alt="t(item.name)" class="style-radio-icon" />
                {{ t(item.name) }}
              </el-radio-button>
            </el-radio-group>
          </div>
          <RemarksInput v-model="localRemarks" :timeout="localTimeout" :max-tokens="localMaxTokens"
            :disabled="isProcessing" @update:modelValue="handleRemarksChange" @update:timeout="handleTimeoutChange"
            @update:maxTokens="handleMaxTokensChange" :placeholder="t('upload.remarksPlaceholder')" />
        </div>
        <div class="file-action-row">
          <el-button class="start-process-btn" :disabled="!localStyle || isProcessing" @click="handleStart">
            <el-icon class="plane-icon">
              <Promotion />
            </el-icon>
            {{ t('upload.startProcess') }}
          </el-button>
        </div>
        <!-- 右下角悬浮的重新选择文件按钮 -->
        <a href="#" @click.prevent="handleReset" class="reset-link-float upload-section-reset-link">
          <el-icon class="reset-icon">
            <RefreshRight />
          </el-icon>
          {{ t('upload.reselect') }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.link-input-section {
  width: 100%;
  margin-top: 18px;
}

.link-input-divider {
  display: flex;
  align-items: center;
  color: #9ca3af;
  font-size: 0.92rem;
  margin-bottom: 12px;
}

.link-input-divider::before,
.link-input-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

.link-input-divider span {
  padding: 0 12px;
}

.link-input-row {
  display: flex;
  gap: 10px;
}

.link-input-tip {
  margin: 8px 0 0 0;
  font-size: 0.85rem;
  color: #9ca3af;
}

.upload-section-outer {
  min-height: 70vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  background: transparent;
  /* margin-top: 12vh; */
}

.upload-section {
  width: 60vw;
  max-width: 900px;
  min-width: 340px;
  background: #fff;
  border-radius: 20px;
  padding: 2.8rem 2.2rem 2.2rem 2.2rem;
  border: none;
  box-sizing: border-box;
  margin: 0;
  height: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #23272f;
  position: relative;
  box-shadow: 0 4px 32px 0 rgba(60, 80, 120, 0.08), 0 1.5px 6px 0 rgba(60, 80, 120, 0.03);
  border: 1.5px solid #f2f3f5;
  transition: box-shadow 0.2s;
}

.welcome {
  width: 100%;
  text-align: center;
  margin-bottom: 1.8rem;
}

.welcome-title {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 0.5rem;
  color: #23272f;
  line-height: 1.2;
}

.ai-highlight {
  color: #23272f;
  background: linear-gradient(90deg, #23272f 40%, #444950 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 900;
  letter-spacing: 0.5px;
}

.welcome-desc {
  font-size: 1.08rem;
  color: #6b7280;
  margin-bottom: 0.2rem;
  font-weight: 400;
  line-height: 1.6;
}

.style-support-list {
  width: 100%;
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-bottom: 1.6rem;
  margin-top: -0.5rem;
  flex-wrap: wrap;
}

.style-support-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f5f6fa;
  border-radius: 12px;
  padding: 0.7rem 1.1rem 0.5rem 1.1rem;
  box-shadow: 0 1px 4px 0 rgba(60, 80, 120, 0.04);
  border: 1px solid #f0f1f3;
  min-width: 80px;
  min-height: 80px;
  transition: box-shadow 0.18s, border-color 0.18s;
}

.style-support-item:hover {
  box-shadow: 0 4px 16px 0 rgba(60, 80, 120, 0.10);
  border-color: #e0e3e8;
}

.style-support-icon {
  width: 32px;
  height: 32px;
  margin-bottom: 0.5rem;
  user-drag: none;
  user-select: none;
}

.style-support-name {
  font-size: 0.98rem;
  color: #23272f;
  font-weight: 600;
  letter-spacing: 0.1px;
}

.section-title {
  font-size: 1.13rem;
  color: #23272f;
  margin-bottom: 0.8rem;
  font-weight: 700;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.2px;
}

.section-title .el-icon {
  font-size: 1.3rem;
  color: #23272f;
  background: #f3f4f6;
  border-radius: 50%;
  padding: 3px;
}

.uploader {
  width: 100%;
}

.upload-content {
  text-align: center;
  padding: 1.2rem 0.5rem 0.5rem 0.5rem;
}

.upload-icon-wrapper {
  width: 58px;
  height: 58px;
  background: linear-gradient(135deg, #f3f4f6 60%, #fff 100%);
  border-radius: 50%;
  margin: 0 auto 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2.5px solid #23272f;
  box-shadow: 0 2px 8px 0 rgba(60, 80, 120, 0.06);
}

.upload-icon {
  font-size: 2.1rem;
  color: #23272f;
}

.upload-title {
  font-size: 1.18rem;
  color: #23272f;
  margin: 0.5rem 0;
  font-weight: 600;
  letter-spacing: 0.1px;
}

.upload-desc {
  color: #6b7280;
  line-height: 1.6;
  font-size: 1.01rem;
  margin-top: 0.2rem;
}

.upload-formats {
  font-size: 0.93rem;
  color: #23272f;
  font-weight: 500;
  letter-spacing: 0.1px;
}

.size-tip-hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 6px;
  border-radius: 50%;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid #e5e7eb;
  cursor: help;
}

.loading-state {
  background-color: #f7f7fa !important;
  pointer-events: none;
  opacity: 0.8;
}

/* 文件信息和风格选择样式 */
.file-info-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.0rem;
  background: transparent;
  box-shadow: none;
  border: none;
}

.file-info-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 不设置gap，间距用margin控制 */
}

.file-info-card {
  width: 93%;
  background: #f7f8fa;
  border-radius: 14px;
  padding: 1.5rem 2rem 1.2rem 2rem;
  box-shadow: 0 2px 10px 0 rgba(60, 80, 120, 0.04);
  border: 1.5px solid #f2f3f5;
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.file-info-row {
  display: grid;
  grid-template-columns: 90px 1fr;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.03rem;
  color: #23272f;
  font-weight: 500;
  word-break: break-all;
  padding: 0.1rem 0;
}

.file-info-label {
  color: #6b7280;
  font-size: 1.01rem;
  font-weight: 500;
  min-width: 70px;
  width: 90px;
  text-align: right;
  justify-self: end;
  /* 右对齐标签 */
}

.file-info-value {
  color: #23272f;
  font-size: 1.03rem;
  font-weight: 600;
  word-break: break-all;
  text-align: left;
  justify-self: start;
}

.file-info-md5 {
  font-family: monospace;
  font-size: 0.98rem;
  color: #888;
  background: #f3f4f6;
  border-radius: 4px;
  padding: 2px 6px;
  word-break: break-all;
  display: flex;
  align-items: center;
  gap: 6px;
}

.md5-loading-icon {
  font-size: 1.1em;
  color: #888;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.md5-loading-dots span {
  animation: blink 1.4s infinite both;
  opacity: 0.5;
  font-size: 1.2em;
}

.md5-loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.md5-loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {

  0%,
  80%,
  100% {
    opacity: 0.5;
  }

  40% {
    opacity: 1;
  }
}

.style-selector-wrapper {
  margin-top: 0;
  margin-bottom: 0.6rem;
  /* 控制与下方remarks的间距 */
}

.start-process-btn {
  background: #23272f !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 1.08rem;
  font-weight: 700;
  padding: 0.7rem 2.2rem;
  transition: background 0.18s;
  box-shadow: 0 2px 8px 0 rgba(60, 80, 120, 0.06);
}

.start-process-btn:disabled {
  background: #e5e7eb !important;
  color: #b0b3b8 !important;
  cursor: not-allowed !important;
  box-shadow: none;
}

.start-process-btn:hover:not(:disabled) {
  background: #444950 !important;
}


.style-selector-flex {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: center;
  gap: 0.5rem 0.5rem;
  /* 允许内容自动换行 */
  overflow-x: auto;
}

.style-radio-group-flex {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 0.5rem 0.5rem;
  width: 100%;
}

.style-radio-btn-flex {
  margin-right: 0 !important;
  margin-bottom: 0 !important;
  flex: 0 1 auto;
  min-width: 110px;
  max-width: 180px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.file-action-row {
  width: 100%;
  max-width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.2rem;
  margin-top: 0.5rem;
  position: relative;
}

/* 右下角悬浮的重新选择文件按钮 */
.upload-section-reset-link {
  position: absolute;
  right: 0.5rem;
  bottom: 0.5rem;
  color: #b0b3b8;
  font-size: 0.95rem;
  /* 移除下划线 */
  text-decoration: none;
  cursor: pointer;
  background: #fff;
  border-radius: 8px;
  padding: 2px 12px 2px 8px;
  transition: color 0.18s, border-color 0.18s;
  z-index: 2;
  opacity: 0.85;
  display: flex;
  align-items: center;
  gap: 4px;
}

.upload-section-reset-link:hover {
  color: #23272f;
  border-color: #e0e3e8;
}

.reset-icon {
  font-size: 1.1em;
  margin-right: 2px;
  vertical-align: middle;
}

/* 隐藏方框内的reset-link-inside和reset-link */
.reset-link-inside,
.reset-link {
  display: none !important;
}

:deep(.el-upload) {
  background: #fff !important;
  border: 2px dashed #23272f !important;
  border-radius: 14px !important;
  color: #23272f !important;
  transition: border-color 0.2s;
}

:deep(.el-upload:hover) {
  border-color: #444950 !important;
}

:deep(.el-upload-dragger) {
  background: transparent !important;
  color: #23272f !important;
}

:deep(.el-upload-list) {
  color: #23272f !important;
}

:deep(.el-radio-button__inner) {
  border: 1px solid #dcdfe6;
  border-radius: 8px !important;
}

.style-radio-icon {
  width: 20px;
  height: 20px;
  margin-right: 6px;
  vertical-align: middle;
}

@media screen and (max-width: 900px) {
  .upload-section {
    width: 98vw;
    max-width: 98vw;
    padding: 1.2rem 0.5rem;
    border-radius: 14px;
  }

  .upload-section-outer {
    min-height: 60vh;
    margin-top: 3vh;
  }

  .welcome-title {
    font-size: 1.13rem;
  }

  .style-support-list {
    gap: 10px;
    margin-bottom: 1.1rem;
  }

  .style-support-item {
    min-width: 64px;
    min-height: 64px;
    padding: 0.5rem 0.7rem 0.4rem 0.7rem;
  }

  .style-support-icon {
    width: 24px;
    height: 24px;
  }
}

.remarks-wrapper {
  width: 93%;
  margin-bottom: 0.5rem;
  margin-top: 0;
  /* 可根据需要调整与上方的距离 */
}

.remarks-input {
  width: 100%;
}

:deep(.remarks-input .el-textarea__inner) {
  background: #f7f8fa !important;
  border: 1.5px solid #f2f3f5 !important;
  border-radius: 14px !important;
  padding: 16px 20px !important;
  font-size: 1.01rem !important;
  color: #23272f !important;
  transition: border-color 0.18s, box-shadow 0.18s !important;
  resize: none !important;
  font-family: inherit !important;
  line-height: 1.5 !important;
  box-shadow: 0 2px 10px 0 rgba(60, 80, 120, 0.04) !important;
}

:deep(.remarks-input .el-textarea__inner:focus) {
  border-color: #23272f !important;
  box-shadow: 0 0 0 2px rgba(35, 39, 47, 0.1), 0 2px 10px 0 rgba(60, 80, 120, 0.04) !important;
  outline: none !important;
}

:deep(.remarks-input .el-textarea__inner::placeholder) {
  color: #9ca3af !important;
  font-size: 0.98rem !important;
  line-height: 1.5 !important;
}

:deep(.remarks-input .el-textarea__inner:disabled) {
  background: #f3f4f6 !important;
  color: #9ca3af !important;
  cursor: not-allowed !important;
  border-color: #e5e7eb !important;
}
</style>
