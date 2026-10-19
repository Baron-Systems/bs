import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    // App shell: persistent header + sidebar; only the child view changes
    path: '/',
    component: () => import('@/layouts/AppShell.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/pages/Home.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'quick-inventory',
        name: 'QuickInventory',
        component: () => import('@/pages/QuickInventory.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'quick-purchase-invoice',
        name: 'QuickPurchaseInvoice',
        component: () => import('@/pages/QuickPurchaseInvoice.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'customer-report',
        name: 'CustomerReport',
        component: () => import('@/pages/CustomerReport.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'customer-payment',
        name: 'CustomerPayment',
        component: () => import('@/pages/CustomerPayment.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'supplier-payment',
        name: 'SupplierPayment',
        component: () => import('@/pages/SupplierPayment.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'store-manage',
        name: 'StoreManage',
        component: () => import('@/pages/StoreManage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { requiresAuth: true },
      },
      // Employees section — static paths must stay above employees/:id
      {
        path: 'employees',
        name: 'EmployeesList',
        component: () => import('@/pages/employees/EmployeesList.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/new',
        name: 'EmployeeNew',
        component: () => import('@/pages/employees/EmployeeForm.vue'),
        meta: { requiresAuth: true, navParent: 'EmployeesList' },
      },
      {
        path: 'employees/attendance',
        name: 'EmployeeAttendance',
        component: () => import('@/pages/employees/Attendance.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/leaves',
        name: 'EmployeeLeaves',
        component: () => import('@/pages/employees/Leaves.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/payroll',
        name: 'EmployeePayroll',
        component: () => import('@/pages/employees/Payroll.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/payroll/:id',
        name: 'EmployeePayrollEntry',
        component: () => import('@/pages/employees/PayrollEntry.vue'),
        meta: { requiresAuth: true, navParent: 'EmployeePayroll' },
      },
      {
        path: 'employees/advances',
        name: 'EmployeeAdvances',
        component: () => import('@/pages/employees/Advances.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/advances/:id',
        name: 'EmployeeAdvanceDetail',
        component: () => import('@/pages/employees/AdvanceDetail.vue'),
        meta: { requiresAuth: true, navParent: 'EmployeeAdvances' },
      },
      {
        path: 'employees/settings',
        name: 'EmployeeSettings',
        component: () => import('@/pages/employees/EmployeeSettings.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'employees/:id/edit',
        name: 'EmployeeEdit',
        component: () => import('@/pages/employees/EmployeeForm.vue'),
        meta: { requiresAuth: true, navParent: 'EmployeesList' },
      },
      {
        path: 'employees/:id',
        name: 'EmployeeDetail',
        component: () => import('@/pages/employees/EmployeeDetail.vue'),
        meta: { requiresAuth: true, navParent: 'EmployeesList' },
      },
      {
        path: 'decision-center',
        name: 'DecisionCenter',
        component: () => import('@/pages/DecisionCenter.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/settings',
        name: 'DecisionCenterSettings',
        component: () => import('@/pages/DecisionCenterSettings.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/plans',
        name: 'DecisionCenterPlans',
        component: () => import('@/pages/DecisionCenterPlans.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/plans/new',
        name: 'DecisionCenterPlanNew',
        component: () => import('@/pages/DecisionCenterPlanForm.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/plans/:planId/edit',
        name: 'DecisionCenterPlanEdit',
        component: () => import('@/pages/DecisionCenterPlanForm.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/plans/:planId',
        name: 'DecisionCenterPlanDetail',
        component: () => import('@/pages/DecisionCenterPlanDetail.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/monthly-reports',
        name: 'DecisionCenterMonthlyReports',
        component: () => import('@/pages/DecisionCenterMonthlyReports.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/monthly-report/:month',
        name: 'DecisionCenterMonthlyReport',
        component: () => import('@/pages/DecisionCenterMonthlyReport.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/help',
        name: 'DecisionCenterHelp',
        component: () => import('@/pages/HelpCenter.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'decision-center/:decisionId',
        name: 'DecisionDetail',
        component: () => import('@/pages/DecisionDetail.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
  },
  {
    path: '/customer-portal/login',
    name: 'CustomerPortalLogin',
    component: () => import('@/pages/CustomerPortalLogin.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/customer-portal',
    name: 'CustomerPortal',
    component: () => import('@/pages/CustomerPortal.vue'),
    meta: { requiresAuth: false },
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
