<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import UploadSection from './UploadSection.vue'
import LoadingOverlay from './LoadingOverlay.vue'
import { loadFFmpeg, extractAudio, captureVideoFrame, frameToBase64, cleanupVideoCache } from '../../utils/ffmpeg'
import { submitAsrTask, pollAsrTaskDetails } from '../../apis/asrService'
import { generateMarkdownResult } from '../../apis/markdownService'
import { submitLinkTask } from '../../apis/linkService'
import { translateText, getTargetLanguage } from '../../apis/translationService'
import { calculateMD5 } from '../../utils/md5'
import { getAudioUploadUrl, uploadFile } from '../../apis'
import { saveTask, checkTaskExistsByMd5AndStyle, getAnyTaskByMd5, getTaskByID } from '../../utils/db'
import { eventBus } from '../../utils/eventBus'
import { createOutputRecord } from '../../apis/outputRecordService'

const stepDefs = [
  { titleKey: 'steps.initFfmpeg', icon: 'Promotion', status: 'wait' },
  { titleKey: 'steps.extractAudio', icon: 'Headset', status: 'wait' },
  { titleKey: 'steps.uploadFile', icon: 'Upload', status: 'wait' },
  { titleKey: 'steps.transcribe', icon: 'Document', status: 'wait' },
  { titleKey: 'steps.generate', icon: 'Document', status: 'wait' }
]

const { t } = useI18n()

const steps = ref(stepDefs.map(s => ({ ...s })))
const activeStep = ref(0)

const ffmpegLoading = ref(false)
const ffmpegLoaded = ref(false)
const isProcessing = ref(false)

const file = ref(null)
const fileName = ref('')
const linkUrl = ref('')
const showStyleSelector = ref(false)
const style = ref('')
const remarks = ref('')
const llmTimeout = ref(120)
const llmMaxTokens = ref(8192)

const showStartButton = ref(false)

const audioData = ref(null)
const audioUrl = ref('')
const audioFilename = ref('')
const audioExtracted = ref(false)
const textTranscribed = ref(false)
const transcriptionText = ref('')
const markdownContent = ref('')
const processingMode = ref('audio')
const keepSourceMedia = ref(false)
const publishOutput = ref(false)
const visualAnalysis = ref(null)
const providerUsage = ref({})
const capturedScreenshots = ref([])

const fileMd5 = ref('')
const fileSize = ref(0)
const md5Calculating = ref(false)

const smartScreenshot = ref(false)
const imageCount = ref(0)
const imageTotal = ref(0)

const resetAll = () => {
  cleanupVideoCache()
  steps.value = stepDefs.map(s => ({ ...s }))
  activeStep.value = 0
  isProcessing.value = false
  file.value = null
  fileName.value = ''
  linkUrl.value = ''
  showStyleSelector.value = false
  style.value = ''
  showStartButton.value = false
  audioData.value = null
  audioUrl.value = ''
  remarks.value = ''
  audioFilename.value = ''
  audioExtracted.value = false
  textTranscribed.value = false
  transcriptionText.value = ''
  markdownContent.value = ''
  processingMode.value = 'audio'
  visualAnalysis.value = null
  providerUsage.value = {}
  capturedScreenshots.value = []
}

const handleFileSelected = async (f) => {
  resetAll()
  file.value = f
  fileName.value = f.name
  fileSize.value = f.size
  md5Calculating.value = true
  // 计算MD5
  fileMd5.value = await calculateMD5(new Uint8Array(await f.arrayBuffer()))
  md5Calculating.value = false
  if (isMP3File(f)) processingMode.value = 'audio'
  showStyleSelector.value = true
}


const handleRemarksUpdate = (val) => {
  remarks.value = val
}

const handleLLMTimeoutChange = (val) => {
  llmTimeout.value = val
}

const handleLLMMaxTokensChange = (val) => {
  llmMaxTokens.value = val
}

const handleStyleSelected = (val) => {
  style.value = val
  showStartButton.value = true
}

