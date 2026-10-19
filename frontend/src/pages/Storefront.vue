<template>
	<div class="min-h-screen flex flex-col bg-slate-50/60" dir="rtl">
		<!-- Header -->
		<header class="bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-cyan-600 shadow-sm">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="CART_ICON" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">{{ config.store_name || __("المتجر") }}</h1>
						<a v-if="config.contact_phone" :href="`tel:${config.contact_phone}`" class="text-xs text-slate-500 truncate" dir="ltr">{{ config.contact_phone }}</a>
					</div>
				</div>
				<div class="flex items-center gap-2 flex-shrink-0">
					<button v-if="config.is_enabled" type="button" class="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50" @click="openTracking()">
						{{ __("تتبع طلبي") }}
					</button>
					<button type="button" class="relative p-2.5 rounded-xl bg-cyan-50 text-cyan-700 hover:bg-cyan-100 transition-all active:scale-95" :aria-label="__('السلة')" @click="cartOpen = true">
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="CART_ICON" />
						</svg>
						<span v-if="cartCount > 0" class="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold rounded-full min-w-[1.25rem] h-5 px-1 flex items-center justify-center">{{ formatQty(cartCount) }}</span>
					</button>
				</div>
			</div>
		</header>

		<!-- Main -->
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col gap-4">
			<div v-if="loading" class="flex items-center justify-center py-20">
				<div class="h-10 w-10 animate-spin rounded-full border-4 border-cyan-600 border-t-transparent"></div>
			</div>

			<!-- Store disabled -->
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
				<div v-if="config.banner_image" class="relative rounded-2xl overflow-hidden shadow-sm h-40 sm:h-56">
					<img :src="config.banner_image" class="w-full h-full object-cover" alt="" />
					<div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
					<div class="absolute bottom-4 right-4">
						<h2 class="text-2xl sm:text-3xl font-extrabold text-white drop-shadow-lg">{{ config.store_name || __("المتجر") }}</h2>
					</div>
				</div>

				<!-- Ads (content is sanitised on the server) -->
				<div v-if="ads.length" class="flex gap-3 overflow-x-auto pb-2 snap-x">
					<component
						:is="ad.link_url ? 'a' : 'div'"
						v-for="ad in ads"
						:key="ad.name"
						:href="ad.link_url || undefined"
						:rel="ad.link_url ? 'noopener' : undefined"
						:class="['bs-card snap-start flex-shrink-0 w-72 sm:w-80 overflow-hidden transition-all', ad.link_url ? 'cursor-pointer hover:shadow-lg hover:border-amber-300' : '']"
					>
						<div class="relative h-28 sm:h-32 bg-slate-100">
							<img v-if="ad.image" :src="ad.image" class="w-full h-full object-cover" alt="" />
							<div v-else class="w-full h-full flex items-center justify-center bg-amber-50/60">
								<svg class="w-10 h-10 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6a1.76 1.76 0 002.585-1.4c.02-.357.134-.708.332-1.02L10 3" />
								</svg>
							</div>
						</div>
						<div class="p-3">
							<p class="text-sm font-bold text-slate-900 truncate">{{ ad.title }}</p>
							<div v-if="ad.content" class="text-xs text-slate-500 line-clamp-2 mt-1" v-html="ad.content"></div>
						</div>
					</component>
				</div>

				<!-- Search -->
				<div class="relative">
					<input v-model="searchQuery" type="search" :placeholder="__('ابحث عن منتج...')" class="bs-input w-full !ps-10 py-3 shadow-sm" />
					<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>

				<!-- Groups -->
				<div v-if="groups.length > 1" class="flex gap-2 overflow-x-auto pb-1">
					<button
						v-for="g in ['', ...groups]"
						:key="g || 'all'"
						type="button"
						:class="['px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all',
							selectedGroup === g ? 'text-white shadow-sm bg-cyan-600 hover:bg-cyan-700' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50']"
						@click="selectedGroup = g"
					>
						{{ g || __("الكل") }}
					</button>
				</div>

				<!-- Products -->
				<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
					<div
						v-for="item in visibleItems"
						:key="item.item_code"
						class="bs-card overflow-hidden transition-all flex flex-col"
						:class="item.sold_out ? 'opacity-70' : 'hover:shadow-lg hover:border-cyan-300'"
					>
						<div class="relative h-32 sm:h-40 bg-slate-100">
							<img v-if="item.image" :src="item.image" class="w-full h-full object-cover" loading="lazy" alt="" />
							<div v-else class="w-full h-full flex items-center justify-center">
								<svg class="w-12 h-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="IMAGE_ICON" />
								</svg>
							</div>
							<span v-if="item.sold_out" class="absolute top-2 start-2 rounded-full bg-slate-900/80 px-2.5 py-1 text-[11px] font-bold text-white">{{ __("نفد") }}</span>
						</div>
						<div class="p-3 flex-1 flex flex-col gap-2">
							<p class="text-sm font-bold text-slate-900 line-clamp-2">{{ item.item_name }}</p>
							<p v-if="item.description" class="text-xs text-slate-500 line-clamp-2">{{ item.description }}</p>
							<div class="flex items-center justify-between mt-auto pt-2 gap-2">
								<p class="text-base font-extrabold text-cyan-700">
									{{ formatPrice(item.price) }}
									<span class="text-[11px] font-medium text-slate-400">/ {{ item.stock_uom }}</span>
								</p>
								<template v-if="!item.sold_out">
									<div v-if="cartQty(item.item_code)" class="flex items-center gap-1">
										<button type="button" class="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 font-bold" @click="changeQtyByCode(item.item_code, -1)">-</button>
										<span class="w-6 text-center text-sm font-bold">{{ formatQty(cartQty(item.item_code)) }}</span>
										<button type="button" class="w-7 h-7 rounded-lg bg-cyan-100 text-cyan-700 hover:bg-cyan-200 font-bold" @click="addToCart(item)">+</button>
									</div>
									<button
										v-else
										type="button"
										class="px-3 py-1.5 rounded-lg text-xs font-bold text-white transition-all shadow-sm flex items-center gap-1 bg-cyan-600 hover:bg-cyan-700"
										@click="addToCart(item)"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
										{{ __("أضف") }}
									</button>
								</template>
							</div>
						</div>
					</div>
				</div>

				<div v-if="!visibleItems.length" class="text-center py-16 text-slate-400">
					<p class="text-sm">{{ items.length ? __("لا توجد نتائج مطابقة") : __("لا توجد منتجات") }}</p>
				</div>
			</template>
		</main>

		<!-- Cart drawer -->
		<transition enter-active-class="transition-transform duration-300" enter-from-class="-translate-x-full" leave-active-class="transition-transform duration-300" leave-to-class="-translate-x-full">
			<div v-if="cartOpen" class="fixed inset-0 z-50 flex justify-end bg-black/30" @click.self="cartOpen = false">
				<div class="bg-white w-full max-w-md h-full shadow-2xl flex flex-col">
					<div class="flex items-center justify-between p-4 border-b border-slate-200">
						<h3 class="text-lg font-bold text-slate-900">{{ __("سلة التسوق") }}</h3>
						<button type="button" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100" :aria-label="__('إغلاق')" @click="cartOpen = false">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
						</button>
					</div>
					<div class="flex-1 overflow-y-auto p-4 space-y-3">
						<div v-for="entry in cart" :key="entry.item_code" class="flex items-center gap-3 bg-slate-50 rounded-xl p-3 border border-slate-200">
							<img v-if="entry.image" :src="entry.image" class="w-12 h-12 rounded-lg object-cover border border-slate-200" alt="" />
							<div v-else class="w-12 h-12 bg-slate-200 rounded-lg flex items-center justify-center">
								<svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="IMAGE_ICON" /></svg>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-semibold text-slate-900 truncate">{{ entry.item_name }}</p>
								<p class="text-xs text-cyan-700 font-bold">{{ formatPrice(entry.price) }} × {{ formatQty(entry.qty) }} = {{ formatPrice(entry.price * entry.qty) }}</p>
							</div>
							<div class="flex items-center gap-1">
								<button type="button" class="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 font-bold" @click="changeQtyByCode(entry.item_code, -1)">-</button>
								<span class="w-8 text-center text-sm font-bold">{{ formatQty(entry.qty) }}</span>
								<button type="button" class="w-7 h-7 rounded-lg bg-cyan-100 text-cyan-700 hover:bg-cyan-200 font-bold" @click="changeQtyByCode(entry.item_code, 1)">+</button>
							</div>
							<button type="button" class="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50" :aria-label="__('حذف')" @click="removeFromCart(entry.item_code)">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
							</button>
						</div>
						<div v-if="!cart.length" class="text-center py-12 text-slate-400">
							<p class="text-sm">{{ __("السلة فارغة") }}</p>
						</div>
					</div>
					<div v-if="cart.length" class="border-t border-slate-200 p-4 space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-sm font-semibold text-slate-700">{{ __("المجموع") }}</span>
							<span class="text-lg font-extrabold text-cyan-700">{{ formatPrice(cartTotal) }}</span>
						</div>
						<button type="button" class="w-full py-3 rounded-xl text-sm font-bold text-white shadow-sm bg-cyan-600 hover:bg-cyan-700" @click="goToCheckout">
							{{ __("إتمام الطلب") }}
						</button>
					</div>
				</div>
			</div>
		</transition>

		<!-- Checkout -->
		<div v-if="checkoutOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="checkoutOpen = false">
			<form class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto" @submit.prevent="submitOrder">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold text-slate-900">{{ __("إتمام الطلب") }}</h3>
					<button type="button" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100" :aria-label="__('إغلاق')" @click="checkoutOpen = false">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
					</button>
				</div>
				<div class="space-y-4">
					<div class="bg-slate-50 rounded-xl p-3 border border-slate-200">
						<p class="text-xs font-bold text-slate-700 mb-2">{{ __("ملخص الطلب") }}</p>
						<div v-for="entry in cart" :key="entry.item_code" class="flex justify-between text-xs text-slate-600 py-0.5">
							<span>{{ entry.item_name }} × {{ formatQty(entry.qty) }}</span>
							<span class="font-semibold">{{ formatPrice(entry.price * entry.qty) }}</span>
						</div>
					</div>
					<div>
						<label class="bs-label">{{ __("الاسم") }} <span class="text-rose-500">*</span></label>
						<input v-model="orderForm.customer_name" type="text" maxlength="140" autocomplete="name" class="bs-input w-full" />
					</div>
					<div>
						<label class="bs-label">{{ __("رقم الهاتف") }} <span class="text-rose-500">*</span></label>
						<input v-model="orderForm.phone" type="tel" inputmode="tel" autocomplete="tel" dir="ltr" placeholder="05XXXXXXXX" class="bs-input w-full text-right" />
					</div>
					<div v-if="config.delivery_areas.length">
						<label class="bs-label">{{ __("منطقة التوصيل") }} <span class="text-rose-500">*</span></label>
						<select v-model="orderForm.delivery_area" class="bs-input w-full">
							<option value="">{{ __("اختر المنطقة") }}</option>
							<option v-for="area in config.delivery_areas" :key="area.area_name" :value="area.area_name">
								{{ area.area_name }} ({{ formatPrice(area.delivery_fee) }})
							</option>
						</select>
					</div>
					<div>
						<label class="bs-label">{{ __("العنوان") }} <span class="text-rose-500">*</span></label>
						<textarea v-model="orderForm.address" rows="2" maxlength="500" autocomplete="street-address" class="bs-input w-full"></textarea>
					</div>
					<div>
						<label class="bs-label">{{ __("ملاحظات") }}</label>
						<textarea v-model="orderForm.notes" rows="2" maxlength="1000" class="bs-input w-full"></textarea>
					</div>
					<div class="bg-cyan-50 rounded-xl p-3 border border-cyan-200">
						<div class="flex justify-between text-xs text-slate-600 py-0.5"><span>{{ __("المجموع") }}</span><span>{{ formatPrice(cartTotal) }}</span></div>
						<div v-if="config.delivery_areas.length" class="flex justify-between text-xs text-slate-600 py-0.5">
							<span>{{ __("التوصيل") }}</span>
							<span>{{ orderForm.delivery_area ? formatPrice(selectedDeliveryFee) : "—" }}</span>
						</div>
						<div class="border-t border-cyan-200 mt-1 pt-1 flex justify-between text-sm font-bold">
							<span>{{ __("الإجمالي النهائي") }}</span>
							<span class="text-cyan-700">{{ formatPrice(cartTotal + selectedDeliveryFee) }}</span>
						</div>
						<p class="mt-1 text-[11px] text-slate-500">{{ __("الدفع عند الاستلام") }}</p>
					</div>
				</div>
				<div class="mt-6 flex justify-end gap-2">
					<button type="button" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50" @click="checkoutOpen = false">{{ __("إلغاء") }}</button>
					<button type="submit" :disabled="placingOrder" class="px-5 py-2 rounded-xl text-sm font-bold text-white shadow-sm disabled:opacity-50 flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700">
						<span v-if="placingOrder" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
						{{ placingOrder ? __("جاري...") : __("تأكيد الطلب") }}
					</button>
				</div>
			</form>
		</div>

		<!-- Order placed -->
		<div v-if="orderSuccess" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center">
				<div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
					<svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
				</div>
				<h3 class="text-lg font-bold text-slate-900 mb-1">{{ __("تم استلام طلبك") }}</h3>
				<p class="text-sm text-slate-500 mb-3">{{ __("سنتواصل معك لتأكيد الطلب") }}</p>
				<p class="text-xs text-slate-500">{{ __("رقم الطلب") }}</p>
				<p class="text-xl font-extrabold text-cyan-700 mb-2" dir="ltr">{{ orderSuccess.sales_order }}</p>
				<p class="text-sm text-slate-600 mb-4">{{ __("الإجمالي") }}: {{ formatPrice(orderSuccess.total) }}</p>
				<div class="flex flex-col gap-2">
					<a v-if="whatsappLink" :href="whatsappLink" target="_blank" rel="noopener" class="w-full py-3 rounded-xl text-sm font-bold text-white shadow-sm bg-emerald-600 hover:bg-emerald-700">
						{{ __("إرسال الطلب عبر واتساب") }}
					</a>
					<button type="button" class="w-full py-2.5 rounded-xl text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50" @click="openTracking(orderSuccess.sales_order, orderSuccess.phone); orderSuccess = null">
						{{ __("تتبع الطلب") }}
					</button>
					<button type="button" class="w-full py-2.5 rounded-xl text-sm font-bold text-white shadow-sm bg-cyan-600 hover:bg-cyan-700" @click="orderSuccess = null">
						{{ __("متابعة التسوق") }}
					</button>
				</div>
			</div>
		</div>

		<!-- Tracking -->
		<div v-if="trackingOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="trackingOpen = false">
			<div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold text-slate-900">{{ __("تتبع طلبي") }}</h3>
					<button type="button" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100" :aria-label="__('إغلاق')" @click="trackingOpen = false">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
					</button>
				</div>
				<form class="grid grid-cols-1 gap-3 sm:grid-cols-2" @submit.prevent="trackOrder">
					<div>
						<label class="bs-label">{{ __("رقم الطلب") }}</label>
						<input v-model="trackForm.order" type="text" dir="ltr" class="bs-input w-full text-right" />
					</div>
					<div>
						<label class="bs-label">{{ __("رقم الهاتف") }}</label>
						<input v-model="trackForm.phone" type="tel" inputmode="tel" dir="ltr" class="bs-input w-full text-right" />
					</div>
					<button type="submit" :disabled="tracking" class="sm:col-span-2 py-2.5 rounded-xl text-sm font-bold text-white bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50">
						{{ tracking ? __("جاري البحث...") : __("عرض حالة الطلب") }}
					</button>
				</form>

				<div v-if="trackResult" class="mt-5">
					<ol class="flex items-start justify-between gap-1">
						<li v-for="(step, i) in TRACK_STEPS" :key="step.key" class="flex flex-1 flex-col items-center gap-1 text-center">
							<span
								class="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold"
								:class="trackResult.status === 'Cancelled' ? 'bg-slate-100 text-slate-400' : i <= trackStepIndex ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-400'"
							>{{ i + 1 }}</span>
							<span class="text-[11px]" :class="i <= trackStepIndex && trackResult.status !== 'Cancelled' ? 'font-bold text-slate-800' : 'text-slate-400'">{{ __(step.label) }}</span>
						</li>
					</ol>
					<p v-if="trackResult.status === 'Cancelled'" class="mt-3 rounded-lg bg-rose-50 p-2 text-center text-sm font-semibold text-rose-700">{{ __("تم إلغاء الطلب") }}</p>
					<div class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
						<div v-for="(it, i) in trackResult.items" :key="i" class="flex justify-between py-0.5">
							<span>{{ it.item_name }} × {{ formatQty(it.qty) }}</span>
							<span>{{ formatPrice(it.amount) }}</span>
						</div>
						<div v-if="trackResult.delivery_fee" class="flex justify-between py-0.5">
							<span>{{ __("التوصيل") }} ({{ trackResult.delivery_area }})</span>
							<span>{{ formatPrice(trackResult.delivery_fee) }}</span>
						</div>
						<div class="mt-1 flex justify-between border-t border-slate-200 pt-1 text-sm font-bold text-slate-800">
							<span>{{ __("الإجمالي") }}</span>
							<span>{{ formatPrice(trackResult.total) }}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { computed, onMounted, ref, watch } from "vue"

