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
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router
