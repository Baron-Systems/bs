<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<button
						@click="goBack"
						class="p-2 rounded-xl text-slate-600 hover:bg-slate-100 transition-all hover:scale-105 active:scale-95 flex-shrink-0"
						:aria-label="__('رجوع')"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
					</button>
					<div class="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
							{{ __("دفع العميل") }}
						</h1>
						<p class="text-xs text-slate-500 truncate">
							{{ __("قبض من العميل أو الدفع له") }}
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2 flex-shrink-0">
					<div class="hidden sm:flex items-center gap-2 bg-slate-100 rounded-full px-3 py-1.5">
						<div class="w-7 h-7 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
							{{ userInitial }}
						</div>
						<span class="text-xs font-medium text-slate-700">{{ userName }}</span>
					</div>
					<button
						@click="logout"
						class="p-2 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-all hover:scale-105 active:scale-95"
						:aria-label="__('تسجيل الخروج')"
						:title="__('تسجيل الخروج')"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
						</svg>
					</button>
				</div>
			</div>
		</header>

		<!-- Main Content -->
		<main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-4 sm:py-6 flex flex-col gap-4">
			<!-- Company Selector -->
			<section class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
				<div class="flex flex-col sm:flex-row gap-3 items-end">
					<div class="flex-1 w-full">
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("الشركة") }}</label>
						<select
							v-model="selectedCompany"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
							:disabled="loadingCompanies"
							@change="onCompanyChange"
						>
							<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
							<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
						</select>
					</div>
				</div>
			</section>

			<!-- Customer Search -->
			<section class="bg-white rounded-2xl border border-slate-200 shadow-md p-4">
				<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("بحث عن عميل") }}</label>
				<div class="relative">
					<input
						ref="searchInputRef"
						v-model="searchQuery"
						type="text"
						:placeholder="__('اسم العميل، الجوال، البريد...')"
						class="w-full border border-slate-300 rounded-xl ps-10 pe-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
						@input="onSearchInput"
						@keydown.enter.prevent="selectFirstCustomer"
						@keydown.arrow-down.prevent="navigateCustomers(1)"
						@keydown.arrow-up.prevent="navigateCustomers(-1)"
					/>
					<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<div
						v-if="showResults && searchResults.length > 0"
						class="absolute top-full inset-x-0 z-30 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl max-h-60 overflow-auto"
					>
					<button
						v-for="(c, idx) in searchResults"
						:key="c.name"
						@click="selectCustomer(c)"
						@mouseenter="selectedResultIndex = idx"
						:class="[
								'w-full text-start px-3 py-2 text-sm hover:bg-blue-50 transition-colors border-b border-slate-100 last:border-0',
							idx === selectedResultIndex ? 'bg-blue-50' : ''
						]"
					>
						<div class="flex items-center justify-between gap-2">
							<div class="min-w-0">
								<p class="font-semibold text-slate-900 truncate">{{ c.customer_name }}</p>
								<p class="text-xs text-slate-500 truncate">{{ c.name }}</p>
							</div>
							<div class="text-xs text-slate-400 flex-shrink-0 text-end">
								<span v-if="c.mobile_no">{{ c.mobile_no }}</span>
							</div>
						</div>
						</button>
					</div>
					<div
						v-else-if="showResults && searchQuery.trim() && !searching && searchResults.length === 0"
						class="absolute top-full inset-x-0 z-30 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl p-3 text-sm text-slate-500"
					>
						{{ __("لا توجد نتائج") }}
					</div>
				</div>
			</section>

			<!-- Payment Area -->
			<section v-if="selectedCustomer" class="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-4 sm:p-5 shadow-md">
				<div class="flex items-center justify-between mb-4 gap-3">
					<div class="min-w-0 flex items-center gap-3">
						<div class="w-11 h-11 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/30">
							<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
						</div>
						<div class="min-w-0">
							<p class="text-sm font-bold text-slate-800 truncate">{{ selectedCustomer.customer_name || selectedCustomer.name }}</p>
							<p v-if="selectedCustomer.mobile_no" class="text-xs text-slate-500">{{ selectedCustomer.mobile_no }}</p>
						</div>
					</div>
					<div class="text-end flex-shrink-0 bg-white/70 rounded-xl px-3 py-2 border border-amber-200">
						<p class="text-xs text-slate-600 font-medium">{{ __("رصيد الحساب") }}</p>
						<p v-if="loading" class="text-xs text-slate-400">{{ __("جاري التحميل...") }}</p>
						<p v-else class="text-lg font-extrabold" :class="accountBalance > 0 ? 'text-red-600' : accountBalance < 0 ? 'text-emerald-600' : 'text-slate-600'">
							{{ formatCurrency(accountBalance) }}
						</p>
					</div>
				</div>

				<div class="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
					<div class="flex-1">
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("المبلغ") }}</label>
						<input
							v-model.number="paymentAmount"
							type="number"
							class="payment-amount-input w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white transition-all"
							:placeholder="__('أدخل المبلغ (سالب = دفع للعميل)')"
							step="0.01"
							@keyup.enter="executePayment"
						/>
					</div>
					<button
						@click="executePayment"
						:disabled="paying || !paymentAmount || paymentAmount === 0"
						:class="[
							'px-5 py-2.5 rounded-xl text-sm font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2 whitespace-nowrap',
							paymentAmount < 0
								? 'bg-gradient-to-l from-rose-600 to-red-600 hover:from-rose-700 hover:to-red-700 shadow-rose-500/30'
								: 'bg-gradient-to-l from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 shadow-emerald-500/30'
						]"
					>
						<svg v-if="paying" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						{{ paymentAmount < 0 ? __("الدفع للعميل") : __("القبض من العميل") }}
					</button>
				</div>
			</section>

			<!-- Customer Statement (General Ledger) -->
		<section v-if="selectedCustomer" class="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-md">
			<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3">
				<h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
					<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					{{ __("كشف حساب العميل - دفتر الأستاذ العام") }}
				</h4>
				<div class="flex items-center gap-2 flex-wrap">
					<div class="flex items-center gap-1">
						<label class="text-[10px] text-slate-500 font-medium">{{ __("من تاريخ") }}</label>
						<input
							type="date"
							v-model="fromDate"
							@change="loadData"
							class="border border-slate-300 rounded-lg px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition-all"
						/>
					</div>
					<button
						v-if="showLastMonth"
						@click="showLastMonth = false"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-l from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md shadow-blue-500/30"
					>{{ __("إظهار الكل") }}</button>
					<button
						v-else
						@click="showLastMonth = true"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all"
					>{{ __("آخر شهر") }}</button>
					<button
						@click="printReport"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all flex items-center gap-1.5"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
						</svg>
						{{ __("طباعة") }}
					</button>
				</div>
			</div>

			<!-- GL Summary Cards -->
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
				<div class="bg-slate-50 rounded-lg p-2 border border-slate-100">
					<p class="text-[10px] text-slate-500 font-medium">{{ __("رصيد افتتاحي") }}</p>
					<p class="text-sm font-bold text-slate-800">{{ formatCurrency(ledger.opening_balance) }}</p>
				</div>
				<div class="bg-blue-50 rounded-lg p-2 border border-blue-100">
					<p class="text-[10px] text-blue-500 font-medium">{{ __("إجمالي مدين") }}</p>
					<p class="text-sm font-bold text-blue-700">{{ formatCurrency(ledger.total_debit) }}</p>
				</div>
				<div class="bg-emerald-50 rounded-lg p-2 border border-emerald-100">
					<p class="text-[10px] text-emerald-500 font-medium">{{ __("إجمالي دائن") }}</p>
					<p class="text-sm font-bold text-emerald-700">{{ formatCurrency(ledger.total_credit) }}</p>
				</div>
				<div class="bg-amber-50 rounded-lg p-2 border border-amber-100">
					<p class="text-[10px] text-amber-500 font-medium">{{ __("رصيد ختامي") }}</p>
					<p class="text-sm font-bold text-amber-700">{{ formatCurrency(ledger.closing_balance) }}</p>
				</div>
			</div>

			<div class="overflow-auto max-h-[400px] rounded-xl border border-slate-100">
				<table v-if="filteredEntries.length" class="min-w-full text-xs">
					<thead class="bg-gradient-to-l from-slate-100 to-blue-50 sticky top-0">
						<tr>
							<th class="px-1 py-2.5 text-center font-bold text-slate-700 w-8"></th>
							<th class="px-2 py-2.5 text-start font-bold text-slate-700">{{ __("التاريخ") }}</th>
							<th class="px-2 py-2.5 text-start font-bold text-slate-700">{{ __("نوع السند") }}</th>
							<th class="px-2 py-2.5 text-start font-bold text-slate-700">{{ __("رقم السند") }}</th>
							<th class="px-2 py-2.5 text-end font-bold text-slate-700">{{ __("مدين") }}</th>
							<th class="px-2 py-2.5 text-end font-bold text-slate-700">{{ __("دائن") }}</th>
							<th class="px-2 py-2.5 text-end font-bold text-slate-700">{{ __("الرصيد") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-slate-100">
						<tr class="bg-slate-50/70 font-semibold">
							<td colspan="4" class="px-2 py-2 text-slate-700">{{ __("رصيد افتتاحي") }}</td>
							<td colspan="2" class="px-2 py-2"></td>
							<td class="px-2 py-2 text-end font-bold text-slate-800">{{ formatCurrency(ledger.opening_balance) }}</td>
						</tr>
						<template v-for="e in filteredEntries" :key="e.gl_entry">
							<tr class="hover:bg-blue-50/50 transition-colors">
								<td class="px-1 py-2 text-center">
									<button
										v-if="isInvoice(e.voucher_type)"
										@click="toggleExpand(e)"
										class="p-1 rounded-md hover:bg-slate-200 transition-all"
										:aria-label="__('تفاصيل')"
									>
										<svg class="w-3.5 h-3.5 text-slate-500 transition-transform" :class="expandedRows[e.voucher_no] ? 'rotate-90' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
										</svg>
									</button>
								</td>
								<td class="px-2 py-2 text-slate-600 whitespace-nowrap">{{ formatDate(e.posting_date) }}</td>
								<td class="px-2 py-2 text-slate-700">{{ formatVoucherType(e.voucher_type) }}</td>
								<td class="px-2 py-2 font-semibold text-slate-900">
									<a :href="glDocUrl(e)" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">{{ e.voucher_no }}</a>
								</td>
								<td class="px-2 py-2 text-end font-semibold text-blue-700">{{ e.debit ? formatCurrency(e.debit) : "" }}</td>
								<td class="px-2 py-2 text-end font-semibold text-emerald-700">{{ e.credit ? formatCurrency(e.credit) : "" }}</td>
								<td class="px-2 py-2 text-end font-bold" :class="e.balance >= 0 ? 'text-slate-800' : 'text-rose-700'">{{ formatCurrency(e.balance) }}</td>
							</tr>
							<tr v-if="expandedRows[e.voucher_no]">
								<td colspan="7" class="px-2 pb-3 pt-1 bg-slate-50/60">
									<div v-if="rowItemsLoading[e.voucher_no]" class="text-center py-3 text-xs text-slate-400">{{ __("جاري تحميل التفاصيل...") }}</div>
									<div v-else-if="rowItems[e.voucher_no] && rowItems[e.voucher_no].length" class="bg-white border border-slate-100 rounded-lg p-2">
										<table class="min-w-full text-[11px]">
											<thead>
												<tr class="text-slate-500 border-b border-slate-100">
													<th class="px-2 py-1 text-start font-semibold">{{ __("الصنف") }}</th>
													<th class="px-2 py-1 text-end font-semibold">{{ __("الكمية") }}</th>
													<th class="px-2 py-1 text-end font-semibold">{{ __("السعر") }}</th>
													<th class="px-2 py-1 text-end font-semibold">{{ __("المبلغ") }}</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-slate-100">
												<tr v-for="item in rowItems[e.voucher_no]" :key="item.name">
													<td class="px-2 py-1 text-start text-slate-700">{{ item.item_name || item.item_code }}</td>
													<td class="px-2 py-1 text-end text-slate-700">{{ item.qty }} {{ item.uom || "" }}</td>
													<td class="px-2 py-1 text-end text-slate-700">{{ formatCurrency(item.rate) }}</td>
													<td class="px-2 py-1 text-end font-semibold text-slate-900">{{ formatCurrency(item.amount) }}</td>
												</tr>
											</tbody>
										</table>
									</div>
									<div v-else class="text-center py-3 text-xs text-slate-400">{{ __("لا توجد أصناف") }}</div>
								</td>
							</tr>
						</template>
						<tr class="bg-slate-100 font-bold border-t-2 border-slate-300">
							<td colspan="4" class="px-2 py-2 text-slate-800">{{ __("الإجمالي") }}</td>
							<td class="px-2 py-2 text-end text-blue-700">{{ formatCurrency(ledger.total_debit) }}</td>
							<td class="px-2 py-2 text-end text-emerald-700">{{ formatCurrency(ledger.total_credit) }}</td>
							<td class="px-2 py-2 text-end text-slate-900">{{ formatCurrency(ledger.closing_balance) }}</td>
						</tr>
					</tbody>
				</table>
				<div v-else class="text-center py-8 text-sm text-slate-400">
					<svg class="w-10 h-10 mx-auto mb-2 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					{{ __("لا توجد حركات") }}
				</div>
			</div>
		</section>

			<!-- Empty State -->
			<div v-if="!selectedCustomer" class="bg-white rounded-2xl border border-slate-200 shadow-md p-12 flex flex-col items-center justify-center gap-3">
				<div class="w-16 h-16 bg-gradient-to-br from-amber-100 to-orange-100 rounded-2xl flex items-center justify-center">
					<svg class="w-8 h-8 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
				</div>
				<p class="text-sm text-slate-500 text-center font-medium">{{ __("اختر عميلاً لعرض تفاصيل الدفع") }}</p>
			</div>
		</main>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { userName } = useUserData()
const { showSuccess, showError } = useToast()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

// State
const companies = ref([])
const selectedCompany = ref("")
const loadingCompanies = ref(false)

const searchQuery = ref("")
const searchResults = ref([])
const showResults = ref(false)
const searching = ref(false)
const selectedResultIndex = ref(-1)
const searchInputRef = ref(null)

const selectedCustomer = ref(null)

const loading = ref(false)
const paying = ref(false)
const paymentAmount = ref(null)
const summary = ref({ outstanding_balance: 0, currency: "" })
const ledger = ref({ opening_balance: 0, closing_balance: 0, total_debit: 0, total_credit: 0, entries: [], currency: "" })
const showLastMonth = ref(true)
	const fromDate = ref("")
const letterhead = ref({ content: "", footer: "" })
const expandedRows = ref({})
const rowItems = ref({})
const rowItemsLoading = ref({})

let searchDebounce = null

// Computed
const accountBalance = computed(() => summary.value.outstanding_balance || 0)

const filteredEntries = computed(() => {
	if (!showLastMonth.value) return ledger.value.entries || []
	const cutoff = new Date()
	cutoff.setDate(cutoff.getDate() - 30)
	cutoff.setHours(0, 0, 0, 0)
	return (ledger.value.entries || []).filter((e) => e.posting_date && new Date(e.posting_date) >= cutoff)
})

// Lifecycle
onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	await loadCompanies()
})

