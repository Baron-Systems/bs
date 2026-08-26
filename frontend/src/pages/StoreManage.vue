<template>
	<div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50" dir="rtl">
		<!-- Header -->
		<header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
				<div class="flex items-center gap-3 min-w-0">
					<button @click="goBack" class="p-2 rounded-xl text-slate-600 hover:bg-slate-100 transition-all hover:scale-105 active:scale-95 flex-shrink-0">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
					</button>
					<div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-cyan-500/30">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
						</svg>
					</div>
					<div class="min-w-0">
						<h1 class="text-base sm:text-lg font-bold text-slate-900 truncate">{{ __("إدارة المتجر") }}</h1>
						<p class="text-xs text-slate-500 truncate">{{ __("إعدادات المتجر والأصناف والمناطق") }}</p>
					</div>
				</div>
				<div class="flex items-center gap-2 flex-shrink-0">
					<a href="/bs/store" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md flex items-center gap-1.5">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
						</svg>
						{{ __("معاينة المتجر") }}
					</a>
					<button @click="logout" class="p-2 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-all hover:scale-105 active:scale-95">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
						</svg>
					</button>
				</div>
			</div>
		</header>

		<!-- Main -->
		<main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 sm:py-6 flex flex-col gap-4">
			<!-- Loading -->
			<div v-if="loading" class="flex items-center justify-center py-20">
				<svg class="animate-spin h-10 w-10 text-cyan-600" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
				</svg>
			</div>

			<template v-else>
				<!-- Tab Navigation -->
				<div class="flex gap-2 bg-white rounded-2xl border border-slate-200 shadow-md p-2 overflow-x-auto">
					<button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
						:class="['px-4 py-2 rounded-xl text-sm font-semibold whitespace-nowrap transition-all',
							activeTab === tab.id ? 'bg-gradient-to-l from-cyan-600 to-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100']">
						{{ __(tab.label) }}
					</button>
				</div>

				<!-- Tab: Settings -->
				<section v-if="activeTab === 'settings'" class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-6">
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
						<!-- Enable -->
						<div class="flex items-center justify-between bg-slate-50 rounded-xl p-4 border border-slate-200">
							<div>
								<p class="text-sm font-bold text-slate-800">{{ __("تفعيل المتجر") }}</p>
								<p class="text-xs text-slate-500">{{ __("عند التفعيل يصبح المتجر متاحاً للعملاء") }}</p>
							</div>
							<button @click="settings.is_enabled = !settings.is_enabled; saveSettings()"
								:class="['relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
									settings.is_enabled ? 'bg-emerald-500' : 'bg-slate-300']">
								<span :class="['inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
									settings.is_enabled ? '-translate-x-1' : '-translate-x-6']" />
							</button>
						</div>
						<!-- Store Name -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("اسم المتجر") }}</label>
							<input v-model="settings.store_name" type="text"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
						<!-- Company -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("الشركة") }}</label>
							<select v-model="settings.company"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white transition-all">
								<option value="">{{ __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
							</select>
						</div>
						<!-- Price List -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("قائمة الأسعار") }}</label>
							<select v-model="settings.selling_price_list"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white transition-all">
								<option value="">{{ __("افتراضية") }}</option>
								<option v-for="p in priceLists" :key="p.name" :value="p.name">{{ p.name }}</option>
							</select>
						</div>
						<!-- Default Customer -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("العميل الافتراضي") }}</label>
							<select v-model="settings.default_customer"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white transition-all">
								<option value="">{{ __("اختر العميل") }}</option>
								<option v-for="c in customers" :key="c.name" :value="c.name">{{ c.name }}</option>
							</select>
						</div>
						<!-- Default Warehouse -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("المستودع") }}</label>
							<select v-model="settings.default_warehouse"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white transition-all">
								<option value="">{{ __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
							</select>
						</div>
						<!-- Contact Phone -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("هاتف المتجر") }}</label>
							<input v-model="settings.contact_phone" type="text"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
						<!-- WhatsApp -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("واتساب") }}</label>
							<input v-model="settings.contact_whatsapp" type="text"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
						<!-- Banner Image -->
						<div class="sm:col-span-2">
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("صورة البنر") }}</label>
							<div class="flex items-center gap-3">
								<img v-if="settings.banner_image" :src="settings.banner_image" class="w-32 h-20 object-cover rounded-xl border border-slate-200" />
								<div v-else class="w-32 h-20 bg-slate-100 rounded-xl border border-dashed border-slate-300 flex items-center justify-center">
									<svg class="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
								</div>
								<input v-model="settings.banner_image" type="text" :placeholder="__('رابط الصورة أو ارفع من Frappe')"
									class="flex-1 border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
							</div>
						</div>
					</div>
					<div class="mt-4 flex justify-end">
						<button @click="saveSettings" :disabled="saving"
							class="px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md disabled:opacity-50">
							{{ saving ? __("جاري الحفظ...") : __("حفظ الإعدادات") }}
						</button>
					</div>
				</section>

				<!-- Tab: Delivery Areas -->
				<section v-if="activeTab === 'areas'" class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-sm font-bold text-slate-800">{{ __("مناطق التوصيل وأسعارها") }}</h3>
						<button @click="addArea" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-l from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 transition-all shadow-md flex items-center gap-1.5">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							{{ __("إضافة منطقة") }}
						</button>
					</div>
					<div class="space-y-2">
						<div v-for="(area, idx) in settings.delivery_areas" :key="idx" class="flex items-center gap-3 bg-slate-50 rounded-xl p-3 border border-slate-200">
							<input v-model="area.area_name" type="text" :placeholder="__('اسم المنطقة')"
								class="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
							<input v-model.number="area.delivery_fee" type="number" :placeholder="__('سعر التوصيل')" step="0.01"
								class="w-32 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
							<button @click="removeArea(idx)" class="p-2 rounded-lg text-rose-600 hover:bg-rose-50 transition-all">
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
						<div v-if="!settings.delivery_areas.length" class="text-center py-8 text-sm text-slate-400">
							{{ __("لا توجد مناطق. اضغط \"إضافة منطقة\" للبدء") }}
						</div>
					</div>
					<div v-if="settings.delivery_areas.length" class="mt-4 flex justify-end">
						<button @click="saveSettings" :disabled="saving"
							class="px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md disabled:opacity-50">
							{{ saving ? __("جاري الحفظ...") : __("حفظ المناطق") }}
						</button>
					</div>
				</section>

				<!-- Tab: Items -->
				<section v-if="activeTab === 'items'" class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-6">
					<!-- Search -->
					<div class="relative mb-4">
						<input v-model="itemSearch" type="text" :placeholder="__('بحث عن صنف...')"
							class="w-full border border-slate-300 rounded-xl ps-10 pe-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"
							@input="debouncedSearch" />
						<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</div>
					<!-- Items Table -->
					<div class="overflow-x-auto">
						<table class="min-w-full text-xs">
							<thead class="bg-slate-50">
								<tr>
									<th class="px-3 py-2.5 text-start font-bold text-slate-700">{{ __("الصنف") }}</th>
									<th class="px-3 py-2.5 text-start font-bold text-slate-700">{{ __("المجموعة") }}</th>
									<th class="px-3 py-2.5 text-end font-bold text-slate-700">{{ __("سعر المتجر") }}</th>
									<th class="px-3 py-2.5 text-center font-bold text-slate-700">{{ __("منشور") }}</th>
									<th class="px-3 py-2.5 text-center font-bold text-slate-700">{{ __("إجراءات") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-100">
								<tr v-for="item in adminItems" :key="item.item_code" class="hover:bg-slate-50 transition-colors">
									<td class="px-3 py-2">
										<div class="flex items-center gap-2">
											<img v-if="item.store_image || item.item_image" :src="item.store_image || item.item_image" class="w-10 h-10 rounded-lg object-cover border border-slate-200" />
											<div v-else class="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
												<svg class="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
												</svg>
											</div>
											<div class="min-w-0">
												<p class="font-semibold text-slate-900 truncate">{{ item.item_name }}</p>
												<p class="text-xs text-slate-400">{{ item.item_code }}</p>
											</div>
										</div>
									</td>
									<td class="px-3 py-2 text-slate-600">{{ item.item_group || "-" }}</td>
									<td class="px-3 py-2 text-end">
										<input v-model.number="item.store_price" type="number" step="0.01"
											class="w-24 border border-slate-300 rounded-lg px-2 py-1 text-xs text-end focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"
											@change="saveItem(item)" />
									</td>
									<td class="px-3 py-2 text-center">
										<button @click="togglePublish(item)"
											:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
												item.is_published ? 'bg-emerald-500' : 'bg-slate-300']">
											<span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
												item.is_published ? '-translate-x-1' : '-translate-x-6']" />
										</button>
									</td>
									<td class="px-3 py-2 text-center">
										<button @click="openItemEditor(item)"
											class="px-2 py-1 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all">
											{{ __("تحرير") }}
										</button>
									</td>
								</tr>
							</tbody>
						</table>
						<div v-if="!adminItems.length" class="text-center py-8 text-sm text-slate-400">{{ __("لا توجد أصناف") }}</div>
					</div>
				</section>

				<!-- Tab: Advertisements -->
				<section v-if="activeTab === 'ads'" class="bg-white rounded-2xl border border-slate-200 shadow-md p-4 sm:p-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-sm font-bold text-slate-800">{{ __("الإعلانات") }}</h3>
						<button @click="openAdEditor()" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-l from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 transition-all shadow-md flex items-center gap-1.5">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							{{ __("إضافة إعلان") }}
						</button>
					</div>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						<div v-for="ad in ads" :key="ad.name" class="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden flex flex-col">
							<div class="relative h-32 bg-slate-200">
								<img v-if="ad.image" :src="ad.image" class="w-full h-full object-cover" />
								<div v-else class="w-full h-full flex items-center justify-center">
									<svg class="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
								</div>
								<div class="absolute top-2 right-2">
									<button @click="toggleAd(ad)"
										:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors shadow-md',
											ad.is_active ? 'bg-emerald-500' : 'bg-slate-400']">
										<span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
											ad.is_active ? '-translate-x-1' : '-translate-x-6']" />
									</button>
								</div>
							</div>
							<div class="p-3 flex-1 flex flex-col gap-2">
								<p class="text-sm font-bold text-slate-900 truncate">{{ ad.title }}</p>
								<div v-if="ad.content" class="text-xs text-slate-500 line-clamp-2 flex-1" v-html="ad.content"></div>
								<div v-if="ad.start_date || ad.end_date" class="text-xs text-slate-400">
									{{ ad.start_date || "?" }} → {{ ad.end_date || "?" }}
								</div>
								<div class="flex items-center gap-2 mt-1">
									<button @click="openAdEditor(ad)" class="flex-1 px-2 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-100 transition-all">{{ __("تحرير") }}</button>
									<button @click="deleteAd(ad)" class="px-2 py-1.5 rounded-lg text-xs font-semibold text-rose-600 border border-rose-200 hover:bg-rose-50 transition-all">{{ __("حذف") }}</button>
								</div>
							</div>
						</div>
					</div>
					<div v-if="!ads.length" class="text-center py-12 text-slate-400">
						<svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6a1.76 1.76 0 002.585-1.4c.02-.357.134-.708.332-1.02L10 3" />
						</svg>
						<p class="text-sm">{{ __("لا توجد إعلانات. اضغط إضافة إعلان للبدء") }}</p>
					</div>
				</section>
			</template>
		</main>

		<!-- Item Editor Modal -->
		<div v-if="editingItem" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="editingItem = null">
			<div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold text-slate-900">{{ __("تحرير صنف المتجر") }}</h3>
					<button @click="editingItem = null" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<div class="space-y-4">
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("الصنف") }}</label>
						<p class="text-sm font-bold text-slate-900">{{ editingItem.item_name }} ({{ editingItem.item_code }})</p>
					</div>
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("سعر المتجر") }}</label>
						<input v-model.number="editingItem.store_price" type="number" step="0.01"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
					</div>
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("صورة المتجر") }}</label>
						<div class="flex items-center gap-3">
							<img v-if="editingItem.store_image" :src="editingItem.store_image" class="w-20 h-20 object-cover rounded-xl border border-slate-200" />
							<div v-else class="w-20 h-20 bg-slate-100 rounded-xl border border-dashed border-slate-300 flex items-center justify-center">
								<svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
							<input v-model="editingItem.store_image" type="text" :placeholder="__('رابط الصورة')"
								class="flex-1 border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
					</div>
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("وصف المتجر") }}</label>
						<textarea v-model="editingItem.store_description" rows="3"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all"></textarea>
					</div>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("ترتيب العرض") }}</label>
							<input v-model.number="editingItem.display_order" type="number"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
						<div>
							<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("أقصى كمية طلب") }}</label>
							<input v-model.number="editingItem.max_order_qty" type="number" step="0.01"
								class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all" />
						</div>
					</div>
				</div>
				<div class="mt-6 flex justify-end gap-2">
					<button @click="editingItem = null" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all">{{ __("إلغاء") }}</button>
					<button @click="saveEditedItem" :disabled="saving"
						class="px-5 py-2 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all shadow-md disabled:opacity-50">
						{{ saving ? __("جاري الحفظ...") : __("حفظ") }}
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Ad Editor Modal -->
	<div v-if="editingAd" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="editingAd = null">
		<div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
			<div class="flex items-center justify-between mb-4">
				<h3 class="text-lg font-bold text-slate-900">{{ editingAd.name ? __("تحرير إعلان") : __("إضافة إعلان") }}</h3>
				<button @click="editingAd = null" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="space-y-4">
				<div>
					<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("العنوان") }}</label>
					<input v-model="editingAd.title" type="text"
						class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
				</div>
				<div>
					<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("صورة الإعلان") }}</label>
					<div class="flex items-center gap-3">
						<img v-if="editingAd.image" :src="editingAd.image" class="w-24 h-16 object-cover rounded-xl border border-slate-200" />
						<div v-else class="w-24 h-16 bg-slate-100 rounded-xl border border-dashed border-slate-300 flex items-center justify-center">
							<svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
						<input v-model="editingAd.image" type="text" :placeholder="__('رابط الصورة')"
							class="flex-1 border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
					</div>
				</div>
				<div>
					<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("المحتوى") }}</label>
					<textarea v-model="editingAd.content" rows="3"
						class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all"></textarea>
				</div>
				<div>
					<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("رابط عند النقر") }}</label>
					<input v-model="editingAd.link_url" type="text" :placeholder="__('https://... (اختياري)')"
						class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("تاريخ البداية") }}</label>
						<input v-model="editingAd.start_date" type="date"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
					</div>
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("تاريخ النهاية") }}</label>
						<input v-model="editingAd.end_date" type="date"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
					</div>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div class="flex items-center justify-between bg-slate-50 rounded-xl p-3 border border-slate-200">
						<span class="text-xs font-semibold text-slate-700">{{ __("تفعيل") }}</span>
						<button @click="editingAd.is_active = !editingAd.is_active"
							:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
								editingAd.is_active ? 'bg-emerald-500' : 'bg-slate-300']">
							<span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
								editingAd.is_active ? '-translate-x-1' : '-translate-x-6']" />
						</button>
					</div>
					<div>
						<label class="block text-xs font-semibold text-slate-700 mb-1.5">{{ __("ترتيب العرض") }}</label>
						<input v-model.number="editingAd.display_order" type="number"
							class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all" />
					</div>
				</div>
			</div>
			<div class="mt-6 flex justify-end gap-2">
				<button @click="editingAd = null" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all">{{ __("إلغاء") }}</button>
				<button @click="saveAd" :disabled="saving"
					class="px-5 py-2 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 transition-all shadow-md disabled:opacity-50">
					{{ saving ? __("جاري الحفظ...") : __("حفظ") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { onMounted, ref } from "vue"

const { showSuccess, showError } = useToast()

const tabs = [
	{ id: "settings", label: "الإعدادات" },
	{ id: "areas", label: "مناطق التوصيل" },
	{ id: "items", label: "الأصناف" },
	{ id: "ads", label: "الإعلانات" },
]
const activeTab = ref("settings")

const loading = ref(false)
const saving = ref(false)
const settings = ref({
	is_enabled: 0,
	store_name: "",
	company: "",
	banner_image: "",
	contact_phone: "",
	contact_whatsapp: "",
	default_customer: "",
	default_warehouse: "",
	selling_price_list: "",
	delivery_areas: [],
})

const companies = ref([])
const customers = ref([])
const warehouses = ref([])
const priceLists = ref([])
const adminItems = ref([])
const itemSearch = ref("")
const editingItem = ref(null)
const ads = ref([])
const editingAd = ref(null)
let searchDebounce = null

onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	loading.value = true
	try {
		await Promise.all([loadSettings(), loadCompanies(), loadCustomers(), loadWarehouses(), loadPriceLists(), loadAdminItems(), loadAds()])
	} catch (e) {
		showError(e?.message || __("فشل التحميل"))
	} finally {
		loading.value = false
	}
})

