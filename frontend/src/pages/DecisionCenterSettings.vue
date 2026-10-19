<template>
<div class="w-full">
<main class="flex flex-col gap-4">
<!-- Page title -->
<div class="flex items-center justify-between gap-3">
<div class="flex items-center gap-3">
<div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-600 to-slate-800 shadow-lg shadow-slate-500/30">
<svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
</svg>
</div>
<div class="min-w-0">
<h1 class="text-lg font-bold text-slate-900 truncate">{{ __("إعدادات مركز القرار") }}</h1>
<p class="text-xs text-slate-500 truncate">{{ __("الحدود والتصنيفات وحسابات المصاريف - مسموح للمدير فقط") }}</p>
</div>
</div>
<router-link
:to="{ name: 'DecisionCenter' }"
class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all flex items-center gap-1"
>
<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
</svg>
{{ __("العودة إلى مركز القرار") }}
</router-link>
</div>

<!-- Unauthorized -->
<div v-if="!isAdmin" class="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center">
<p class="text-rose-700 font-semibold">{{ __("غير مصرح") }}</p>
<p class="text-sm text-rose-600 mt-1">{{ __("هذه الصفحة مخصصة لحساب Administrator فقط") }}</p>
</div>

<template v-else>
<!-- Loading -->
<div v-if="loading" class="flex items-center justify-center py-20">
<div class="flex flex-col items-center gap-3">
<svg class="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
<p class="text-slate-500 text-sm">{{ __("جاري التحميل...") }}</p>
</div>
</div>

<template v-else>
<!-- Tab Navigation -->
<div class="bg-white border border-slate-200 rounded-2xl shadow-sm">
<nav class="flex flex-wrap gap-1 p-2" role="tablist">
<button
v-for="tab in tabs"
:key="tab.id"
@click="activeTab = tab.id"
role="tab"
:aria-selected="activeTab === tab.id"
:class="[
'flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all',
activeTab === tab.id
? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
: 'text-slate-600 hover:bg-slate-100'
]"
>
{{ __(tab.label) }}
<span v-if="tabDirty[tab.id]" class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
</button>
</nav>
</div>

<!-- Thresholds -->
<div v-if="activeTab === 'analysis'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("الحدود العامة") }} <HelpLink topic="settings_overview" /></h2>
</div>
<div class="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
<div v-for="group in thresholdGroups" :key="group.key" class="border border-slate-200 rounded-xl p-3 space-y-2">
<div class="flex items-center gap-2 pb-2 border-b border-slate-100">
<svg class="w-5 h-5" :class="group.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="group.iconPath" />
</svg>
<h3 class="font-bold text-slate-800">{{ __(group.title) }}</h3>
</div>
<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
<SettingField
v-for="field in group.fields"
:key="field.key"
v-model="settings[field.key]"
:label="field.label"
:help="field.help"
:suffix="field.suffix"
:type="field.type"
:min="field.min"
:max="field.max"
:step="field.step"
:error="errors[field.key]"
/>
</div>
</div>
</div>
</div>

<!-- Expense Thresholds -->
<div v-if="activeTab === 'expenses'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("حدود المصاريف") }}</h2>
</div>
<div class="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
<SettingField
v-for="field in expenseFields"
:key="field.key"
v-model="settings[field.key]"
:label="field.label"
:help="field.help"
:suffix="field.suffix"
:type="field.type"
:min="field.min"
:max="field.max"
:step="field.step"
:error="errors[field.key]"
/>
</div>
</div>