// Methods
async function loadCompanies() {
	loadingCompanies.value = true
	try {
		companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
		if (companies.value.length === 1) {
			selectedCompany.value = companies.value[0].name
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	} finally {
		loadingCompanies.value = false
	}
}

function onCompanyChange() {
	if (selectedCustomer.value) loadData()
}

function onSearchInput() {
	clearTimeout(searchDebounce)
	showResults.value = true
	if (!searchQuery.value.trim()) {
		searchResults.value = []
		showResults.value = false
		return
	}
	searchDebounce = setTimeout(() => doSearch(), 300)
}

async function doSearch() {
	if (!searchQuery.value.trim()) return
	searching.value = true
	try {
		searchResults.value = await call("bs.baron_servies.api.customers.get_customers", {
			search_term: searchQuery.value.trim(),
			limit: 30,
		}) || []
		selectedResultIndex.value = searchResults.value.length > 0 ? 0 : -1
	} catch (e) {
		searchResults.value = []
	} finally {
		searching.value = false
	}
}

function navigateCustomers(delta) {
	if (searchResults.value.length === 0) return
	let next = selectedResultIndex.value + delta
	if (next < 0) next = searchResults.value.length - 1
	if (next >= searchResults.value.length) next = 0
	selectedResultIndex.value = next
}

async function selectFirstCustomer() {
	if (searchResults.value.length === 0 && searchQuery.value.trim()) {
		clearTimeout(searchDebounce)
		await doSearch()
		if (searchResults.value.length === 0) return
	}
	if (searchResults.value.length === 0) return
	const idx = selectedResultIndex.value >= 0 ? selectedResultIndex.value : 0
	selectCustomer(searchResults.value[idx])
}

function selectCustomer(c) {
	selectedCustomer.value = c
	searchQuery.value = c.customer_name
	showResults.value = false
	paymentAmount.value = null
	loadData()
}

async function loadData() {
	const cust = selectedCustomer.value?.name || selectedCustomer.value
	if (!cust || !selectedCompany.value) return
	loading.value = true
	try {
		const [sumResult, ledgerResult, lhResult] = await Promise.all([
			call("bs.baron_servies.api.customer_payment.get_customer_financial_summary", { customer: cust, company: selectedCompany.value }),
			call("bs.baron_servies.api.ledger_report.get_party_ledger", { party_type: "Customer", party: cust, company: selectedCompany.value, from_date: fromDate.value || undefined, limit: 1000 }),
			call("bs.baron_servies.api.utilities.get_company_letterhead", { company: selectedCompany.value }),
		])
		summary.value = sumResult || { outstanding_balance: 0, currency: "" }
		ledger.value = ledgerResult || { opening_balance: 0, closing_balance: 0, total_debit: 0, total_credit: 0, entries: [], currency: summary.value.currency || "" }
		if (!ledger.value.currency && summary.value.currency) ledger.value.currency = summary.value.currency
		letterhead.value = lhResult || { content: "", footer: "" }
	} catch (e) {
		showError(e?.message || __("فشل تحميل البيانات"))
	} finally {
		loading.value = false
	}
}

async function executePayment() {
	const cust = selectedCustomer.value?.name || selectedCustomer.value
	if (!cust || !selectedCompany.value || !paymentAmount.value || paymentAmount.value === 0) return
	paying.value = true
	try {
		const result = await call("bs.baron_servies.api.customer_payment.create_customer_payment", {
			customer: cust,
			company: selectedCompany.value,
			amount: Math.abs(paymentAmount.value),
			mode_of_payment: "Cash",
			payment_type: paymentAmount.value < 0 ? "Pay" : "Receive",
		})
		showSuccess(__("تم إنشاء الدفع {0} بنجاح", [result.payment_entry]))
		paymentAmount.value = null
		await loadData()
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الدفع"))
	} finally {
		paying.value = false
	}
}

function isInvoice(voucher_type) {
	return voucher_type === "Sales Invoice" || voucher_type === "Purchase Invoice"
}

async function toggleExpand(e) {
	const no = e.voucher_no
	if (!no) return
	if (expandedRows.value[no]) {
		expandedRows.value = { ...expandedRows.value, [no]: false }
		return
	}
	expandedRows.value = { ...expandedRows.value, [no]: true }
	if (rowItems.value[no]) return
	rowItemsLoading.value = { ...rowItemsLoading.value, [no]: true }
	try {
		const items = await call("bs.baron_servies.api.ledger_report.get_voucher_items", {
			voucher_type: e.voucher_type,
			voucher_no: no,
		})
		rowItems.value = { ...rowItems.value, [no]: Array.isArray(items) ? items : [] }
	} catch (err) {
		rowItems.value = { ...rowItems.value, [no]: [] }
	} finally {
		rowItemsLoading.value = { ...rowItemsLoading.value, [no]: false }
	}
}

function goBack() {
	router.push({ name: "Home" })
}

async function logout() {
	await session.logout.submit()
}

// Formatters
function formatCurrency(value) {
	const n = Number(value || 0)
	const cur = summary.value.currency || ""
	return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + (cur ? " " + cur : "")
}

function formatDate(date) {
	if (!date) return "-"
	return new Date(date).toLocaleDateString("en-GB")
}

function formatVoucherType(voucher_type) {
	const map = {
		"Sales Invoice": __("فاتورة مبيعات"),
		"Purchase Invoice": __("فاتورة مشتريات"),
		"Payment Entry": __("دفعة"),
		"Journal Entry": __("قيد يومية"),
	}
	return map[voucher_type] || voucher_type || ""
}

function glDocUrl(e) {
	const t = e.voucher_type
	const n = encodeURIComponent(e.voucher_no || "")
	if (t === "Sales Invoice") return `/app/sales-invoice/${n}`
	if (t === "Purchase Invoice") return `/app/purchase-invoice/${n}`
	if (t === "Payment Entry") return `/app/payment-entry/${n}`
	if (t === "Journal Entry") return `/app/journal-entry/${n}`
	return `/app/${n}`
}

function printReport() {
	const w = window.open("", "_blank", "width=1000,height=750")
	if (!w) return
	const customerName = selectedCustomer.value?.customer_name || selectedCustomer.value?.name || ""
	const cur = ledger.value.currency || summary.value.currency || ""
	const opening = formatCurrency(ledger.value.opening_balance)
	const closing = formatCurrency(ledger.value.closing_balance)
	const totDebit = formatCurrency(ledger.value.total_debit)
	const totCredit = formatCurrency(ledger.value.total_credit)

	const bodyRows = filteredEntries.value.map((e) => {
		return "<tr>" +
			"<td>" + formatDate(e.posting_date) + "</td>" +
			"<td>" + (formatVoucherType(e.voucher_type)) + "</td>" +
			"<td>" + (e.voucher_no || "") + "</td>" +
			'<td class="num debit">' + (e.debit ? formatCurrency(e.debit) : "") + "</td>" +
			'<td class="num credit">' + (e.credit ? formatCurrency(e.credit) : "") + "</td>" +
			'<td class="num bal">' + formatCurrency(e.balance) + "</td>" +
		"</tr>"
	}).join("")

	const html = `<!DOCTYPE html>
<html dir=rtl>
<head>
<meta charset=UTF-8>
<title>${__("كشف حساب العميل - دفتر الأستاذ العام")}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Tahoma', 'Arial', sans-serif; margin: 0; padding: 24px; background: #fff; color: #333; }
  .header { text-align: center; margin-bottom: 16px; border-bottom: 2px solid #2563eb; padding-bottom: 12px; }
  .header h2 { margin: 0 0 6px; color: #1e40af; font-size: 22px; }
  .header .meta { margin: 0; color: #666; font-size: 13px; }
  .summary { display: flex; justify-content: space-around; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
  .summary .box { flex: 1; min-width: 140px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 10px; text-align: center; }
  .summary .box .lbl { font-size: 11px; color: #6b7280; margin: 0; }
  .summary .box .val { font-size: 15px; font-weight: 700; margin: 2px 0 0; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: right; font-size: 12px; }
  th { background: #f3f4f6; color: #374151; font-weight: 600; }
  td.num, th.num { text-align: left; font-variant-numeric: tabular-nums; }
  td.debit { color: #1e40af; font-weight: 600; }
  td.credit { color: #047857; font-weight: 600; }
  td.bal { font-weight: 700; }
  tr.opening td, tr.totals td { background: #f9fafb; font-weight: 700; }
  .footer { margin-top: 24px; text-align: center; font-size: 12px; color: #9ca3af; }
  .letterhead-top { margin-bottom: 12px; }
  .letterhead-footer { margin-top: 24px; }
</style>
</head>
<body>
<div class='letterhead-top'>${letterhead.value.content}</div>
<div class='header'>
  <h2>${__("كشف حساب العميل - دفتر الأستاذ العام")}</h2>
  <p class='meta'>${customerName} · ${selectedCompany.value} · ${new Date().toLocaleDateString('en-GB')}</p>
</div>
<div class='summary'>
  <div class='box'><p class='lbl'>${__("رصيد افتتاحي")}</p><p class='val'>${opening}</p></div>
  <div class='box'><p class='lbl'>${__("إجمالي مدين")}</p><p class='val' style='color:#1e40af'>${totDebit}</p></div>
  <div class='box'><p class='lbl'>${__("إجمالي دائن")}</p><p class='val' style='color:#047857'>${totCredit}</p></div>
  <div class='box'><p class='lbl'>${__("رصيد ختامي")}</p><p class='val'>${closing}</p></div>
</div>
<table>
  <thead>
    <tr>
      <th>${__("التاريخ")}</th>
      <th>${__("نوع السند")}</th>
      <th>${__("رقم السند")}</th>
      <th class="num">${__("مدين")}</th>
      <th class="num">${__("دائن")}</th>
      <th class="num">${__("الرصيد")}</th>
    </tr>
  </thead>
  <tbody>
    <tr class="opening"><td colspan="4">${__("رصيد افتتاحي")}</td><td colspan="2"></td><td class="num">${opening}</td></tr>
    ${bodyRows}
    <tr class="totals"><td colspan="4">${__("الإجمالي")}</td><td class="num">${totDebit}</td><td class="num">${totCredit}</td><td class="num">${closing}</td></tr>
  </tbody>
</table>
<div class='footer'>${__("كشف حساب العميل - دفتر الأستاذ العام")} · ${cur}</div>
<div class='letterhead-footer'>${letterhead.value.footer}</div>
</body>
</html>`
	w.document.open()
	w.document.write(html)
	w.document.close()
	w.print()
}
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}
</style>
