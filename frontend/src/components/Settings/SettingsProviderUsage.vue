<script setup>
import { onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { modelCapabilities, providerUsage, providerUsageError, providerUsageLoading, refreshModelCapabilities, refreshProviderUsage } from '../../apis/providerUsageService'

const labels = { gemini: 'Gemini', openrouter: 'OpenRouter', cloudflare: 'Cloudflare R2' }

const refresh = async () => {
  try {
    await refreshProviderUsage(true)
  } catch {
    // The shared store exposes a redacted error for the panel.
  }
}

onMounted(() => {
  if (!providerUsage.value) refreshProviderUsage().catch(() => {})
  refreshModelCapabilities().catch(() => {})
})
</script>

<template>
  <section class="provider-usage">
    <div class="provider-toolbar">
      <p>Provider-reported account usage and quota</p>
      <el-button :icon="Refresh" :loading="providerUsageLoading" :disabled="providerUsageLoading" @click="refresh">
        Refresh
      </el-button>
    </div>
    <p v-if="providerUsageError" class="usage-error">{{ providerUsageError }}</p>
    <div class="provider-list">
      <article v-for="(item, name) in providerUsage" :key="name" class="provider-item">
        <header>
          <strong>{{ labels[name] }}</strong>
          <el-tag :type="item.status === 'available' ? 'success' : item.status === 'error' ? 'danger' : 'info'">
            {{ item.status.replace('_', ' ') }}<span v-if="item.stale"> · stale</span>
          </el-tag>
        </header>
        <dl v-if="item.metrics.length">
          <template v-for="metric in item.metrics" :key="metric.name + JSON.stringify(metric.dimensions || {})">
            <dt>{{ metric.name.replaceAll('_', ' ') }}</dt>
            <dd>{{ metric.value }} {{ metric.unit }}</dd>
          </template>
        </dl>
        <p v-else class="empty-metrics">No live metrics returned.</p>
        <footer>
          <time v-if="item.retrieved_at">{{ new Date(item.retrieved_at).toLocaleString() }}</time>
          <a v-if="item.dashboard_url" :href="item.dashboard_url" target="_blank" rel="noreferrer">Dashboard</a>
        </footer>
      </article>
    </div>
    <h3>Configured model allow-list</h3>
    <div class="capability-list">
      <div v-for="(models, role) in modelCapabilities" :key="role">
        <strong>{{ role }}</strong>
        <span v-if="!models.length">Not configured</span>
        <el-tag v-for="model in models" :key="model.provider + model.model" effect="plain">
          {{ model.provider }} · {{ model.model }}
        </el-tag>
      </div>
    </div>
  </section>
</template>

<style scoped>
.provider-usage { width: 100%; }
.provider-toolbar, .provider-item header, .provider-item footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.provider-toolbar p { color: #536176; }
.provider-list { display: grid; gap: 12px; }
.provider-item { border: 1px solid #dbe2ea; border-radius: 8px; padding: 16px; background: #fff; }
.provider-item dl { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px 16px; margin: 14px 0; }
.provider-item dt { color: #536176; text-transform: capitalize; }
.provider-item dd { margin: 0; font-variant-numeric: tabular-nums; }
.provider-item footer, .empty-metrics, .usage-error { color: #6b7280; font-size: 13px; }
.usage-error { color: #b42318; }
.capability-list { display: grid; gap: 10px; }
.capability-list > div { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.capability-list strong { width: 64px; text-transform: capitalize; }
</style>