const handleProcessingModeChange = (value) => {
  if (value === 'audio_video' && isMP3File(file.value)) {
    processingMode.value = 'audio'
    return
  }
  processingMode.value = value
}

const updateStepStatus = (idx, status) => {
  steps.value[idx].status = status
  activeStep.value = idx
}

const isMP3File = (f) => f && (f.type === 'audio/mpeg' || f.name.toLowerCase().endsWith('.mp3'))

const getVideoApiMaxSize = () => {
  const configured = Number.parseInt(localStorage.getItem('videoApiMaxSizeMB') || '200', 10)
  return Number.isFinite(configured) ? configured : 200
}

// 转写结果默认保留原始语言，仅在用户选择目标语言时翻译
const applyTargetLanguage = async (segments) => {
  const targetLanguage = getTargetLanguage()
  if (!targetLanguage || !segments) return segments

  if (!Array.isArray(segments)) {
    return await translateText(String(segments), targetLanguage, llmTimeout.value, llmMaxTokens.value)
  }

  const translated = []
  for (const seg of segments) {
    if (!seg?.text) {
      translated.push(seg)
      continue
    }
    translated.push({ ...seg, text: await translateText(seg.text, targetLanguage, llmTimeout.value, llmMaxTokens.value) })
  }
  return translated
}

