<template>
	<div class="w-full">
		<main class="flex flex-col gap-5">
			<PageHeader :title="__('دفع المورد')" :subtitle="__('الدفع للمورد أو القبض منه')" />
			<!-- Company Selector -->
			<section class="bs-card p-4">
				<div class="flex flex-col sm:flex-row gap-3 items-end">
					<div class="flex-1 w-full">
						<label class="bs-label">{{ __("الشركة") }}</label>
						<select
							v-model="selectedCompany"
							class="bs-input w-full px-3 py-2.5"
							:disabled="loadingCompanies"
							@change="onCompanyChange"
						>
							<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
							<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
						</select>
					</div>
				</div>
			</section>

			<!-- Supplier Search -->
			<section class="bs-card p-4">
				<label class="bs-label">{{ __("بحث عن مورد") }}</label>
				<div class="relative">
					<input
						ref="searchInputRef"
						v-model="searchQuery"
						type="text"
						:placeholder="__('اسم المورد، الجوال، البريد...')"
						class="bs-input w-full ps-10 pe-3 py-2.5"
						@input="onSearchInput"
						@keydown.enter.prevent="selectFirstSupplier"
						@keydown.arrow-down.prevent="navigateSuppliers(1)"
						@keydown.arrow-up.prevent="navigateSuppliers(-1)"
					/>
					<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<div
						v-if="showResults && searchResults.length > 0"
						class="bs-popover absolute top-full inset-x-0 z-30 mt-1 rounded-xl max-h-60 overflow-auto"
					>
					<button
						v-for="(s, idx) in searchResults"
						:key="s.name"
						@click="selectSupplier(s)"
						@mouseenter="selectedResultIndex = idx"
						:class="[
								'w-full text-start px-3 py-2 text-sm hover:bg-purple-50 transition-colors border-b border-slate-100 last:border-0',
							idx === selectedResultIndex ? 'bg-purple-50' : ''
						]"
					>
						<div class="flex items-center justify-between gap-2">
							<div class="min-w-0">
								<p class="font-semibold text-slate-900 truncate">{{ s.supplier_name }}</p>
								<p class="text-xs text-slate-500 truncate">{{ s.name }}</p>
							</div>
							<div class="text-xs text-slate-400 flex-shrink-0 text-end">
								<span v-if="s.mobile_no">{{ s.mobile_no }}</span>
							</div>
						</div>
						</button>
					</div>
					<div
						v-else-if="showResults && searchQuery.trim() && !searching && searchResults.length === 0"
						class="bs-popover absolute top-full inset-x-0 z-30 mt-1 rounded-xl p-3 text-sm text-slate-500"
					>
						{{ __("لا توجد نتائج") }}
					</div>
				</div>
			</section>

			<!-- Payment Area -->
			<section v-if="selectedSupplier" class="border border-purple-200 rounded-2xl p-4 sm:p-5 shadow-sm bg-purple-50/60">
				<div class="flex items-center justify-between mb-4 gap-3">
					<div class="min-w-0 flex items-center gap-3">
						<div class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 bg-purple-600 shadow-sm">
							<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
							</svg>
						</div>
						<div class="min-w-0">
							<p class="text-sm font-bold text-slate-800 truncate">{{ selectedSupplier.supplier_name || selectedSupplier.name }}</p>
							<p v-if="selectedSupplier.mobile_no" class="text-xs text-slate-500">{{ selectedSupplier.mobile_no }}</p>
						</div>
					</div>
					<div class="text-end flex-shrink-0 bg-white/70 rounded-xl px-3 py-2 border border-purple-200">
						<p class="text-xs text-slate-600 font-medium">{{ __("رصيد الحساب") }}</p>
						<p v-if="loading" class="text-xs text-slate-400">{{ __("جاري التحميل...") }}</p>
						<p v-else class="text-lg font-extrabold" :class="accountBalance > 0 ? 'text-red-600' : accountBalance < 0 ? 'text-emerald-600' : 'text-slate-600'">
							{{ formatCurrency(accountBalance) }}
						</p>
					</div>
				</div>

				<div class="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
					<div class="flex-1">
						<label class="bs-label">{{ __("المبلغ") }}</label>
						<input
							v-model.number="paymentAmount"
							type="number"
							class="bs-input payment-amount-input w-full px-3 py-2.5"
							:placeholder="__('أدخل المبلغ (سالب = قبض من المورد)')"
							step="0.01"
							@keyup.enter="executePayment"
						/>
					</div>
					<button
						@click="executePayment"
						:disabled="paying || !paymentAmount || paymentAmount === 0"
						:class="[
							'px-5 py-2.5 rounded-xl text-sm font-bold text-white shadow-sm transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap',
							paymentAmount < 0
								? 'bg-rose-600 hover:bg-rose-700 shadow-sm'
								: 'bg-purple-600 hover:bg-purple-700 shadow-sm'
						]"
					>
						<svg v-if="paying" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						{{ paymentAmount < 0 ? __("القبض من المورد") : __("الدفع للمورد") }}
					</button>
				</div>
			</section>

			<!-- Supplier Statement (General Ledger) -->
		<section v-if="selectedSupplier" class="bs-card p-4 sm:p-5">
			<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3">
				<h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
					<svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					{{ __("كشف حساب المورد - دفتر الأستاذ العام") }}
				</h4>
				<div class="flex items-center gap-2 flex-wrap">
					<div class="flex items-center gap-1">
						<label class="text-[10px] text-slate-500 font-medium">{{ __("من تاريخ") }}</label>
						<input
							type="date"
							v-model="fromDate"
							@change="loadData"
							class="bs-input bs-input-sm px-2 py-1 text-xs"
						/>
					</div>
					<button
						v-if="showLastMonth"
						@click="toggleDateRange"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all bg-purple-600 hover:bg-purple-700 shadow-sm"
					>{{ __("إظهار الكل") }}</button>
					<button
						v-else
						@click="toggleDateRange"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all"
					>{{ __("آخر شهر") }}</button>
					<button
						@click="printReport"
						class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all flex items-center gap-1.5"
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
					<thead class="sticky top-0 bg-slate-50/60">
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
							<tr class="hover:bg-purple-50/50 transition-colors">
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
								<td class="px-2 py-2 text-slate-700">{{ formatVoucherType(e.voucher_type, e.voucher_subtype) }}</td>
								<td class="px-2 py-2 font-semibold text-slate-900">
									<a :href="glDocUrl(e)" target="_blank" class="text-purple-600 hover:text-purple-800 hover:underline">{{ e.voucher_no }}</a>
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
						<tr class="bg-slate-100 font-bold border-t-2 border-slate-200">
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
			<div v-if="!selectedSupplier" class="bs-card p-12 flex flex-col items-center justify-center gap-3">
				<div class="w-16 h-16 rounded-2xl flex items-center justify-center bg-purple-50/60">
					<svg class="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
				</div>
				<p class="text-sm text-slate-500 text-center font-medium">{{ __("اختر موردًا لعرض تفاصيل الدفع") }}</p>
			</div>
		</main>
	</div>
