<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 mb-4">Сайти</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Список сайтів</span>
            <v-btn color="primary" @click="showAddDialog = true">
              <v-icon left>mdi-plus</v-icon>
              Додати сайт
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="websites"
              :loading="loading"
            >
              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click="startScan(item.id)" :loading="scanningWebsites.includes(item.id)">
                  <v-icon>mdi-play</v-icon>
                </v-btn>
                <v-btn icon size="small" @click="editWebsite(item)">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" color="error" @click="deleteWebsite(item.id)">
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
              
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add/Edit Dialog -->
    <v-dialog v-model="showAddDialog" max-width="600">
      <v-card>
        <v-card-title>{{ editMode ? 'Редагувати' : 'Додати' }} сайт</v-card-title>
        
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="currentWebsite.url"
              label="URL сайту"
              placeholder="https://example.com"
              :rules="[rules.required, rules.url]"
              :disabled="editMode"
              required
            ></v-text-field>
            
            <v-text-field
              v-model="currentWebsite.name"
              label="Назва"
              placeholder="Мій сайт"
            ></v-text-field>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">Скасувати</v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="saveWebsite">
            Зберегти
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
const websites = ref([])
const showAddDialog = ref(false)
const formValid = ref(false)
const editMode = ref(false)
const scanningWebsites = ref([])
const currentWebsite = ref({
  url: '',
  name: '',
})

const headers = [
  { title: 'ID', value: 'id', sortable: true },
  { title: 'Назва', value: 'name', sortable: true },
  { title: 'URL', value: 'url', sortable: true },
  { title: 'Домен', value: 'domain', sortable: true },
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

const loadWebsites = async () => {
  loading.value = true
  try {
    const response = await api.getWebsites()
    websites.value = response.data
  } catch (error) {
    console.error('Error loading websites:', error)
  } finally {
    loading.value = false
  }
}

const saveWebsite = async () => {
  try {
    if (editMode.value) {
      await api.updateWebsite(currentWebsite.value.id, currentWebsite.value)
    } else {
      await api.createWebsite(currentWebsite.value)
    }
    closeDialog()
    loadWebsites()
  } catch (error) {
    console.error('Error saving website:', error)
  }
}

const editWebsite = (website) => {
  currentWebsite.value = { ...website }
  editMode.value = true
  showAddDialog.value = true
}

const deleteWebsite = async (id) => {
  if (confirm('Ви впевнені, що хочете видалити цей сайт?')) {
    try {
      await api.deleteWebsite(id)
      loadWebsites()
    } catch (error) {
      console.error('Error deleting website:', error)
    }
  }
}

const startScan = async (websiteId) => {
  scanningWebsites.value.push(websiteId)
  try {
    const response = await api.createScan(websiteId)
    const scanId = response.data.id
    router.push({ name: 'ScanDetail', params: { id: scanId } })
  } catch (error) {
    console.error('Error starting scan:', error)
  } finally {
    scanningWebsites.value = scanningWebsites.value.filter(id => id !== websiteId)
  }
}

const closeDialog = () => {
  showAddDialog.value = false
  editMode.value = false
  currentWebsite.value = { url: '', name: '' }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('uk-UA')
}

onMounted(() => {
  loadWebsites()
})
</script>

