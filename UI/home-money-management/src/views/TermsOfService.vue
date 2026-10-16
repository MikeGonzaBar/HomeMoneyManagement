<template>
  <div class="bg-gray-50">
    <AppHeader :userData="userData" />

    <main class="w-full">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-6">Terms of Service</h1>
          <p class="text-sm text-gray-500 mb-6">Effective Date: {{ currentYear }}</p>

          <section class="space-y-8">
            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">1. Acceptance of Terms</h2>
              <p class="text-gray-700 leading-relaxed">
                By accessing and using Budget Buddy ("the Service"), you accept and agree to be bound by these Terms of Service. If you do not agree to these terms, you must not use the Service.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">2. Description of Service</h2>
              <p class="text-gray-700 leading-relaxed">
                Budget Buddy is a personal finance management application that allows you to track expenses, manage accounts, plan budgets, manage recurring transactions, reconcile bank statements, and visualize financial data. The Service includes AI-powered bank statement parsing using Google Gemini.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">3. User Accounts</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                To use the Service, you must:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Provide accurate and complete information when creating an account</li>
                <li>Maintain the security of your account credentials</li>
                <li>Be responsible for all activities under your account</li>
                <li>Notify us immediately if you suspect unauthorized access to your account</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">4. User Data & Privacy</h2>
              <p class="text-gray-700 leading-relaxed">
                Your use of the Service is also governed by our <router-link to="/privacy-policy" class="text-blue-600 hover:text-blue-800 underline">Privacy Policy</router-link>. You acknowledge that you have read and understand our Privacy Policy, including how we collect, use, and protect your data, particularly with respect to AI-powered processing of uploaded bank statements.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">5. AI-Powered Statement Processing</h2>
              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">5.1 Your Consent</h3>
              <p class="text-gray-700 leading-relaxed">
                By uploading bank statements (including password-protected PDFs), you explicitly consent to the transmission of those documents to Google Gemini API for the sole purpose of extracting transaction data to populate your account within the Service.
              </p>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">5.2 Accuracy & Limitations</h3>
              <p class="text-gray-700 leading-relaxed mb-2">
                AI-powered extraction is provided as a convenience feature. You acknowledge and agree that:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Extracted data may contain errors, omissions, or misclassifications</li>
                <li>You are responsible for reviewing, verifying, correcting, and approving all extracted transactions before or after import</li>
                <li>We do not guarantee the accuracy, completeness, or reliability of AI-extracted data</li>
                <li>Bank statement formats vary and may affect extraction quality</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">6. Your Responsibilities</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                You agree to use the Service responsibly and lawfully, including:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Only upload bank statements that you own or are authorized to access</li>
                <li>Maintain accurate financial records</li>
                <li>Not use the Service for illegal purposes or to violate any applicable laws</li>
                <li>Not attempt to gain unauthorized access to systems, data, or accounts</li>
                <li>Not interfere with or disrupt the Service's operation</li>
                <li>Keep your device and access secure</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">7. Data Ownership</h2>
              <p class="text-gray-700 leading-relaxed">
                You retain full ownership of all financial data you input into the Service. We do not claim ownership of your personal financial information. You are responsible for backing up your data as needed.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">8. Prohibited Uses</h2>
              <p class="text-gray-700 leading-relaxed mb-2">
                You may not:
              </p>
              <ul class="list-disc pl-6 space-y-1 text-gray-700">
                <li>Reverse engineer, decompile, or attempt to extract source code</li>
                <li>Share your account with others or transfer account access</li>
                <li>Upload malicious files or content that could harm the Service</li>
                <li>Use automated tools to scrape, crawl, or access the Service inappropriately</li>
                <li>Misrepresent your identity or provide false information</li>
              </ul>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">9. Service Availability & Modifications</h2>
              <p class="text-gray-700 leading-relaxed">
                We strive to provide reliable access to the Service, but we do not guarantee uninterrupted or error-free operation. We reserve the right to modify, suspend, or discontinue any part of the Service at any time, with or without notice.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">10. Disclaimers & Limitation of Liability</h2>
              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">10.1 No Financial Advice</h3>
              <p class="text-gray-700 leading-relaxed">
                Budget Buddy is a personal finance management tool only. The information and features provided do not constitute financial, investment, tax, legal, or accounting advice. You should consult qualified professionals for advice specific to your situation.
              </p>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">10.2 Disclaimer of Warranties</h3>
              <p class="text-gray-700 leading-relaxed">
                THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, OR NON-INFRINGEMENT.
              </p>

              <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">10.3 Limitation of Liability</h3>
              <p class="text-gray-700 leading-relaxed">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA, OR GOODWILL, ARISING FROM YOUR USE OF THE SERVICE OR INABILITY TO USE IT, EVEN IF WE HAVE BEEN ADVISED OF SUCH DAMAGES.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">11. Indemnification</h2>
              <p class="text-gray-700 leading-relaxed">
                You agree to indemnify, defend, and hold harmless Budget Buddy and its operators from any claims, damages, liabilities, costs, or expenses (including reasonable attorneys' fees) arising from your use of the Service, violation of these Terms, or infringement of any third-party rights.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">12. Termination</h2>
              <p class="text-gray-700 leading-relaxed">
                You may terminate your account at any time. We reserve the right to suspend or terminate your access to the Service for violations of these Terms or for any other reason, with or without notice. Upon termination, your right to use the Service ceases, though provisions of these Terms that should survive (including disclaimers, limitations, indemnification) will remain in effect.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">13. Governing Law</h2>
              <p class="text-gray-700 leading-relaxed">
                These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law principles.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">14. Changes to Terms</h2>
              <p class="text-gray-700 leading-relaxed">
                We may update these Terms of Service from time to time. We will notify you of material changes by posting the updated terms and revising the effective date. Your continued use of the Service after changes constitutes acceptance of the updated Terms.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-3">15. Contact Information</h2>
              <p class="text-gray-700 leading-relaxed">
                If you have questions about these Terms of Service, please contact us through the application's support channels.
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
  name: 'TermsOfService',
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