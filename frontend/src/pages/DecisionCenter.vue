<template>
<div class="w-full">
<main class="flex flex-col gap-5 max-w-[1400px] mx-auto">
	<!-- ═══ Header ═══ -->
	<header class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
		<div class="min-w-0">
			<p class="text-[11px] font-semibold tracking-wide text-blue-600">{{ __("مركز القرار") }}</p>
			<h1 class="mt-1 text-2xl font-extrabold text-slate-900 tracking-tight">{{ __("تحليلات الأداء") }}</h1>
			<p class="mt-1 text-xs text-slate-500">
				{{ __("أرقام مطابقة لدفتر الأستاذ العام") }}
				<template v-if="d.period"> · <span class="tabular-nums">{{ d.period.from_date }} → {{ d.period.to_date }}</span></template>
			</p>
		</div>
		<div class="flex items-center gap-2">
			<div class="relative">
				<svg class="absolute top-1/2 -translate-y-1/2 start-3 w-4 h-4 text-slate-400 pointer-events-none" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
				</svg>
				<select
					v-model="company"
					class="appearance-none bg-white border border-slate-200 rounded-xl ps-9 pe-8 py-2 text-sm font-medium text-slate-700 shadow-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 min-w-[180px]"
					:disabled="loadingCompanies"
				>
					<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
					<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
				</select>
			</div>
			<button
				@click="reloadActiveTab"
				class="w-9 h-9 flex items-center justify-center rounded-xl bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 shadow-sm transition-colors"
				:title="__('تحديث')"
			>
				<svg class="w-4 h-4" :class="currentLoading ? 'animate-spin' : ''" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			</button>
		</div>
	</header>

	<!-- ═══ Filter row: period + tabs ═══ -->
	<div class="sticky top-14 z-20 -mx-4 px-4 sm:mx-0 sm:px-0 py-2 bg-slate-50/85 backdrop-blur supports-[backdrop-filter]:bg-slate-50/70">
		<div class="flex flex-col xl:flex-row xl:items-center gap-2">
			<!-- Tabs -->
			<nav class="flex gap-1 p-1 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto">
				<button
					v-for="tab in tabs"
					:key="tab.key"
					@click="activeTab = tab.key"
					class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-[13px] font-semibold whitespace-nowrap transition-all"
					:class="activeTab === tab.key ? 'bg-slate-900 text-white shadow' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" :d="tab.icon" />
					</svg>
					{{ tab.label }}
				</button>
			</nav>
			<div class="xl:ms-auto flex flex-wrap items-center gap-2">
				<div class="flex gap-1 p-1 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto max-w-full">
					<button
						v-for="p in periods"
						:key="p.value"
						@click="period = p.value"
						class="px-3 py-1.5 rounded-xl text-[12px] font-semibold whitespace-nowrap transition-all"
						:class="period === p.value ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'"
					>{{ p.label }}</button>
				</div>
				<div v-if="period === 'custom'" class="flex items-center gap-1.5 p-1 bg-white border border-slate-200 rounded-2xl shadow-sm">
					<input type="date" v-model="customFrom" class="border-0 bg-transparent text-[12px] py-1 px-2 focus:ring-0" />
					<span class="text-slate-300">←</span>
					<input type="date" v-model="customTo" class="border-0 bg-transparent text-[12px] py-1 px-2 focus:ring-0" />
				</div>
			</div>
		</div>
	</div>

	<!-- ═══ Error ═══ -->
	<div v-if="currentError && !view" class="bg-white border border-rose-200 rounded-2xl p-8 text-center">
		<p class="text-sm text-rose-700">{{ currentError }}</p>
		<button @click="reloadActiveTab" class="mt-3 text-xs font-semibold text-rose-600 hover:text-rose-800">{{ __("إعادة المحاولة") }}</button>
	</div>

	<!-- ═══ Skeleton (first load only) ═══ -->
	<div v-else-if="!view && currentLoading" class="grid grid-cols-12 gap-4 animate-pulse">
		<div v-for="i in 4" :key="'k' + i" class="col-span-6 lg:col-span-3 h-28 rounded-2xl bg-white border border-slate-200/80"></div>
		<div class="col-span-12 lg:col-span-8 h-80 rounded-2xl bg-white border border-slate-200/80"></div>
		<div class="col-span-12 lg:col-span-4 h-80 rounded-2xl bg-white border border-slate-200/80"></div>
	</div>

	<div v-else-if="!company" class="bg-white border border-slate-200 rounded-2xl p-10 text-center text-sm text-slate-500">
		{{ __("اختر شركة لعرض البيانات") }}
	</div>

	<!-- ═══ Content (previous render held while refetching) ═══ -->
	<div v-else-if="view" class="flex flex-col gap-4 transition-opacity" :class="currentLoading ? 'opacity-50 pointer-events-none' : ''">

		<!-- ───────── نظرة عامة ───────── -->
		<template v-if="activeTab === 'overview'">
			<div class="grid grid-cols-12 gap-4">
				<!-- Hero -->
				<section class="col-span-12 lg:col-span-8 rounded-2xl bg-white border border-slate-200/80 shadow-[0_1px_2px_rgba(15,23,42,0.04)] p-5 sm:p-6 flex flex-col">
					<div class="flex flex-wrap items-start justify-between gap-4">
						<div>
							<p class="text-[12px] font-semibold text-slate-500">{{ __("صافي المبيعات") }}</p>
							<div class="mt-1 flex items-baseline gap-3 flex-wrap">
								<span class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">{{ money(k.sales) }}</span>
								<DeltaPill :value="k.sales_change_pct" />
							</div>
							<p class="mt-1 text-[11px] text-slate-400">{{ __("الفترة السابقة") }}: <span class="tabular-nums">{{ money(prevOf('المبيعات')) }}</span></p>
						</div>
						<div class="flex gap-6">
							<div>
								<p class="text-[11px] font-semibold text-slate-400">{{ __("مجمل الربح") }}</p>
								<p class="text-lg font-bold text-slate-900">{{ money(k.gross_profit) }}</p>
							</div>
							<div>
								<p class="text-[11px] font-semibold text-slate-400">{{ __("هامش الربح") }}</p>
								<p class="text-lg font-bold text-slate-900">{{ pct(k.gross_margin_pct) }}</p>
							</div>
						</div>
					</div>
					<div class="mt-5 relative h-[280px]">
						<Bar v-if="!isEmpty(view.trend, ['sales'])" :data="overviewTrendChart" :options="moneyOptions({ legend: true })" />
						<p v-else class="h-full flex items-center justify-center text-xs text-slate-400">{{ __("لا توجد بيانات للفترة المحددة") }}</p>
					</div>
				</section>

				<!-- Side KPIs -->
				<div class="col-span-12 lg:col-span-4 grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-4">
					<KpiTile :label="__('صافي الربح')" :value="money(k.net_profit)" :delta="k.net_profit_change_pct" :spark="series('net_profit')" :color="SERIES[2]" :hint="__('مقارنة بالفترة السابقة')" />
					<KpiTile :label="__('المصاريف التشغيلية')" :value="money(k.expenses)" :delta="k.expenses_change_pct" invert :spark="series('expenses')" :color="SERIES[1]" :hint="__('مقارنة بالفترة السابقة')" />
					<KpiTile :label="__('المشتريات')" :value="money(k.purchases)" :delta="k.purchases_change_pct" invert :hint="__('مقارنة بالفترة السابقة')" />
				</div>
			</div>

			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('عدد الفواتير')" :value="num(k.invoices)" />
				<KpiTile :label="__('متوسط الفاتورة')" :value="money(k.avg_invoice)" />
				<KpiTile :label="__('العملاء النشطون')" :value="num(k.customers)" />
				<KpiTile :label="__('تكلفة المبيعات')" :value="money(breakdownValue('تكلفة المبيعات'))" />
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-5" fluid :title="__('أين تذهب المبيعات؟')" :subtitle="__('من كل 100 من صافي المبيعات')" :empty="!k.sales">
					<div class="flex h-3 rounded-full overflow-hidden gap-[2px] bg-white">
						<div v-for="s in composition" :key="s.label" :style="{ width: s.share + '%', backgroundColor: s.color }" class="h-full first:rounded-s-full last:rounded-e-full"></div>
					</div>
					<ul class="mt-5 flex flex-col gap-3">
						<li v-for="s in composition" :key="s.label" class="flex items-center gap-3 text-[13px]">
							<span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: s.color }"></span>
							<span class="flex-1 text-slate-600">{{ s.label }}</span>
							<span class="font-bold text-slate-900 tabular-nums">{{ money(s.value) }}</span>
							<span class="w-14 text-end text-[12px] font-semibold text-slate-400 tabular-nums">{{ s.share.toFixed(1) }}%</span>
						</li>
					</ul>
					<p v-if="k.net_profit < 0" class="mt-4 text-[11px] text-rose-600">{{ __("صافي الربح سالب في هذه الفترة") }}: {{ money(k.net_profit) }}</p>
				</ChartCard>

				<ChartCard class="col-span-12 lg:col-span-7" fluid :title="__('الفترة الحالية مقابل السابقة')" :subtitle="previousLabel">
					<div class="overflow-x-auto">
						<table class="w-full text-[13px]">
							<thead>
								<tr class="text-[11px] text-slate-400">
									<th class="text-start font-semibold pb-2">{{ __("المؤشر") }}</th>
									<th class="text-end font-semibold pb-2">{{ __("الحالية") }}</th>
									<th class="text-end font-semibold pb-2">{{ __("السابقة") }}</th>
									<th class="text-end font-semibold pb-2">{{ __("التغير") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-100">
								<tr v-for="r in view.comparison" :key="r.label">
									<td class="py-2.5 font-medium text-slate-700">{{ r.label }}</td>
									<td class="py-2.5 text-end font-bold text-slate-900 tabular-nums">{{ money(r.current) }}</td>
									<td class="py-2.5 text-end text-slate-500 tabular-nums">{{ money(r.previous) }}</td>
									<td class="py-2.5 text-end"><DeltaPill :value="changePct(r.previous, r.current)" :invert="['المصاريف', 'المشتريات'].includes(r.label)" /></td>
								</tr>
							</tbody>
						</table>
					</div>
				</ChartCard>
			</div>
		</template>

		<!-- ───────── المبيعات ───────── -->
		<template v-if="activeTab === 'sales'">
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('صافي المبيعات')" :value="money(k.sales)" :delta="k.sales_change_pct" :spark="series('amount')" :color="SERIES[0]" />
				<KpiTile :label="__('عدد الفواتير')" :value="num(k.invoices)" :spark="series('invoices')" :color="SERIES[5]" />
				<KpiTile :label="__('متوسط الفاتورة')" :value="money(k.avg_invoice)" :hint="k.gross_margin_pct != null ? __('هامش الربح') + ' ' + pct(k.gross_margin_pct) : ''" />
				<KpiTile :label="__('المرتجعات')" :value="money(k.returns)" :hint="k.returns_pct != null ? pct(k.returns_pct) + ' ' + __('من المبيعات') : ''" />
			</div>

			<ChartCard :title="__('اتجاه المبيعات')" :subtitle="granularityLabel + ' · ' + __('عدد الفواتير يظهر عند التمرير')" :height="300" :empty="isEmpty(view.trend, ['amount'])">
				<Bar :data="trendBar(view.trend, __('صافي المبيعات'), SERIES[0])" :options="moneyOptions({ footerKey: 'invoices', footerLabel: __('عدد الفواتير') })" />
			</ChartCard>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-5" :title="__('حسب يوم الأسبوع')" :empty="isEmpty(view.by_weekday, ['amount'])">
					<Bar :data="trendBar(view.by_weekday, __('المبيعات'), SERIES[0])" :options="moneyOptions({ footerKey: 'invoices', footerLabel: __('عدد الفواتير'), rows: view.by_weekday })" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-7" :title="__('حسب ساعة اليوم')" :subtitle="__('أوقات الذروة')" :empty="isEmpty(view.by_hour, ['amount'])">
					<Bar :data="trendBar(activeHours, __('المبيعات'), SERIES[5])" :options="moneyOptions({ footerKey: 'invoices', footerLabel: __('عدد الفواتير'), rows: activeHours })" />
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-7" fluid :title="__('الأصناف الأعلى مبيعًا')" :empty="!view.top_items?.length">
					<RankList :rows="view.top_items" value-key="amount" secondary-key="qty" :format="money" :secondary-format="(v) => num(v) + ' ' + __('وحدة')" :color="SERIES[0]" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-5" fluid :title="__('حسب مجموعة الأصناف')" :empty="isEmptyValues(view.by_item_group)">
					<DonutPanel :rows="view.by_item_group" :format="money" :center-label="__('الإجمالي')" />
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أكبر نمو')" :subtitle="previousLabel" :empty="!view.growing_items?.length">
					<ChangeList :rows="view.growing_items" :format="money" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أكبر تراجع')" :subtitle="previousLabel" :empty="!view.declining_items?.length">
					<ChangeList :rows="view.declining_items" :format="money" />
				</ChartCard>
			</div>
		</template>

		<!-- ───────── المشتريات ───────── -->
		<template v-if="activeTab === 'purchases'">
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('إجمالي المشتريات')" :value="money(k.purchases)" :delta="k.purchases_change_pct" invert :spark="series('amount')" :color="SERIES[5]" />
				<KpiTile :label="__('عدد الفواتير')" :value="num(k.invoices)" :spark="series('invoices')" :color="SERIES[0]" />
				<KpiTile :label="__('متوسط الفاتورة')" :value="money(k.avg_invoice)" />
				<KpiTile :label="__('عدد الموردين')" :value="num(k.suppliers)" />
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-8" :title="__('اتجاه المشتريات')" :subtitle="granularityLabel" :height="300" :empty="isEmpty(view.trend, ['amount'])">
					<Bar :data="trendBar(view.trend, __('المشتريات'), SERIES[5])" :options="moneyOptions({ footerKey: 'invoices', footerLabel: __('عدد الفواتير') })" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('حسب مجموعة الأصناف')" :empty="isEmptyValues(view.by_item_group)">
					<DonutPanel :rows="view.by_item_group" :format="money" :center-label="__('الإجمالي')" />
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أعلى الموردين')" :empty="!view.top_suppliers?.length">
					<RankList :rows="view.top_suppliers" value-key="amount" secondary-key="invoices" :format="money" :secondary-format="(v) => num(v) + ' ' + __('فاتورة')" :color="SERIES[5]" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أعلى الأصناف شراءً')" :empty="!view.top_items?.length">
					<RankList :rows="view.top_items" value-key="amount" secondary-key="qty" :format="money" :secondary-format="(v) => num(v) + ' ' + __('وحدة')" :color="SERIES[0]" />
				</ChartCard>
			</div>

			<ChartCard fluid :title="__('تغير متوسط سعر الشراء')" :subtitle="previousLabel" :empty="!view.price_changes?.length">
				<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2.5">
					<div v-for="r in view.price_changes" :key="r.name" class="flex items-center gap-3 text-[12px] min-w-0 py-1 border-b border-slate-100">
						<span class="flex-1 font-medium text-slate-700 truncate" :title="r.name">{{ r.name }}</span>
						<span class="text-slate-400 tabular-nums">{{ money(r.previous_rate) }} ← {{ money(r.current_rate) }}</span>
						<DeltaPill :value="r.change_pct" invert />
					</div>
				</div>
			</ChartCard>
		</template>

		<!-- ───────── المخزون ───────── -->
		<template v-if="activeTab === 'inventory'">
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('قيمة المخزون')" :value="money(k.stock_value)" :badge="__('لحظي')" />
				<KpiTile :label="__('أصناف متوفرة')" :value="num(k.item_count)" :badge="__('لحظي')" />
				<KpiTile :label="__('أصناف راكدة')" :value="num(k.dead_count)" :hint="money(k.dead_value)" :badge="__('لحظي')" />
				<KpiTile :label="__('قريبة من النفاد')" :value="num(k.low_count)" :badge="__('لحظي')" />
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('حالة المخزون حسب القيمة')" :subtitle="__('حسب سرعة البيع خلال آخر 90 يوم')" :empty="isEmptyValues(view.classification)">
					<DonutPanel :rows="stockClasses" :format="money" :center-label="__('قيمة المخزون')" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('القيمة حسب مجموعة الأصناف')" :empty="isEmptyValues(view.by_item_group)">
					<DonutPanel :rows="view.by_item_group" :format="money" :center-label="__('الإجمالي')" />
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-7" :title="__('حركة المخزون بالقيمة')" :subtitle="granularityLabel" :height="300" :empty="isEmpty(view.movement, ['incoming', 'outgoing'])">
					<Bar :data="movementChart" :options="moneyOptions({ legend: true })" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-5" fluid :title="__('الأصناف الأعلى قيمة')" :empty="!view.top_items?.length">
					<RankList :rows="view.top_items" value-key="value" secondary-key="qty" :format="money" :secondary-format="(v) => num(v) + ' ' + __('وحدة')" :color="SERIES[2]" />
				</ChartCard>
			</div>
		</template>

		<!-- ───────── العملاء ───────── -->
		<template v-if="activeTab === 'customers'">
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('العملاء النشطون')" :value="num(k.active_customers)" :delta="k.active_change_pct" :spark="series('active')" :color="SERIES[0]" />
				<KpiTile :label="__('عملاء جدد')" :value="num(k.new_customers)" :spark="series('new')" :color="SERIES[2]" />
				<KpiTile :label="__('متوسط المبيعات لكل عميل')" :value="money(k.avg_per_customer)" />
				<KpiTile :label="__('الذمم المدينة')" :value="money(k.receivable)" :badge="__('حتى نهاية الفترة')" />
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-8" :title="__('العملاء النشطون والجدد')" :subtitle="granularityLabel" :height="290" :empty="isEmpty(view.trend, ['active', 'new'])">
					<Bar :data="customerTrendChart" :options="countOptions" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('تركّز المبيعات')" :subtitle="__('حصة أعلى 10 عملاء')" :empty="isEmptyValues(view.concentration)">
					<div class="flex flex-col items-center justify-center h-full py-2">
						<p class="text-4xl font-extrabold text-slate-900 tracking-tight">{{ pct(k.top10_share_pct) }}</p>
						<p class="text-[12px] text-slate-500 mt-1">{{ __("من صافي المبيعات") }}</p>
						<div class="w-full mt-5 flex h-3 rounded-full overflow-hidden gap-[2px]">
							<div class="h-full rounded-s-full" :style="{ width: (k.top10_share_pct || 0) + '%', backgroundColor: SERIES[0] }"></div>
							<div class="h-full flex-1 rounded-e-full" :style="{ backgroundColor: OTHER }"></div>
						</div>
						<div class="w-full mt-3 flex justify-between text-[11px] text-slate-500">
							<span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full" :style="{ backgroundColor: SERIES[0] }"></span>{{ __("أعلى 10") }}</span>
							<span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full" :style="{ backgroundColor: OTHER }"></span>{{ __("الباقي") }}</span>
						</div>
					</div>
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أعلى العملاء مبيعًا')" :empty="!view.top_customers?.length">
					<RankList :rows="view.top_customers" value-key="amount" secondary-key="invoices" :format="money" :secondary-format="(v) => num(v) + ' ' + __('فاتورة')" :color="SERIES[0]" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('أعلى أرصدة الذمم')" :subtitle="__('الرصيد حتى نهاية الفترة')" :empty="!view.top_receivables?.length">
					<RankList :rows="view.top_receivables" value-key="balance" :format="money" :color="SERIES[1]" />
				</ChartCard>
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('عملاء بنمو في المبيعات')" :subtitle="previousLabel" :empty="!view.growing_customers?.length">
					<ChangeList :rows="view.growing_customers" :format="money" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-6" fluid :title="__('عملاء بتراجع في المبيعات')" :subtitle="previousLabel" :empty="!view.declining_customers?.length">
					<ChangeList :rows="view.declining_customers" :format="money" />
				</ChartCard>
			</div>
		</template>

		<!-- ───────── المصاريف ───────── -->
		<template v-if="activeTab === 'expenses'">
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
				<KpiTile :label="__('المصاريف التشغيلية')" :value="money(k.expenses)" :delta="k.expenses_change_pct" invert :spark="series('amount')" :color="SERIES[1]" />
				<KpiTile :label="__('مصاريف الفترة السابقة')" :value="money(k.previous_expenses)" />
				<KpiTile :label="__('المصاريف إلى المبيعات')" :value="pct(k.expenses_to_sales_pct)" />
				<KpiTile :label="__('حسابات المصاريف')" :value="num(k.accounts)" />
			</div>

			<div class="grid grid-cols-12 gap-4">
				<ChartCard class="col-span-12 lg:col-span-8" :title="__('اتجاه المصاريف')" :subtitle="granularityLabel" :height="300" :empty="isEmpty(view.trend, ['amount'])">
					<Bar :data="trendBar(view.trend, __('المصاريف'), SERIES[1])" :options="moneyOptions()" />
				</ChartCard>
				<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('التوزيع حسب الحساب')" :empty="isEmptyValues(view.by_account)">
					<DonutPanel :rows="view.by_account" :format="money" :center-label="__('الإجمالي')" />
				</ChartCard>
			</div>

			<ChartCard fluid :title="__('الحسابات: الحالية مقابل السابقة')" :subtitle="previousLabel" :empty="!view.comparison?.length">
				<div class="overflow-x-auto">
					<table class="w-full text-[13px]">
						<thead>
							<tr class="text-[11px] text-slate-400">
								<th class="text-start font-semibold pb-2">{{ __("الحساب") }}</th>
								<th class="text-end font-semibold pb-2">{{ __("الحالية") }}</th>
								<th class="text-end font-semibold pb-2">{{ __("السابقة") }}</th>
								<th class="text-end font-semibold pb-2">{{ __("التغير") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr v-for="r in view.comparison" :key="r.label">
								<td class="py-2.5 font-medium text-slate-700">{{ r.label }}</td>
								<td class="py-2.5 text-end font-bold text-slate-900 tabular-nums">{{ money(r.current) }}</td>
								<td class="py-2.5 text-end text-slate-500 tabular-nums">{{ money(r.previous) }}</td>
								<td class="py-2.5 text-end"><DeltaPill :value="changePct(r.previous, r.current)" invert /></td>
							</tr>
						</tbody>
					</table>
				</div>
			</ChartCard>
		</template>
	</div>
</main>
</div>
</template>

<script setup>
import { computed, watch, onMounted, ref, h } from "vue"
import { Bar } from "vue-chartjs"
import {
	Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement,
	ArcElement, BarController, LineController, Tooltip, Legend, Filler,
} from "chart.js"
import { useDecisionCenter } from "@/composables/useDecisionCenter"
import KpiTile from "@/components/dc/KpiTile.vue"
import ChartCard from "@/components/dc/ChartCard.vue"
import RankList from "@/components/dc/RankList.vue"
import ChangeList from "@/components/dc/ChangeList.vue"
import DonutPanel from "@/components/dc/DonutPanel.vue"
import {
	SERIES, OTHER, STATUS, FONT, alpha, tooltip, legend, valueAxis, categoryAxis, barStyle, lineStyle,
} from "@/components/dc/vizTheme"

ChartJS.register(
	CategoryScale, LinearScale, PointElement, LineElement, BarElement,
	ArcElement, BarController, LineController, Tooltip, Legend, Filler,
)
ChartJS.defaults.font.family = FONT

const {
	company, period, customFrom, customTo,
	companies, loadingCompanies,
	tabData, tabLoading, tabError,
	initFromQuery, loadTab, reloadTab, loadCompanies,
	formatCurrency, formatNumber,
} = useDecisionCenter()

// ── Small inline component: delta pill ──
const DeltaPill = (props) => {
	const v = props.value
	if (v === null || v === undefined || v === "" || isNaN(Number(v))) {
		return h("span", { class: "text-[11px] text-slate-300" }, "—")
	}
	const n = Number(v)
	const good = props.invert !== undefined && props.invert !== false ? n < 0 : n > 0
	const cls = n === 0 ? "bg-slate-100 text-slate-500" : good ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
	return h("span", { class: `inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-bold tabular-nums ${cls}` },
		`${n > 0 ? "▲" : n < 0 ? "▼" : ""} ${Math.abs(n).toFixed(1)}%`)
}
DeltaPill.props = ["value", "invert"]

// ── Tabs & periods ──
const activeTab = ref("overview")
const tabs = [
	{ key: "overview", label: __("نظرة عامة"), icon: "M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-3a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" },
	{ key: "sales", label: __("المبيعات"), icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" },
	{ key: "purchases", label: __("المشتريات"), icon: "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" },
	{ key: "inventory", label: __("المخزون"), icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" },
	{ key: "customers", label: __("العملاء"), icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" },
	{ key: "expenses", label: __("المصاريف"), icon: "M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" },
]
const periods = [
	{ value: "today", label: __("اليوم") },
	{ value: "last_7_days", label: __("7 أيام") },
	{ value: "last_30_days", label: __("30 يوم") },
	{ value: "this_month", label: __("هذا الشهر") },
	{ value: "last_month", label: __("الشهر السابق") },
	{ value: "this_quarter", label: __("هذا الربع") },
	{ value: "this_year", label: __("هذه السنة") },
	{ value: "custom", label: __("مخصص") },
]

const API = "bs.baron_servies.api.decision_center.analytics."
const TAB_API = {
	overview: API + "get_overview_analytics",
	sales: API + "get_sales_analytics",
	purchases: API + "get_purchase_analytics",
	inventory: API + "get_inventory_analytics",
	customers: API + "get_customer_analytics",
	expenses: API + "get_expense_analytics",
}

// ── Data (hold the last render per tab while refetching) ──
const currentLoading = computed(() => !!tabLoading.value[activeTab.value])
const currentError = computed(() => tabError.value[activeTab.value])
const lastShown = ref({})
watch(() => tabData.value[activeTab.value], (v) => {
	if (v) lastShown.value = { ...lastShown.value, [activeTab.value]: v }
}, { immediate: true })
const view = computed(() => tabData.value[activeTab.value] || (currentLoading.value ? lastShown.value[activeTab.value] : null))
const d = computed(() => view.value || {})
const k = computed(() => d.value.kpis || {})

const granularityLabel = computed(() => (d.value.granularity === "daily" ? __("يومي") : __("شهري")))
const previousLabel = computed(() => {
	const p = d.value.period
	return p?.prev_from ? `${__("مقارنة بـ")} ${p.prev_from} → ${p.prev_to}` : ""
})

// ── Formatters ──
const money = (v) => formatCurrency(v)
const num = (v) => formatNumber(v)
const pct = (v) => (v === null || v === undefined ? "—" : `${Number(v).toFixed(1)}%`)
function changePct(prev, cur) {
	prev = Number(prev || 0)
	cur = Number(cur || 0)
	if (Math.abs(prev) < 1) return null
	return ((cur - prev) / Math.abs(prev)) * 100
}
const prevOf = (label) => (d.value.comparison || []).find((r) => r.label === label)?.previous
const breakdownValue = (label) => (d.value.sales_breakdown || []).find((r) => r.label === label)?.value
const series = (key) => (d.value.trend || []).map((r) => r[key])

function isEmpty(rows, fields) {
	return !(rows || []).some((r) => fields.some((f) => Number(r[f] || 0) !== 0))
}
function isEmptyValues(rows) {
	return !(rows || []).some((r) => Number(r.value || 0) > 0)
}

// ── Derived views ──
const composition = computed(() => {
	const sales = Number(k.value.sales || 0)
	if (!sales) return []
	const parts = [
		{ label: __("تكلفة المبيعات"), value: breakdownValue("تكلفة المبيعات") || 0, color: SERIES[5] },
		{ label: __("المصاريف التشغيلية"), value: breakdownValue("المصاريف") || 0, color: SERIES[1] },
		{ label: __("صافي الربح"), value: Math.max(Number(k.value.net_profit || 0), 0), color: SERIES[2] },
	]
	const total = parts.reduce((a, p) => a + Number(p.value), 0) || 1
	return parts.map((p) => ({ ...p, share: (Number(p.value) / total) * 100 }))
})

const activeHours = computed(() => {
	const rows = d.value.by_hour || []
	const first = rows.findIndex((r) => Number(r.amount) !== 0 || Number(r.invoices) !== 0)
	if (first < 0) return rows
	let last = rows.length - 1
	while (last > first && Number(rows[last].amount) === 0 && Number(rows[last].invoices) === 0) last--
	return rows.slice(first, last + 1)
})

const stockClasses = computed(() => {
	const colorFor = { dead: STATUS.critical, slow: STATUS.serious, low: STATUS.warning, normal: STATUS.good }
	return (d.value.classification || []).map((c) => ({ label: c.label, value: c.value, color: colorFor[c.key] }))
})

// ── Chart data ──
const labelsOf = (rows) => (rows || []).map((r) => r.label)

function trendBar(rows, label, color) {
	return {
		labels: labelsOf(rows),
		datasets: [{ label, data: (rows || []).map((r) => r.amount), backgroundColor: color, hoverBackgroundColor: alpha(color, 0.8), ...barStyle }],
	}
}

const overviewTrendChart = computed(() => {
	const t = d.value.trend || []
	return {
		labels: labelsOf(t),
		datasets: [
			{ type: "bar", label: __("صافي المبيعات"), data: t.map((r) => r.sales), backgroundColor: alpha(SERIES[0], 0.85), ...barStyle, order: 3 },
			{ type: "line", label: __("مجمل الربح"), data: t.map((r) => r.gross_profit), borderColor: SERIES[1], backgroundColor: SERIES[1], ...lineStyle, order: 1 },
			{ type: "line", label: __("صافي الربح"), data: t.map((r) => r.net_profit), borderColor: SERIES[2], backgroundColor: SERIES[2], ...lineStyle, order: 2 },
		],
	}
})

const movementChart = computed(() => {
	const t = d.value.movement || []
	return {
		labels: labelsOf(t),
		datasets: [
			{ label: __("وارد"), data: t.map((r) => r.incoming), backgroundColor: SERIES[2], ...barStyle },
			{ label: __("صادر"), data: t.map((r) => r.outgoing), backgroundColor: SERIES[1], ...barStyle },
		],
	}
})

const customerTrendChart = computed(() => {
	const t = d.value.trend || []
	return {
		labels: labelsOf(t),
		datasets: [
			{ type: "bar", label: __("عملاء نشطون"), data: t.map((r) => r.active), backgroundColor: SERIES[0], ...barStyle, order: 2 },
			{ type: "line", label: __("عملاء جدد"), data: t.map((r) => r.new), borderColor: SERIES[2], backgroundColor: SERIES[2], ...lineStyle, order: 1 },
		],
	}
})

// ── Chart options (one value axis per chart) ──
function moneyOptions({ legend: showLegend = false, footerKey = "", footerLabel = "", rows = null } = {}) {
	return {
		responsive: true,
		maintainAspectRatio: false,
		interaction: { mode: "index", intersect: false },
		plugins: {
			legend: showLegend ? legend : { display: false },
			tooltip: tooltip({
				callbacks: {
					label: (ctx) => ` ${ctx.dataset.label}: ${money(ctx.parsed.y)}`,
					footer: footerKey
						? (items) => {
							const src = rows || d.value.trend || []
							const r = src[items[0]?.dataIndex]
							return r ? `${footerLabel}: ${num(r[footerKey])}` : ""
						}
						: undefined,
				},
			}),
		},
		scales: { x: categoryAxis(), y: valueAxis() },
	}
}

const countOptions = {
	responsive: true,
	maintainAspectRatio: false,
	interaction: { mode: "index", intersect: false },
	plugins: { legend, tooltip: tooltip() },
	scales: { x: categoryAxis(), y: valueAxis({ ticks: { ...valueAxis().ticks, precision: 0 } }) },
}

// ── Loading ──
function loadActiveTab() {
	if (company.value) loadTab(activeTab.value, TAB_API[activeTab.value])
}
function reloadActiveTab() {
	if (company.value) reloadTab(activeTab.value, TAB_API[activeTab.value])
}

watch(activeTab, loadActiveTab)
watch([company, period, customFrom, customTo], loadActiveTab)

onMounted(async () => {
	initFromQuery()
	await loadCompanies()
	loadActiveTab()
})
</script>