</template>

<script setup>
import PageHeader from "@/components/ui/PageHeader.vue"
import { Button } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { showSuccess, showError } = useToast()


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

const selectedSupplier = ref(null)

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
	fromDate.value = getDefaultFromDate()
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
	if (selectedSupplier.value) loadData()
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
		searchResults.value = await call("bs.baron_servies.api.supplier.get_suppliers", {
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

function navigateSuppliers(delta) {
	if (searchResults.value.length === 0) return
	let next = selectedResultIndex.value + delta
	if (next < 0) next = searchResults.value.length - 1
	if (next >= searchResults.value.length) next = 0
	selectedResultIndex.value = next
}

async function selectFirstSupplier() {
	if (searchResults.value.length === 0 && searchQuery.value.trim()) {
		clearTimeout(searchDebounce)
		await doSearch()
		if (searchResults.value.length === 0) return
	}
	if (searchResults.value.length === 0) return
	const idx = selectedResultIndex.value >= 0 ? selectedResultIndex.value : 0
	selectSupplier(searchResults.value[idx])
}

function selectSupplier(s) {
	selectedSupplier.value = s
	searchQuery.value = s.supplier_name
	showResults.value = false
	paymentAmount.value = null
	loadData()
}

async function loadData(opts = {}) {
	const sup = selectedSupplier.value?.name || selectedSupplier.value
	if (!sup || !selectedCompany.value) return
	loading.value = true
	try {
		const calls = []
		if (!opts.skipSummary) {
			calls.push(call("bs.baron_servies.api.supplier.get_supplier_financial_summary", { supplier: sup, company: selectedCompany.value }))
		}
		calls.push(call("bs.baron_servies.api.ledger_report.get_party_ledger", { party_type: "Supplier", party: sup, company: selectedCompany.value, from_date: fromDate.value || undefined, limit: 1000 }))
		calls.push(call("bs.baron_servies.api.utilities.get_company_letterhead", { company: selectedCompany.value }))

		const results = await Promise.all(calls)
		let sumResult, ledgerResult, lhResult
		if (opts.skipSummary) {
			[ledgerResult, lhResult] = results
		} else {
			[sumResult, ledgerResult, lhResult] = results
			summary.value = sumResult || { outstanding_balance: 0, currency: "" }
		}
		ledger.value = ledgerResult || { opening_balance: 0, closing_balance: 0, total_debit: 0, total_credit: 0, entries: [], currency: summary.value.currency || "" }
		if (!ledger.value.currency && summary.value.currency) ledger.value.currency = summary.value.currency
		letterhead.value = lhResult || { content: "", footer: "" }
		expandAllInvoices()
	} catch (e) {
		showError(e?.message || __("فشل تحميل البيانات"))
	} finally {
		loading.value = false
	}
}

async function executePayment() {
	const sup = selectedSupplier.value?.name || selectedSupplier.value
	if (!sup || !selectedCompany.value || !paymentAmount.value || paymentAmount.value === 0) return
	paying.value = true
	try {
		const result = await call("bs.baron_servies.api.supplier.create_supplier_payment", {
			supplier: sup,
			company: selectedCompany.value,
			amount: Math.abs(paymentAmount.value),
			mode_of_payment: "Cash",
			payment_type: paymentAmount.value < 0 ? "Receive" : "Pay",
		})
		showSuccess(__("تم إنشاء الدفع {0} بنجاح", [result.payment_entry]))
		paymentAmount.value = null
		if (result.updated_summary) summary.value = result.updated_summary
		await loadData({ skipSummary: true })
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الدفع"))
	} finally {
		paying.value = false
	}
}

function isInvoice(voucher_type) {
	return voucher_type === "Sales Invoice" || voucher_type === "Purchase Invoice"
}

// Invoice details are shown by default: open every invoice row and load all items in one call.
async function expandAllInvoices() {
	const invoices = []
	const seen = new Set()
	for (const e of ledger.value.entries || []) {
		if (isInvoice(e.voucher_type) && e.voucher_no && !seen.has(e.voucher_no)) {
			seen.add(e.voucher_no)
			invoices.push({ voucher_type: e.voucher_type, voucher_no: e.voucher_no })
		}
	}
	const expanded = {}
	invoices.forEach((v) => { expanded[v.voucher_no] = true })
	expandedRows.value = expanded

	const missing = invoices.filter((v) => !rowItems.value[v.voucher_no])
	if (!missing.length) return
	const loadingMap = { ...rowItemsLoading.value }
	missing.forEach((v) => { loadingMap[v.voucher_no] = true })
	rowItemsLoading.value = loadingMap
	try {
		const byVoucher = await call("bs.baron_servies.api.ledger_report.get_vouchers_items", {
			vouchers: JSON.stringify(missing),
		}) || {}
		const items = { ...rowItems.value }
		missing.forEach((v) => { items[v.voucher_no] = byVoucher[v.voucher_no] || [] })
		rowItems.value = items
	} catch (err) {
		// rows stay expandable one by one through toggleExpand
		const expandedNow = { ...expandedRows.value }
		missing.forEach((v) => { delete expandedNow[v.voucher_no] })
		expandedRows.value = expandedNow
	} finally {
		const done = { ...rowItemsLoading.value }
		missing.forEach((v) => { done[v.voucher_no] = false })
		rowItemsLoading.value = done
	}
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


// Formatters
function formatCurrency(value) {
	const n = Number(value || 0)
	const cur = summary.value.currency || ""
	return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + (cur ? " " + cur : "")
}

function getDefaultFromDate() {
	const d = new Date()
	d.setDate(d.getDate() - 30)
	d.setHours(0, 0, 0, 0)
	return d.toISOString().split("T")[0]
}

function toggleDateRange() {
	showLastMonth.value = !showLastMonth.value
	fromDate.value = showLastMonth.value ? getDefaultFromDate() : ""
	if (selectedSupplier.value) loadData()
}

function formatDate(date) {
	if (!date) return "-"
	return new Date(date).toLocaleDateString("en-GB")
}

// The ledger sends voucher_subtype (Receive / Pay / Credit Note / Debit Note …) so a receipt
// is not labelled as a payment and returns are distinguishable from invoices.
function formatVoucherType(voucher_type, voucher_subtype) {
	const bySubtype = {
		"Payment Entry|Receive": __("قبض"),
		"Payment Entry|Pay": __("دفع"),
		"Payment Entry|Internal Transfer": __("تحويل داخلي"),
		"Sales Invoice|Credit Note": __("مرتجع مبيعات"),
		"Purchase Invoice|Debit Note": __("مرتجع مشتريات"),
	}
	const map = {
		"Sales Invoice": __("فاتورة مبيعات"),
		"Purchase Invoice": __("فاتورة مشتريات"),
		"Payment Entry": __("دفعة"),
		"Journal Entry": __("قيد يومية"),
	}
	return bySubtype[`${voucher_type}|${voucher_subtype}`] || map[voucher_type] || voucher_type || ""
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

// Printed statements include the invoice items that are expanded on screen.
function escapeHtml(value) {
	return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]))
}

function printItemsRow(e) {
	if (!isInvoice(e.voucher_type) || !expandedRows.value[e.voucher_no]) return ""
	const items = rowItems.value[e.voucher_no] || []
	if (!items.length) return ""
	const rows = items.map((it) =>
		"<tr>" +
			"<td>" + escapeHtml(it.item_name || it.item_code) + "</td>" +
			'<td class="num">' + escapeHtml(it.qty) + " " + escapeHtml(it.uom || "") + "</td>" +
			'<td class="num">' + formatCurrency(it.rate) + "</td>" +
			'<td class="num">' + formatCurrency(it.amount) + "</td>" +
		"</tr>"
	).join("")
	return '<tr class="items"><td colspan="6"><table class="sub"><thead><tr>' +
		"<th>" + __("الصنف") + '</th><th class="num">' + __("الكمية") + '</th><th class="num">' + __("السعر") + '</th><th class="num">' + __("المبلغ") + "</th>" +
		"</tr></thead><tbody>" + rows + "</tbody></table></td></tr>"
}

function printReport() {
	const w = window.open("", "_blank", "width=1000,height=750")
	if (!w) return
	const supplierName = selectedSupplier.value?.supplier_name || selectedSupplier.value?.name || ""
	const cur = ledger.value.currency || summary.value.currency || ""
	const opening = formatCurrency(ledger.value.opening_balance)
	const closing = formatCurrency(ledger.value.closing_balance)
	const totDebit = formatCurrency(ledger.value.total_debit)
	const totCredit = formatCurrency(ledger.value.total_credit)

	const bodyRows = filteredEntries.value.map((e) => {
		return "<tr>" +
			"<td>" + formatDate(e.posting_date) + "</td>" +
			"<td>" + (formatVoucherType(e.voucher_type, e.voucher_subtype)) + "</td>" +
			"<td>" + (e.voucher_no || "") + "</td>" +
			'<td class="num debit">' + (e.debit ? formatCurrency(e.debit) : "") + "</td>" +
			'<td class="num credit">' + (e.credit ? formatCurrency(e.credit) : "") + "</td>" +
			'<td class="num bal">' + formatCurrency(e.balance) + "</td>" +
		"</tr>" + printItemsRow(e)
	}).join("")

	const html = `<!DOCTYPE html>
<html dir=rtl>
<head>
<meta charset=UTF-8>
<title>${__("كشف حساب المورد - دفتر الأستاذ العام")}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Tahoma', 'Arial', sans-serif; margin: 0; padding: 24px; background: #fff; color: #333; }
  .header { text-align: center; margin-bottom: 16px; border-bottom: 2px solid #7c3aed; padding-bottom: 12px; }
  .header h2 { margin: 0 0 6px; color: #6d28d9; font-size: 22px; }
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
  tr.items > td { background: #fafafa; padding: 4px 8px 8px; }
  table.sub { width: 100%; margin: 0; border-collapse: collapse; }
  table.sub th, table.sub td { border: 1px solid #eef0f3; padding: 3px 6px; font-size: 10.5px; color: #4b5563; }
  table.sub th { background: #f3f4f6; font-weight: 600; }
  tr.items { page-break-inside: avoid; }
  tr.opening td, tr.totals td { background: #f9fafb; font-weight: 700; }
  .footer { margin-top: 24px; text-align: center; font-size: 12px; color: #9ca3af; }
  .letterhead-top { margin-bottom: 12px; }
  .letterhead-footer { margin-top: 24px; }
</style>
</head>
<body>
<div class='letterhead-top'>${letterhead.value.content}</div>
<div class='header'>
  <h2>${__("كشف حساب المورد - دفتر الأستاذ العام")}</h2>
  <p class='meta'>${supplierName} · ${selectedCompany.value} · ${new Date().toLocaleDateString('en-GB')}</p>
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
    <tr class="opening"><td colspan="3">${__("رصيد افتتاحي")}</td><td colspan="2"></td><td class="num">${opening}</td></tr>
    ${bodyRows}
    <tr class="totals"><td colspan="3">${__("الإجمالي")}</td><td class="num">${totDebit}</td><td class="num">${totCredit}</td><td class="num">${closing}</td></tr>
  </tbody>
</table>
<div class='footer'>${__("كشف حساب المورد - دفتر الأستاذ العام")} · ${cur}</div>
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