async function loadSettings() {
	const data = await call("bs.baron_servies.api.store.get_admin_settings")
	settings.value = { ...settings.value, ...data }
	if (!settings.value.delivery_areas) settings.value.delivery_areas = []
}

async function loadCompanies() {
	companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
}

async function loadCustomers() {
	customers.value = await call("bs.baron_servies.api.customers.get_customers", { search: "" }) || []
}

async function loadWarehouses() {
	warehouses.value = await call("bs.baron_servies.api.stock_reconciliation.get_warehouses", { company: settings.value.company || "" }) || []
}

async function loadPriceLists() {
	priceLists.value = await call("bs.baron_servies.api.stock_reconciliation.get_price_lists") || []
}

async function loadAdminItems() {
	adminItems.value = await call("bs.baron_servies.api.store.get_admin_items", { search: itemSearch.value || "" }) || []
}

async function saveSettings() {
	saving.value = true
	try {
		await call("bs.baron_servies.api.store.update_admin_settings", { data: settings.value })
		showSuccess(__("تم حفظ الإعدادات"))
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
	} finally {
		saving.value = false
	}
}

function addArea() {
	if (!settings.value.delivery_areas) settings.value.delivery_areas = []
	settings.value.delivery_areas.push({ area_name: "", delivery_fee: 0 })
}