const CART_ICON = "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
const IMAGE_ICON = "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
const TRACK_STEPS = [
	{ key: "New", label: "تم الاستلام" },
	{ key: "Confirmed", label: "مؤكد" },
	{ key: "Out for Delivery", label: "قيد التوصيل" },
	{ key: "Delivered", label: "تم التسليم" },
]
// Per-browser conveniences only (orders themselves live on the server)
const CART_KEY = "bs_store_cart"
const CUSTOMER_KEY = "bs_store_customer"
const LAST_ORDER_KEY = "bs_store_last_order"

const { showSuccess, showError } = useToast()

const loading = ref(false)
const placingOrder = ref(false)
const config = ref({ is_enabled: 0, store_name: "", banner_image: "", contact_phone: "", contact_whatsapp: "", currency: "", delivery_areas: [] })
const items = ref([])
const groups = ref([])
const ads = ref([])
const searchQuery = ref("")
const selectedGroup = ref("")
const cart = ref([])
const cartOpen = ref(false)
const checkoutOpen = ref(false)
const orderSuccess = ref(null)
const orderForm = ref({ customer_name: "", phone: "", delivery_area: "", address: "", notes: "" })
const trackingOpen = ref(false)
const tracking = ref(false)
const trackForm = ref({ order: "", phone: "" })
const trackResult = ref(null)

