<template>
  <div class="p-4 sm:p-6 max-w-5xl mx-auto space-y-4" dir="rtl">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3 min-w-0">
        <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 shadow-lg shadow-indigo-500/25">
          <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="min-w-0">
          <h1 class="text-lg font-bold text-slate-900 truncate">{{ __('مركز المساعدة') }}</h1>
          <p class="text-xs text-slate-500 truncate">{{ __('دليلك لفهم مركز القرار واستخدامه بثقة') }}</p>
        </div>
      </div>

      <!-- Search -->
      <div class="relative w-full sm:w-72" ref="searchBoxRef">
        <div class="relative">
          <svg class="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 10.5a6.5 6.5 0 11-13 0 6.5 6.5 0 0113 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="__('ابحث في المساعدة…')"
            class="w-full border border-slate-300 rounded-xl bg-white ps-9 pe-8 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            @focus="searchOpen = true"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute end-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            @click="searchQuery = ''"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div
          v-if="searchOpen && searchQuery && searchResults.length"
          class="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden"
        >
          <button
            v-for="(r, i) in searchResults"
            :key="i"
            type="button"
            class="w-full text-start px-3 py-2.5 hover:bg-indigo-50 border-b border-slate-100 last:border-0"
            @click="goToResult(r)"
          >
            <span class="block text-xs font-semibold text-slate-800">{{ r.title }}</span>
            <span class="block text-[10px] text-slate-500 mt-0.5">{{ tabLabel(r.tab) }}</span>
          </button>
        </div>
        <div
          v-else-if="searchOpen && searchQuery && !searchResults.length"
          class="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg px-3 py-2.5 text-xs text-slate-500"
        >
          {{ __('لا توجد نتائج') }}
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <HelpTabs :tabs="HELP_TABS" v-model="activeTab" />

    <!-- ═══════════════════════ ابدأ من هنا ═══════════════════════ -->
    <div v-if="activeTab === 'start'" class="space-y-4">
      <HelpCard :title="__('ما الذي يفعله مركز القرار؟')" icon="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z">
        <p class="text-xs text-slate-600 leading-relaxed mb-3">
          {{ __('مركز القرار لا ينفذ شيئًا نيابة عنك — هو يراقب بياناتك، يكتشف ما يحتاج انتباهك، ويساعدك على تخطيط التحسين ومتابعته:') }}
        </p>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div v-for="f in startFeatures" :key="f.label" class="rounded-xl border border-slate-200 bg-slate-50/60 p-3 text-center">
            <svg class="h-5 w-5 mx-auto text-indigo-600 mb-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="f.icon" />
            </svg>
            <p class="text-xs font-bold text-slate-800">{{ f.label }}</p>
            <p class="text-[10px] text-slate-500 mt-0.5 leading-snug">{{ f.caption }}</p>
          </div>
        </div>
      </HelpCard>

      <HelpCard :title="__('كيف تعمل المنظومة؟')" icon="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
        <HelpFlow :steps="systemFlow" />
        <p class="text-[11px] text-slate-500 mt-3 leading-relaxed">
          {{ __('الدورة تتكرر: القرارات تُغذّي الخطة، ونتائج الخطة تظهر في القرارات والتقارير التالية.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('كيف تقرأ قرارًا؟')" icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" anchor="decision-anatomy">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
          <MiniMockup
            url="/bs/decision-center"
            :zones="[
              { label: 'عنوان القرار + شريحة الأولوية' },
              { label: 'الشدة والفئة', tone: 'accent' },
              { label: 'الأدلة الرقمية (لماذا ظهر؟)', tone: 'accent' },
              { label: 'التوصية وزر الإجراء' },
              { label: 'تفاصيل الكيانات المتأثرة' },
            ]"
          />
          <ul class="space-y-2">
            <li v-for="(f, i) in decisionAnatomy" :key="i" class="flex items-start gap-2 text-xs text-slate-600 leading-snug">
              <span class="flex h-4.5 w-4.5 min-w-[18px] min-h-[18px] flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold mt-0.5">{{ i + 1 }}</span>
              <span>{{ f }}</span>
            </li>
          </ul>
        </div>
      </HelpCard>

      <HelpCard :title="__('روتين إداري مقترح')" icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" anchor="routine">
        <DisclaimerBanner tone="info" class="mb-3">
          {{ __('هذا روتين مقترح لاستخدام مركز القرار — طريقة عمل إدارية مقترحة وليست سلوكًا آليًا مفروضًا من النظام.') }}
        </DisclaimerBanner>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div class="rounded-xl border border-slate-200 p-3">
            <p class="text-xs font-bold text-slate-800 mb-1">{{ __('يوميًا (دقيقتان)') }}</p>
            <p class="text-[11px] text-slate-500 leading-snug">{{ __('افتح نظرة عامة، تصفح قرارات «عاجل» و«مهم» الجديدة.') }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 p-3">
            <p class="text-xs font-bold text-slate-800 mb-1">{{ __('أسبوعيًا (١٠ دقائق)') }}</p>
            <p class="text-[11px] text-slate-500 leading-snug">{{ __('راجع تقدم الخطة النشطة وصحتها، وحدّث إجراءاتها.') }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 p-3">
            <p class="text-xs font-bold text-slate-800 mb-1">{{ __('شهريًا (٢٠ دقيقة)') }}</p>
            <p class="text-[11px] text-slate-500 leading-snug">{{ __('راجع التقرير الشهري للشهر الماضي، أغلق الخطة المنتهية أو جدّلها، وخطط للقادم.') }}</p>
          </div>
        </div>
      </HelpCard>

      <HelpCard :title="__('ابدأ الآن')" icon="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" accent="emerald">
        <div class="flex flex-wrap gap-2">
          <RouterLink :to="{ name: 'DecisionCenter' }" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700">
            {{ __('افتح نظرة عامة') }}
          </RouterLink>
          <RouterLink :to="{ name: 'DecisionCenterPlans' }" class="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            {{ __('استعرض الخطط') }}
          </RouterLink>
          <RouterLink :to="{ name: 'DecisionCenterSettings' }" class="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            {{ __('راجع الإعدادات') }}
          </RouterLink>
        </div>
      </HelpCard>
    </div>

    <!-- ═══════════════════════ الخطط ═══════════════════════ -->
    <div v-else-if="activeTab === 'plans'" class="space-y-4">
      <HelpCard :title="__('ما هي الخطة؟')" icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" anchor="what-is-plan">
        <p class="text-xs text-slate-600 leading-relaxed mb-3">
          {{ __('الخطة تحوّل قرارًا إداريًا إلى هدف قابل للقياس: مؤشرات رئيسية (KPIs)، إجراءات تنفيذية، ومدة زمنية. في كل لحظة يُسمح بخطة نشطة واحدة فقط.') }}
        </p>
        <HelpFlow :steps="planLifecycle" />
        <div class="flex flex-wrap gap-1.5 mt-3">
          <StatusChip kind="plan-status" value="Draft" />
          <StatusChip kind="plan-status" value="Scheduled" />
          <StatusChip kind="plan-status" value="Active" />
          <StatusChip kind="plan-status" value="Completed" />
          <StatusChip kind="plan-status" value="Cancelled" />
        </div>
      </HelpCard>

      <HelpCard :title="__('حالة المجدول — توصية فقط')" icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" anchor="scheduler_status">
        <div class="flex gap-2 flex-wrap mb-2">
          <StatusChip kind="scheduler" value="ready_to_start" />
          <StatusChip kind="scheduler" value="ready_to_close" />
        </div>
        <p class="text-xs text-slate-600 leading-relaxed">
          {{ __('يوميًا يفحص النظام تواريخ الخطط ويعرض توصية: «جاهزة للبدء» عند حلول تاريخ بدايتها، و«جاهزة للإغلاق» عند انتهائها. لا يفعّل ولا يغلق تلقائيًا — القرار دائمًا لك.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('كيف تُقاس النتيجة؟ ثلاث طرق')" icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" anchor="progress-strategies">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div v-for="s in PROGRESS_STRATEGIES" :key="s.key" class="rounded-xl border border-slate-200 p-3 space-y-2">
            <p class="text-xs font-bold text-slate-800">{{ s.label }}</p>
            <p class="text-[10px] text-slate-500">{{ __('مثال مؤشرات:') }} {{ s.examples }}</p>
            <p class="text-[11px] text-slate-600 leading-snug">{{ s.explanation }}</p>
          </div>
        </div>
      </HelpCard>

      <HelpCard :title="__('صحة الخطة')" icon="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" anchor="plan_health">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
          <div class="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3">
            <StatusChip kind="health" value="on_track" />
            <p class="text-[11px] text-slate-600 mt-1.5 leading-snug">{{ __('تقدم النتيجة ضمن هامش التسامح عن الوقت المنقضي.') }}</p>
          </div>
          <div class="rounded-xl border border-amber-200 bg-amber-50/50 p-3">
            <StatusChip kind="health" value="needs_attention" />
            <p class="text-[11px] text-slate-600 mt-1.5 leading-snug">{{ __('متأخرة جزئيًا — تستحق مراجعة الإجراءات.') }}</p>
          </div>
          <div class="rounded-xl border border-rose-200 bg-rose-50/50 p-3">
            <StatusChip kind="health" value="behind" />
            <p class="text-[11px] text-slate-600 mt-1.5 leading-snug">{{ __('متأخرة بوضوح — قد تحتاج تعديل الهدف أو الإجراءات.') }}</p>
          </div>
        </div>
        <p class="text-[11px] text-slate-500 leading-snug">
          {{ __('الهامش الافتراضي ١٠٪ ويُضبط من الإعدادات (هامش تسامح صحة الخطة) أو لكل مؤشر رئيسي داخل الخطة.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('نقاط القياس الشهرية')" icon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" anchor="checkpoints">
        <HelpFlow :steps="checkpointFlow" />
        <p class="text-xs text-slate-600 leading-relaxed mt-3">
          {{ __('عند تفعيل الخطة تُنشأ نقطة قياس لكل شهر من مدتها، بقيمة مستهدفة على المسار بين خط الأساس والهدف. مع كل شهر تُقارن القيمة الفعلية بالمستهدفة — فتعرف مبكرًا إن كنت خلف المسار.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('اللقطة الشهرية')" icon="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" anchor="monthly_snapshot">
        <p class="text-xs text-slate-600 leading-relaxed">
          {{ __('في بداية كل شهر يحفظ النظام تلقائيًا تقرير الشهر السابق كاملًا (مؤشرات، قرارات، حالة الخطة). تبقى اللقطة قابلة لإعادة التوليد خلال «أيام السماح» ثم تُقفل نهائيًا — مرجع تاريخي لا يتغير.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('مثال كامل: خطة خفض المصاريف')" icon="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" anchor="plan-example" accent="emerald">
        <HelpFlow :steps="planExampleFlow" />
      </HelpCard>

      <HelpCard :title="__('مصطلحات الخطط')" icon="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" anchor="plans-glossary">
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2.5">
          <div v-for="c in conceptsFor('plans')" :key="c.id" :id="`help-section-${c.id}`" class="scroll-mt-24">
            <dt class="text-xs font-bold text-slate-800">{{ c.title }}</dt>
            <dd class="text-[11px] text-slate-500 leading-snug mt-0.5">{{ c.text }}</dd>
          </div>
        </dl>
      </HelpCard>
    </div>

    <!-- ═══════════════════════ شرح الواجهات ═══════════════════════ -->
    <div v-else-if="activeTab === 'screens'" class="space-y-4">
      <HelpCard :title="__('خريطة الشاشات')" icon="M4 5a1 1 0 011-1h14a1 1 0 011 1v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm4 15h8" anchor="screens-intro">
        <p class="text-xs text-slate-600 leading-relaxed">
          {{ __('سبع شاشات رئيسية داخل مركز القرار + صفحات تفاصيل القرار والخطة والتقرير. كل شاشة تجيب على سؤال إداري محدد — ابدأ بالنظرة العامة ثم تعمّق حسب ما تكشفه.') }}
        </p>
      </HelpCard>

      <HelpCard
        v-for="s in SCREENS_HELP"
        :key="s.id"
        :title="s.title"
        :anchor="s.id"
        accent="blue"
      >
        <div class="space-y-3">
          <p class="text-xs text-slate-600 leading-relaxed">{{ s.purpose }}</p>
          <MiniMockup :zones="s.hotspots.map((h) => ({ label: h }))" />
          <ul class="space-y-1">
            <li v-for="(k, i) in s.keyElements" :key="i" class="flex items-start gap-1.5 text-[11px] text-slate-600 leading-snug">
              <svg class="h-3 w-3 mt-0.5 flex-shrink-0 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ k }}
            </li>
          </ul>
          <p class="text-[11px] text-slate-600 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 leading-snug">
            <span class="font-semibold text-amber-700">{{ __('إذا رأيت مشكلة:') }}</span> {{ s.problemAction }}
          </p>
        </div>
      </HelpCard>

      <HelpCard :title="__('مفاهيم الشاشات')" icon="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" anchor="screens-glossary">
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2.5">
          <div v-for="c in conceptsFor('screens')" :key="c.id" :id="`help-section-${c.id}`" class="scroll-mt-24">
            <dt class="text-xs font-bold text-slate-800">{{ c.title }}</dt>
            <dd class="text-[11px] text-slate-500 leading-snug mt-0.5">{{ c.text }}</dd>
          </div>
        </dl>
      </HelpCard>
    </div>

    <!-- ═══════════════════════ الإعدادات ═══════════════════════ -->
    <div v-else-if="activeTab === 'settings'" class="space-y-4">
      <HelpCard :title="__('كيف تؤثر الإعدادات في القرارات؟')" icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z" anchor="settings-intro">
        <DisclaimerBanner class="mb-3">
          {{ __('هذا التبويب للشرح فقط — التعديل الفعلي يتم في صفحة الإعدادات (مدير النظام). القيمة الحالية تُعرض للقراءة عند توفر الصلاحية.') }}
        </DisclaimerBanner>
        <HelpFlow :steps="settingsFlow" />
      </HelpCard>

      <template v-for="sec in SETTINGS_SECTIONS" :key="sec.id">
        <h3 class="text-sm font-bold text-slate-700 px-1 pt-2">{{ sec.label }}</h3>
        <SettingCard
          v-for="s in settingsIn(sec.id)"
          :key="s.key"
          :setting="s"
          :current="liveSettings?.[s.key]"
          @open-rule="openRule"
        />
      </template>

      <h3 class="text-sm font-bold text-slate-700 px-1 pt-2">{{ __('إعدادات غير رقمية') }}</h3>
      <HelpCard
        v-for="s in SPECIAL_SETTINGS_HELP"
        :key="s.key"
        :title="s.label"
        :subtitle="__('الافتراضي:') + ' ' + s.default"
        :anchor="s.key"
        accent="slate"
      >
        <p class="text-xs text-slate-600 leading-relaxed">{{ s.meaning }}</p>
        <p class="text-[11px] text-slate-500 mt-2 leading-snug">
          <span class="font-semibold text-slate-600">{{ __('مثال:') }}</span> {{ s.example }}
        </p>
      </HelpCard>
    </div>

    <!-- ═══════════════════════ القواعد الإدارية ═══════════════════════ -->
    <div v-else-if="activeTab === 'rules'" class="space-y-4">
      <HelpCard :title="__('ما هي القواعد الإدارية؟')" icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" anchor="rules-intro">
        <p class="text-xs text-slate-600 leading-relaxed mb-3">
          {{ __('١٣ قاعدة تفحص بياناتك كلما حدّثت مركز القرار: ٤ للمخزون، ٢ للمبيعات، ٢ للعملاء، ١ للمشتريات، ٤ للمصاريف. كل قاعدة تنتج قرارًا بأدلة وتوصية. يمكن إيقاف أي قاعدة من تبويب القواعد في الإعدادات.') }}
        </p>
        <HelpFlow :steps="ruleEngineFlow" />
      </HelpCard>

      <template v-for="cat in RULE_CATEGORIES" :key="cat.id">
        <h3 class="text-sm font-bold text-slate-700 px-1 pt-2 flex items-center gap-2">
          <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="cat.icon" />
          </svg>
          {{ cat.label }}
        </h3>
        <RuleCard
          v-for="r in rulesIn(cat.id)"
          :key="r.id"
          :rule="r"
          :enabled="ruleEnabled[r.id] ?? null"
          @open-setting="openSetting"
        />
      </template>
    </div>

    <!-- ═══════════════════════ كيف تُحسب الأرقام ═══════════════════════ -->
    <div v-else-if="activeTab === 'formulas'" class="space-y-4">
      <HelpCard :title="__('الفترات والمقارنات')" icon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" anchor="periods">
        <p class="text-xs text-slate-600 leading-relaxed mb-2">
          {{ __('كل مؤشر يُقاس على «الفترة الحالية» المختارة في أعلى الشاشة، ويُقارن بـ«فترة سابقة مكافئة» بنفس الطول:') }}
        </p>
        <ul class="space-y-1.5 text-[11px] text-slate-600 leading-snug">
          <li>· {{ __('«هذا الشهر» حتى اليوم ← نفس الجزء المنقضي من الشهر الماضي') }}</li>
          <li>· {{ __('«هذا الربع» و«هذه السنة» ← نفس الجزء المنقضي من الفترة السابقة') }}</li>
          <li>· {{ __('«آخر ٣٠ يومًا» والفترات المخصصة ← نافذة سابقة متساوية الطول') }}</li>
        </ul>
      </HelpCard>

      <FormulaCard v-for="f in FORMULA_CARDS" :key="f.key" :card="f" />

      <HelpCard :title="__('حدود الأولوية')" icon="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" anchor="priority-bands">
        <div class="flex flex-wrap gap-1.5 mb-2">
          <StatusChip kind="priority" value="urgent" />
          <StatusChip kind="priority" value="important" />
          <StatusChip kind="priority" value="review" />
          <StatusChip kind="priority" value="opportunity" />
        </div>
        <p class="text-xs text-slate-600 leading-relaxed">
          {{ __('بعد حساب الدرجة (٠–١٠٠):') }} ≥ <strong>{{ liveSettings?.priority_urgent ?? 80 }}</strong> {{ __('عاجل، ≥') }} <strong>{{ liveSettings?.priority_important ?? 60 }}</strong> {{ __('مهم، ≥') }} <strong>{{ liveSettings?.priority_review ?? 40 }}</strong> {{ __('مراجعة، وما دونها فرصة. الحدود قابلة للضبط من الإعدادات.') }}
        </p>
      </HelpCard>

      <HelpCard :title="__('مؤشرات غير متاحة حاليًا')" icon="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" anchor="unavailable" accent="slate">
        <div class="space-y-2">
          <div v-for="m in UNAVAILABLE_METRICS" :key="m.key" class="flex items-start gap-2 rounded-lg bg-slate-50 border border-slate-200 px-3 py-2">
            <svg class="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <div>
              <p class="text-xs font-bold text-slate-700">{{ m.label }}</p>
              <p class="text-[11px] text-slate-500 leading-snug">{{ m.reason }}</p>
            </div>
          </div>
        </div>
      </HelpCard>
    </div>

    <!-- ═══════════════════════ أمثلة عملية ═══════════════════════ -->
    <div v-else-if="activeTab === 'scenarios'" class="space-y-4">
      <HelpCard :title="__('سيناريوهات من واقع الاستخدام')" icon="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" anchor="scenarios-intro">
        <p class="text-xs text-slate-600 leading-relaxed">
          {{ __('ستة سيناريوهات متكررة: كلٌّ يبدأ بملاحظة إدارية وينتهي بإجراء واضح — اتبع الخطوات بالترتيب.') }}
        </p>
      </HelpCard>
      <ScenarioCard
        v-for="s in SCENARIOS"
        :key="s.id"
        :scenario="s"
        @open-help="goToResult({ tab: $event.tab, section: $event.section })"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { call } from '@/utils/apiWrapper'
import HelpTabs from '@/components/help/HelpTabs.vue'
import HelpCard from '@/components/help/HelpCard.vue'
import HelpFlow from '@/components/help/HelpFlow.vue'
import MiniMockup from '@/components/help/MiniMockup.vue'
import StatusChip from '@/components/help/StatusChip.vue'
import RuleCard from '@/components/help/RuleCard.vue'
import SettingCard from '@/components/help/SettingCard.vue'
import FormulaCard from '@/components/help/FormulaCard.vue'
import ScenarioCard from '@/components/help/ScenarioCard.vue'
import DisclaimerBanner from '@/components/help/DisclaimerBanner.vue'
import {
  HELP_TABS, DEFAULT_TAB, HELP_SEARCH_INDEX,
  RULES_HELP, RULE_CATEGORIES,
  SETTINGS_HELP, SPECIAL_SETTINGS_HELP, SETTINGS_SECTIONS,
  SCREENS_HELP, SCENARIOS, CONCEPTS,
  FORMULA_CARDS, PROGRESS_STRATEGIES, UNAVAILABLE_METRICS,
} from '@/data/help'

const route = useRoute()
const router = useRouter()

// ── tabs & deep links ────────────────────────────────────────────────────────
const activeTab = ref(DEFAULT_TAB)

function tabLabel(id) {
  return HELP_TABS.find((t) => t.id === id)?.label || ''
}

function scrollToSection(section) {
  nextTick(() => {
    requestAnimationFrame(() => {
      document.getElementById(`help-section-${section}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' })
    })
  })
}

function applyQuery() {
  const tab = route.query.tab
  activeTab.value = HELP_TABS.some((t) => t.id === tab) ? tab : DEFAULT_TAB
  if (route.query.section) scrollToSection(route.query.section)
}

watch(() => route.query, applyQuery)

watch(activeTab, (tab) => {
  // keep ?tab= in the URL for shareable deep links (replace, not push)
  const q = { ...route.query, tab }
  delete q.section
  router.replace({ query: q })
})

// ── live settings & rule states ──────────────────────────────────────────────
const liveSettings = ref(null)
const ruleEnabled = ref({})

async function loadSettings() {
  try {
    const res = await call('bs.baron_servies.api.decision_center.api.get_decision_center_settings')
    liveSettings.value = res
    const map = {}
    for (const r of res?.rule_settings || []) map[r.rule_id] = !!r.enabled
    ruleEnabled.value = map
  } catch (e) {
    // no permission / offline → current values simply stay hidden
    liveSettings.value = null
    ruleEnabled.value = {}
  }
}

// ── search ───────────────────────────────────────────────────────────────────
const searchQuery = ref('')
const searchOpen = ref(false)
const searchBoxRef = ref(null)

const searchResults = computed(() => {
  const q = searchQuery.value.trim()
  if (!q) return []
  return HELP_SEARCH_INDEX
    .filter((e) => e.text.includes(q))
    .slice(0, 8)
})

function goToResult(r) {
  searchQuery.value = ''
  searchOpen.value = false
  if (r.tab && r.tab !== activeTab.value) {
    router.replace({ query: { tab: r.tab, section: r.section } })
    activeTab.value = r.tab
    if (r.section) scrollToSection(r.section)
  } else if (r.section) {
    router.replace({ query: { tab: activeTab.value, section: r.section } })
    scrollToSection(r.section)
  }
}

function onDocClick(e) {
  if (searchBoxRef.value && !searchBoxRef.value.contains(e.target)) searchOpen.value = false
}

// ── cross-tab navigation from cards ──────────────────────────────────────────
function openSetting(key) {
  goToResult({ tab: 'settings', section: key })
}
function openRule(id) {
  goToResult({ tab: 'rules', section: id })
}

// ── content groupings ────────────────────────────────────────────────────────
function settingsIn(section) { return SETTINGS_HELP.filter((s) => s.section === section) }
function rulesIn(category) { return RULES_HELP.filter((r) => r.category === category) }
function conceptsFor(tab) { return CONCEPTS.filter((c) => c.section === tab) }

// ── static content ───────────────────────────────────────────────────────────
const startFeatures = [
  { label: 'يراقب', caption: 'مبيعاتك ومشترياتك ومخزونك وعملاءك ومصاريفك', icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' },
  { label: 'يكتشف', caption: '١٣ قاعدة تحوّل البيانات إلى قرارات مرقّمة بالأولوية', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
  { label: 'يخطّط', caption: 'خطط بأهداف وإجراءات ونقاط قياس شهرية', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { label: 'يتابع', caption: 'تقارير شهرية مقفلة تُظهر أثر قراراتك', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
]

const systemFlow = [
  { label: 'بياناتك اليومية', caption: 'فواتير، مخزون، قيود', tone: 'info' },
  { label: 'القواعد الإدارية', caption: '١٣ فحصًا آليًا', tone: 'default' },
  { label: 'القرارات', caption: 'مشاكل وفرص بالأولوية', tone: 'warn' },
  { label: 'الخطة', caption: 'هدف + إجراءات + متابعة', tone: 'info' },
  { label: 'التقرير الشهري', caption: 'أثر القرارات محفوظًا', tone: 'success' },
]

const decisionAnatomy = [
  'العنوان وشريحة الأولوية (عاجل/مهم/مراجعة/فرصة) تخبرك بالأهمية فورًا',
  'الشدة والفئة تحددان مجال المشكلة وخطورتها',
  'الأدلة الرقمية توضّح لماذا ظهر القرار — القيم التي تجاوزت الحدود',
  'التوصية والإجراء المقترح: ماذا تفعل وعلى أي شاشة',
  'قائمة الكيانات المتأثرة: الأصناف أو العملاء أو التصنيفات داخل القرار',
]

const planLifecycle = [
  { label: 'مسودة', caption: 'صياغة ومراجعة', tone: 'default' },
  { label: 'مجدولة', caption: 'جاهزة بتاريخ بداية', tone: 'info' },
  { label: 'نشطة', caption: 'الأهداف تُقاس فعليًا', tone: 'warn' },
  { label: 'مكتملة / ملغاة', caption: 'قرار إداري منك', tone: 'success' },
]

const checkpointFlow = [
  { label: 'تفعيل الخطة', tone: 'default' },
  { label: 'نقطة قياس لكل شهر', caption: 'بقيمة مستهدفة على المسار', tone: 'info' },
  { label: 'مقارنة شهرية', caption: 'فعلي مقابل مستهدف', tone: 'warn' },
  { label: 'تدخّل مبكر', caption: 'قبل نهاية الخطة', tone: 'success' },
]

const planExampleFlow = [
  { label: 'قرار: مصاريف مرتفعة', caption: '١٥٪ من المبيعات', tone: 'warn' },
  { label: 'خطة: خفض إلى ١٢٪', caption: '٣ أشهر', tone: 'default' },
  { label: 'إجراءات', caption: 'مراجعة عقود، إيقاف بند', tone: 'info' },
  { label: 'متابعة شهرية', caption: 'نقاط قياس + صحة', tone: 'info' },
  { label: 'إكمال + تقرير', caption: 'الأثر محفوظ', tone: 'success' },
]

const settingsFlow = [
  { label: 'تغيّر الإعداد', caption: 'من صفحة الإعدادات', tone: 'default' },
  { label: 'يُحفظ في النظام', tone: 'info' },
  { label: 'القواعد تقرأه فورًا', caption: 'في الفحص التالي', tone: 'warn' },
  { label: 'القرارات تتغير', caption: 'أكثر أو أقل حساسية', tone: 'success' },
]

const ruleEngineFlow = [
  { label: 'تحديث مركز القرار', tone: 'info' },
  { label: 'القواعد المفعّلة تفحص', caption: 'بحدودك المضبوطة', tone: 'default' },
  { label: 'تُنتج قرارات', caption: 'بأدلة وشدة', tone: 'warn' },
  { label: 'تُرتَّب بالأولوية', caption: 'درجة ٠–١٠٠', tone: 'success' },
]

// ── lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  applyQuery()
  loadSettings()
  document.addEventListener('click', onDocClick)
})
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>