const startProcessing = async () => {
  if (!file.value || !style.value) return
  if (processingMode.value === 'audio_video' && file.value.size > getVideoApiMaxSize() * 1024 * 1024) {
    ElMessage.error(t('upload.videoTooLarge', { size: getVideoApiMaxSize() }))
    return
  }
  isProcessing.value = true
  steps.value = stepDefs.map(s => ({ ...s }))
  try {
    let sourceData
    let sourceMd5
    let sourceFilename
    if (processingMode.value === 'audio') {
      updateStepStatus(0, 'processing')
      ffmpegLoading.value = true
      await loadFFmpeg()
      ffmpegLoaded.value = true
      updateStepStatus(0, 'success')
      ffmpegLoading.value = false

      updateStepStatus(1, 'processing')
      if (isMP3File(file.value)) {
        sourceData = new Uint8Array(await file.value.arrayBuffer())
        ElMessage.success(t('process.mp3Detected'))
      } else {
        sourceData = await extractAudio(new Uint8Array(await file.value.arrayBuffer()))
      }
      sourceMd5 = await calculateMD5(sourceData)
      sourceFilename = `temporary/${crypto.randomUUID()}/source.mp3`
    } else {
      updateStepStatus(0, 'success')
      updateStepStatus(1, 'success')
      sourceData = file.value
      sourceMd5 = fileMd5.value || await calculateMD5(new Uint8Array(await file.value.arrayBuffer()))
      const extension = file.value.name.includes('.') ? file.value.name.split('.').pop().toLowerCase() : 'mp4'
      sourceFilename = `temporary/${crypto.randomUUID()}/source.${extension}`
    }
    audioExtracted.value = true
    updateStepStatus(1, 'success')

    audioFilename.value = sourceFilename
    const exists = await checkTaskExistsByMd5AndStyle(sourceMd5, style.value, processingMode.value)
    if (exists) {
      const existingTask = await getAnyTaskByMd5(sourceMd5)
      isProcessing.value = false
      showStartButton.value = false
      if (existingTask && existingTask.contentStyle === style.value && (existingTask.processingMode || 'audio') === processingMode.value && existingTask.markdownContent) {
        ElMessage.info(t('process.alreadyProcessed'))
        eventBus.emit('view-task', existingTask)
      } else {
        ElMessage.warning(t('process.alreadyProcessedSameStyle'))
      }
      return
    }

    updateStepStatus(3, 'processing')
    const existingTask = await getAnyTaskByMd5(sourceMd5)
    if (existingTask && (existingTask.processingMode || 'audio') === processingMode.value && existingTask.transcriptionText) {
      transcriptionText.value = existingTask.transcriptionText
      visualAnalysis.value = existingTask.visualAnalysis || null
      providerUsage.value = existingTask.usage || {}
      textTranscribed.value = true
      updateStepStatus(3, 'success')
    } else {
      updateStepStatus(2, 'processing')
      const uploadUrl = await getAudioUploadUrl(audioFilename.value)
      const uploadBody = sourceData instanceof Blob ? sourceData : new Blob([sourceData], { type: 'audio/mpeg' })
      await uploadFile(uploadUrl, uploadBody)
      updateStepStatus(2, 'success')

      updateStepStatus(3, 'processing')
      const taskId = await submitAsrTask(audioFilename.value, processingMode.value, fileName.value, keepSourceMedia.value)
      const result = await pollAsrTaskDetails(taskId)
      transcriptionText.value = await applyTargetLanguage(result.result)
      visualAnalysis.value = result.visual_analysis || null
      providerUsage.value = result.usage || {}
      textTranscribed.value = true
      updateStepStatus(3, 'success')
      eventBus.emit('transcription-completed')
    }

    updateStepStatus(4, 'processing')
    const processedText = formatTranscript(transcriptionText.value)
    const generation = await generateMarkdownResult(processedText, style.value, remarks.value, llmTimeout.value, llmMaxTokens.value)
    const md = generation.content
    providerUsage.value = { transcription: providerUsage.value, generation: { model: generation.model, ...generation.usage } }
    const imageTimeRegex = /#image\[(\d+)\]/g
    let contentWithMarkers = md
    let imageTimeMarkers = md.match(imageTimeRegex) || []
    if (processingMode.value === 'audio_video' && imageTimeMarkers.length === 0) {
      const visualSegments = visualAnalysis.value?.segments || []
      const selectedSegments = visualSegments.some(segment => segment.important)
        ? visualSegments.filter(segment => segment.important)
        : visualSegments.filter(segment => segment.start_time >= 0)
      imageTimeMarkers = selectedSegments
        .slice(0, 8)
        .map(segment => `#image[${Math.floor(segment.start_time / 1000)}]`)
      if (imageTimeMarkers.length) contentWithMarkers += `\n\n${imageTimeMarkers.join('\n')}`
    }
    markdownContent.value = await processImageMarkers(contentWithMarkers, file.value, imageTimeMarkers)
    cleanupVideoCache()
    updateStepStatus(4, 'success')

    const outputRecord = await createOutputRecord({
      processingMode: processingMode.value,
      transcript: transcriptionText.value,
      generatedContent: markdownContent.value,
      visualAnalysis: visualAnalysis.value,
      screenshots: capturedScreenshots.value,
      publish: publishOutput.value,
      metadata: {
        source_type: 'upload',
        original_name: fileName.value,
        detected_language: visualAnalysis.value?.detected_language,
        target_language: getTargetLanguage(),
        content_style: style.value,
        model: providerUsage.value?.transcription?.model || providerUsage.value?.generation?.model,
        usage: providerUsage.value
      }
    })

    const task = {
      fileName: fileName.value,
      md5: sourceMd5,
      transcriptionText: transcriptionText.value,
      markdownContent: markdownContent.value,
      contentStyle: style.value,
      processingMode: processingMode.value,
      outputFormat: processingMode.value === 'audio_video' ? 'html' : 'markdown',
      outputPath: outputRecord.output_path,
      outputContent: outputRecord.files[outputRecord.output_path],
      outputFiles: outputRecord.files,
      visualAnalysis: visualAnalysis.value,
      usage: providerUsage.value,
      publication: outputRecord.publication,
      createdAt: new Date().toISOString()
    }
    const taskId = await saveTask(task)
    eventBus.emit('task-updated')
    ElMessage.success(t('process.completed'))
    const savedTask = await getTaskByID(taskId)
    if (savedTask) {
      eventBus.emit('view-task', savedTask)
    }
  } catch (e) {
    updateStepStatus(activeStep.value, 'error')
    ElMessage.error(e.message || t('process.failed'))
  } finally {
    isProcessing.value = false
    showStartButton.value = false
  }
}

