<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-cyan-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">{{ config.store_name || __("المتجر") }}</h1>
						<p v-if="config.contact_phone" class="text-xs text-slate-500 truncate">{{ config.contact_phone }}</p>
					</div>
				</div>
				<!-- Cart Button -->
				<button @click="cartOpen = true" class="relative p-2.5 rounded-xl bg-cyan-50 text-cyan-700 hover:bg-cyan-100 transition-all hover:scale-105 active:scale-95 flex-shrink-0">
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
					<span v-if="cartCount > 0" class="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">{{ cartCount }}</span>
				</button>
			</div>
		</header>

		<!-- Main -->
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col gap-4">
			<!-- Loading -->
			<div v-if="loading" class="flex items-center justify-center py-20">
				<svg class="animate-spin h-10 w-10 text-cyan-600" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
				</svg>
			</div>

			<!-- Store Disabled -->
			<div v-else-if="!config.is_enabled" class="flex flex-col items-center justify-center py-20 gap-4">
				<div class="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center">
					<svg class="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
					</svg>
				</div>
				<p class="text-lg font-bold text-slate-700">{{ __("المتجر غير متاح حالياً") }}</p>
				<p class="text-sm text-slate-500">{{ __("يرجى العودة لاحقاً") }}</p>
			</div>

			<template v-else>
				<!-- Banner -->
				<div v-if="config.banner_image" class="relative rounded-2xl overflow-hidden shadow-lg h-40 sm:h-56">
					<img :src="config.banner_image" class="w-full h-full object-cover" />
					<div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
					<div class="absolute bottom-4 right-4">
						<h2 class="text-2xl sm:text-3xl font-extrabold text-white drop-shadow-lg">{{ config.store_name || __("المتجر") }}</h2>
					</div>
				</div>


				<!-- Advertisements -->
				<div v-if="storeAds.length" class="flex gap-3 overflow-x-auto pb-2 snap-x">
					<a v-for="ad in storeAds" :key="ad.name"
						:href="ad.link_url || undefined"
						:class="['snap-start flex-shrink-0 w-72 sm:w-80 rounded-2xl overflow-hidden shadow-md border border-slate-200 bg-white hover:shadow-lg transition-all',
							ad.link_url ? 'cursor-pointer hover:border-amber-300' : '']">
						<div class="relative h-28 sm:h-32 bg-slate-100">
							<img v-if="ad.image" :src="ad.image" class="w-full h-full object-cover" />
							<div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-amber-100 to-orange-100">
								<svg class="w-10 h-10 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6a1.76 1.76 0 002.585-1.4c.02-.357.134-.708.332-1.02L10 3" />
								</svg>
							</div>
						</div>
						<div class="p-3">
							<p class="text-sm font-bold text-slate-900 truncate">{{ ad.title }}</p>
							<div v-if="ad.content" class="text-xs text-slate-500 line-clamp-2 mt-1" v-html="ad.content"></div>
						</div>
					</a>
				</div>

				<!-- Search Bar -->
				<div class="relative">
					<input v-model="searchQuery" type="text" :placeholder="__('ابحث عن منتج...')"
						class="w-full border border-slate-300 rounded-xl ps-10 pe-3 py-3 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white shadow-sm transition-all"
						@input="debouncedSearch" />
					<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>

				<!-- Group Filter -->
				<div v-if="itemGroups.length" class="flex gap-2 overflow-x-auto pb-1">
					<button @click="selectedGroup = ''; loadItems()"
						:class="['px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all',
							!selectedGroup ? 'bg-gradient-to-l from-cyan-600 to-blue-600 text-white shadow-md' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50']">
						{{ __("الكل") }}
					</button>
					<button v-for="g in itemGroups" :key="g" @click="selectedGroup = g; loadItems()"
						:class="['px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all',
							selectedGroup === g ? 'bg-gradient-to-l from-cyan-600 to-blue-600 text-white shadow-md' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50']">
						{{ g }}
					</button>
				</div>

				<!-- Products Grid -->
				<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
					<div v-for="item in storeItems" :key="item.item_code"
						class="bg-white rounded-2xl border border-slate-200 shadow-md overflow-hidden hover:shadow-lg hover:border-cyan-300 transition-all flex flex-col">
						<!-- Image -->
						<div class="relative h-32 sm:h-40 bg-slate-100">
							<img v-if="item.image" :src="item.image" class="w-full h-full object-cover" />
							<div v-else class="w-full h-full flex items-center justify-center">
								<svg class="w-12 h-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
						</div>
						<!-- Info -->
						<div class="p-3 flex-1 flex flex-col gap-2">
							<p class="text-sm font-bold text-slate-900 line-clamp-2">{{ item.item_name }}</p>
							<p v-if="item.description" class="text-xs text-slate-500 line-clamp-2">{{ item.description }}</p>
							<div class="flex items-center justify-between mt-auto pt-2">
								<p class="text-base font-extrabold text-cyan-700">{{ formatPrice(item.price) }}</p>
								<button @click="addToCart(item)"
									class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md flex items-center gap-1">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
									</svg>
									{{ __("أضف") }}
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Empty -->
				<div v-if="!loading && !storeItems.length" class="text-center py-16 text-slate-400">
					<svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
					</svg>
					<p class="text-sm">{{ __("لا توجد منتجات") }}</p>
				</div>
			</template>
		</main>

		<!-- Cart Sidebar -->
		<transition enter-active-class="transition-transform duration-300" enter-from-class="translate-x-full" leave-active-class="transition-transform duration-300" leave-to-class="translate-x-full">
			<div v-if="cartOpen" class="fixed inset-0 z-50 flex justify-end" @click.self="cartOpen = false">
				<div class="bg-white w-full max-w-md h-full shadow-2xl flex flex-col">
					<!-- Cart Header -->
					<div class="flex items-center justify-between p-4 border-b border-slate-200">
						<h3 class="text-lg font-bold text-slate-900">{{ __("سلة التسوق") }}</h3>
						<button @click="cartOpen = false" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<!-- Cart Items -->
					<div class="flex-1 overflow-y-auto p-4 space-y-3">
						<div v-for="(entry, idx) in cart" :key="entry.item_code" class="flex items-center gap-3 bg-slate-50 rounded-xl p-3 border border-slate-200">
							<img v-if="entry.image" :src="entry.image" class="w-12 h-12 rounded-lg object-cover border border-slate-200" />
							<div v-else class="w-12 h-12 bg-slate-200 rounded-lg flex items-center justify-center">
								<svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-semibold text-slate-900 truncate">{{ entry.item_name }}</p>
								<p class="text-xs text-cyan-700 font-bold">{{ formatPrice(entry.price) }}</p>
							</div>
							<div class="flex items-center gap-1">
								<button @click="changeQty(idx, -1)" class="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 transition-all font-bold">-</button>
								<span class="w-8 text-center text-sm font-bold">{{ entry.qty }}</span>
								<button @click="changeQty(idx, 1)" class="w-7 h-7 rounded-lg bg-cyan-100 text-cyan-700 hover:bg-cyan-200 transition-all font-bold">+</button>
							</div>
							<button @click="removeFromCart(idx)" class="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
						<div v-if="!cart.length" class="text-center py-12 text-slate-400">
							<svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
							<p class="text-sm">{{ __("السلة فارغة") }}</p>
						</div>
					</div>
					<!-- Cart Footer -->
					<div v-if="cart.length" class="border-t border-slate-200 p-4 space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-sm font-semibold text-slate-700">{{ __("الإجمالي") }}</span>
							<span class="text-lg font-extrabold text-cyan-700">{{ formatPrice(cartTotal) }}</span>
						</div>
						<button @click="goToCheckout"
							class="w-full py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md">
							{{ __("إتمام الطلب") }}
						</button>
					</div>
				</div>
			</div>
		</transition>

		<!-- Checkout Modal -->
		<div v-if="checkoutOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="checkoutOpen = false">
			<div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold text-slate-900">{{ __("إتمام الطلب") }}</h3>
					<button @click="checkoutOpen = false" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<div class="space-y-4">
					<!-- Order Summary -->
					<div class="bg-slate-50 rounded-xl p-3 border border-slate-200">
						<p class="text-xs font-bold text-slate-700 mb-2">{{ __("ملخص الطلب") }}</p>
						<div v-for="entry in cart" :key="entry.item_code" class="flex justify-between text-xs text-slate-600 py-0.5">
							<span>{{ entry.item_name }} × {{ entry.qty }}</span>
							<span class="font-semibold">{{ formatPrice(entry.price * entry.qty) }}</span>
						</div>
						<div class="border-t border-slate-200 mt-2 pt-2 flex justify-between text-sm font-bold">
							<span>{{ __("الإجمالي") }}</span>
							<span class="text-cyan-700">{{ formatPrice(cartTotal) }}</span>
						</div>
					</div>
					<!-- Customer Name -->
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("الاسم") }}</label>
						<input v-model="orderForm.customer_name" type="text"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
					</div>
					<!-- Phone -->
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("رقم التواصل") }}</label>
						<input v-model="orderForm.phone" type="tel"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
					</div>
					<!-- Delivery Area -->
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("منطقة التوصيل") }}</label>
						<select v-model="orderForm.delivery_area"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white transition-all">
							<option value="">{{ __("اختر المنطقة") }}</option>
							<option v-for="area in config.delivery_areas" :key="area.area_name" :value="area.area_name">
								{{ area.area_name }} ({{ formatPrice(area.delivery_fee) }})
							</option>
						</select>
					</div>
					<!-- Address -->
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("العنوان") }}</label>
						<textarea v-model="orderForm.address" rows="2"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"></textarea>
					</div>
					<!-- Notes -->
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("ملاحظات") }}</label>
						<textarea v-model="orderForm.notes" rows="2"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"></textarea>
					</div>
					<!-- Total with delivery -->
					<div v-if="orderForm.delivery_area" class="bg-cyan-50 rounded-xl p-3 border border-cyan-200">
						<div class="flex justify-between text-xs text-slate-600 py-0.5">
							<span>{{ __("المجموع") }}</span>
							<span>{{ formatPrice(cartTotal) }}</span>
						</div>
						<div class="flex justify-between text-xs text-slate-600 py-0.5">
							<span>{{ __("التوصيل") }}</span>
							<span>{{ formatPrice(selectedDeliveryFee) }}</span>
						</div>
						<div class="border-t border-cyan-200 mt-1 pt-1 flex justify-between text-sm font-bold">
							<span>{{ __("الإجمالي النهائي") }}</span>
							<span class="text-cyan-700">{{ formatPrice(cartTotal + selectedDeliveryFee) }}</span>
						</div>
					</div>
				</div>
				<div class="mt-6 flex justify-end gap-2">
					<button @click="checkoutOpen = false" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all">{{ __("إلغاء") }}</button>
					<button @click="submitOrder" :disabled="placingOrder"
						class="px-5 py-2 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 transition-all shadow-md disabled:opacity-50 flex items-center gap-2">
						<svg v-if="placingOrder" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						{{ placingOrder ? __("جاري...") : __("تأكيد الطلب") }}
					</button>
				</div>
			</div>
		</div>

		<!-- Order Success Modal -->
		<div v-if="orderSuccess" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="orderSuccess = null">
			<div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center">
				<div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
					<svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
					</svg>
				</div>
				<h3 class="text-lg font-bold text-slate-900 mb-2">{{ __("تم إنشاء الطلب بنجاح") }}</h3>
				<p class="text-sm text-slate-600 mb-1">{{ __("رقم الطلب") }}</p>
				<p class="text-xl font-extrabold text-cyan-700 mb-4">{{ orderSuccess.sales_order }}</p>
				<p class="text-sm text-slate-600 mb-4">{{ __("الإجمالي") }}: {{ formatPrice(orderSuccess.total) }}</p>
				<button @click="orderSuccess = null; resetCart()"
					class="w-full py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md">
					{{ __("متابعة التسوق") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { computed, onMounted, ref } from "vue"

const { showSuccess, showError } = useToast()

const loading = ref(false)
const placingOrder = ref(false)
const config = ref({ is_enabled: 0, store_name: "", banner_image: "", contact_phone: "", contact_whatsapp: "", delivery_areas: [] })
const storeItems = ref([])
const itemGroups = ref([])
const storeAds = ref([])
const searchQuery = ref("")
const selectedGroup = ref("")
const cart = ref([])
const cartOpen = ref(false)
const checkoutOpen = ref(false)
const orderSuccess = ref(null)
const orderForm = ref({
	customer_name: "",
	phone: "",
	delivery_area: "",
	address: "",
	notes: "",
})

let searchDebounce = null

onMounted(async () => {
	loading.value = true
	try {
		await loadConfig()
		if (config.value.is_enabled) {
			await Promise.all([loadItems(), loadGroups(), loadAds()])
		}
	} catch (e) {
		showError(e?.message || __("فشل التحميل"))
	} finally {
		loading.value = false
	}
})

async function loadConfig() {
	config.value = await call("bs.baron_servies.api.store.get_store_config")
}

async function loadItems() {
	storeItems.value = await call("bs.baron_servies.api.store.get_store_items", {
		group: selectedGroup.value || undefined,
		search: searchQuery.value || undefined,
	}) || []
}

async function loadGroups() {
	itemGroups.value = await call("bs.baron_servies.api.store.get_store_item_groups") || []
}

async function loadAds() {
	storeAds.value = await call("bs.baron_servies.api.store.get_store_ads") || []
}

function debouncedSearch() {
	if (searchDebounce) clearTimeout(searchDebounce)
	searchDebounce = setTimeout(() => loadItems(), 400)
}

// Cart
const cartCount = computed(() => cart.value.reduce((sum, e) => sum + e.qty, 0))
const cartTotal = computed(() => cart.value.reduce((sum, e) => sum + e.price * e.qty, 0))
const selectedDeliveryFee = computed(() => {
	const area = config.value.delivery_areas.find((a) => a.area_name === orderForm.value.delivery_area)
	return area ? area.delivery_fee : 0
})

function addToCart(item) {
	const existing = cart.value.find((e) => e.item_code === item.item_code)
	if (existing) {
		existing.qty += 1
	} else {
		cart.value.push({
			item_code: item.item_code,
			item_name: item.item_name,
			price: item.price,
			image: item.image,
			qty: 1,
		})
	}
	showSuccess(__("تمت الإضافة للسلة"))
}

function changeQty(idx, delta) {
	cart.value[idx].qty += delta
	if (cart.value[idx].qty <= 0) {
		cart.value.splice(idx, 1)
	}
}

function removeFromCart(idx) {
	cart.value.splice(idx, 1)
}

function goToCheckout() {
	if (!cart.value.length) {
		showError(__("السلة فارغة"))
		return
	}
	cartOpen.value = false
	checkoutOpen.value = true
}

async function submitOrder() {
	if (!orderForm.value.customer_name.trim()) {
		showError(__("الاسم مطلوب"))
		return
	}
	if (!orderForm.value.phone.trim()) {
		showError(__("رقم التواصل مطلوب"))
		return
	}
	if (!orderForm.value.address.trim()) {
		showError(__("العنوان مطلوب"))
		return
	}

	placingOrder.value = true
	try {
		// SECURITY: Only send item_code + qty + customer data
		// Pricing, company, warehouse, delivery fee are all re-fetched by backend
		const items = cart.value.map((e) => ({
			item_code: e.item_code,
			qty: e.qty,
		}))

		const result = await call("bs.baron_servies.api.store.create_store_order", {
			customer_name: orderForm.value.customer_name,
			phone: orderForm.value.phone,
			delivery_area: orderForm.value.delivery_area,
			address: orderForm.value.address,
			items: JSON.stringify(items),
			notes: orderForm.value.notes,
		})

		orderSuccess.value = result
		checkoutOpen.value = false
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الطلب"))
	} finally {
		placingOrder.value = false
	}
}

function resetCart() {
	cart.value = []
	orderForm.value = { customer_name: "", phone: "", delivery_area: "", address: "", notes: "" }
}

function formatPrice(value) {
	const n = Number(value || 0)
	return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}
</script>