<!-- Expense Categories -->
<div v-if="activeTab === 'categories'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
<div class="flex items-center gap-2">
<svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("تصنيفات المصاريف") }}</h2>
</div>
<button
@click="addCategory"
class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-all flex items-center gap-1"
>
<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
</svg>
{{ __("إضافة تصنيف") }}
</button>
</div>
<div class="divide-y divide-slate-100">
<div v-for="(cat, idx) in categories" :key="cat.name || cat._tempId" class="transition-colors">
<!-- Compact summary row -->
<div
class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50/70"
@click="toggleCategory(cat)"
>
<div class="min-w-0 flex-1">
<div class="flex items-center gap-2">
<p class="text-sm font-semibold text-slate-800 truncate">{{ cat.category_name || __("بدون اسم") }}</p>
<span
:class="cat.enabled ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
class="text-[10px] font-medium px-1.5 py-0.5 rounded border"
>{{ cat.enabled ? __("مفعّل") : __("غير مفعّل") }}</span>
</div>
<p v-if="cat.description" class="text-xs text-slate-500 truncate mt-0.5">{{ cat.description }}</p>
</div>
<div class="flex items-center gap-2 flex-shrink-0">
<span class="text-[11px] text-slate-500 whitespace-nowrap">{{ cat.accounts.length }} {{ __("حساب") }}</span>
<span v-if="cat.target_percent_of_sales != null" class="text-[11px] font-medium text-blue-600 bg-blue-50 border border-blue-100 px-1.5 py-0.5 rounded whitespace-nowrap">{{ __("هدف") }}: {{ cat.target_percent_of_sales }}%</span>
<span v-if="cat.max_percent_of_sales != null" class="text-[11px] font-medium text-amber-600 bg-amber-50 border border-amber-100 px-1.5 py-0.5 rounded whitespace-nowrap">{{ __("حد") }}: {{ cat.max_percent_of_sales }}%</span>
<button
@click.stop="toggleCategory(cat)"
class="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
:aria-label="expandedCategoryId === cat._tempId ? __('إغلاق') : __('تعديل')"
>
<svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': expandedCategoryId === cat._tempId }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
</svg>
</button>
<button
@click.stop="removeCategory(idx)"
class="p-1.5 text-rose-400 hover:text-rose-600 transition-colors"
:aria-label="__('حذف')"
>
<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
</svg>
</button>
</div>
</div>

<!-- Inline editor -->
<div v-if="expandedCategoryId === cat._tempId" class="border-t border-slate-100 px-4 py-4 bg-slate-50/50 space-y-4" @click.stop>
<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
<div>
<label class="text-xs font-medium text-slate-600 block mb-1">{{ __("اسم التصنيف") }}</label>
<input
v-model="cat.category_name"
:placeholder="__('اسم التصنيف')"
class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
/>
</div>
<div>
<label class="text-xs font-medium text-slate-600 block mb-1">{{ __("الوصف") }}</label>
<input
v-model="cat.description"
:placeholder="__('وصف مختصر')"
class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
/>
</div>
<div>
<label class="text-xs font-medium text-slate-600 block mb-1">{{ __("النسبة المستهدفة من المبيعات") }} (%)</label>
<input
type="number"
v-model="cat.target_percent_of_sales"
min="0"
step="0.1"
class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
/>
</div>
<div>
<label class="text-xs font-medium text-slate-600 block mb-1">{{ __("الحد الأقصى من المبيعات") }} (%)</label>
<input
type="number"
v-model="cat.max_percent_of_sales"
min="0"
step="0.1"
class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
/>
</div>
<label class="flex items-center gap-2 text-sm text-slate-700 self-end pb-2">
<input type="checkbox" v-model="cat.enabled" class="rounded text-blue-600" />
{{ __("مفعل") }}
</label>
</div>

