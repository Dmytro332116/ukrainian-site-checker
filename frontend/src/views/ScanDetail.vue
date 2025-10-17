<template>
  <div>
    <v-row v-if="scan">
      <v-col cols="12">
        <v-btn @click="$router.back()" text class="mb-4">
          <v-icon left>mdi-arrow-left</v-icon>
          Назад
        </v-btn>
        
        <h1 class="text-h3 mb-4">Деталі сканування #{{ scan.id }}</h1>
      </v-col>
    </v-row>

    <!-- Status Card -->
    <v-row v-if="scan">
      <v-col cols="12">
        <v-card>
          <v-card-title>Статус сканування</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <div class="text-h6">Статус</div>
                <v-chip :color="getStatusColor(scan.status)" size="large">
                  {{ getStatusText(scan.status) }}
                </v-chip>
              </v-col>
              
              <v-col cols="12" md="3">
                <div class="text-h6">Знайдено сторінок</div>
                <div class="text-h4">{{ scan.pages_found }}</div>
              </v-col>
              
              <v-col cols="12" md="3">
                <div class="text-h6">Оброблено</div>
                <div class="text-h4">{{ scan.pages_processed }}</div>
              </v-col>
              
              <v-col cols="12" md="3">
                <div class="text-h6">Помилок знайдено</div>
                <div class="text-h4" :class="scan.errors_found > 0 ? 'text-error' : 'text-success'">
                  {{ scan.errors_found }}
                </div>
              </v-col>
            </v-row>
            
            <v-progress-linear
              v-if="scan.status === 'running'"
              :model-value="(scan.pages_processed / scan.pages_found) * 100"
              color="primary"
              height="25"
              class="mt-4"
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.ceil(value) }}%</strong>
              </template>
            </v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Statistics -->
    <v-row v-if="scan && scan.errors_found > 0">
      <v-col cols="12">
        <v-card>
          <v-card-title>Статистика помилок</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6" md="2" v-for="type in errorTypes" :key="type.value">
                <v-card outlined>
                  <v-card-text class="text-center">
                    <v-icon :color="type.color" size="48">{{ type.icon }}</v-icon>
                    <div class="text-h5 mt-2">{{ errorStats[type.value] || 0 }}</div>
                    <div class="text-caption">{{ type.label }}</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Errors Table -->
    <v-row v-if="scan && scan.pages && scan.pages.length > 0">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Знайдені помилки</span>
            <div>
              <v-select
                v-model="filterErrorType"
                :items="errorTypeFilter"
                label="Тип помилки"
                style="min-width: 200px"
                density="compact"
                class="mr-2"
              ></v-select>
            </div>
          </v-card-title>
          
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel v-for="page in pagesWithErrors" :key="page.id">
                <v-expansion-panel-title>
                  <div class="d-flex align-center justify-space-between" style="width: 100%">
                    <div>
                      <v-icon left>mdi-file-document</v-icon>
                      {{ page.title || page.url }}
                    </div>
                    <v-chip color="error" size="small">
                      {{ page.errors.length }} помилок
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                
                <v-expansion-panel-text>
                  <v-list>
                    <v-list-item v-for="error in page.errors" :key="error.id">
                      <v-list-item-title>
                        <v-icon :color="getErrorTypeColor(error.error_type)" class="mr-2">
                          {{ getErrorTypeIcon(error.error_type) }}
                        </v-icon>
                        {{ error.message }}
                      </v-list-item-title>
                      <v-list-item-subtitle v-if="error.context">
                        Контекст: {{ error.context }}
                      </v-list-item-subtitle>
                      <v-list-item-subtitle v-if="error.suggestion" class="text-success">
                        Пропозиція: {{ error.suggestion }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'

const route = useRoute()
const scan = ref(null)
const filterErrorType = ref('all')
const refreshInterval = ref(null)

const errorTypes = [
  { value: 'spelling', label: 'Орфографія', icon: 'mdi-spellcheck', color: 'warning' },
  { value: 'address', label: 'Адреси', icon: 'mdi-map-marker', color: 'error' },
  { value: 'broken_link', label: 'Посилання', icon: 'mdi-link-off', color: 'error' },
  { value: 'phone', label: 'Телефони', icon: 'mdi-phone', color: 'warning' },
  { value: 'seo', label: 'SEO', icon: 'mdi-magnify', color: 'info' },
]

const errorTypeFilter = computed(() => [
  { title: 'Всі помилки', value: 'all' },
  ...errorTypes.map(t => ({ title: t.label, value: t.value }))
])

const errorStats = computed(() => {
  if (!scan.value || !scan.value.pages) return {}
  
  const stats = {}
  scan.value.pages.forEach(page => {
    page.errors.forEach(error => {
      stats[error.error_type] = (stats[error.error_type] || 0) + 1
    })
  })
  return stats
})

const pagesWithErrors = computed(() => {
  if (!scan.value || !scan.value.pages) return []
  
  return scan.value.pages
    .filter(page => page.errors && page.errors.length > 0)
    .filter(page => {
      if (filterErrorType.value === 'all') return true
      return page.errors.some(e => e.error_type === filterErrorType.value)
    })
})

const loadScan = async () => {
  try {
    const response = await api.getScan(route.params.id)
    scan.value = response.data
    
    // If scan is running, poll for updates
    if (scan.value.status === 'running') {
      startPolling()
    } else {
      stopPolling()
    }
  } catch (error) {
    console.error('Error loading scan:', error)
  }
}

const startPolling = () => {
  if (!refreshInterval.value) {
    refreshInterval.value = setInterval(loadScan, 3000) // Poll every 3 seconds
  }
}

const stopPolling = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'grey',
    running: 'blue',
    completed: 'success',
    failed: 'error',
  }
  return colors[status] || 'grey'
}

const getStatusText = (status) => {
  const texts = {
    pending: 'Очікується',
    running: 'Виконується',
    completed: 'Завершено',
    failed: 'Помилка',
  }
  return texts[status] || status
}

const getErrorTypeIcon = (type) => {
  const typeObj = errorTypes.find(t => t.value === type)
  return typeObj?.icon || 'mdi-alert'
}

const getErrorTypeColor = (type) => {
  const typeObj = errorTypes.find(t => t.value === type)
  return typeObj?.color || 'grey'
}

onMounted(() => {
  loadScan()
})

onUnmounted(() => {
  stopPolling()
})
</script>

