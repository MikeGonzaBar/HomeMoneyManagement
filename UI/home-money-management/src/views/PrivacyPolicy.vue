<template>
  <div class="bg-gray-50">
    <AppHeader :userData="userData" />

    <main class="w-full">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-6">Privacy Policy</h1>
          <p class="text-sm text-gray-500 mb-6">Effective Date: {{ currentYear }}</p>

          <section class="space-y-8">
            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">1. Introduction</h2>
              <p class="text-gray-700 leading-relaxed">
                Budget Buddy ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our personal finance management application. By using Budget Buddy, you agree to the terms of this Privacy Policy.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">2. Information We Collect</h2>
              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">2.1 Account Information</h3>
              <p class="text-gray-700 leading-relaxed mb-2">
                When you create an account, we collect:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Username, first name, and last name</li>
                <li>Authentication credentials (stored securely in encrypted form)</li>
                <li>Account preferences (e.g., theme preference)</li>
              </ul>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">2.2 Financial Data</h3>
              <p class="text-gray-700 leading-relaxed mb-2">
                To provide our services, we collect and store your personal financial information, including:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Account names, types, and balances (checking, savings, credit cards, etc.)</li>
                <li>Transaction details (date, title/description, category, amount, type)</li>
                <li>Budget goals and categories</li>
                <li>Recurring transaction rules and occurrences</li>
                <li>Bank statements uploaded by you</li>
              </ul>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">2.3 AI Processing Data (Bank Statement Extraction)</h3>
              <p class="text-gray-700 leading-relaxed mb-2">
                When you upload bank statements (PDFs, including password-protected PDFs), we process them using Google Gemini AI (via Google AI Studio API) to extract transaction data. This processing may involve:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Transmission of your uploaded PDF document to Google's Gemini API for parsing</li>
                <li>Extraction of transaction details (dates, amounts, descriptions, merchants)</li>
                <li>Detection of account information and initial balances</li>
              </ul>
              <p class="text-gray-700 leading-relaxed mt-2">
                <strong>Important:</strong> Your bank statements contain sensitive financial information. We only send this data to Google Gemini for the explicit purpose of extracting transactions for your use. We do not use this data for training our models. Please review Google's <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">Privacy Policy</a> to understand how Google processes data sent to their APIs.
              </p>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">2.4 Usage Data</h3>
              <p class="text-gray-700 leading-relaxed">
                We may collect technical information such as IP addresses, browser type, device information, and access logs for security, debugging, and to improve service reliability.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">3. How We Use Your Information</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                We use your information solely to provide and improve our services, including:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Authenticating and managing your account</li>
                <li>Storing and organizing your financial data</li>
                <li>Processing uploaded bank statements via AI to extract transactions</li>
                <li>Generating reports, forecasts, and insights about your finances</li>
                <li>Sending in-app alerts for budgets, recurring items, and forecasts</li>
                <li>Maintaining security and preventing unauthorized access</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">4. Data Ownership & Isolation</h2>
              <p class="text-gray-700 leading-relaxed">
                Your data is private and belongs to you. We enforce strict user-specific data isolation - each user's financial data is only accessible to that authenticated user. We do not sell, rent, or share your personal financial information with third parties for marketing or commercial purposes.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">5. Data Sharing & Disclosure</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                We only share your data in limited circumstances:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li><strong>AI Processing:</strong> Bank statement PDFs are transmitted to Google Gemini API solely for transaction extraction as described above</li>
                <li><strong>Legal Requirements:</strong> If required by law, court order, or government regulation</li>
                <li><strong>Security:</strong> To protect our rights, property, or safety, or that of our users</li>
                <li><strong>Service Providers:</strong> Only those necessary to provide the service (e.g., hosting, database) under strict confidentiality obligations</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">6. Data Security</h2>
              <p class="text-gray-700 leading-relaxed">
                We take data security seriously. We implement appropriate technical and organizational measures to protect your information, including token-based authentication, secure data transmission (HTTPS), and access controls. However, no method of electronic storage or transmission is 100% secure. While we strive to protect your personal information, we cannot guarantee absolute security.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">7. Data Storage & Retention</h2>
              <p class="text-gray-700 leading-relaxed">
                Your financial data is stored for as long as your account remains active or as needed to provide you with our services. If you delete your account, we will delete or anonymize your personal data in accordance with applicable laws, except where retention is required for legal, tax, or security purposes.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">8. Your Rights</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                You have the right to:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Access and review your stored financial data</li>
                <li>Update or correct your account information</li>
                <li>Export your transaction and financial data</li>
                <li>Delete specific records or your entire account</li>
                <li>Opt out of any non-essential communications (if applicable)</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">9. Children's Privacy</h2>
              <p class="text-gray-700 leading-relaxed">
                Our services are not intended for individuals under the age of 13. We do not knowingly collect personal information from children under 13. If we become aware that we have collected such information, we will take steps to delete it.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">10. Changes to This Privacy Policy</h2>
              <p class="text-gray-700 leading-relaxed">
                We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on this page and updating the effective date. Your continued use of Budget Buddy after such changes constitutes acceptance of the updated policy.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">11. Contact Us</h2>
              <p class="text-gray-700 leading-relaxed">
                If you have questions or concerns about this Privacy Policy or our data practices, please contact us through the application's support channels.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import AppHeader from '@/components/AppHeader.vue'

export default {
  name: 'PrivacyPolicy',
  components: {
    AppHeader
  },
  data() {
    return {
      userData: null as any,
    }
  },
  computed: {
    currentYear() {
      return new Date().getFullYear()
    }
  }
}
</script>