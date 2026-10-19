<template>
	<div class="w-full">
		<main class="flex flex-col gap-5">
			<PageHeader :title="__('جرد سريع - مخزون أول المدة')" :subtitle="__('إنشاء سجل Stock Reconciliation كمسودة')" />

			<!-- Settings (collapsible) -->
			<section class="bs-card">
				<button
					type="button"
					class="flex w-full items-center justify-between gap-3 px-4 py-3 text-start sm:px-5"
					@click="settingsOpen = !settingsOpen"
				>
					<span class="flex items-center gap-2">
						<svg class="h-4 w-4 text-slate-400 transition-transform" :class="{ 'rotate-90': settingsOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
						<span class="bs-card-title">{{ __("إعدادات الجرد") }}</span>
					</span>
					<span class="truncate text-xs text-slate-500">
						<template v-if="selectedCompany">{{ selectedCompany }}<template v-if="selectedWarehouse"> / {{ selectedWarehouse }}</template></template>
						<template v-else>{{ __("اضغط للإعداد") }}</template>
					</span>
				</button>

				<div v-show="settingsOpen" class="border-t border-slate-100 px-4 pb-4 pt-3 sm:px-5">
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<div>
							<label class="bs-label">{{ __("الشركة") }}</label>
							<select v-model="selectedCompany" class="bs-input" :disabled="loadingCompanies" @change="onCompanyChange">
								<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
							</select>
						</div>
						<div>
							<label class="bs-label">{{ __("المستودع") }}</label>
							<select v-model="selectedWarehouse" class="bs-input" :disabled="!selectedCompany || loadingWarehouses">
								<option value="" disabled>{{ loadingWarehouses ? __("جاري التحميل...") : __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.warehouse_name || w.name }}</option>
							</select>
						</div>
						<div>
							<label class="bs-label">{{ __("تاريخ الترحيل") }}</label>
							<input v-model="postingDate" type="date" class="bs-input" />
						</div>
						<div>
							<label class="bs-label">{{ __("قائمة أسعار احتياطية") }}</label>
							<select v-model="selectedPriceList" class="bs-input" :disabled="loadingPriceLists">
								<option value="">{{ __("بدون") }}</option>
								<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">
									{{ pl.name }}{{ pl.buying ? " (" + __("شراء") + ")" : "" }}
								</option>
							</select>
							<p class="mt-1 text-[11px] text-slate-400">{{ __("يُبحث فيها إذا لم يوجد سعر شراء") }}</p>
						</div>
					</div>
				</div>
			</section>

			<!-- Not configured hint -->
			<section v-if="!selectedCompany || !selectedWarehouse" class="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
				{{ __("اختر شركة ومستودع للبدء") }}
			</section>

			<!-- Work area -->
			<section
				v-if="selectedCompany && selectedWarehouse"
				class="bs-card flex min-h-[400px] flex-1 flex-col"
				@click="refocusSearch($event)"
			>
				<!-- Search -->
				<div class="sticky top-14 z-20 rounded-t-2xl border-b border-slate-100 bg-white p-4 sm:px-5">
					<div class="relative">
						<div class="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-3">
							<svg v-if="!searching" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
							<div v-else class="h-4 w-4 animate-spin rounded-full border-b-2 border-blue-500"></div>
						</div>
						<input
							ref="searchInputRef"
							v-model="searchQuery"
							type="text"
							:placeholder="__('ابحث عن صنف بالاسم أو الكود أو امسح الباركود...')"
							class="bs-input !pe-10 !ps-10"
							autocomplete="off"
							@input="onSearchInput"
							@keydown.enter.prevent="selectFirstResult"
							@keydown.down.prevent="navigateResults(1)"
							@keydown.up.prevent="navigateResults(-1)"
							@keydown.escape="clearSearch"
						/>
						<button v-if="searchQuery" type="button" class="absolute inset-y-0 end-0 flex items-center pe-3" :aria-label="__('مسح')" @click="clearSearch">
							<svg class="h-5 w-5 text-slate-400 hover:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Results -->
					<div v-if="showResults && (searchResults.length > 0 || (searchQuery.length >= 1 && !searching))" class="relative z-30 mt-2">
						<div class="bs-popover max-h-80 overflow-y-auto">
							<template v-if="searchResults.length > 0">
								<button
									v-for="(item, index) in searchResults"
									:key="item.item_code"
									type="button"
									class="flex w-full items-center gap-3 border-b border-slate-100 px-4 py-2.5 text-start transition-colors last:border-0"
									:class="selectedResultIndex === index ? 'bg-blue-50' : 'hover:bg-slate-50'"
									@click="addItem(item)"
									@mouseenter="selectedResultIndex = index"
								>
									<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
										<img v-if="item.image" :src="item.image" :alt="item.item_name" class="h-full w-full object-cover" />
										<svg v-else class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="BOX_ICON" />
										</svg>
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-semibold text-slate-900">{{ item.item_name }}</p>
										<p class="truncate text-[11px] text-slate-400">{{ item.item_code }}</p>
									</div>
									<div class="flex flex-shrink-0 flex-col items-end gap-0.5">
										<span class="bs-badge" :class="(item.actual_qty || 0) > 0 ? 'bs-badge-green' : 'bs-badge-red'">
											{{ formatQty(item.actual_qty) }} {{ item.stock_uom }}
										</span>
										<span v-if="item.has_batch_no || item.has_serial_no" class="text-[10px] text-amber-600">{{ __("باتش/سيريال") }}</span>
									</div>
								</button>
							</template>
							<div v-else class="px-4 py-6 text-center text-sm text-slate-500">{{ __("لا توجد نتائج") }}</div>
						</div>
					</div>
				</div>

				<!-- List header -->
				<div class="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 sm:px-5">
					<h2 class="bs-card-title">
						{{ __("قائمة الجرد") }}
						<span v-if="cart.length > 0" class="ms-2 text-xs font-normal text-slate-400">{{ __("{0} / {1} صنف", [cart.length, MAX_ITEMS]) }}</span>
					</h2>
					<button v-if="cart.length > 0" type="button" class="bs-btn bs-btn-ghost bs-btn-sm !text-rose-600" @click="clearCart">
						{{ __("مسح الكل") }}
					</button>
				</div>

				<!-- Items -->
				<div class="flex-1 overflow-x-auto">
					<div v-if="cart.length === 0" class="bs-empty">
						<svg class="h-12 w-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
						<p>{{ __("ابحث وأضف أصنافاً لبدء الجرد") }}</p>
					</div>

					<table v-else class="bs-table w-full min-w-[720px] table-fixed">
						<colgroup>
							<col class="w-10" />
							<col />
							<col class="w-24" />
							<col class="w-24" />
							<col class="w-32" />
							<col class="w-40" />
							<col class="w-12" />
						</colgroup>
						<thead class="sticky top-0 z-10">
							<tr>
								<th class="text-center">#</th>
								<th class="text-start">{{ __("الصنف") }}</th>
								<th class="text-center">{{ __("الرصيد") }}</th>
								<th class="text-center">{{ __("الوحدة") }}</th>
								<th class="text-center">{{ __("الكمية") }}</th>
								<th class="text-center">{{ __("سعر التقييم") }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="(row, idx) in cart" :key="row.item_code">
								<td class="text-center text-xs tabular-nums text-slate-400">{{ cart.length - idx }}</td>
								<td>
									<div class="flex items-center gap-2.5">
										<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
											<img v-if="row.image" :src="row.image" :alt="row.item_name" class="h-full w-full object-cover" />
											<svg v-else class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="BOX_ICON" />
											</svg>
										</div>
										<div class="min-w-0 flex-1">
											<!-- Name: view / inline edit -->
											<div v-if="editingCode === row.item_code" class="flex items-center gap-1">
												<input
													ref="nameInputRef"
													v-model="editingName"
													type="text"
													maxlength="140"
													class="bs-input bs-input-sm"
													@keydown.enter.prevent="saveName(row)"
													@keydown.escape.prevent="cancelEditName"
												/>
												<button type="button" class="bs-icon-btn !h-8 !w-8 !text-emerald-600 hover:!bg-emerald-50" :title="__('حفظ')" :disabled="savingName" @click="saveName(row)">
													<svg v-if="!savingName" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" /></svg>
													<span v-else class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></span>
												</button>
												<button type="button" class="bs-icon-btn !h-8 !w-8" :title="__('إلغاء')" :disabled="savingName" @click="cancelEditName">
													<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
												</button>
											</div>
											<div v-else class="group flex min-w-0 items-center gap-1">
												<p class="truncate font-semibold text-slate-900" :title="row.item_name">{{ row.item_name }}</p>
												<button
													type="button"
													class="flex-shrink-0 rounded-md p-1 text-slate-400 transition hover:bg-blue-50 hover:text-blue-600"
													:title="__('تعديل اسم الصنف')"
													:aria-label="__('تعديل اسم الصنف')"
													@click="startEditName(row)"
												>
													<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
													</svg>
												</button>
											</div>
											<p class="truncate text-[11px] text-slate-400" dir="ltr" style="text-align: right">{{ row.item_code }}</p>
											<span v-if="row.has_batch_no || row.has_serial_no" class="text-[10px] text-amber-600">{{ __("يتطلب باتش/سيريال - غير مدعوم") }}</span>
										</div>
									</div>
								</td>
								<td class="text-center tabular-nums" :class="(row.actual_qty || 0) > 0 ? 'text-slate-700' : 'text-slate-400'">
									{{ formatQty(row.actual_qty) }}
								</td>
								<td class="text-center">
									<span class="bs-badge bs-badge-neutral">{{ row.stock_uom || "—" }}</span>
								</td>
								<td class="text-center">
									<input
										v-model.number="row.qty"
										type="number"
										min="0"
										step="any"
										class="bs-input bs-input-sm text-center tabular-nums"
										:class="Number(row.qty) > 0 ? '' : '!border-rose-300 !bg-rose-50'"
										@focus="$event.target.select()"
										@click="$event.target.select()"
										@keydown.enter.prevent="focusSearch"
									/>
								</td>
								<td class="text-center">
									<input
										v-model.number="row.valuation_rate"
										type="number"
										min="0"
										step="any"
										class="bs-input bs-input-sm text-center tabular-nums"
										:class="(row.valuation_rate || 0) > 0 ? '' : '!border-rose-300 !bg-rose-50'"
										@focus="$event.target.select()"
										@click="$event.target.select()"
										@keydown.enter.prevent="focusSearch"
									/>
									<p class="mt-0.5 text-[10px] text-slate-400">{{ rateSourceLabel(row) }}</p>
								</td>
								<td class="text-center">
									<button type="button" class="rounded-md p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600" :aria-label="__('حذف')" @click="removeItem(idx)">
										<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
										</svg>
									</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- Footer -->
				<div v-if="cart.length > 0" class="flex flex-col items-stretch justify-between gap-3 rounded-b-2xl border-t border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:px-5">
					<div class="text-xs">
						<p v-if="itemsWithoutPrice > 0" class="text-rose-600">{{ __("{0} صنف بدون سعر تقييم", [itemsWithoutPrice]) }}</p>
						<p v-else-if="cart.length >= MAX_ITEMS" class="text-amber-600">{{ __("بلغت الحد الأقصى ({0} صنف) - احفظ ثم ابدأ جرداً جديداً", [MAX_ITEMS]) }}</p>
						<p v-else class="text-slate-500">{{ __("جميع الأصناف لها سعر تقييم") }}</p>
					</div>
					<div class="flex items-center gap-2">
						<button type="button" class="bs-btn bs-btn-secondary" @click="clearCart">{{ __("مسح") }}</button>
						<button type="button" class="bs-btn bs-btn-primary" :disabled="!canSubmit" @click="handleSubmit">
							<span v-if="submitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
							{{ __("حفظ كمسودة") }}
						</button>
					</div>
				</div>
			</section>
		</main>

		<!-- Success Dialog -->
		<Dialog v-model="showSuccessDialog" :options="{ title: __('تم الحفظ'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col items-center gap-3 py-4 text-center">
					<div class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
						<svg class="h-7 w-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-slate-700">{{ __("تم إنشاء سجل جرد مخزون أول المدة بنجاح") }}</p>
					<p class="text-xs text-slate-500">{{ __("رقم السجل: {0}", [lastCreatedName]) }}</p>
				</div>
			</template>
			<template #actions>
				<div class="flex w-full gap-2">
					<button type="button" class="bs-btn bs-btn-secondary flex-1" @click="showSuccessDialog = false">{{ __("البقاء هنا") }}</button>
					<a :href="lastCreatedUrl" target="_blank" class="bs-btn bs-btn-primary flex-1">{{ __("فتح في Desk") }}</a>
					<button type="button" class="bs-btn bs-btn-success flex-1" @click="resetAfterSave">{{ __("جرد جديد") }}</button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import PageHeader from "@/components/ui/PageHeader.vue"
import { Dialog } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { session } from "@/data/session"
import router from "@/router"
import { computed, nextTick, onMounted, ref } from "vue"

const { showSuccess, showError } = useToast()


const MAX_ITEMS = 50
const BOX_ICON = "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"

const RATE_SOURCES = {
	last_purchase_rate: "آخر سعر شراء",
	buying_price_list: "قائمة أسعار الشراء",
	fallback_price_list: "قائمة احتياطية",
}

function rateSourceLabel(row) {
	if (RATE_SOURCES[row.valuation_rate_source]) return __(RATE_SOURCES[row.valuation_rate_source])
	return (row.valuation_rate || 0) > 0 ? __("يدوي") : __("أدخل السعر")
}

// Inline item-name editing (pencil next to the name)
const editingCode = ref("")
const editingName = ref("")
const savingName = ref(false)
const nameInputRef = ref(null)

async function startEditName(row) {
	editingCode.value = row.item_code
	editingName.value = row.item_name
	await nextTick()
	const el = Array.isArray(nameInputRef.value) ? nameInputRef.value[0] : nameInputRef.value
	el?.focus()
	el?.select()
}

function cancelEditName() {
	editingCode.value = ""
	editingName.value = ""
	focusSearch()
}

async function saveName(row) {
	const name = editingName.value.trim()
	if (!name) return showError(__("اسم الصنف مطلوب"))
	if (name === row.item_name) return cancelEditName()
	savingName.value = true
	try {
		const res = await call("bs.baron_servies.api.stock_reconciliation.update_item_name", {
			item_code: row.item_code,
			item_name: name,
		})
		row.item_name = res.item_name
		showSuccess(__("تم تعديل اسم الصنف"))
		cancelEditName()
	} catch (e) {
		showError(e?.message || __("فشل تعديل اسم الصنف"))
	} finally {
		savingName.value = false
	}
}

// State
const companies = ref([])
const warehouses = ref([])
const priceLists = ref([])
const selectedCompany = ref("")
const selectedWarehouse = ref("")
const selectedPriceList = ref("")
const postingDate = ref(new Date().toISOString().split("T")[0])
const settingsOpen = ref(false)

const loadingCompanies = ref(false)
const loadingWarehouses = ref(false)
const loadingPriceLists = ref(false)

const searchQuery = ref("")
const searchResults = ref([])
const showResults = ref(false)
const searching = ref(false)
const selectedResultIndex = ref(-1)
const searchInputRef = ref(null)

const cart = ref([])
const submitting = ref(false)

const showSuccessDialog = ref(false)
const lastCreatedName = ref("")
const lastCreatedUrl = ref("")

let searchDebounce = null

// Computed
const itemsWithoutPrice = computed(() =>
	cart.value.filter(r => !r.valuation_rate || Number(r.valuation_rate) <= 0).length
)

const canSubmit = computed(() =>
	!submitting.value &&
	cart.value.length > 0 &&
	itemsWithoutPrice.value === 0 &&
	cart.value.every(r => Number(r.qty) > 0) &&
	selectedCompany.value &&
	selectedWarehouse.value &&
	postingDate.value
)

// Lifecycle
onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	await Promise.all([loadCompanies(), loadPriceLists()])
})

