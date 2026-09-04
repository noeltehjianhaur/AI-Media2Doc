<template>
    <div class="language-settings">
        <div class="setting-block">
            <div class="setting-label">{{ t('settings.language.displayLanguage') }}</div>
            <p class="setting-tip">{{ t('settings.language.displayLanguageTip') }}</p>
            <el-radio-group v-model="displayLocale" @change="handleLocaleChange">
                <el-radio-button v-for="item in SUPPORTED_LOCALES" :key="item.value" :value="item.value">
                    {{ item.label }}
                </el-radio-button>
            </el-radio-group>
        </div>

        <div class="setting-block">
            <div class="setting-label">{{ t('settings.language.outputLanguage') }}</div>
            <p class="setting-tip">{{ t('settings.language.outputLanguageTip') }}</p>
            <el-select v-model="outputLanguage" class="output-select" :teleported="false"
                :placeholder="t('settings.language.original')" @change="handleOutputChange">
                <el-option v-for="item in TARGET_LANGUAGES" :key="item.value" :value="item.value"
                    :label="t(item.labelKey)" />
            </el-select>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElRadioGroup, ElRadioButton, ElSelect, ElOption, ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { SUPPORTED_LOCALES, setLocale, getStoredLocale } from '../../i18n'
import { TARGET_LANGUAGES, getTargetLanguage, setTargetLanguage } from '../../apis/translationService'

const { t } = useI18n()

const displayLocale = ref(getStoredLocale())
const outputLanguage = ref(getTargetLanguage())

function handleLocaleChange(value) {
    setLocale(value)
    ElMessage.success(t('common.saved'))
}

function handleOutputChange(value) {
    setTargetLanguage(value)
    ElMessage.success(t('common.saved'))
}
</script>

<style scoped>
.language-settings {
    display: flex;
    flex-direction: column;
    gap: 28px;
    padding: 8px 2px;
}

.setting-block {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.setting-label {
    font-size: 1.02rem;
    font-weight: 600;
    color: #23272f;
}

.setting-tip {
    margin: 0 0 6px 0;
    font-size: 0.88rem;
    color: #6b7280;
    line-height: 1.6;
}

.output-select {
    max-width: 320px;
}
</style>