function readJSON(key, fallback) {
	try {
		return JSON.parse(localStorage.getItem(key) || "null") ?? fallback
	} catch {
		return fallback
	}
}

function writeJSON(key, value) {
	try {
		localStorage.setItem(key, JSON.stringify(value))
	} catch {
		// storage unavailable — the page still works without persistence
	}
}

onMounted(async () => {
	loading.value = true
	try {
		const data = await call("bs.baron_servies.api.store.get_storefront")
		config.value = data.config
		items.value = data.items || []
		groups.value = data.groups || []
		ads.value = data.ads || []
		restoreCart()
		const saved = readJSON(CUSTOMER_KEY, {})
		orderForm.value = { ...orderForm.value, ...saved, notes: "" }
	} catch (e) {
		showError(e?.message || __("فشل التحميل"))
	} finally {
		loading.value = false
	}
})

// Cart survives reloads; re-checked against the current catalogue (prices, availability).
function restoreCart() {
	const byCode = Object.fromEntries(items.value.map((i) => [i.item_code, i]))
	cart.value = readJSON(CART_KEY, [])
		.filter((e) => byCode[e.item_code] && !byCode[e.item_code].sold_out && Number(e.qty) > 0)
		.map((e) => {
			const it = byCode[e.item_code]
			return { ...e, item_name: it.item_name, price: it.price, image: it.image, max: it.max_order_qty }
		})
}