// 将转写分段格式化为带时间标记的文本
function formatTranscript(segments) {
  if (Array.isArray(segments) && segments.length > 0 && typeof segments[0] === 'object' && 'text' in segments[0]) {
    return segments.map(seg => {
      const startMin = Math.floor(seg.start_time / 60000)
      const startSec = Math.floor((seg.start_time % 60000) / 1000)
      const endMin = Math.floor(seg.end_time / 60000)
      const endSec = Math.floor((seg.end_time % 60000) / 1000)
      const startTime = `${startMin.toString().padStart(2, '0')}:${startSec.toString().padStart(2, '0')}`
      const endTime = `${endMin.toString().padStart(2, '0')}:${endSec.toString().padStart(2, '0')}`
      const startTotalSec = Math.floor(seg.start_time / 1000)
      const endTotalSec = Math.floor(seg.end_time / 1000)

      const visualContext = [seg.on_screen_text, ...(seg.visual_actions || [])].filter(Boolean).join('; ')
      return `[${startTime} - ${endTime} 时间范围秒数:(${startTotalSec}s-${endTotalSec}s)] ${seg.text}${visualContext ? `\nVisual context: ${visualContext}` : ''}`
    }).join('\n')
  }
  return segments
}

const handleLinkSubmitted = async (url) => {
  resetAll()
  linkUrl.value = url
  fileName.value = url
  showStyleSelector.value = true
}