<!-- Accounts -->
<div class="bg-white rounded-xl border border-slate-200 p-3">
<div class="flex items-center justify-between mb-2">
<p class="text-xs font-semibold text-slate-700">{{ __("الحسابات المرتبطة") }}</p>
<button
@click="addAccount(cat)"
class="text-xs font-medium text-blue-600 hover:text-blue-800"
>{{ __("إضافة حساب") }}</button>
</div>
<div class="space-y-2">
<div v-for="(acc, aidx) in cat.accounts" :key="acc._tempId || aidx" class="flex items-center gap-2">
<div class="flex-1 relative account-search min-w-0">
<input
:ref="(el) => { if (el) accountInputRefs[acc._tempId] = el }"
v-model="acc.account"
@input="onAccountSearch(acc, $event)"
@focus="onAccountSearch(acc, $event)"
:placeholder="__('اختر حساب')"
class="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
/>
<div
v-if="accSearchFocused[acc._tempId || aidx]"
class="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-auto"
>
<div v-if="accSearchLoading[acc._tempId || aidx]" class="px-3 py-2 text-xs text-slate-400 text-center">{{ __("جاري البحث...") }}</div>
<template v-else-if="accSearchResults[acc._tempId || aidx]?.length">
<button
v-for="r in accSearchResults[acc._tempId || aidx]"
:key="r.value"
@click="selectAccount(acc, r)"
class="w-full text-start px-3 py-2 text-xs hover:bg-blue-50 border-b border-slate-50 last:border-0"
>
<p class="font-medium text-slate-800">{{ r.value }}</p>
<p class="text-slate-500 truncate">{{ r.description }}</p>
</button>
</template>
<div v-else class="px-3 py-2 text-xs text-slate-400 text-center">{{ __("اكتب اسم الحساب أو اختر من القائمة") }}</div>
</div>
</div>
<input
v-model="acc.description"
:placeholder="__('وصف')"
class="w-32 md:w-40 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
/>
<label class="flex items-center gap-1 text-xs text-slate-600 whitespace-nowrap">
<input type="checkbox" v-model="acc.enabled" class="rounded text-blue-600" />
{{ __("مفعل") }}
</label>
<button
@click="removeAccount(cat, aidx)"
class="text-rose-400 hover:text-rose-600 p-1 transition-colors"
:aria-label="__('حذف حساب')"
>
<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
</svg>
</button>
</div>
<p v-if="!cat.accounts.length" class="text-xs text-slate-400">{{ __("لا توجد حسابات مرتبطة") }}</p>
</div>
</div>
</div>
</div>
<p v-if="!categories.length" class="px-5 py-8 text-center text-sm text-slate-400">{{ __("لا توجد تصنيفات مصاريف") }}</p>
</div>
</div>

<!-- Rule Settings -->
<div v-if="activeTab === 'rules'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
<svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("تفعيل قواعد القرارات") }}</h2>
</div>
<div class="p-5 space-y-5">
<div v-for="(rules, category) in groupedRules" :key="category" class="border border-slate-200 rounded-xl p-4 space-y-3">
<div class="flex items-center gap-2 pb-2 border-b border-slate-100">
<span class="w-2 h-2 rounded-full" :class="ruleCategoryColor(category)"></span>
<h3 class="font-bold text-slate-800">{{ categoryLabel(category) }}</h3>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
<div v-for="rule in rules" :key="rule.rule_id" class="flex items-start justify-between gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50">
<div class="min-w-0">
<p class="text-sm font-medium text-slate-800">{{ rule.title }}</p>
<p class="text-xs text-slate-500 mt-0.5">{{ rule.description }}</p>
<p class="text-[10px] text-slate-400 font-mono mt-1">{{ rule.rule_id }}</p>
</div>
<label class="relative inline-flex items-center cursor-pointer flex-shrink-0 mt-0.5">
<input type="checkbox" v-model="rule.enabled" class="sr-only peer" />
<div class="w-9 h-5 bg-slate-300 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:right-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
</label>
</div>
</div>
</div>
</div>
</div>

<!-- Plan Settings -->
<div v-if="activeTab === 'plans'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("إعدادات الخطط") }}</h2>
</div>
<div class="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
<SettingField
v-for="field in planFields"
:key="field.key"
v-model="settings[field.key]"
:label="field.label"
:help="field.help"
:suffix="field.suffix"
:type="field.type"
:min="field.min"
:max="field.max"
:step="field.step"
:error="errors[field.key]"
/>
<div class="flex flex-col gap-1">
<label class="text-xs font-medium text-slate-600">{{ __('الأولوية الافتراضية للخطة') }}</label>
<select v-model="settings.default_plan_priority" class="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white">
<option value="Low">منخفضة</option>
<option value="Medium">متوسطة</option>
<option value="High">عالية</option>
<option value="Critical">حرجة</option>
</select>
</div>
<div class="flex items-center gap-2 p-3 rounded-lg border border-slate-200 bg-slate-50">
<input type="checkbox" id="monthly_snapshot_enabled" v-model="settings.monthly_snapshot_enabled" class="rounded text-blue-600" />
<label for="monthly_snapshot_enabled" class="text-sm text-slate-700 font-medium">{{ __('تمكين اللقطة الشهرية') }}</label>
</div>
</div>
</div>

<!-- Advanced Priority Settings -->
<div v-if="activeTab === 'advanced'" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
<div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
<svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
</svg>
<h2 class="font-bold text-slate-800">{{ __("إعدادات متقدمة — أولوية القرارات") }}</h2>
</div>
<div class="p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
<SettingField
v-for="field in advancedFields"
:key="field.key"
v-model="settings[field.key]"
:label="field.label"
:help="field.help"
:suffix="field.suffix"
:type="field.type"
:min="field.min"
:max="field.max"
:step="field.step"
:error="errors[field.key]"
/>
</div>
</div>