function removeArea(idx) {
	settings.value.delivery_areas.splice(idx, 1)
}

async function togglePublish(item) {
	try {
		const result = await call("bs.baron_servies.api.store.toggle_store_item", {
			item_code: item.item_code,
			is_published: item.is_published ? 0 : 1,
		})
		item.is_published = result.is_published
		showSuccess(item.is_published ? __("تم نشر الصنف") : __("تم إلغاء النشر"))
	} catch (e) {
		showError(e?.message || __("فشل"))
	}
}

async function saveItem(item) {
	try {
		await call("bs.baron_servies.api.store.upsert_store_item", {
			item_code: item.item_code,
			price: item.store_price,
			image: item.store_image,
			description: item.store_description,
			is_published: item.is_published ? 1 : 0,
			display_order: item.display_order || 0,
			max_order_qty: item.max_order_qty || 0,
		})
		showSuccess(__("تم حفظ الصنف"))
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
	}
}

function openItemEditor(item) {
	editingItem.value = { ...item }
}

async function saveEditedItem() {
	saving.value = true
	try {
		await call("bs.baron_servies.api.store.upsert_store_item", {
			item_code: editingItem.value.item_code,
			price: editingItem.value.store_price,
			image: editingItem.value.store_image,
			description: editingItem.value.store_description,
			is_published: editingItem.value.is_published ? 1 : 0,
			display_order: editingItem.value.display_order || 0,
			max_order_qty: editingItem.value.max_order_qty || 0,
		})
		// Update in list
		const idx = adminItems.value.findIndex((i) => i.item_code === editingItem.value.item_code)
		if (idx >= 0) {
			adminItems.value[idx] = { ...editingItem.value }
		}
		editingItem.value = null
		showSuccess(__("تم حفظ الصنف"))
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
	} finally {
		saving.value = false
	}
}

