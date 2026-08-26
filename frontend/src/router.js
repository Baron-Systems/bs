import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
  },
  {
    path: '/quick-inventory',
    name: 'QuickInventory',
    component: () => import('@/pages/QuickInventory.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/customer-report',
    name: 'CustomerReport',
    component: () => import('@/pages/CustomerReport.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/customer-payment',
    name: 'CustomerPayment',
    component: () => import('@/pages/CustomerPayment.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/supplier-payment',
    name: 'SupplierPayment',
    component: () => import('@/pages/SupplierPayment.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/store-manage',
    name: 'StoreManage',
    component: () => import('@/pages/StoreManage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/store',
    name: 'Storefront',
    component: () => import('@/pages/Storefront.vue'),
  },
]

let router = createRouter({
  history: createWebHistory('/bs'),
  routes,
})

// Navigation guard: redirect to login if not authenticated
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    const user = cookies.get('user_id')
    if (!user || user === 'Guest') {
      next({ name: 'Login' })
      return
    }
  }
  next()
})

export default router