<!-- Save -->
<div class="sticky bottom-4 bg-white/90 backdrop-blur border border-slate-200 rounded-2xl shadow-lg p-4 flex items-center justify-between gap-4 z-20">
<div class="text-sm">
<span v-if="hasUnsavedChanges" class="text-amber-600 font-medium">{{ __('لديك تغييرات غير محفوظة') }}</span>
<span v-else class="text-emerald-600 font-medium">{{ __('تم حفظ جميع الإعدادات') }}</span>
<p v-if="Object.keys(errors).length" class="text-xs text-rose-600 mt-1">{{ __('يرجى تصحيح الأخطاء قبل الحفظ') }}</p>
</div>
<div class="flex items-center gap-2">
<button
v-if="hasUnsavedChanges"
@click="discardChanges"
:disabled="saving"
class="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition-all"
>
{{ __('إلغاء التغييرات') }}
</button>
<button
@click="saveSettings"
:disabled="saving || !hasUnsavedChanges"
class="px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-l from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/30 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
>
<svg v-if="saving" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
{{ saving ? __("جاري الحفظ...") : __("حفظ الإعدادات") }}
</button>
</div>
</div>
</template>
</template>
</main>
</div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { session } from "@/data/session"
import SettingField from "@/components/SettingField.vue"
import HelpLink from "@/components/HelpLink.vue"

const { showSuccess, showError } = useToast()

const isAdmin = ref(false)
const loading = ref(true)
const saving = ref(false)
const settings = ref({})
const categories = ref([])
const originalSnapshot = ref(null)
const errors = ref({})
const accSearchResults = ref({})
const accSearchFocused = ref({})
const accSearchLoading = ref({})
const accountInputRefs = ref([])
let accSearchDebounce = {}

const activeTab = ref("analysis")
const expandedCategoryId = ref(null)

const tabs = [
{ id: "analysis", label: "التحليل" },
{ id: "expenses", label: "المصاريف" },
{ id: "categories", label: "تصنيفات المصاريف" },
{ id: "rules", label: "قواعد القرارات" },
{ id: "plans", label: "الخطط" },
{ id: "advanced", label: "متقدم" },
]

const CATEGORY_LABELS = {
inventory: "المخزون",
sales: "المبيعات",
purchases: "المشتريات",
customers: "العملاء",
expenses: "المصاريف",
}

const CATEGORY_COLORS = {
inventory: "bg-amber-500",
sales: "bg-blue-500",
purchases: "bg-purple-500",
customers: "bg-pink-500",
expenses: "bg-emerald-500",
}