const startLinkProcessing = async () => {
  if (!linkUrl.value || !style.value) return
  isProcessing.value = true
  steps.value = stepDefs.map(s => ({ ...s }))
  try {
    // 链接模式不需要本地 FFmpeg 与音频提取
    updateStepStatus(0, 'success')
    updateStepStatus(1, 'success')

    updateStepStatus(2, 'processing')
    updateStepStatus(3, 'processing')
    const { task_id: taskId } = await submitLinkTask(linkUrl.value, processingMode.value, keepSourceMedia.value)
    updateStepStatus(2, 'success')
    const result = await pollAsrTaskDetails(taskId)
    transcriptionText.value = await applyTargetLanguage(result.result)
    visualAnalysis.value = result.visual_analysis || null
    providerUsage.value = result.usage || {}
    textTranscribed.value = true
    updateStepStatus(3, 'success')
    eventBus.emit('transcription-completed')

    updateStepStatus(4, 'processing')
    const generation = await generateMarkdownResult(
      formatTranscript(transcriptionText.value),
      style.value,
      remarks.value,
      llmTimeout.value,
      llmMaxTokens.value
    )
    const md = generation.content
    providerUsage.value = { transcription: providerUsage.value, generation: { model: generation.model, ...generation.usage } }
    // 链接模式没有本地视频文件，移除截图标记
    markdownContent.value = md.replace(/#image\[\d+\]/g, '')
    updateStepStatus(4, 'success')

    const outputRecord = await createOutputRecord({
      processingMode: processingMode.value,
      transcript: transcriptionText.value,
      generatedContent: markdownContent.value,
      visualAnalysis: visualAnalysis.value,
      publish: publishOutput.value,
      metadata: {
        source_type: 'link',
        source_url: linkUrl.value,
        detected_language: visualAnalysis.value?.detected_language,
        target_language: getTargetLanguage(),
        content_style: style.value,
        model: providerUsage.value?.transcription?.model || providerUsage.value?.generation?.model,
        usage: providerUsage.value
      }
    })

    const task = {
      fileName: linkUrl.value,
      md5: `link-${Date.now()}`,
      transcriptionText: transcriptionText.value,
      markdownContent: markdownContent.value,
      contentStyle: style.value,
      processingMode: processingMode.value,
      outputFormat: processingMode.value === 'audio_video' ? 'html' : 'markdown',
      outputPath: outputRecord.output_path,
      outputContent: outputRecord.files[outputRecord.output_path],
      outputFiles: outputRecord.files,
      visualAnalysis: visualAnalysis.value,
      usage: providerUsage.value,
      sourceUrl: linkUrl.value,
      publication: outputRecord.publication,
      createdAt: new Date().toISOString()
    }
    const savedId = await saveTask(task)
    eventBus.emit('task-updated')
    const savedTask = await getTaskByID(savedId)
    if (savedTask) {
      eventBus.emit('view-task', savedTask)
    }
  } catch (e) {
    updateStepStatus(activeStep.value, 'error')
    ElMessage.error(e.message || t('process.failed'))
  } finally {
    isProcessing.value = false
    showStartButton.value = false
  }
}

const handleStartProcess = () => {
  if (linkUrl.value) {
    startLinkProcessing()
  } else {
    startProcessing()
  }
}

// 智能截图开关读取
function isSmartScreenshotEnabled() {
  try {
    return localStorage.getItem('smartScreenshotEnabled') === 'true'
  } catch {
    return false
  }
}

// 抽离截图处理逻辑
async function processImageMarkers(md, file, imageTimeMarkers) {
  // 去除掉 md 开头的 ```markdown 和 结尾的 ```
  if (md.startsWith('```markdown')) {
    md = md.replace(/^```markdown\s*/, '').replace(/```$/, '').trim()
  } else if (md.startsWith('```')) {
    md = md.replace(/^```/, '').replace(/```$/, '').trim()
  }
  smartScreenshot.value = isSmartScreenshotEnabled()
  capturedScreenshots.value = []
  imageCount.value = 0
  imageTotal.value = imageTimeMarkers.length
  if (!smartScreenshot.value) {
    // 未开启，全部替换为空
    let result = md
    for (const marker of imageTimeMarkers) {
      result = result.replaceAll(marker, '')
    }
    imageCount.value = 0
    imageTotal.value = 0
    return result
  }
  // 已开启，执行截图逻辑
  if (imageTimeMarkers.length > 0 && !isMP3File(file)) {
    const videoData = new Uint8Array(await file.arrayBuffer())
    let result = md
    let imageIdx = 1 // 新增编号计数器
    for (const marker of imageTimeMarkers) {
      try {
        // 匹配 #image[20] 形式
        const timeMatch = marker.match(/#image\[(\d+)\]/)
        if (timeMatch) {
          const totalSeconds = parseInt(timeMatch[1])
          console.log(`正在截图: ${marker} (时间: ${totalSeconds}秒) 当前进度 ${imageIdx}/${imageTimeMarkers.length}`)
          // 捕获视频帧
          const frameData = await captureVideoFrame(videoData, totalSeconds)
          const base64Image = frameToBase64(frameData)
          capturedScreenshots.value.push({ timestamp: totalSeconds, data_url: base64Image })
          // 使用 HTML img 标签并加编号，设置最大宽度自适应
          const imageTag = `<div style="text-align:center;"><span style="font-size:0.98em;color:#888;">截图${imageIdx}</span><br><img src="${base64Image}" alt="截图${imageIdx}" style="max-width:100%;height:auto;border-radius:8px;box-shadow:0 2px 8px #0001;margin:8px 0;" /></div><p></p>`
          result = result.replace(marker, imageTag)
          imageCount.value = imageIdx // 实时更新进度
          imageIdx++
        }
      } catch (error) {
        console.warn(`跳过标记 ${marker}:`, error.message)
        // 如果是时间点超出错误，直接移除标记，不显示错误
        if (error.code === 'TIME_OUT_OF_RANGE') {
          result = result.replace(marker, '')
          console.log(`跳过超出时长的截图标记: ${marker} (${error.timeInSeconds}s > ${error.videoDuration}s)`)
        } else {
          // 其他错误仍然显示错误信息
          console.error(`处理标记 ${marker} 时出错:`, error)
          ElMessage.error(`处理标记 ${marker} 时出错: ${error.message}`)
        }
      }
    }
    imageCount.value = imageTotal.value // 处理完成
    return result
  } else if (imageTimeMarkers.length > 0 && isMP3File(file)) {
    imageCount.value = 0
    imageTotal.value = 0
    return md
  }
  imageCount.value = 0
  imageTotal.value = 0
  return md
}

// 步骤百分比辅助
const stepPercents = [10, 30, 50, 80, 100]
const percent = computed(() => stepPercents[activeStep.value] || 0)
const stepText = computed(() => {
  const key = steps.value[activeStep.value]?.titleKey
  return key ? t(key) : ''
})

</script>

<template>
  <div class="video-markdown-container">
    <div class="main-content">
      <!-- 步骤1：上传/风格选择/文件信息，始终显示，除非正在处理或有结果 -->
      <div v-if="!isProcessing && !markdownContent" class="component-wrapper">
        <UploadSection :ffmpeg-loading="ffmpegLoading" :is-processing="isProcessing" :file="file" :file-name="fileName"
          :file-size="fileSize" :file-md5="fileMd5" :md5-calculating="md5Calculating" :style="style"
          :link-url="linkUrl" @file-selected="handleFileSelected" @link-submitted="handleLinkSubmitted"
          @update:style="handleStyleSelected" @start-process="handleStartProcess"
          :processing-mode="processingMode" :keep-source-media="keepSourceMedia" :publish-output="publishOutput"
          @update:processing-mode="handleProcessingModeChange"
          @update:keep-source-media="value => keepSourceMedia = value"
          @update:publish-output="value => publishOutput = value"
          :remarks="remarks" @update:remarks="handleRemarksUpdate" @reset="resetAll"
          @update:timeout="handleLLMTimeoutChange" @update:max-tokens="handleLLMMaxTokensChange" />
      </div>
      <!-- 步骤3：处理进度（全屏loading） -->
      <LoadingOverlay v-if="isProcessing" :step-text="stepText" :percent="percent" :smart-screenshot="smartScreenshot"
        :image-count="imageCount" :image-total="imageTotal" />
    </div>
  </div>
</template>

<style scoped>
.video-markdown-container {
  width: 100%;
  flex: 1;
  margin-top: 0;
  display: flex;
  flex-direction: column;
  background-color: transparent;
  padding: 0;
  min-height: auto;
  height: auto;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  width: 100%;
  /* 只占父容器宽度 */
  max-width: 100%;
  /* 只占父容器宽度 */
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  height: 100vh;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.component-wrapper {
  width: auto;
  max-width: 900px;
  box-sizing: border-box;
  border-radius: 12px;
  overflow: visible;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 24px 0;
  /* 新增，防止极小屏幕时贴边 */
}

/* 文件信息卡片和风格选择区域样式与 UploadSection.vue 保持一致 */
.file-info-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2.2rem;
  background: transparent;
  box-shadow: none;
  border: none;
}

.file-info-card {
  width: 100%;
  max-width: 520px;
  background: #fff;
  /* 纯白色 */
  border-radius: 14px;
  padding: 1.5rem 2rem 1.2rem 2rem;
  box-shadow: 0 2px 10px 0 rgba(60, 80, 120, 0.04);
  border: 1px solid #23272f22;
  /* 淡黑色边框 */
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.file-info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.03rem;
  color: #23272f;
  font-weight: 500;
  word-break: break-all;
}

.file-info-label {
  color: #6b7280;
  font-size: 1.01rem;
  font-weight: 500;
  min-width: 70px;
}

.file-info-value {
  color: #23272f;
  font-size: 1.03rem;
  font-weight: 600;
}

.file-info-md5 {
  font-family: monospace;
  font-size: 0.98rem;
  color: #888;
  background: #f3f4f6;
  border-radius: 4px;
  padding: 2px 6px;
}

.style-selector-wrapper {
  width: 100%;
  max-width: 520px;
}

.file-action-row {
  width: 100%;
  max-width: 520px;
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-top: 0.5rem;
  justify-content: flex-start;
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

.reset-link {
  color: #888;
  font-size: 0.98rem;
  text-decoration: underline;
  cursor: pointer;
  margin-left: 0.5rem;
  transition: color 0.18s;
}

.reset-link:hover {
  color: #23272f;
}
</style>