watch(cart, (value) => writeJSON(CART_KEY, value.map(({ item_code, qty }) => ({ item_code, qty }))), { deep: true })

const visibleItems = computed(() => {
	const q = searchQuery.value.trim().toLowerCase()
	return items.value.filter((i) =>
		(!selectedGroup.value || i.item_group === selectedGroup.value) &&
		(!q || (i.item_name || "").toLowerCase().includes(q) || i.item_code.toLowerCase().includes(q))
	)
})

const cartCount = computed(() => cart.value.reduce((sum, e) => sum + Number(e.qty), 0))
const cartTotal = computed(() => cart.value.reduce((sum, e) => sum + e.price * e.qty, 0))
const selectedDeliveryFee = computed(() => {
	const area = config.value.delivery_areas.find((a) => a.area_name === orderForm.value.delivery_area)
	return area ? Number(area.delivery_fee) : 0
})

function cartQty(code) {
	return cart.value.find((e) => e.item_code === code)?.qty || 0
}

function addToCart(item) {
	const existing = cart.value.find((e) => e.item_code === item.item_code)
	const max = Number(item.max_order_qty) || 0
	if (existing) {
		if (max && existing.qty + 1 > max) return showError(__("أقصى كمية لهذا المنتج {0}", [max]))
		existing.qty += 1
	} else {
		cart.value.push({ item_code: item.item_code, item_name: item.item_name, price: item.price, image: item.image, max, qty: 1 })
		showSuccess(__("تمت الإضافة للسلة"))
	}
}

