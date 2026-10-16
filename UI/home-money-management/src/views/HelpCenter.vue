<template>
  <div class="bg-gray-50 min-h-screen">
    <AppHeader :userData="userData" />

    <main class="w-full">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-6">Help Center</h1>
          <p class="text-gray-600 mb-8">Find answers to common questions about Budget Buddy.</p>

          <section class="space-y-8">
            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Getting Started</h2>
              <div class="space-y-4">
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How do I create an account?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    From the home page, use the Register tab to create a new account with a username and password. Your data is private and isolated per user.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How do I add my first account?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Go to the Dashboard or Accounts page and add your bank/checking/savings/credit card accounts. You can also track balances over time.
                  </p>
                </details>
              </div>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Transactions & AI Extraction</h2>
              <div class="space-y-4">
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How does AI bank statement extraction work?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    When you upload a PDF bank statement (including password-protected PDFs) in the Statements section, we send it to Google Gemini AI to extract transactions, dates, amounts, descriptions, and detect initial balances. The extracted data is presented for your review before importing.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">Is my bank statement data safe when using AI?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    We only send your uploaded statement to Google Gemini for transaction extraction. We do not use it to train models. All processing is for your account only. Review Google's Privacy Policy for details on how their APIs handle data.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">Do I need to verify AI-extracted transactions?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Yes. AI extraction may have errors due to statement formats. Always review extracted transactions in the Import Review screen, correct any issues, and confirm before committing them to your account.
                  </p>
                </details>
              </div>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Budgets, Recurring & Reports</h2>
              <div class="space-y-4">
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How do budgets work?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    You can set overall or category-specific monthly budgets. Budget Buddy tracks spent amounts, remaining amounts, percent used, and status (on track, warning, or exceeded).
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">What are recurring transactions?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Recurring transactions let you define rules for income, expenses, or transfers. Due occurrences appear for your confirmation before posting real transactions to your accounts.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How do reports and forecasting work?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Reports show spending by category, cashflow, and trends. Forecasting projects future balances based on current balances, confirmed transactions, recurring items, budgets, and trailing history.
                  </p>
                </details>
              </div>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Data & Privacy</h2>
              <div class="space-y-4">
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">Is my financial data private?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Yes. Your data is user-scoped and isolated - only you can access it when authenticated. We do not sell or share your personal financial data for marketing purposes.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">Can I export my data?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    Yes, you can export transactions from the Transactions page to keep your own backups.
                  </p>
                </details>
                <details class="border border-gray-200 rounded-lg p-4">
                  <summary class="font-medium text-gray-900 cursor-pointer">How is my account secured?</summary>
                  <p class="mt-3 text-gray-700 leading-relaxed">
                    We use token-based authentication. Sessions are stored locally on your device, and invalid/legacy sessions are cleared. Access is restricted to authenticated users only.
                  </p>
                </details>
              </div>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Need More Help?</h2>
              <p class="text-gray-700 leading-relaxed">
                If you can't find what you're looking for, please check the
                <router-link to="/privacy-policy" class="text-blue-600 hover:text-blue-800 underline">Privacy Policy</router-link> and
                <router-link to="/terms-of-service" class="text-blue-600 hover:text-blue-800 underline">Terms of Service</router-link> for more details, or
                <a href="https://github.com/gonzales-juan/HomeMoneyManagement/issues" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">report an issue on GitHub</a>.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import { getStoredSession } from '@/services/session'

export default {
  name: 'HelpCenter',
  components: {
    AppHeader,
    AppFooter
  },
  data() {
    const session = getStoredSession()
    return {
      userData: session ? { user: session.user } : { user: {} }
    }
  }
}
</script>