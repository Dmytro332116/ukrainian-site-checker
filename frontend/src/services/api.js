import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  // Websites
  getWebsites() {
    return api.get('/websites/')
  },
  
  getWebsite(id) {
    return api.get(`/websites/${id}`)
  },
  
  createWebsite(data) {
    return api.post('/websites/', data)
  },
  
  updateWebsite(id, data) {
    return api.patch(`/websites/${id}`, data)
  },
  
  deleteWebsite(id) {
    return api.delete(`/websites/${id}`)
  },
  
  // Scans
  getScans(websiteId = null) {
    const params = websiteId ? { website_id: websiteId } : {}
    return api.get('/scans/', { params })
  },
  
  getScan(id) {
    return api.get(`/scans/${id}`)
  },
  
  createScan(websiteId) {
    return api.post('/scans/', { website_id: websiteId })
  },
  
  getScanStatus(id) {
    return api.get(`/scans/${id}/status`)
  },
  
  deleteScan(id) {
    return api.delete(`/scans/${id}`)
  },
  
  // Pages
  getPage(id) {
    return api.get(`/pages/${id}`)
  },
  
  getPagesByScan(scanId) {
    return api.get(`/pages/scan/${scanId}`)
  },
  
  // Errors
  getErrorsByScan(scanId, errorType = null, severity = null) {
    const params = {}
    if (errorType) params.error_type = errorType
    if (severity) params.severity = severity
    return api.get(`/errors/scan/${scanId}`, { params })
  },
  
  getErrorsByPage(pageId) {
    return api.get(`/errors/page/${pageId}`)
  },
}

