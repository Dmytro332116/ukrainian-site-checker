<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 mb-4">Дашборд</h1>
      </v-col>
    </v-row>

    <!-- Recent Scans -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Останні сканування</span>
            <v-btn color="primary" @click="showAddWebsiteDialog = true">
              <v-icon left>mdi-plus</v-icon>
              Новий сайт
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="recentScans"
              :loading="loading"
              @click:row="goToScan"
            >
              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ getStatusText(item.status) }}
                </v-chip>
              </template>
              
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
              
              <template v-slot:item.errors_found="{ item }">
                <v-chip :color="item.errors_found > 0 ? 'error' : 'success'" size="small">
                  {{ item.errors_found }}
                </v-chip>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click.stop="viewScan(item.id)">
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add Website Dialog -->
    <v-dialog v-model="showAddWebsiteDialog" max-width="600">
      <v-card>
        <v-card-title>Додати новий сайт</v-card-title>
        
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="newWebsite.url"
              label="URL сайту"
              placeholder="https://example.com"
              :rules="[rules.required, rules.url]"
              required
            ></v-text-field>
            
            <v-text-field
              v-model="newWebsite.name"
              label="Назва (опціонально)"
              placeholder="Мій сайт"
            ></v-text-field>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddWebsiteDialog = false">Скасувати</v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="addWebsite">
            Додати і сканувати
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()

const loading = ref(false)
const recentScans = ref([])
const showAddWebsiteDialog = ref(false)
const formValid = ref(false)
const newWebsite = ref({
  url: '',
  name: '',
})

const headers = [
  { title: 'ID', value: 'id', sortable: true },
  { title: 'Сайт', value: 'website_id', sortable: true },
  { title: 'Статус', value: 'status', sortable: true },
  { title: 'Знайдено сторінок', value: 'pages_found', sortable: true },
  { title: 'Оброблено', value: 'pages_processed', sortable: true },
  { title: 'Помилки', value: 'errors_found', sortable: true },
  { title: 'Створено', value: 'created_at', sortable: true },
  { title: 'Дії', value: 'actions', sortable: false },
]

const rules = {
  required: value => !!value || 'Обов\'язкове поле',
  url: value => {
    const pattern = /^https?:\/\/.+/
    return pattern.test(value) || 'Невірний формат URL'
  },
}

const loadRecentScans = async () => {
  loading.value = true
  try {
    const response = await api.getScans()
    recentScans.value = response.data
  } catch (error) {
    console.error('Error loading scans:', error)
  } finally {
    loading.value = false
  }
}

const addWebsite = async () => {
  try {
    // Create website
    const websiteResponse = await api.createWebsite(newWebsite.value)
    const websiteId = websiteResponse.data.id
    
    // Start scan
    await api.createScan(websiteId)
    
    // Reset form
    showAddWebsiteDialog.value = false
    newWebsite.value = { url: '', name: '' }
    
    // Reload scans
    loadRecentScans()
  } catch (error) {
    console.error('Error adding website:', error)
  }
}

const viewScan = (scanId) => {
  router.push({ name: 'ScanDetail', params: { id: scanId } })
}

const goToScan = (event, { item }) => {
  viewScan(item.id)
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

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('uk-UA')
}

onMounted(() => {
  loadRecentScans()
})
</script>

