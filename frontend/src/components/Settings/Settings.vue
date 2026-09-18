<template>
    <el-dialog v-model="visible" :title="t('settings.title')" width="65vw" class="settings-dialog" :close-on-click-modal="true"
        :close-on-press-escape="true" :show-close="true" @close="handleClose" append-to-body :z-index="9999">
        <div class="settings-dialog-body">
            <div class="settings-sidebar">
                <div class="sidebar-header">
                    <h3>{{ t('settings.title') }}</h3>
                </div>
                <ul class="sidebar-menu">
                    <li :class="{ active: activeMenu === 'style' }" @click="activeMenu = 'style'">
                        <el-icon>
                            <Document />
                        </el-icon>
                        <span>{{ t('settings.style') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'language' }" @click="activeMenu = 'language'">
                        <el-icon>
                            <ChatLineSquare />
                        </el-icon>
                        <span>{{ t('settings.language.title') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'password' }" @click="activeMenu = 'password'">
                        <el-icon>
                            <Lock />
                        </el-icon>
                        <span>{{ t('settings.password') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'screenshot' }" @click="activeMenu = 'screenshot'">
                        <el-icon>
                            <Picture />
                        </el-icon>
                        <span>{{ t('settings.screenshot') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'other' }" @click="activeMenu = 'other'">
                        <el-icon>
                            <Setting />
                        </el-icon>
                        <span>{{ t('settings.other') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'connectivity' }" @click="activeMenu = 'connectivity'">
                        <el-icon>
                            <Link />
                        </el-icon>
                        <span>{{ t('settings.connectivity') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'providerUsage' }" @click="activeMenu = 'providerUsage'">
                        <el-icon><DataAnalysis /></el-icon>
                        <span>{{ t('settings.providerUsage') }}</span>
                    </li>
                    <li :class="{ active: activeMenu === 'about' }" @click="activeMenu = 'about'">
                        <el-icon>
                            <InfoFilled />
                        </el-icon>
                        <span>{{ t('settings.about') }}</span>
                    </li>
                </ul>
            </div>
            <div class="settings-content">
                <div class="content-header">
                    <h2>{{ getMenuTitle() }}</h2>
                </div>
                <div class="content-body">
                    <SettingsStyle v-if="activeMenu === 'style'" />
                    <SettingsLanguage v-if="activeMenu === 'language'" />
                    <SettingsPassword v-if="activeMenu === 'password'" />
                    <SettingsScreenshot v-if="activeMenu === 'screenshot'" />
                    <SettingsOther v-if="activeMenu === 'other'" />
                    <SettingsAbout v-if="activeMenu === 'about'" />
                    <SettingsConnectivity v-if="activeMenu === 'connectivity'" />
                    <SettingsProviderUsage v-if="activeMenu === 'providerUsage'" />
                </div>
            </div>
        </div>
    </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue'
import { Document, Lock, Picture, Setting, InfoFilled, Link, ChatLineSquare, DataAnalysis } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import SettingsStyle from './SettingsStyle.vue'
import SettingsLanguage from './SettingsLanguage.vue'
import SettingsPassword from './SettingsPassword.vue'
import SettingsScreenshot from './SettingsScreenshot.vue'
import SettingsOther from './SettingsOther.vue'
import SettingsAbout from './SettingsAbout.vue'
import SettingsConnectivity from './SettingsConnectivity.vue'
import SettingsProviderUsage from './SettingsProviderUsage.vue'

const { t } = useI18n()

const props = defineProps({
    visible: {
        type: Boolean,
        default: false
    }
})
const emit = defineEmits(['update:visible'])

const visible = ref(props.visible)
watch(() => props.visible, v => visible.value = v)
watch(visible, v => emit('update:visible', v))

function handleClose() {
    visible.value = false
}

const activeMenu = ref('style')

const menuTitleKeys = {
    style: 'settings.style',
    language: 'settings.language.title',
    password: 'settings.password',
    screenshot: 'settings.screenshot',
    other: 'settings.other',
    connectivity: 'settings.connectivity',
    providerUsage: 'settings.providerUsage',
    about: 'settings.about'
}

function getMenuTitle() {
    const key = menuTitleKeys[activeMenu.value]
    return key ? t(key) : t('settings.title')
}
</script>

<style scoped>
.settings-dialog :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px 12px 0 0;
    padding: 20px 24px;
}

.settings-dialog :deep(.el-dialog__title) {
    color: white;
    font-size: 18px;
    font-weight: 600;
}

.settings-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: white;
    font-size: 20px;
}

.settings-dialog :deep(.el-dialog__body) {
    padding: 0;
}

.settings-dialog-body {
    display: flex;
    min-height: 500px;
    background: #f8fafc;
    border-radius: 0 0 12px 12px;
    overflow: hidden;
}

.settings-sidebar {
    width: 200px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 24px 20px 16px;
    border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sidebar-menu {
    padding: 16px 0;
    margin: 0;
    list-style: none;
}

.sidebar-menu li {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    margin: 4px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #64748b;
    font-size: 14px;
    font-weight: 500;
}

.sidebar-menu li:hover {
    background: #f1f5f9;
    color: #475569;
}

.sidebar-menu li.active {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.sidebar-menu li .el-icon {
    margin-right: 12px;
    font-size: 16px;
}

.settings-content {
    flex: 1;
    background: white;
    display: flex;
    flex-direction: column;
}

.content-header {
    padding: 24px 32px 16px;
    border-bottom: 1px solid #e2e8f0;
    background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

.content-header h2 {
    margin: 0 0 8px 0;
    font-size: 20px;
    font-weight: 600;
    color: #1e293b;
}

.content-subtitle {
    margin: 0;
    color: #64748b;
    font-size: 14px;
    line-height: 1.5;
}

.content-body {
    flex: 1;
    padding: 24px 32px;
    overflow-y: auto;
}

@media (max-width: 768px) {
    :global(.settings-dialog) {
        width: 94vw !important;
        margin-top: 3vh !important;
    }

    .settings-dialog-body {
        flex-direction: column;
        min-height: 0;
        max-height: 86vh;
    }

    .settings-sidebar {
        width: 100%;
        border-right: 0;
        border-bottom: 1px solid #e2e8f0;
    }

    .sidebar-header {
        display: none;
    }

    .sidebar-menu {
        display: flex;
        gap: 6px;
        overflow-x: auto;
        padding: 8px;
    }

    .sidebar-menu li {
        flex: 0 0 auto;
        margin: 0;
        padding: 9px 12px;
    }

    .settings-content {
        min-width: 0;
        overflow: hidden;
    }

    .content-header {
        padding: 16px;
    }

    .content-body {
        padding: 16px;
        max-height: 64vh;
    }
}
</style>