function debouncedSearch() {
	if (searchDebounce) clearTimeout(searchDebounce)
	searchDebounce = setTimeout(() => loadAdminItems(), 400)
}

// ===== Ads =====
async function loadAds() {
	ads.value = await call("bs.baron_servies.api.store.get_admin_ads") || []
}

function openAdEditor(ad = null) {
	if (ad) {
		editingAd.value = { ...ad }
	} else {
		editingAd.value = {
			title: "",
			content: "",
			image: "",
			link_url: "",
			is_active: 1,
			display_order: 0,
			start_date: "",
			end_date: "",
		}
	}
}

async function saveAd() {
	if (!editingAd.value.title || !editingAd.value.title.trim()) {
		showError(__("العنوان مطلوب"))
		return
	}
	saving.value = true
	try {
		const payload = {
			title: editingAd.value.title,
			content: editingAd.value.content || "",
			image: editingAd.value.image || "",
			link_url: editingAd.value.link_url || "",
			is_active: editingAd.value.is_active ? 1 : 0,
			display_order: editingAd.value.display_order || 0,
			start_date: editingAd.value.start_date || null,
			end_date: editingAd.value.end_date || null,
		}
		if (editingAd.value.name) {
			await call("bs.baron_servies.api.store.update_ad", { name: editingAd.value.name, ...payload })
		} else {
			await call("bs.baron_servies.api.store.create_ad", payload)
		}
		await loadAds()
		editingAd.value = null
		showSuccess(__("تم حفظ الإعلان"))
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
	} finally {
		saving.value = false
	}
}

async function toggleAd(ad) {
	try {
		const result = await call("bs.baron_servies.api.store.toggle_ad", {
			name: ad.name,
			is_active: ad.is_active ? 0 : 1,
		})
		ad.is_active = result.is_active
		showSuccess(ad.is_active ? __("تم تفعيل الإعلان") : __("تم تعطيل الإعلان"))
	} catch (e) {
		showError(e?.message || __("فشل"))
	}
}

async function deleteAd(ad) {
	if (!confirm(__("هل أنت متأكد من حذف هذا الإعلان؟"))) return
	try {
		await call("bs.baron_servies.api.store.delete_ad", { name: ad.name })
		await loadAds()
		showSuccess(__("تم حذف الإعلان"))
	} catch (e) {
		showError(e?.message || __("فشل الحذف"))
	}
}

function goBack() {
	router.push({ name: "Home" })
}

async function logout() {
	await session.logout.submit()
}
</script>
