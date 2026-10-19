// Help Center — formula / metric content.
// `key` values MUST match METRIC_REGISTRY keys in
// bs/baron_servies/api/decision_center/registry.py.
// `strategy` mirrors registry `progress_strategy` (level / cumulative_growth
// / cumulative_ceiling). `available:false` mirrors `system_available: 0`.

export const FORMULA_CARDS = [
	{
		key: "expenses_to_sales_pct",
		title: "نسبة المصاريف إلى المبيعات",
		formula: ["إجمالي المصاريف", "÷", "صافي المبيعات", "×", "١٠٠"],
		example: "مصاريف ٩٠٬٠٠٠ ÷ مبيعات ٦٠٠٬٠٠٠ × ١٠٠ = ١٥٪",
		explanation: "كلما انخفضت النسبة كان التشغيل أكفأ. الهدف الإداري المعتاد هو الخفض.",
		techDetails: "المصاريف = مجموع (مدين − دائن) قيود اليومية العامة على الحسابات المفعّلة في تصنيفات مركز القرار.",
	},
	{
		key: "change_pct",
		title: "نسبة التغير عن الفترة السابقة",
		formula: ["(الفترة الحالية", "−", "الفترة السابقة)", "÷", "الفترة السابقة", "×", "١٠٠"],
		example: "مبيعات ١٢٠٬٠٠٠ مقابل ١٠٠٬٠٠٠ → +٢٠٪",
		explanation: "«الفترة السابقة» فترة مكافئة بالطول نفسه: الشهر الحالي يُقارن بنفس الجزء المنقضي من الشهر الماضي، وآخر ٣٠ يومًا بالثلاثين التي قبلها، وهكذا.",
		techDetails: "الفترات المالية (هذا الشهر/الربع/السنة) تقارن بالجزء المنقضي المكافئ من الفترة السابقة؛ الفترات المتدحرجة والمخصصة بنافذة متساوية الطول.",
	},
	{
		key: "days_of_stock",
		title: "أيام تغطية المخزون",
		formula: ["الكمية الحالية", "÷", "متوسط البيع اليومي"],
		example: "مخزون ٦٠ ÷ مبيعات ٣ يوميًا = ٢٠ يوم تغطية",
		explanation: "الصنف بلا مبيعات لا تُحسب له أيام تغطية (يُعرض كمخزون بلا حركة).",
		techDetails: "متوسط البيع اليومي يُحسب من آخر ٣٠ يومًا في فحص نقص المخزون، ومن نافذة «أيام البطء» في فحص البطء.",
	},
	{
		key: "priority_score",
		title: "درجة أولوية القرار",
		formula: ["شدة القاعدة", "+", "الأثر المالي", "+", "حجم التغير", "=", "درجة من ١٠٠"],
		example: "شدة عالية (٤٠) + أثر >٥٠ ألفًا (٢٥) + تغير ٥٠٪ (١٥) = ٨٠ نقطة → «عاجل»",
		explanation: "الشدة: حرجة ٥٠، عالية ٤٠، متوسطة ٢٥، منخفضة ١٠. الأثر المالي يضيف حتى ٣٠ نقطة، وحجم التغير حتى ٢٠. الدرجة تُقارن بحدود الأولوية في الإعدادات (عاجل/مهم/مراجعة/فرصة).",
		techDetails: "شرائح الأثر: >١٠٠ ألف=٣٠، >٥٠=٢٥، >٢٠=٢٠، >١٠=١٥، >٥=١٠، >١=٥. شرائح التغير: ≥٨٠٪=٢٠، ≥٦٠=١٥، ≥٤٠=١٠، ≥٢٠=٥.",
	},
]

// ── استراتيجيات قياس تقدم الخطة ─────────────────────────────────────────────
export const PROGRESS_STRATEGIES = [
	{
		key: "level",
		label: "مستوى مستهدف",
		examples: "نسبة المصاريف إلى المبيعات، متوسط الفاتورة",
		explanation: "الهدف مستوى يُقاس في لحظة واحدة: خط أساس (الوضع الحالي عند بدء الخطة) → هدف. التقدم = نسبة المسافة المقطوعة بينهما.",
		visual: { baseline: 18, current: 15, target: 12, unit: "٪" },
	},
	{
		key: "cumulative_growth",
		label: "هدف تراكمي (نمو)",
		examples: "إجمالي المبيعات، إجمالي المشتريات",
		explanation: "الهدف مبلغ إجمالي يتراكم خلال مدة الخطة (مثل: مبيعات ١٫٢ مليون في ٣ أشهر). النظام يقارن المنجز فعليًا بما يفترض أن يكون منجزًا حتى اليوم.",
		visual: { baseline: 0, current: 400, target: 1200, unit: "" },
	},
	{
		key: "cumulative_ceiling",
		label: "سقف استهلاك",
		examples: "إجمالي المصاريف (سقف مصروف)",
		explanation: "الهدف هنا «حد أقصى» لا يجب تجاوزه خلال مدة الخطة (مثل: مصاريف لا تتجاوز ١٥٠ ألفًا). كلما قلّ الاستهلاك مقارنة بالمسار المتوقع كان الأداء أفضل.",
		visual: { baseline: 0, current: 60, target: 150, unit: "" },
	},
]

// ── مؤشرات غير متاحة حاليًا ─────────────────────────────────────────────────
export const UNAVAILABLE_METRICS = [
	{
		key: "gross_profit",
		label: "الربح الإجمالي",
		reason: "تكلفة البضاعة المباعة لم يتم التحقق منها بعد في إعدادات الحسابات.",
	},
	{
		key: "net_profit",
		label: "صافي الربح",
		reason: "يتطلب ربطًا محاسبيًا كاملًا غير مفعّل حاليًا.",
	},
]

// ── المؤشرات المتاحة للخطط ──────────────────────────────────────────────────
export const AVAILABLE_METRICS = [
	{ key: "sales_total", label: "إجمالي المبيعات", unit: "currency", strategy: "cumulative_growth" },
	{ key: "purchase_total", label: "إجمالي المشتريات", unit: "currency", strategy: "cumulative_growth" },
	{ key: "expenses_to_sales_pct", label: "نسبة المصاريف إلى المبيعات", unit: "percent", strategy: "level" },
	{ key: "total_expenses", label: "إجمالي المصاريف", unit: "currency", strategy: "cumulative_ceiling" },
	{ key: "active_customers", label: "العملاء النشطون", unit: "quantity", strategy: "level" },
	{ key: "average_invoice_value", label: "متوسط قيمة الفاتورة", unit: "currency", strategy: "level" },
	{ key: "declining_customer_count", label: "عدد العملاء المتراجعين", unit: "quantity", strategy: "level" },
	{ key: "dead_stock_value", label: "قيمة المخزون الراكد", unit: "currency", strategy: "level" },
	{ key: "slow_moving_stock_value", label: "قيمة المخزون البطيء", unit: "currency", strategy: "level" },
	{ key: "days_of_stock", label: "أيام المخزون", unit: "days", strategy: "level" },
]
