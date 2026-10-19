<template>
	<div class="w-full">
		<main class="flex flex-col gap-5">
			<PageHeader :eyebrow="__('المتجر')" :title="__('إدارة المتجر')" :subtitle="__('الطلبات والإعدادات والأصناف والمناطق')">
				<template #actions>
					<a href="/bs/store" target="_blank" class="bs-btn bs-btn-secondary">
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
						</svg>
						{{ __("معاينة المتجر") }}
					</a>
				</template>
			</PageHeader>
			<!-- Loading -->
			<div v-if="loading" class="flex items-center justify-center py-20">
				<svg class="animate-spin h-10 w-10 text-cyan-600" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
				</svg>
			</div>

			<template v-else>
				<!-- Tab Navigation -->
				<div class="bs-segment self-start max-w-full">
					<button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
						:class="['bs-segment-item', activeTab === tab.id ? 'bs-segment-item-active' : '']">
						{{ __(tab.label) }}
						<span v-if="tab.id === 'orders' && orderCounts.New" class="ms-1 rounded-full bg-rose-500 px-1.5 text-[10px] font-bold text-white">{{ orderCounts.New }}</span>
					</button>
				</div>

				<!-- Tab: Orders -->
				<section v-if="activeTab === 'orders'" class="bs-card p-4 sm:p-6">
					<div class="mb-4 flex flex-wrap items-center gap-2">
						<button
							v-for="st in ORDER_FILTERS"
							:key="st.key"
							type="button"
							class="rounded-full px-3 py-1 text-xs font-semibold"
							:class="orderStatus === st.key ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
							@click="orderStatus = st.key"
						>
							{{ __(st.label) }}<span v-if="st.key" class="ms-1 opacity-70">{{ orderCounts[st.key] || 0 }}</span>
						</button>
						<input v-model="orderSearch" type="search" :placeholder="__('رقم الطلب أو الاسم أو الهاتف')" class="bs-input bs-input-sm ms-auto !w-56" />
					</div>
					<div v-if="ordersLoading && !orders.length" class="bs-empty">{{ __("جاري التحميل...") }}</div>
					<div v-else-if="!orders.length" class="bs-empty">{{ __("لا توجد طلبات") }}</div>
					<div v-else class="bs-table-wrap">
						<table class="bs-table w-full">
							<thead>
								<tr>
									<th class="text-start">{{ __("الطلب") }}</th>
									<th class="text-start">{{ __("العميل") }}</th>
									<th class="hidden text-start md:table-cell">{{ __("المنطقة") }}</th>
									<th class="text-center">{{ __("الإجمالي") }}</th>
									<th class="text-center">{{ __("الحالة") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="o in orders" :key="o.name" class="cursor-pointer" @click="openOrder(o.name)">
									<td>
										<p class="font-semibold text-slate-900" dir="ltr" style="text-align: right">{{ o.name }}</p>
										<p class="text-[11px] text-slate-400">{{ formatDateTime(o.creation) }}</p>
									</td>
									<td>
										<p class="font-semibold text-slate-800">{{ o.store_customer_name || o.customer }}</p>
										<p class="text-[11px] text-slate-400" dir="ltr" style="text-align: right">{{ o.store_phone }}</p>
									</td>
									<td class="hidden text-slate-600 md:table-cell">{{ o.store_delivery_area || "—" }}</td>
									<td class="text-center font-semibold tabular-nums">{{ formatMoney(o.grand_total) }}</td>
									<td class="text-center"><span class="bs-badge" :class="ORDER_STATUS[o.store_status || 'New'].cls">{{ __(ORDER_STATUS[o.store_status || "New"].label) }}</span></td>
								</tr>
							</tbody>
						</table>
					</div>
				</section>

				<!-- Tab: Settings -->
				<section v-if="activeTab === 'settings'" class="bs-card p-4 sm:p-6">
					<p v-if="settings.missing && settings.missing.length" class="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
						{{ __("المتجر لا يستقبل طلبات قبل تحديد: {0}", [settings.missing.join("، ")]) }}
					</p>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
						<!-- Enable -->
						<div class="flex items-center justify-between bg-slate-50 rounded-xl p-4 border border-slate-200">
							<div>
								<p class="text-sm font-bold text-slate-800">{{ __("تفعيل المتجر") }}</p>
								<p class="text-xs text-slate-500">{{ __("عند التفعيل يصبح المتجر متاحاً للعملاء") }}</p>
							</div>
							<button @click="toggleStore"
								:class="['relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
									settings.is_enabled ? 'bg-emerald-500' : 'bg-slate-300']">
								<span :class="['inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
									settings.is_enabled ? '-translate-x-1' : '-translate-x-6']" />
							</button>
						</div>
						<!-- Store Name -->
						<div>
							<label class="bs-label">{{ __("اسم المتجر") }}</label>
							<input v-model="settings.store_name" type="text"
								class="bs-input w-full px-3 py-2.5" />
						</div>
						<!-- Company -->
						<div>
							<label class="bs-label">{{ __("الشركة") }}</label>
							<select v-model="settings.company"
								class="bs-input w-full px-3 py-2.5">
								<option value="">{{ __("اختر الشركة") }}</option>
								<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
							</select>
						</div>
						<!-- Price List -->
						<div>
							<label class="bs-label">{{ __("قائمة الأسعار") }}</label>
							<select v-model="settings.selling_price_list"
								class="bs-input w-full px-3 py-2.5">
								<option value="">{{ __("افتراضية") }}</option>
								<option v-for="p in priceLists" :key="p.name" :value="p.name">{{ p.name }}</option>
							</select>
						</div>
						<!-- New customers -->
						<div>
							<label class="bs-label">{{ __("مجموعة العملاء الجدد") }}</label>
							<select v-model="settings.customer_group" class="bs-input w-full px-3 py-2.5">
								<option value="">{{ __("افتراضي إعدادات البيع") }}</option>
								<option v-for="g in settingsOptions.customer_groups" :key="g" :value="g">{{ g }}</option>
							</select>
							<p class="mt-1 text-[11px] text-slate-400">{{ __("كل رقم هاتف جديد يُنشأ له عميل في هذه المجموعة") }}</p>
						</div>
						<div>
							<label class="bs-label">{{ __("المنطقة الجغرافية للعملاء الجدد") }}</label>
							<select v-model="settings.territory" class="bs-input w-full px-3 py-2.5">
								<option value="">{{ __("افتراضي إعدادات البيع") }}</option>
								<option v-for="t in settingsOptions.territories" :key="t" :value="t">{{ t }}</option>
							</select>
						</div>
						<!-- Stock policy -->
						<div>
							<label class="bs-label">{{ __("الأصناف التي نفد رصيدها") }}</label>
							<select v-model="settings.out_of_stock_policy" class="bs-input w-full px-3 py-2.5">
								<option value="Allow">{{ __("السماح بالطلب (يُراجع عند التأكيد)") }}</option>
								<option value="Show Sold Out">{{ __("إظهار «نفد» ومنع الطلب") }}</option>
								<option value="Hide">{{ __("إخفاء من المتجر") }}</option>
							</select>
							<p class="mt-1 text-[11px] text-slate-400">{{ __("زر «غير متوفر» في الأصناف يعمل دائمًا بغض النظر عن الرصيد") }}</p>
						</div>
						<div>
							<label class="bs-label">{{ __("طريقة الدفع عند التسليم") }}</label>
							<select v-model="settings.delivery_mode_of_payment" class="bs-input w-full px-3 py-2.5">
								<option value="">—</option>
								<option v-for="m in settingsOptions.modes_of_payment" :key="m" :value="m">{{ m }}</option>
							</select>
						</div>
						<!-- Default Warehouse -->
						<div>
							<label class="bs-label">{{ __("المستودع") }}</label>
							<select v-model="settings.default_warehouse"
								class="bs-input w-full px-3 py-2.5">
								<option value="">{{ __("اختر المستودع") }}</option>
								<option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
							</select>
						</div>
						<!-- Contact Phone -->
						<div>
							<label class="bs-label">{{ __("هاتف المتجر") }}</label>
							<input v-model="settings.contact_phone" type="text"
								class="bs-input w-full px-3 py-2.5" />
						</div>
						<!-- WhatsApp -->
						<div>
							<label class="bs-label">{{ __("واتساب") }}</label>
							<input v-model="settings.contact_whatsapp" type="text"
								class="bs-input w-full px-3 py-2.5" />
						</div>
						<!-- Banner Image -->
						<div class="sm:col-span-2">
							<label class="bs-label">{{ __("صورة البنر") }}</label>
							<div class="flex items-center gap-3">
								<img v-if="settings.banner_image" :src="settings.banner_image" class="w-32 h-20 object-cover rounded-xl border border-slate-200" />
								<div v-else class="w-32 h-20 bg-slate-100 rounded-xl border border-dashed border-slate-200 flex items-center justify-center">
									<svg class="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
								</div>
								<input v-model="settings.banner_image" type="text" :placeholder="__('رابط الصورة أو ارفع من Frappe')"
									class="bs-input flex-1 px-3 py-2.5" />
							</div>
						</div>
					</div>
					<div class="mt-4 flex justify-end">
						<button @click="saveSettings" :disabled="saving"
							class="px-5 py-2.5 rounded-xl text-sm font-bold text-white transition-all shadow-sm disabled:opacity-50 bg-cyan-600 hover:bg-cyan-700">
							{{ saving ? __("جاري الحفظ...") : __("حفظ الإعدادات") }}
						</button>
					</div>
				</section>

				<!-- Tab: Delivery Areas -->
				<section v-if="activeTab === 'areas'" class="bs-card p-4 sm:p-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-sm font-bold text-slate-800">{{ __("مناطق التوصيل وأسعارها") }}</h3>
						<button @click="addArea" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all shadow-sm flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							{{ __("إضافة منطقة") }}
						</button>
					</div>
					<div class="space-y-2">
						<div v-for="(area, idx) in settings.delivery_areas" :key="idx" class="flex items-center gap-3 bg-slate-50 rounded-xl p-3 border border-slate-200">
							<input v-model="area.area_name" type="text" :placeholder="__('اسم المنطقة')"
								class="bs-input bs-input-sm flex-1 px-3 py-2" />
							<input v-model.number="area.delivery_fee" type="number" :placeholder="__('سعر التوصيل')" step="0.01"
								class="bs-input bs-input-sm w-32 px-3 py-2" />
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
							class="px-5 py-2.5 rounded-xl text-sm font-bold text-white transition-all shadow-sm disabled:opacity-50 bg-cyan-600 hover:bg-cyan-700">
							{{ saving ? __("جاري الحفظ...") : __("حفظ المناطق") }}
						</button>
					</div>
				</section>

				<!-- Tab: Items -->
				<section v-if="activeTab === 'items'" class="bs-card p-4 sm:p-6">
					<!-- Search -->
					<div class="relative mb-4">
						<input v-model="itemSearch" type="text" :placeholder="__('بحث عن صنف...')"
							class="bs-input w-full ps-10 pe-3 py-2.5"
							@input="debouncedSearch" />
						<svg class="absolute inset-y-0 start-3 my-auto w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</div>
					<label class="mb-3 flex items-center gap-2 text-xs text-slate-600">
						<input v-model="onlyPublished" type="checkbox" class="rounded border-slate-300" @change="loadAdminItems" />
						{{ __("المنشورة فقط") }}
					</label>
					<div class="bs-table-wrap">
						<table class="bs-table w-full min-w-[860px]">
							<thead>
								<tr>
									<th class="text-start">{{ __("الصنف") }}</th>
									<th class="text-start">{{ __("المجموعة") }}</th>
									<th class="text-center">{{ __("الرصيد") }}</th>
									<th class="text-center">{{ __("سعر المتجر") }}</th>
									<th class="text-center">{{ __("سعر خاص") }}</th>
									<th class="text-center">{{ __("منشور") }}</th>
									<th class="text-center">{{ __("غير متوفر") }}</th>
									<th class="text-center"></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="item in adminItems" :key="item.item_code">
									<td>
										<div class="flex items-center gap-2">
											<img v-if="item.store_image || item.item_image" :src="item.store_image || item.item_image" class="w-10 h-10 rounded-lg object-cover border border-slate-200" alt="" />
											<div v-else class="w-10 h-10 bg-slate-100 rounded-lg"></div>
											<div class="min-w-0">
												<p class="font-semibold text-slate-900 truncate">{{ item.item_name }}</p>
												<p class="text-[11px] text-slate-400">{{ item.item_code }} · {{ item.stock_uom }}</p>
											</div>
										</div>
									</td>
									<td class="text-slate-600">{{ item.item_group || "—" }}</td>
									<td class="text-center tabular-nums" :class="item.actual_qty > 0 ? 'text-slate-700' : 'text-rose-600'">{{ formatQty(item.actual_qty) }}</td>
									<td class="text-center">
										<p class="font-semibold tabular-nums" :class="item.effective_price > 0 ? 'text-slate-900' : 'text-rose-600'">{{ item.effective_price > 0 ? formatMoney(item.effective_price) : __("بدون سعر") }}</p>
										<p class="text-[10px] text-slate-400">{{ __(PRICE_SOURCES[item.price_source] || "") }}</p>
									</td>
									<td class="text-center">
										<input v-model.number="item.store_price" type="number" min="0" step="0.01" :placeholder="__('من القائمة')"
											class="bs-input bs-input-sm !w-24 text-center" @change="saveItem(item)" />
									</td>
									<td class="text-center">
										<button @click="togglePublish(item)" :title="item.effective_price > 0 ? '' : __('لا يظهر في المتجر بدون سعر')"
											:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors', item.is_published ? 'bg-emerald-500' : 'bg-slate-300']">
											<span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform', item.is_published ? '-translate-x-1' : '-translate-x-6']" />
										</button>
									</td>
									<td class="text-center">
										<button v-if="item.is_published" @click="toggleUnavailable(item)"
											:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors', item.is_unavailable ? 'bg-rose-500' : 'bg-slate-300']">
											<span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform', item.is_unavailable ? '-translate-x-1' : '-translate-x-6']" />
										</button>
									</td>
									<td class="text-center">
										<button @click="openItemEditor(item)" class="bs-btn bs-btn-secondary bs-btn-sm">{{ __("تحرير") }}</button>
									</td>
								</tr>
							</tbody>
						</table>
						<div v-if="!adminItems.length" class="text-center py-8 text-sm text-slate-400">{{ __("لا توجد أصناف") }}</div>
					</div>
				</section>

				<!-- Tab: Advertisements -->
				<section v-if="activeTab === 'ads'" class="bs-card p-4 sm:p-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-sm font-bold text-slate-800">{{ __("الإعلانات") }}</h3>
						<button @click="openAdEditor()" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all shadow-sm flex items-center gap-1.5 bg-amber-600 hover:bg-amber-700">
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
										:class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors shadow-sm',
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
									<button @click="openAdEditor(ad)" class="flex-1 px-2 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-slate-100 transition-all">{{ __("تحرير") }}</button>
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
						<label class="bs-label">{{ __("الصنف") }}</label>
						<p class="text-sm font-bold text-slate-900">{{ editingItem.item_name }} ({{ editingItem.item_code }})</p>
					</div>
					<div>
						<label class="bs-label">{{ __("سعر خاص بالمتجر") }}</label>
						<input v-model.number="editingItem.store_price" type="number" min="0" step="0.01" :placeholder="__('اتركه فارغًا لاستخدام قائمة الأسعار')"
							class="bs-input w-full px-3 py-2.5" />
						<p class="mt-1 text-[11px] text-slate-400">{{ __("السعر الحالي: {0}", [formatMoney(editingItem.effective_price)]) }}</p>
					</div>
					<div>
						<label class="bs-label">{{ __("صورة المتجر") }}</label>
						<div class="flex items-center gap-3">
							<img v-if="editingItem.store_image" :src="editingItem.store_image" class="w-20 h-20 object-cover rounded-xl border border-slate-200" />
							<div v-else class="w-20 h-20 bg-slate-100 rounded-xl border border-dashed border-slate-200 flex items-center justify-center">
								<svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
							<input v-model="editingItem.store_image" type="text" :placeholder="__('رابط الصورة')"
								class="bs-input flex-1 px-3 py-2.5" />
						</div>
					</div>
					<div>
						<label class="bs-label">{{ __("وصف المتجر") }}</label>
						<textarea v-model="editingItem.store_description" rows="3"
							class="bs-input w-full px-3 py-2.5"></textarea>
					</div>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label class="bs-label">{{ __("ترتيب العرض") }}</label>
							<input v-model.number="editingItem.display_order" type="number"
								class="bs-input w-full px-3 py-2.5" />
						</div>
						<div>
							<label class="bs-label">{{ __("أقصى كمية طلب") }}</label>
							<input v-model.number="editingItem.max_order_qty" type="number" step="0.01"
								class="bs-input w-full px-3 py-2.5" />
						</div>
					</div>
				</div>
				<div class="mt-6 flex justify-end gap-2">
					<button @click="editingItem = null" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all">{{ __("إلغاء") }}</button>
					<button @click="saveEditedItem" :disabled="saving"
						class="px-5 py-2 rounded-xl text-sm font-bold text-white transition-all shadow-sm disabled:opacity-50 bg-cyan-600 hover:bg-cyan-700">
						{{ saving ? __("جاري الحفظ...") : __("حفظ") }}
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Order detail -->
	<div v-if="order" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="order = null">
		<div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-5 sm:p-6 max-h-[92vh] overflow-y-auto">
			<div class="mb-4 flex items-start justify-between gap-3">
				<div>
					<h3 class="text-lg font-bold text-slate-900" dir="ltr" style="text-align: right">{{ order.name }}</h3>
					<p class="text-xs text-slate-500">{{ formatDateTime(order.creation) }}</p>
				</div>
				<div class="flex items-center gap-2">
					<span class="bs-badge" :class="ORDER_STATUS[order.status].cls">{{ __(ORDER_STATUS[order.status].label) }}</span>
					<button type="button" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100" :aria-label="__('إغلاق')" @click="order = null">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
					</button>
				</div>
			</div>

			<div class="grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm sm:grid-cols-2">
				<div>
					<p class="text-[11px] text-slate-400">{{ __("العميل") }}</p>
					<p class="font-semibold text-slate-900">{{ order.store_customer_name }}</p>
					<p v-if="order.customer !== order.store_customer_name" class="text-[11px] text-slate-500">{{ __("مسجّل باسم: {0}", [order.customer]) }}</p>
				</div>
				<div>
					<p class="text-[11px] text-slate-400">{{ __("الهاتف") }}</p>
					<div class="flex items-center gap-2">
						<a :href="`tel:${order.store_phone}`" class="font-semibold text-blue-600" dir="ltr">{{ order.store_phone }}</a>
						<a :href="customerWhatsapp" target="_blank" rel="noopener" class="bs-badge bs-badge-green">{{ __("واتساب") }}</a>
					</div>
				</div>
				<div>
					<p class="text-[11px] text-slate-400">{{ __("المنطقة") }}</p>
					<p class="font-semibold text-slate-900">{{ order.store_delivery_area || "—" }}</p>
				</div>
				<div>
					<p class="text-[11px] text-slate-400">{{ __("العنوان") }}</p>
					<p class="text-slate-800">{{ order.store_address || "—" }}</p>
				</div>
				<div v-if="order.store_notes" class="sm:col-span-2">
					<p class="text-[11px] text-slate-400">{{ __("ملاحظات") }}</p>
					<p class="text-slate-800">{{ order.store_notes }}</p>
				</div>
			</div>

			<div class="bs-table-wrap mt-4">
				<table class="bs-table w-full">
					<thead>
						<tr>
							<th class="text-start">{{ __("الصنف") }}</th>
							<th class="text-center">{{ __("الرصيد") }}</th>
							<th class="text-center">{{ __("الكمية") }}</th>
							<th class="text-center">{{ __("السعر") }}</th>
							<th class="text-center">{{ __("المبلغ") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="it in order.items" :key="it.name">
							<td class="font-semibold text-slate-800">{{ it.is_delivery ? __("رسوم التوصيل") : it.item_name }}</td>
							<td class="text-center tabular-nums" :class="it.is_delivery ? 'text-slate-300' : (it.actual_qty || 0) >= it.qty ? 'text-slate-600' : 'font-bold text-rose-600'">
								{{ it.is_delivery ? "—" : formatQty(it.actual_qty) }}
							</td>
							<td class="text-center">
								<input v-if="order.status === 'New' && !it.is_delivery" v-model.number="it.qty" type="number" min="0" step="any" class="bs-input bs-input-sm !w-20 text-center" />
								<span v-else class="tabular-nums">{{ formatQty(it.qty) }} <span class="text-[11px] text-slate-400">{{ it.uom }}</span></span>
							</td>
							<td class="text-center tabular-nums">{{ formatMoney(it.rate) }}</td>
							<td class="text-center font-semibold tabular-nums">{{ formatMoney(it.qty * it.rate) }}</td>
						</tr>
					</tbody>
					<tfoot>
						<tr class="border-t border-slate-200 bg-slate-50">
							<td colspan="4" class="px-3 py-2 text-end font-bold">{{ __("الإجمالي") }}</td>
							<td class="px-3 py-2 text-center font-extrabold tabular-nums">{{ formatMoney(orderLiveTotal) }}</td>
						</tr>
					</tfoot>
				</table>
			</div>
			<p v-if="order.status === 'New'" class="mt-2 text-[11px] text-slate-500">{{ __("عدّل الكميات أو اجعلها 0 لحذف صنف، ثم احفظ قبل التأكيد. الرصيد الأحمر = أقل من الكمية المطلوبة") }}</p>
			<p v-if="order.store_invoice" class="mt-3 text-sm">
				{{ __("فاتورة التسليم") }}:
				<a :href="`/app/sales-invoice/${order.store_invoice}`" target="_blank" class="font-semibold text-blue-600 hover:underline">{{ order.store_invoice }}</a>
			</p>

			<!-- Deliver options -->
			<div v-if="order.next_statuses.includes('Delivered')" class="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/60 p-3">
				<p class="mb-2 text-xs font-bold text-emerald-800">{{ __("عند التسليم") }}</p>
				<div class="flex flex-wrap items-center gap-3 text-sm">
					<label class="flex items-center gap-2"><input v-model="deliverPaid" type="radio" :value="true" /> {{ __("دُفع نقدًا") }}</label>
					<select v-if="deliverPaid" v-model="deliverMode" class="bs-input bs-input-sm !w-40">
						<option v-for="m in order.modes_of_payment" :key="m" :value="m">{{ m }}</option>
					</select>
					<label class="flex items-center gap-2"><input v-model="deliverPaid" type="radio" :value="false" /> {{ __("على الحساب (دين)") }}</label>
				</div>
			</div>

			<div class="mt-5 flex flex-wrap justify-end gap-2">
				<button v-if="order.status === 'New' && orderItemsChanged" type="button" class="bs-btn bs-btn-secondary" :disabled="orderBusy" @click="saveOrderItems">{{ __("حفظ التعديلات") }}</button>
				<button v-if="order.next_statuses.includes('Cancelled')" type="button" class="bs-btn bs-btn-ghost !text-rose-600" :disabled="orderBusy" @click="setOrderStatus('Cancelled')">{{ __("إلغاء الطلب") }}</button>
				<button v-if="order.next_statuses.includes('Confirmed')" type="button" class="bs-btn bs-btn-primary" :disabled="orderBusy || orderItemsChanged" @click="setOrderStatus('Confirmed')">{{ __("تأكيد الطلب") }}</button>
				<button v-if="order.next_statuses.includes('Out for Delivery')" type="button" class="bs-btn bs-btn-secondary" :disabled="orderBusy" @click="setOrderStatus('Out for Delivery')">{{ __("خرج للتوصيل") }}</button>
				<button v-if="order.next_statuses.includes('Delivered')" type="button" class="bs-btn bs-btn-success" :disabled="orderBusy" @click="setOrderStatus('Delivered')">
					<span v-if="orderBusy" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
					{{ __("تم التسليم وإصدار الفاتورة") }}
				</button>
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
					<label class="bs-label">{{ __("العنوان") }}</label>
					<input v-model="editingAd.title" type="text"
						class="bs-input w-full px-3 py-2.5" />
				</div>
				<div>
					<label class="bs-label">{{ __("صورة الإعلان") }}</label>
					<div class="flex items-center gap-3">
						<img v-if="editingAd.image" :src="editingAd.image" class="w-24 h-16 object-cover rounded-xl border border-slate-200" />
						<div v-else class="w-24 h-16 bg-slate-100 rounded-xl border border-dashed border-slate-200 flex items-center justify-center">
							<svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
						<input v-model="editingAd.image" type="text" :placeholder="__('رابط الصورة')"
							class="bs-input flex-1 px-3 py-2.5" />
					</div>
				</div>
				<div>
					<label class="bs-label">{{ __("المحتوى") }}</label>
					<textarea v-model="editingAd.content" rows="3"
						class="bs-input w-full px-3 py-2.5"></textarea>
				</div>
				<div>
					<label class="bs-label">{{ __("رابط عند النقر") }}</label>
					<input v-model="editingAd.link_url" type="text" :placeholder="__('https://... (اختياري)')"
						class="bs-input w-full px-3 py-2.5" />
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="bs-label">{{ __("تاريخ البداية") }}</label>
						<input v-model="editingAd.start_date" type="date"
							class="bs-input w-full px-3 py-2.5" />
					</div>
					<div>
						<label class="bs-label">{{ __("تاريخ النهاية") }}</label>
						<input v-model="editingAd.end_date" type="date"
							class="bs-input w-full px-3 py-2.5" />
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
						<label class="bs-label">{{ __("ترتيب العرض") }}</label>
						<input v-model.number="editingAd.display_order" type="number"
							class="bs-input w-full px-3 py-2.5" />
					</div>
				</div>
			</div>
			<div class="mt-6 flex justify-end gap-2">
				<button @click="editingAd = null" class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all">{{ __("إلغاء") }}</button>
				<button @click="saveAd" :disabled="saving"
					class="px-5 py-2 rounded-xl text-sm font-bold text-white transition-all shadow-sm disabled:opacity-50 bg-amber-600 hover:bg-amber-700">
					{{ saving ? __("جاري الحفظ...") : __("حفظ") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import PageHeader from "@/components/ui/PageHeader.vue"
import { call } from "@/utils/apiWrapper"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"

const { showSuccess, showError } = useToast()

const tabs = [
	{ id: "orders", label: "الطلبات" },
	{ id: "settings", label: "الإعدادات" },
	{ id: "areas", label: "مناطق التوصيل" },
	{ id: "items", label: "الأصناف" },
	{ id: "ads", label: "الإعلانات" },
]
const activeTab = ref("orders")

const ORDER_STATUS = {
	New: { label: "جديد", cls: "bs-badge-red" },
	Confirmed: { label: "مؤكد", cls: "bs-badge-blue" },
	"Out for Delivery": { label: "قيد التوصيل", cls: "bs-badge-amber" },
	Delivered: { label: "تم التسليم", cls: "bs-badge-green" },
	Cancelled: { label: "ملغي", cls: "bs-badge-neutral" },
}
const ORDER_FILTERS = [
	{ key: "", label: "الكل" },
	{ key: "New", label: "جديد" },
	{ key: "Confirmed", label: "مؤكد" },
	{ key: "Out for Delivery", label: "قيد التوصيل" },
	{ key: "Delivered", label: "تم التسليم" },
	{ key: "Cancelled", label: "ملغي" },
]
const PRICE_SOURCES = { store: "سعر خاص", price_list: "قائمة الأسعار", standard_rate: "سعر الصنف" }

const loading = ref(false)
const saving = ref(false)
const settings = ref({
	is_enabled: 0,
	store_name: "",
	company: "",
	banner_image: "",
	contact_phone: "",
	contact_whatsapp: "",
	default_warehouse: "",
	selling_price_list: "",
	customer_group: "",
	territory: "",
	out_of_stock_policy: "Allow",
	delivery_mode_of_payment: "",
	delivery_areas: [],
	missing: [],
})
const settingsOptions = ref({ customer_groups: [], territories: [], modes_of_payment: [] })
const onlyPublished = ref(false)

// Orders
const orders = ref([])
const orderCounts = ref({})
const ordersLoading = ref(false)
const orderStatus = ref("New")
const orderSearch = ref("")
const order = ref(null)
const orderOriginalQty = ref({})
const orderBusy = ref(false)
const deliverPaid = ref(true)
const deliverMode = ref("")
let ordersTimer = null
let orderSearchTimer = null

const companies = ref([])
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
		await Promise.all([loadSettings(), loadCompanies(), loadWarehouses(), loadPriceLists(), loadAdminItems(), loadAds(), loadOrders()])
	} catch (e) {
		showError(e?.message || __("فشل التحميل"))
	} finally {
		loading.value = false
	}
	// New orders show up without reloading the page
	ordersTimer = setInterval(() => { if (!order.value) loadOrders() }, 60000)
})

onBeforeUnmount(() => clearInterval(ordersTimer))

function applySettings(data) {
	const { options, ...rest } = data
	settings.value = { ...settings.value, ...rest }
	if (options) settingsOptions.value = options
	if (!settings.value.delivery_areas) settings.value.delivery_areas = []
}

async function loadSettings() {
	applySettings(await call("bs.baron_servies.api.store.get_admin_settings"))
}

async function loadCompanies() {
	companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
}

async function loadWarehouses() {
	warehouses.value = await call("bs.baron_servies.api.stock_reconciliation.get_warehouses", { company: settings.value.company || "" }) || []
}

async function loadPriceLists() {
	priceLists.value = await call("bs.baron_servies.api.stock_reconciliation.get_price_lists") || []
}

async function loadAdminItems() {
	adminItems.value = await call("bs.baron_servies.api.store.get_admin_items", { search: itemSearch.value || "", only_published: onlyPublished.value ? 1 : 0 }) || []
}

async function saveSettings() {
	saving.value = true
	try {
		const { missing, ...data } = settings.value
		const res = await call("bs.baron_servies.api.store.update_admin_settings", { data: JSON.stringify(data) })
		if (res?.settings) applySettings(res.settings)
		showSuccess(__("تم حفظ الإعدادات"))
		return true
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
		return false
	} finally {
		saving.value = false
	}
}

async function toggleStore() {
	settings.value.is_enabled = settings.value.is_enabled ? 0 : 1
	if (!(await saveSettings())) settings.value.is_enabled = settings.value.is_enabled ? 0 : 1
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

async function toggleUnavailable(item) {
	try {
		const res = await call("bs.baron_servies.api.store.set_store_item_unavailable", {
			item_code: item.item_code,
			is_unavailable: item.is_unavailable ? 0 : 1,
		})
		item.is_unavailable = res.is_unavailable
		showSuccess(item.is_unavailable ? __("الصنف غير متوفر في المتجر") : __("الصنف متوفر"))
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
		loadAdminItems()
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
		editingItem.value = null
		loadAdminItems()
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

// ===== Orders =====
async function loadOrders() {
	ordersLoading.value = true
	try {
		const res = await call("bs.baron_servies.api.store.get_store_orders", {
			status: orderStatus.value || null,
			search: orderSearch.value.trim() || null,
		})
		orders.value = res.rows || []
		orderCounts.value = res.counts || {}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الطلبات"))
	} finally {
		ordersLoading.value = false
	}
}

watch(orderStatus, loadOrders)
watch(orderSearch, () => {
	clearTimeout(orderSearchTimer)
	orderSearchTimer = setTimeout(loadOrders, 400)
})

function setOrder(data) {
	order.value = data
	orderOriginalQty.value = Object.fromEntries(data.items.map((i) => [i.name, i.qty]))
	deliverMode.value = data.default_mode_of_payment || data.modes_of_payment?.[0] || ""
}

async function openOrder(name) {
	try {
		deliverPaid.value = true
		setOrder(await call("bs.baron_servies.api.store.get_store_order", { name }))
	} catch (e) {
		showError(e?.message || __("فشل تحميل الطلب"))
	}
}

const orderItemsChanged = computed(() =>
	!!order.value && order.value.items.some((i) => Number(i.qty) !== Number(orderOriginalQty.value[i.name]))
)
const orderLiveTotal = computed(() => (order.value?.items || []).reduce((t, i) => t + Number(i.qty || 0) * Number(i.rate || 0), 0))

const customerWhatsapp = computed(() => {
	const digits = String(order.value?.store_phone || "").replace(/\D/g, "").replace(/^0/, "970")
	return `https://wa.me/${digits}`
})

async function saveOrderItems() {
	orderBusy.value = true
	try {
		setOrder(await call("bs.baron_servies.api.store.update_store_order_items", {
			name: order.value.name,
			items: JSON.stringify(order.value.items.map((i) => ({ name: i.name, qty: i.qty }))),
		}))
		showSuccess(__("تم حفظ تعديلات الطلب"))
		loadOrders()
	} catch (e) {
		showError(e?.message || __("فشل الحفظ"))
	} finally {
		orderBusy.value = false
	}
}

const STATUS_CONFIRM = {
	Confirmed: "تأكيد الطلب؟",
	"Out for Delivery": "تحويل الطلب إلى «قيد التوصيل»؟",
	Delivered: "تأكيد التسليم؟ ستُصدر فاتورة مبيعات وتُخصم الكميات من المخزون",
	Cancelled: "إلغاء الطلب؟",
}

async function setOrderStatus(status) {
	if (!confirm(__(STATUS_CONFIRM[status]))) return
	orderBusy.value = true
	try {
		setOrder(await call("bs.baron_servies.api.store.set_store_order_status", {
			name: order.value.name,
			status,
			paid: deliverPaid.value ? 1 : 0,
			mode_of_payment: deliverMode.value || null,
		}))
		showSuccess(__("تم تحديث الطلب"))
		loadOrders()
	} catch (e) {
		showError(e?.message || __("فشل تحديث الطلب"))
	} finally {
		orderBusy.value = false
	}
}

function formatMoney(v) {
	return Number(v || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatQty(v) {
	const n = Number(v || 0)
	return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, "")
}

function formatDateTime(v) {
	if (!v) return ""
	const [d, t] = String(v).split(" ")
	const [y, m, day] = d.split("-")
	return `${day}/${m}/${y} ${String(t || "").slice(0, 5)}`
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

</script>