function changeQtyByCode(code, delta) {
	const entry = cart.value.find((e) => e.item_code === code)
	if (!entry) return
	if (delta > 0 && entry.max && entry.qty + delta > entry.max) return showError(__("أقصى كمية لهذا المنتج {0}", [entry.max]))
	entry.qty += delta
	if (entry.qty <= 0) removeFromCart(code)
}

function removeFromCart(code) {
	cart.value = cart.value.filter((e) => e.item_code !== code)
}

function goToCheckout() {
	if (!cart.value.length) return showError(__("السلة فارغة"))
	cartOpen.value = false
	checkoutOpen.value = true
}

const whatsappLink = computed(() => {
	const o = orderSuccess.value
	const number = String(config.value.contact_whatsapp || "").replace(/\D/g, "").replace(/^0+/, "")
	if (!o || !number) return ""
	const lines = [
		__("طلب جديد رقم {0}", [o.sales_order]),
		...o.lines.map((l) => `- ${l.item_name} × ${formatQty(l.qty)}`),
		__("الإجمالي: {0}", [formatPrice(o.total)]),
		`${o.customer_name} — ${o.phone}`,
	]
	return `https://wa.me/${number}?text=${encodeURIComponent(lines.join("\n"))}`
})

async function submitOrder() {
	const f = orderForm.value
	if (!f.customer_name.trim()) return showError(__("الاسم مطلوب"))
	if (f.phone.replace(/\D/g, "").length < 7) return showError(__("رقم الهاتف غير صحيح"))
	if (config.value.delivery_areas.length && !f.delivery_area) return showError(__("يرجى اختيار منطقة التوصيل"))
	if (!f.address.trim()) return showError(__("العنوان مطلوب"))

	placingOrder.value = true
	try {
		// Only item_code + qty are sent; prices, fees and stock are checked on the server
		const result = await call("bs.baron_servies.api.store.create_store_order", {
			customer_name: f.customer_name,
			phone: f.phone,
			delivery_area: f.delivery_area,
			address: f.address,
			items: JSON.stringify(cart.value.map((e) => ({ item_code: e.item_code, qty: e.qty }))),
			notes: f.notes,
		})
		orderSuccess.value = { ...result, customer_name: f.customer_name, lines: cart.value.map((e) => ({ ...e })) }
		writeJSON(CUSTOMER_KEY, { customer_name: f.customer_name, phone: f.phone, delivery_area: f.delivery_area, address: f.address })
		writeJSON(LAST_ORDER_KEY, { order: result.sales_order, phone: f.phone })
		cart.value = []
		f.notes = ""
		checkoutOpen.value = false
	} catch (e) {
		showError(e?.message || __("فشل إنشاء الطلب"))
	} finally {
		placingOrder.value = false
	}
}

