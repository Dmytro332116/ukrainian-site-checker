import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import WebsiteList from '../views/WebsiteList.vue'
import ScanDetail from '../views/ScanDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/websites',
    name: 'WebsiteList',
    component: WebsiteList,
  },
  {
    path: '/scan/:id',
    name: 'ScanDetail',
    component: ScanDetail,
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

