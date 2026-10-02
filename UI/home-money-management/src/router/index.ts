// Composables
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "home" */ '@/views/Home.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import(/* webpackChunkName: "profile" */ '@/views/Profile.vue'),
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import(/* webpackChunkName: "transactions" */ '@/views/Transactions.vue'),
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: () => import(/* webpackChunkName: "budgets" */ '@/views/Budgets.vue'),
  },
  {
    path: '/recurring',
    name: 'Recurring',
    component: () => import(/* webpackChunkName: "recurring" */ '@/views/Recurring.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import(/* webpackChunkName: "reports" */ '@/views/Reports.vue'),
  },
  {
    path: '/statements',
    name: 'Statements',
    component: () => import(/* webpackChunkName: "statements" */ '@/views/Statements.vue'),
  },
  {
    path: '/statements/:batchId/review',
    name: 'ImportReview',
    component: () => import(/* webpackChunkName: "import-review" */ '@/views/ImportReview.vue'),
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: () => import(/* webpackChunkName: "accounts" */ '@/views/Accounts.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router