function openTracking(order = "", phone = "") {
	const last = readJSON(LAST_ORDER_KEY, {})
	trackForm.value = { order: order || last.order || "", phone: phone || last.phone || orderForm.value.phone || "" }
	trackResult.value = null
	trackingOpen.value = true
	if (trackForm.value.order && trackForm.value.phone) trackOrder()
}

const trackStepIndex = computed(() => TRACK_STEPS.findIndex((s) => s.key === trackResult.value?.status))

async function trackOrder() {
	if (!trackForm.value.order.trim() || !trackForm.value.phone.trim()) return showError(__("أدخل رقم الطلب والهاتف"))
	tracking.value = true
	try {
		trackResult.value = await call("bs.baron_servies.api.store.track_store_order", {
			order: trackForm.value.order.trim(),
			phone: trackForm.value.phone,
		})
	} catch (e) {
		trackResult.value = null
		showError(e?.message || __("لم يتم العثور على الطلب"))
	} finally {
		tracking.value = false
	}
}

function formatQty(v) {
	const n = Number(v || 0)
	return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, "")
}

function formatPrice(value) {
	const n = Number(value || 0)
	const text = n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
	const symbol = { ILS: "₪", USD: "$", JOD: "د.أ" }[config.value.currency] || config.value.currency || ""
	return symbol ? `${text} ${symbol}` : text
}
</script>
