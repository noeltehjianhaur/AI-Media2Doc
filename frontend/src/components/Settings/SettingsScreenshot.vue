<template>
    <div class="screenshot-settings">
        <h3 class="screenshot-title">{{ t('settingsPanel.screenshotTitle') }}</h3>
        <div class="screenshot-tip">
            {{ t('settingsPanel.screenshotTip') }}
        </div>
        <div class="screenshot-form-row">
            <label class="screenshot-label">{{ t('settingsPanel.screenshotLabel') }}</label>
            <el-switch v-model="smartScreenshotEnabled" size="default" :active-text="t('settingsPanel.on')" :inactive-text="t('settingsPanel.off')"
                class="screenshot-switch" />
        </div>
        <transition name="fade-slide">
            <div v-if="smartScreenshotEnabled" class="screenshot-warn-tip-row">
                <el-icon style="margin-right: 6px; color: #e67e22;">
                    <svg viewBox="0 0 1024 1024" width="18" height="18">
                        <path fill="currentColor"
                            d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.3 0-372-166.7-372-372S306.7 140 512 140s372 166.7 372 372-166.7 372-372 372zm-36-236h72v72h-72v-72zm0-360h72v288h-72V288z">
                        </path>
                    </svg>
                </el-icon>
                <span class="screenshot-warn-tip-text">{{ t('settingsPanel.screenshotWarning') }}</span>
            </div>
        </transition>
        <div class="save-btn-row screenshot-save-btn-row">
            <el-button type="primary" @click="saveScreenshotSettings">{{ t('common.save') }}</el-button>
            <span v-if="screenshotSaveSuccess" class="save-success-msg">{{ t('settingsPanel.savedBang') }}</span>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElSwitch, ElButton, ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

function getLocalSmartScreenshot() {
    try {
        const v = localStorage.getItem('smartScreenshotEnabled')
        return v === 'true'
    } catch {
        return false
    }
}
function setLocalSmartScreenshot(enabled) {
    localStorage.setItem('smartScreenshotEnabled', String(enabled))
}
const smartScreenshotEnabled = ref(getLocalSmartScreenshot())
const screenshotSaveSuccess = ref(false)

function saveScreenshotSettings() {
    setLocalSmartScreenshot(smartScreenshotEnabled.value)
    screenshotSaveSuccess.value = true
    ElMessage.success(t('settingsPanel.screenshotSaved'))
    setTimeout(() => {
        screenshotSaveSuccess.value = false
    }, 2000)
}
</script>

<style scoped>
.screenshot-settings {
    width: 100%;
    max-width: 600px;
    margin: 0;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 12px;
    padding: 24px 32px 24px 32px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    min-height: 220px;
    border: 1px solid #e2e8f0;
}

.screenshot-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 16px 0;
    color: #1e293b;
    letter-spacing: 0.2px;
    align-self: flex-start;
    display: flex;
    align-items: center;
    gap: 8px;
}

.screenshot-title::before {
    content: '';
    width: 4px;
    height: 18px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 2px;
}

.screenshot-tip {
    color: #64748b;
    font-size: 14px;
    margin-bottom: 24px;
    line-height: 1.7;
    text-align: left;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border-left: 4px solid #94a3b8;
    padding: 12px 16px;
    border-radius: 8px;
    width: 100%;
    align-self: flex-start;
    box-shadow: 0 2px 8px rgba(148, 163, 184, 0.1);
}

.screenshot-form-row {
    display: flex;
    align-items: center;
    width: 100%;
    margin-bottom: 20px;
    gap: 16px;
    justify-content: flex-start;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    padding: 16px 20px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
}

.screenshot-label {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
    min-width: 140px;
    text-align: left;
    margin-bottom: 0;
    letter-spacing: 0.1px;
}

.screenshot-switch {
    margin-left: 8px;
}

.screenshot-warn-tip-row {
    display: flex;
    align-items: center;
    margin-top: 4px;
    margin-bottom: 12px;
    font-size: 13px;
    color: #d97706;
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 12px 16px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
    width: 100%;
    align-self: flex-start;
    text-align: left;
}

.screenshot-warn-tip-text {
    color: #d97706;
    font-weight: 500;
    text-align: left;
}

.screenshot-save-btn-row {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
    align-self: flex-start;
}

.save-btn-row {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.save-success-msg {
    color: #059669;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}

.save-success-msg::before {
    content: '✓';
    font-weight: bold;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
    transition: all 0.25s cubic-bezier(.55, 0, .1, 1);
}

.fade-slide-enter-from,
.fade-slide-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
    opacity: 1;
    transform: translateY(0);
}
</style>
