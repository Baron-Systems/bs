<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">
							{{ __("جرد سريع - مخزون أول المدة") }}
						</h1>
						<p class="text-xs text-slate-500 truncate">
							{{ __("إنشاء سجل Stock Reconciliation كمسودة") }}
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
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col gap-4">
			<!-- Settings Bar (Collapsible) -->
			<section class="bg-white rounded-lg border border-gray-200 shadow-sm">
				<!-- Toggle Header -->
				<button
					@click="settingsOpen = !settingsOpen"
					class="w-full px-4 py-3 flex items-center justify-between text-start hover:bg-gray-50 transition-colors rounded-lg"
				>
					<div class="flex items-center gap-2">
						<svg
							class="w-4 h-4 text-gray-500 transition-transform"
							:class="{ 'rotate-90': settingsOpen }"
							fill="none" stroke="currentColor" viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
						<span class="text-sm font-semibold text-gray-900">{{ __("إعدادات الجرد") }}</span>
					</div>
					<div class="text-xs text-gray-500 truncate">
						<span v-if="selectedCompany">{{ selectedCompany }}</span>
						<span v-if="selectedWarehouse"> / {{ selectedWarehouse }}</span>
						<span v-if="!selectedCompany">{{ __("اضغط للإعداد") }}</span>
					</div>
				</button>

				<!-- Collapsible Content -->
				<div v-show="settingsOpen" class="px-4 pb-4 pt-2 border-t border-gray-100">
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
						<!-- Company -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("الشركة") }}</label>
							<select
								v-model="selectedCompany"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
								:disabled="loadingCompanies"
								@change="onCompanyChange"
							>
								<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">
									{{ c.name }}
								</option>
							</select>
						</div>

						<!-- Warehouse -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("المستودع") }}</label>
							<select
								v-model="selectedWarehouse"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
								:disabled="!selectedCompany || loadingWarehouses"
							>
								<option value="" disabled>{{ loadingWarehouses ? __("جاري التحميل...") : __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">
									{{ w.warehouse_name || w.name }}
								</option>
							</select>
						</div>

						<!-- Posting Date -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("تاريخ الترحيل") }}</label>
							<input
								v-model="postingDate"
								type="date"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							/>
						</div>

						<!-- Fallback Price List -->
						<div class="flex flex-col gap-1">
							<label class="text-xs font-medium text-gray-700">{{ __("قائمة أسعار احتياطية") }}</label>
							<select
								v-model="selectedPriceList"
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
								:disabled="loadingPriceLists"
							>
								<option value="">{{ __("بدون") }}</option>
								<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">
									{{ pl.name }}{{ pl.buying ? ' (' + __('شراء') + ')' : '' }}
								</option>
							</select>
							<p class="text-[10px] text-gray-400">{{ __("يُبحث فيها إذا لم يوجد سعر شراء") }}</p>
						</div>
					</div>
				</div>
			</section>

			<!-- Not configured hint -->
			<section v-if="!selectedCompany || !selectedWarehouse" class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
				{{ __("اختر شركة ومستودع للبدء") }}
			</section>

			<!-- Work Area: Search (sticky) + Cart (scroll) -->
			<section
				v-if="selectedCompany && selectedWarehouse"
				class="bg-white rounded-lg border border-gray-200 shadow-sm flex flex-col flex-1 min-h-[400px]"
				@click="refocusSearch($event)"
			>
				<!-- Sticky Search Bar -->
				<div class="p-4 border-b border-gray-200 sticky top-0 bg-white z-20 rounded-t-lg">
					<div class="relative">
						<div class="absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none">
							<svg v-if="!searching" class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
							<div v-else class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
						</div>
						<input
							ref="searchInputRef"
							v-model="searchQuery"
							type="text"
							:placeholder="__('ابحث عن صنف بالاسم أو الكود أو امسح الباركود...')"
							class="w-full ps-10 pe-10 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							@input="onSearchInput"
							@keydown.enter.prevent="selectFirstResult"
							@keydown.down.prevent="navigateResults(1)"
							@keydown.up.prevent="navigateResults(-1)"
							@keydown.escape="clearSearch"
							autocomplete="off"
						/>
						<button
							v-if="searchQuery"
							@click="clearSearch"
							class="absolute inset-y-0 end-0 pe-3 flex items-center"
							:aria-label="__('مسح')"
						>
							<svg class="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Search Results Dropdown -->
					<div
						v-if="showResults && (searchResults.length > 0 || (searchQuery.length >= 1 && !searching))"
						class="relative z-30 mt-2"
					>
						<div class="bg-white border border-gray-200 rounded-lg shadow-2xl max-h-80 overflow-y-auto">
							<div v-if="searchResults.length > 0">
								<button
									v-for="(item, index) in searchResults"
									:key="item.item_code"
									@click="addItem(item)"
									@mouseenter="selectedResultIndex = index"
									:class="[
										'w-full text-start px-4 py-3 flex items-center gap-3 border-b border-gray-100 last:border-0 transition-colors',
										selectedResultIndex === index ? 'bg-blue-50' : 'hover:bg-gray-50'
									]"
								>
									<div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
										<img v-if="item.image" :src="item.image" :alt="item.item_name" class="w-full h-full object-cover" />
										<svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
										</svg>
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900 truncate">{{ item.item_name }}</p>
										<p class="text-xs text-gray-500 truncate">{{ item.item_code }}</p>
									</div>
									<div class="text-end flex-shrink-0 flex flex-col items-end gap-0.5">
										<span :class="[
											'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
											(item.actual_qty || 0) > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
										]">
											{{ formatQty(item.actual_qty) }} {{ item.stock_uom }}
										</span>
										<span v-if="item.has_batch_no || item.has_serial_no" class="text-[10px] text-amber-600">
											{{ __("باتش/سيريال") }}
										</span>
									</div>
								</button>
							</div>
							<div v-else class="px-4 py-6 text-center text-sm text-gray-500">
								{{ __("لا توجد نتائج") }}
							</div>
						</div>
					</div>
				</div>

				<!-- Cart Header -->
				<div class="px-4 py-2 border-b border-gray-200 flex items-center justify-between bg-gray-50">
					<h2 class="text-sm font-semibold text-gray-900">
						{{ __("قائمة الجرد") }}
						<span v-if="cart.length > 0" class="ms-2 text-xs font-normal text-gray-500">
							{{ __("{0} / {1} صنف", [cart.length, MAX_ITEMS]) }}
						</span>
					</h2>
					<button
						v-if="cart.length > 0"
						@click="clearCart"
						class="text-xs text-red-600 hover:text-red-800 hover:bg-red-50 px-2 py-1 rounded transition-colors"
					>
						{{ __("مسح الكل") }}
					</button>
				</div>

				<!-- Scrollable Cart -->
				<div class="flex-1 overflow-y-auto">
					<!-- Empty State -->
					<div v-if="cart.length === 0" class="flex items-center justify-center p-12">
						<div class="text-center">
							<svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
							</svg>
							<p class="mt-2 text-sm text-gray-500">{{ __("ابحث وأضف أصنافاً لبدء الجرد") }}</p>
						</div>
					</div>

					<!-- Cart Table -->
					<table v-else class="w-full text-sm">
						<thead class="bg-gray-50 text-xs text-gray-600 uppercase sticky top-0 z-10">
							<tr>
								<th class="px-3 py-2 text-start font-medium">{{ __("الصنف") }}</th>
								<th class="px-3 py-2 text-end font-medium w-28">{{ __("الرصيد") }}</th>
								<th class="px-3 py-2 text-end font-medium w-28">{{ __("الكمية") }}</th>
								<th class="px-3 py-2 text-end font-medium w-36">{{ __("سعر التقييم") }}</th>
								<th class="px-3 py-2 w-12"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="(row, idx) in cart" :key="row.item_code" class="hover:bg-gray-50">
								<td class="px-3 py-2 text-start">
									<div class="flex items-center gap-2">
										<div class="w-8 h-8 bg-gray-100 rounded flex items-center justify-center overflow-hidden flex-shrink-0">
											<img v-if="row.image" :src="row.image" :alt="row.item_name" class="w-full h-full object-cover" />
											<svg v-else class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
											</svg>
										</div>
										<div class="min-w-0">
											<p class="font-medium text-gray-900 truncate">{{ row.item_name }}</p>
											<p class="text-xs text-gray-500 truncate">{{ row.item_code }}</p>
											<span v-if="row.has_batch_no || row.has_serial_no" class="text-[10px] text-amber-600">
												{{ __("يتطلب باتش/سيريال - غير مدعوم") }}
											</span>
										</div>
									</div>
								</td>
								<td class="px-3 py-2 text-end text-gray-600">
									{{ formatQty(row.actual_qty) }}
									<span class="text-xs text-gray-400">{{ row.stock_uom }}</span>
								</td>
								<td class="px-3 py-2 text-end">
									<input
										v-model.number="row.qty"
										type="number"
										min="0"
										step="any"
										class="w-24 text-end border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
										@focus="($event.target).select()"
										@click="($event.target).select()"
										@keydown.enter.prevent="focusSearch"
									/>
								</td>
								<td class="px-3 py-2 text-end">
									<input
										v-model.number="row.valuation_rate"
										type="number"
										min="0"
										step="any"
										:class="[
											'w-28 text-end border rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
											(row.valuation_rate || 0) > 0 ? 'border-gray-300' : 'border-red-300 bg-red-50'
										]"
										@focus="($event.target).select()"
										@click="($event.target).select()"
										@keydown.enter.prevent="focusSearch"
									/>
									<div class="text-[10px] text-gray-500 mt-0.5">
										<template v-if="row.valuation_rate_source === 'last_purchase_rate'">{{ __('آخر سعر شراء') }}</template>
										<template v-else-if="row.valuation_rate_source === 'buying_price_list'">{{ __('قائمة أسعار الشراء') }}</template>
										<template v-else-if="row.valuation_rate_source === 'fallback_price_list'">{{ __('قائمة احتياطية') }}</template>
										<template v-else-if="(row.valuation_rate || 0) > 0">{{ __('يدوي') }}</template>
										<template v-else>{{ __("أدخل السعر") }}</template>
									</div>
								</td>
								<td class="px-3 py-2 text-center">
									<button
										@click="removeItem(idx)"
										class="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
										:aria-label="__('حذف')"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
										</svg>
									</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- Footer / Actions -->
				<div v-if="cart.length > 0" class="px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white">
					<div class="text-xs text-gray-500">
						<p v-if="itemsWithoutPrice > 0" class="text-red-600">
							{{ __("{0} صنف بدون سعر تقييم", [itemsWithoutPrice]) }}
						</p>
						<p v-else-if="cart.length >= MAX_ITEMS" class="text-amber-600">
							{{ __("بلغت الحد الأقصى ({0} صنف) - احفظ ثم ابدأ جرداً جديداً", [MAX_ITEMS]) }}
						</p>
						<p v-else>{{ __("جميع الأصناف لها سعر تقييم") }}</p>
					</div>
					<div class="flex items-center gap-2">
						<Button
							variant="subtle"
							@click="clearCart"
						>
							{{ __("مسح") }}
						</Button>
						<Button
							variant="solid"
							theme="blue"
							:loading="submitting"
							:disabled="!canSubmit"
							@click="handleSubmit"
						>
							{{ __("حفظ كمسودة") }}
						</Button>
					</div>
				</div>
			</section>
		</main>

		<!-- Success Dialog -->
		<Dialog v-model="showSuccessDialog" :options="{ title: __('تم الحفظ'), size: 'sm' }">
			<template #body-content>
				<div class="flex flex-col items-center text-center py-4 gap-3">
					<div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center">
						<svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-gray-700">{{ __("تم إنشاء سجل جرد مخزون أول المدة بنجاح") }}</p>
					<p class="text-xs text-gray-500">{{ __("رقم السجل: {0}", [lastCreatedName]) }}</p>
				</div>
			</template>
			<template #actions>
				<div class="flex gap-2 w-full">
					<Button class="flex-1" variant="subtle" @click="showSuccessDialog = false">
						{{ __("البقاء هنا") }}
					</Button>
					<a
						:href="lastCreatedUrl"
						target="_blank"
						class="flex-1 inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
					>
						{{ __("فتح في Desk") }}
					</a>
					<Button class="flex-1" variant="solid" theme="green" @click="resetAfterSave">
						{{ __("جرد جديد") }}
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import router from "@/router"
import { computed, onMounted, ref } from "vue"

const { showSuccess, showError } = useToast()
const { userName } = useUserData()

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

const MAX_ITEMS = 50

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
	const tag = e.target?.tagName?.toLowerCase()
	if (tag === "input" || tag === "select" || tag === "button" || tag === "a") return
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

async function logout() {
	await session.logout.submit()
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