// Methods
async function loadCompanies() {
	loadingCompanies.value = true
	try {
		companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
		if (companies.value.length === 1) {
			selectedCompany.value = companies.value[0].name
			await onCompanyChange()
		} else if (companies.value.length > 1) {
			// Open settings to let user choose
			settingsOpen.value = true
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	} finally {
		loadingCompanies.value = false
	}
}

async function loadPriceLists() {
	loadingPriceLists.value = true
	try {
		priceLists.value = await call("bs.baron_servies.api.stock_reconciliation.get_price_lists") || []
	} catch (e) {
		priceLists.value = []
	} finally {
		loadingPriceLists.value = false
	}
}

async function onCompanyChange() {
	selectedWarehouse.value = ""
	warehouses.value = []
	cart.value = []
	clearSearch()
	if (!selectedCompany.value) return

	loadingWarehouses.value = true
	try {
		warehouses.value = await call("bs.baron_servies.api.stock_reconciliation.get_warehouses", {
			company: selectedCompany.value,
		}) || []
		if (warehouses.value.length === 1) {
			selectedWarehouse.value = warehouses.value[0].name
			// Collapse settings once configured
			settingsOpen.value = false
			focusSearch()
		} else if (warehouses.value.length > 1) {
			settingsOpen.value = true
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل المستودعات"))
	} finally {
		loadingWarehouses.value = false
	}
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
	if (!searchQuery.value.trim() || !selectedCompany.value || !selectedWarehouse.value) return
	searching.value = true
	try {
		searchResults.value = await call("bs.baron_servies.api.stock_reconciliation.search_items_for_reconciliation", {
			search_term: searchQuery.value.trim(),
			company: selectedCompany.value,
			warehouse: selectedWarehouse.value,
			limit: 20,
			price_list: selectedPriceList.value || undefined,
		}) || []
		// If the search term is an exact barcode match, the backend returns exactly
		// one item — auto-add it to the cart (like a barcode scanner).
		if (searchResults.value.length === 1) {
			const term = searchQuery.value.trim()
			const item = searchResults.value[0]
			if (term === item.item_code || (!term.includes(" ") && term.length <= 32)) {
				addItem(item)
				return
			}
		}
		selectedResultIndex.value = searchResults.value.length > 0 ? 0 : -1
	} catch (e) {
		showError(e?.message || __("فشل البحث"))
		searchResults.value = []
	} finally {
		searching.value = false
	}
}

function clearSearch() {
	searchQuery.value = ""
	searchResults.value = []
	showResults.value = false
	selectedResultIndex.value = -1
}

function navigateResults(delta) {
	if (searchResults.value.length === 0) return
	let next = selectedResultIndex.value + delta
	if (next < 0) next = searchResults.value.length - 1
	if (next >= searchResults.value.length) next = 0
	selectedResultIndex.value = next
}

async function selectFirstResult() {
	if (searchResults.value.length === 0 && searchQuery.value.trim()) {
		clearTimeout(searchDebounce)
		await doSearch()
		if (searchResults.value.length === 0) return
	}
	if (searchResults.value.length === 0) return
	const idx = selectedResultIndex.value >= 0 ? selectedResultIndex.value : 0
	addItem(searchResults.value[idx])
}

function addItem(item) {
	if (!item) return
	// Batch/serial items not supported in Phase 1
	if (item.has_batch_no || item.has_serial_no) {
		showError(__("الصنف {0} يتطلب باتش/سيريال وهو غير مدعوم في هذه المرحلة", [item.item_name]))
		return
	}
	// 50 item limit
	if (cart.value.length >= MAX_ITEMS) {
		showError(__("بلغت الحد الأقصى ({0} صنف). احفظ السجل الحالي ثم ابدأ جرداً جديداً.", [MAX_ITEMS]))
		return
	}
	if (cart.value.some(r => r.item_code === item.item_code)) {
		showError(__("الصنف موجود مسبقاً في القائمة"))
		return
	}
	cart.value.unshift({
		item_code: item.item_code,
		item_name: item.item_name,
		stock_uom: item.stock_uom,
		image: item.image,
		actual_qty: item.actual_qty || 0,
		last_purchase_rate: item.last_purchase_rate || 0,
		valuation_rate: item.valuation_rate,
		valuation_rate_source: item.valuation_rate_source,
		has_price: !!item.has_price,
		has_batch_no: item.has_batch_no,
		has_serial_no: item.has_serial_no,
		qty: 1,
	})
	clearSearch()
	focusSearch()
}

function removeItem(idx) {
	cart.value.splice(idx, 1)
}

function clearCart() {
	cart.value = []
}

function focusSearch() {
	setTimeout(() => searchInputRef.value?.focus(), 0)
}

function refocusSearch(e) {
	// Only refocus if the click was NOT on an input, select, or button
	// clicks inside controls (incl. icons inside buttons) keep their own focus
	if (editingCode.value || e.target?.closest?.("input, select, textarea, button, a")) return
	focusSearch()
}

function formatQty(v) {
	const n = Number(v || 0)
	return Number.isInteger(n) ? String(n) : n.toFixed(3).replace(/\.?0+$/, "")
}

async function handleSubmit() {
	if (!canSubmit.value) return
	submitting.value = true
	try {
		// Send item_code + qty + valuation_rate (user may have edited the rate)
		const payload = cart.value.map(r => ({
			item_code: r.item_code,
			qty: Number(r.qty),
			valuation_rate: Number(r.valuation_rate) > 0 ? Number(r.valuation_rate) : undefined,
		}))
		const result = await call("bs.baron_servies.api.stock_reconciliation.create_opening_stock_reconciliation", {
			company: selectedCompany.value,
			warehouse: selectedWarehouse.value,
			posting_date: postingDate.value,
			items: payload,
			price_list: selectedPriceList.value || undefined,
		})
		lastCreatedName.value = result.name
		lastCreatedUrl.value = result.url
		showSuccessDialog.value = true
		showSuccess(__("تم حفظ السجل {0}", [result.name]))
	} catch (e) {
		const msg = e?.message || e?.toString() || __("فشل حفظ السجل")
		showError(msg)
	} finally {
		submitting.value = false
	}
}

function resetAfterSave() {
	showSuccessDialog.value = false
	cart.value = []
	lastCreatedName.value = ""
	lastCreatedUrl.value = ""
	focusSearch()
}

</script>

<style scoped>
/* Hide number input spinners (up/down arrows) */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}
input[type="number"] {
	-moz-appearance: textfield;
}
</style>