const thresholdGroups = [
{
key: "inventory",
title: "المخزون",
iconColor: "text-amber-600",
iconPath: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
fields: [
{ key: "slow_moving_days", label: "أيام المخزون البطيء", suffix: "يوم", type: "int", min: 1, help: "يعتبر الصنف بطيء الحركة عندما تتجاوز مدة تغطيته هذا الحد." },
{ key: "dead_stock_days", label: "أيام المخزون الراكد", suffix: "يوم", type: "int", min: 1, help: "يعتبر الصنف راكدًا عندما لا توجد مبيعات له خلال هذه المدة." },
{ key: "low_stock_days", label: "حد النقص الحرج", suffix: "يوم", type: "int", min: 1, help: "يعلّق مركز القرار تنبيهًا عاجلاً عندما يكفي المخزون لأقل من هذا العدد من الأيام." },
{ key: "warning_stock_days", label: "حد التحذير من نقص المخزون", suffix: "يوم", type: "int", min: 1, help: "يعلّق مركز القرار تحذيرًا عندما يكفي المخزون لأقل من هذا العدد من الأيام." },
],
},
{
key: "sales",
title: "المبيعات",
iconColor: "text-blue-600",
iconPath: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
fields: [
{ key: "sales_drop_percent", label: "حد انخفاض المبيعات", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عند انخفاض مبيعات صنف عن الفترة السابقة بنسبة تتجاوز هذا الحد." },
{ key: "sales_growth_percent", label: "حد نمو المبيعات", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عند نمو مبيعات صنف عن الفترة السابقة بنسبة تتجاوز هذا الحد." },
{ key: "min_sales_baseline", label: "الحد الأدنى لمبيعات الصنف للمقارنة", suffix: "قطعة", type: "int", min: 0, help: "الحد الأدنى لكمية المبيعات السابقة التي تُجعل الصنف مستحقًا للمقارنة." },
],
},
{
key: "purchases",
title: "المشتريات",
iconColor: "text-purple-600",
iconPath: "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z",
fields: [
{ key: "purchase_price_increase_percent", label: "حد زيادة سعر الشراء", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عند ارتفاع سعر شراء صنف بهذه النسبة عن المتوسط السابق." },
{ key: "overstock_purchase_ratio", label: "نسبة الشراء الزائد عن المبيعات", suffix: "x", type: "float", min: 0, step: 0.1, help: "يُنشأ تنبيه عندما تتجاوز كمية الشراء هذا المضاعف من كمية المبيعات." },
],
},
{
key: "customers",
title: "العملاء",
iconColor: "text-pink-600",
iconPath: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
fields: [
{ key: "customer_drop_percent", label: "حد انخفاض مبيعات العميل", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عند انخفاض مشتريات عميل عن الفترة السابقة بنسبة تتجاوز هذا الحد." },
{ key: "customer_inactive_multiplier", label: "مضاعف فترة توقف العميل", suffix: "x", type: "float", min: 0, step: 0.1, help: "يُعتبر العميل متوقفًا عندما تتجاوز فترة عدم الشراء هذا المضاعف من متوسط فترة شرائه." },
{ key: "min_customer_invoices", label: "الحد الأدنى لعدد فواتير العميل", suffix: "فاتورة", type: "int", min: 0, help: "الحد الأدنى لعدد الفواتير السابقة التي تُجعل العميل مستحقًا للمقارنة أو للكشف عن التوقف." },
],
},
]

const expenseFields = [
{ key: "expense_vs_sales_threshold", label: "حد نسبة المصاريف إلى المبيعات", suffix: "%", type: "percent", min: 0, max: 100, help: "إذا تجاوزت نسبة المصاريف الإجمالية إلى المبيعات هذا الحد، يُنشأ تنبيه." },
{ key: "expense_increase_threshold", label: "حد زيادة المصروف", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عندما ترتفع مصروفات تصنيف معين بنسبة تتجاوز هذا الحد مقارنة بالفترة السابقة." },
{ key: "expense_anomaly_threshold", label: "حد الشذوذ في المصاريف", suffix: "%", type: "percent", min: 0, max: 100, help: "يُنشأ تنبيه عندما يتجاوز إجمالي المصاريف المتوسط التاريخي بهذا النسبة." },
]

const advancedFields = [
{ key: "priority_urgent", label: "الحد العاجل للأولوية", suffix: "درجة", type: "int", min: 0, max: 100, help: "الدرجة الدنيا لتصنيف القرار كعاجل." },
{ key: "priority_important", label: "حد الأولوية المهمة", suffix: "درجة", type: "int", min: 0, max: 100, help: "الدرجة الدنيا لتصنيف القرار كمهم." },
{ key: "priority_review", label: "حد أولوية المراجعة", suffix: "درجة", type: "int", min: 0, max: 100, help: "الدرجة الدنيا لتصنيف القرار للمراجعة." },
]

const planFields = [
{ key: "plan_health_tolerance_pct", label: "نسبة تسامح صحة الخطة", suffix: "%", type: "percent", min: 0, max: 100, help: "النسبة المسموح بها بين التقدم الفعلي والمتوقع قبل تغيير حالة صحة الخطة." },
{ key: "auto_lock_snapshots_days", label: "أيام القفل التلقائي للقطة الشهرية", suffix: "يوم", type: "int", min: 0, help: "عدد الأيام بعد نهاية الشهر قبل قفل اللقطة الشهرية تلقائيًا." },
]

const groupedRules = computed(() => {
const map = {}
for (const rule of settings.value.rule_settings || []) {
if (!map[rule.category]) map[rule.category] = []
map[rule.category].push(rule)
}
return map
})

const hasUnsavedChanges = computed(() => {
if (!originalSnapshot.value) return false
return JSON.stringify(snapshot()) !== JSON.stringify(originalSnapshot.value)
})

function stripTempIds(list) {
return (list || []).map((c) => ({
name: c.name,
category_name: c.category_name,
description: c.description,
enabled: c.enabled,
target_percent_of_sales: c.target_percent_of_sales,
max_percent_of_sales: c.max_percent_of_sales,
accounts: (c.accounts || []).map((a) => ({
account: a.account,
enabled: a.enabled,
description: a.description,
})),
}))
}

const tabDirty = computed(() => {
if (!originalSnapshot.value) return {}
const orig = originalSnapshot.value
const s = settings.value
const os = orig.settings || {}
return {
analysis: thresholdGroups.some((g) => g.fields.some((f) => s[f.key] !== os[f.key])),
expenses: expenseFields.some((f) => s[f.key] !== os[f.key]),
categories:
JSON.stringify(stripTempIds(categories.value)) !== JSON.stringify(stripTempIds(orig.categories)),
rules:
JSON.stringify((s.rule_settings || []).map((r) => ({ rule_id: r.rule_id, enabled: r.enabled }))) !==
JSON.stringify((os.rule_settings || []).map((r) => ({ rule_id: r.rule_id, enabled: r.enabled }))),
plans:
planFields.some((f) => s[f.key] !== os[f.key]) ||
s.default_plan_priority !== os.default_plan_priority ||
!!s.monthly_snapshot_enabled !== !!os.monthly_snapshot_enabled,
advanced: advancedFields.some((f) => s[f.key] !== os[f.key]),
}
})

onMounted(async () => {
isAdmin.value = session.user === "Administrator"
if (!isAdmin.value) {
loading.value = false
return
}
await loadSettings()
window.addEventListener("beforeunload", onBeforeUnload)
document.addEventListener("click", onDocumentClick)
})

onBeforeUnmount(() => {
window.removeEventListener("beforeunload", onBeforeUnload)
document.removeEventListener("click", onDocumentClick)
})

function onBeforeUnload(e) {
if (hasUnsavedChanges.value) {
e.preventDefault()
e.returnValue = ""
}
}

function categoryLabel(category) {
return __(CATEGORY_LABELS[category] || category)
}

function ruleCategoryColor(category) {
return CATEGORY_COLORS[category] || "bg-slate-400"
}

function snapshot() {
return {
settings: JSON.parse(JSON.stringify(settings.value)),
categories: JSON.parse(JSON.stringify(categories.value)),
}
}

async function loadSettings() {
loading.value = true
try {
const result = await call("bs.baron_servies.api.decision_center.api.get_decision_center_settings")
settings.value = result?.settings || {}
categories.value = (result?.categories || []).map((c) => ({
...c,
accounts: (c.accounts || []).map((a) => ({ ...a, _tempId: Math.random().toString(36).slice(2) })),
_tempId: c.name || Math.random().toString(36).slice(2),
}))
originalSnapshot.value = snapshot()
errors.value = {}
} catch (e) {
showError(e?.message || "فشل تحميل الإعدادات")
} finally {
loading.value = false
}
}

function validate() {
errors.value = {}
const allFields = [
...thresholdGroups.flatMap((g) => g.fields),
...expenseFields,
...planFields,
...advancedFields,
]
for (const field of allFields) {
const value = settings.value[field.key]
if (value === "" || value === null || value === undefined || Number.isNaN(Number(value))) {
errors.value[field.key] = __("هذا الحقل مطلوب")
continue
}
const num = Number(value)
if (field.min !== undefined && num < field.min) {
errors.value[field.key] = __("القيمة يجب ألا تقل عن {0}", [field.min])
}
if (field.max !== undefined && num > field.max) {
errors.value[field.key] = __("القيمة يجب ألا تتجاوز {0}", [field.max])
}
}

const low = Number(settings.value.low_stock_days)
const warning = Number(settings.value.warning_stock_days)
if (!Number.isNaN(low) && !Number.isNaN(warning) && low >= warning) {
errors.value.low_stock_days = __("يجب أن يكون حد النقص الحرج أقل من حد التحذير")
errors.value.warning_stock_days = __("يجب أن يكون حد التحذير أكبر من حد النقص الحرج")
}

const urgent = Number(settings.value.priority_urgent)
const important = Number(settings.value.priority_important)
const review = Number(settings.value.priority_review)
if (!Number.isNaN(urgent) && !Number.isNaN(important) && urgent <= important) {
errors.value.priority_urgent = __("الحد العاجل يجب أن يكون أكبر من الحد المهم")
}
if (!Number.isNaN(important) && !Number.isNaN(review) && important <= review) {
errors.value.priority_important = __("الحد المهم يجب أن يكون أكبر من حد المراجعة")
}

return Object.keys(errors.value).length === 0
}

async function saveSettings() {
if (!validate()) {
showError(__("يرجى تصحيح الأخطاء قبل الحفظ"))
return
}
saving.value = true
try {
const payload = {
settings: settings.value,
categories: categories.value.map((c) => ({
name: c.name,
category_name: c.category_name,
description: c.description,
enabled: c.enabled,
target_percent_of_sales: c.target_percent_of_sales,
max_percent_of_sales: c.max_percent_of_sales,
accounts: c.accounts.map((a) => ({
account: a.account,
enabled: a.enabled,
description: a.description,
})),
})),
}
await call("bs.baron_servies.api.decision_center.api.update_decision_center_settings", {
payload: JSON.stringify(payload),
})
showSuccess("تم حفظ الإعدادات")
await loadSettings()
} catch (e) {
showError(e?.message || "فشل حفظ الإعدادات")
} finally {
saving.value = false
}
}

function toggleCategory(cat) {
expandedCategoryId.value = expandedCategoryId.value === cat._tempId ? null : cat._tempId
}

function discardChanges() {
if (!originalSnapshot.value) return
const snap = JSON.parse(JSON.stringify(originalSnapshot.value))
settings.value = snap.settings
categories.value = snap.categories
errors.value = {}
}

function addCategory() {
const newCat = {
name: "",
category_name: "",
description: "",
enabled: true,
target_percent_of_sales: null,
max_percent_of_sales: null,
accounts: [],
_tempId: Math.random().toString(36).slice(2),
}
categories.value.push(newCat)
expandedCategoryId.value = newCat._tempId
}

function removeCategory(idx) {
const cat = categories.value[idx]
if (cat.name) {
deleteCategory(cat)
} else {
categories.value.splice(idx, 1)
}
}

async function deleteCategory(cat) {
if (!confirm(__('هل تريد حذف التصنيف "{0}"؟', [cat.category_name])))
return
try {
await call("bs.baron_servies.api.decision_center.api.delete_expense_category", {
category_name: cat.name,
})
categories.value = categories.value.filter((c) => c._tempId !== cat._tempId)
showSuccess("تم حذف التصنيف")
} catch (e) {
showError(e?.message || "فشل حذف التصنيف")
}
}

function addAccount(cat) {
const tempId = Math.random().toString(36).slice(2)
cat.accounts.push({
account: "",
enabled: true,
description: "",
_tempId: tempId,
})
nextTick(() => {
const el = accountInputRefs.value[tempId]
if (el) {
el.focus()
accSearchFocused.value[tempId] = true
accSearchResults.value[tempId] = []
doAccountSearch({ _tempId: tempId }, "")
}
})
}

function removeAccount(cat, idx) {
cat.accounts.splice(idx, 1)
}

function onAccountSearch(acc, event) {
const key = acc._tempId
accSearchFocused.value[key] = true
clearTimeout(accSearchDebounce[key])
accSearchDebounce[key] = setTimeout(() => doAccountSearch(acc, event.target.value), 300)
}

async function doAccountSearch(acc, term) {
const key = acc._tempId
if (!term || term.length < 2) {
term = ""
}
accSearchLoading.value[key] = true
try {
const res = await call("frappe.desk.search.search_link", {
doctype: "Account",
txt: term,
filters: JSON.stringify({ is_group: 0, root_type: "Expense" }),
})
const list = Array.isArray(res) ? res : res?.results || []
accSearchResults.value[key] = list.slice(0, 20)
} catch (e) {
console.error("Account search failed:", e)
accSearchResults.value[key] = []
} finally {
accSearchLoading.value[key] = false
}
}

function selectAccount(acc, result) {
acc.account = result.value
accSearchResults.value[acc._tempId] = []
accSearchFocused.value[acc._tempId] = false
}

function onDocumentClick(e) {
const inside = e.target.closest(".account-search")
if (!inside) {
accSearchFocused.value = {}
}
}
</script>
