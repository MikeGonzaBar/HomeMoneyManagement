/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

import {
  VDataTable,
} from "vuetify/labs/VDataTable";

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          // Budget Buddy Brand Colors
          primary: '#2E7D32', // Deep Green
          secondary: '#4CAF50', // Medium Green
          accent: '#8BC34A', // Light Green
          error: '#F44336',
          warning: '#FF9800',
          info: '#2196F3',
          success: '#4CAF50',

          // Custom Budget Buddy Palette
          'budget-primary': '#2E7D32',
          'budget-secondary': '#4CAF50',
          'budget-accent': '#8BC34A',
          'budget-success': '#4CAF50',
          'budget-warning': '#FF9800',
          'budget-error': '#F44336',

          // Background Colors
          background: '#FAFAFA',
          surface: '#FFFFFF',
          'surface-variant': '#F5F5F5',

          // Text Colors
          'on-primary': '#FFFFFF',
          'on-secondary': '#FFFFFF',
          'on-surface': '#212121',
          'on-background': '#212121',

          // Income/Expense Colors
          'income': '#4CAF50',
          'expense': '#F44336',
        },
      },
    },
  },
  components: {
    VDataTable,
  },
  defaults: {
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
    VBtn: {
      rounded: 'lg',
      elevation: 1,
    },
    VTextField: {
      rounded: 'lg',
      variant: 'outlined',
    },
    VSelect: {
      rounded: 'lg',
      variant: 'outlined',
    },
  },
})
