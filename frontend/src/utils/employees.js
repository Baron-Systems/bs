// Shared labels and formatters for the Employees section.

export const API = "bs.baron_servies.api.employees"

export const EMPLOYEE_STATUS = {
	Active: { label: "فعال", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
	"On Leave": { label: "في إجازة", cls: "bg-sky-50 text-sky-700 ring-sky-200" },
	Suspended: { label: "موقوف", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
	Inactive: { label: "موقوف", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
	Left: { label: "أنهى العمل", cls: "bg-slate-100 text-slate-600 ring-slate-200" },
}

export const ATTENDANCE_STATUS = {
	Present: { label: "حاضر", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
	Late: { label: "متأخر", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
	Absent: { label: "غائب", cls: "bg-red-50 text-red-700 ring-red-200" },
	"On Leave": { label: "إجازة", cls: "bg-sky-50 text-sky-700 ring-sky-200" },
	"Work Mission": { label: "مهمة عمل", cls: "bg-violet-50 text-violet-700 ring-violet-200" },
	"Day Off": { label: "يوم راحة", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
	Holiday: { label: "عطلة", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
}

export const LEAVE_TYPES = {
	Annual: "سنوية",
	Sick: "مرضية",
	Emergency: "طارئة",
	Unpaid: "بدون راتب",
	Other: "أخرى",
}

export const LEAVE_STATUS = {
	Pending: { label: "بانتظار الموافقة", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
	Approved: { label: "مقبولة", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
	Rejected: { label: "مرفوضة", cls: "bg-red-50 text-red-700 ring-red-200" },
	Cancelled: { label: "ملغاة", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
}

export const PAYROLL_STATUS = {
	Draft: { label: "مسودة", cls: "bg-slate-100 text-slate-600 ring-slate-200" },
	Approved: { label: "معتمد", cls: "bg-blue-50 text-blue-700 ring-blue-200" },
	Paid: { label: "مدفوع", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
}

export const ADVANCE_STATUS = {
	Active: { label: "نشطة", cls: "bg-amber-50 text-amber-700 ring-amber-200" },
	Paused: { label: "موقوفة مؤقتًا", cls: "bg-slate-100 text-slate-600 ring-slate-200" },
	Completed: { label: "مكتملة", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
	Closed: { label: "مغلقة", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
}

export const INSTALLMENT_STATUS = {
	Paid: { label: "مدفوع", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
	Upcoming: { label: "قادم", cls: "bg-blue-50 text-blue-700 ring-blue-200" },
	Paused: { label: "موقوف", cls: "bg-slate-100 text-slate-500 ring-slate-200" },
}

export const RECOVERY_METHODS = {
	Installments: "أقساط شهرية",
	"Next Payroll": "خصم كامل من الاستحقاق القادم",
	Manual: "خصم يدوي",
}

export const REPAYMENT_SOURCES = { Payroll: "من الاستحقاق", Manual: "دفعة يدوية", "Write Off": "شطب" }

export const EARNING_COMPONENTS = {
	Overtime: "ساعات إضافية",
	Bonus: "مكافأة",
	Commission: "عمولة",
	"Transport Allowance": "بدل مواصلات",
	"Food Allowance": "بدل طعام",
	"Phone Allowance": "بدل هاتف",
	"Other Earning": "أخرى",
}

export const DEDUCTION_COMPONENTS = {
	Absence: "غياب",
	Late: "تأخير",
	"Unpaid Leave": "إجازة بدون راتب",
	Administrative: "خصم إداري",
	"Other Deduction": "أخرى",
}

export const COMPONENT_LABELS = { ...EARNING_COMPONENTS, ...DEDUCTION_COMPONENTS, "Advance Installment": "قسط سلفة" }

// Components a user may add by hand (auto ones come from attendance).
export const MANUAL_EARNINGS = ["Bonus", "Commission", "Transport Allowance", "Food Allowance", "Phone Allowance", "Overtime", "Other Earning"]
export const MANUAL_DEDUCTIONS = ["Administrative", "Other Deduction", "Absence", "Late"]

export const PAY_TYPES = { Monthly: "راتب شهري", Hourly: "بالساعة", Daily: "باليوم" }
export const PAY_TYPES_SHORT = { Monthly: "شهري", Hourly: "بالساعة", Daily: "يومي" }
export const PAY_UNITS = { month: "", hour: " / ساعة", day: " / يوم" }

export const EMPLOYEE_TYPES = { "Full Time": "دوام كامل", "Part Time": "دوام جزئي", Temporary: "مؤقت", Seasonal: "موسمي" }
export const SALARY_MODES = { Cash: "نقدي", Bank: "تحويل بنكي", Cheque: "شيك" }

// Order matches the usual local week (Saturday first).
export const WEEK_DAYS = [
	{ code: "Sat", label: "السبت" },
	{ code: "Sun", label: "الأحد" },
	{ code: "Mon", label: "الاثنين" },
	{ code: "Tue", label: "الثلاثاء" },
	{ code: "Wed", label: "الأربعاء" },
	{ code: "Thu", label: "الخميس" },
	{ code: "Fri", label: "الجمعة" },
]

const AR_WEEKDAY = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
const AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

export function formatMoney(value, currency = "") {
	const n = Number(value || 0)
	const text = n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
	if (!currency) return text
	return `${text} ${currencySymbol(currency)}`
}

export function currencySymbol(currency) {
	return { ILS: "₪", USD: "$", EUR: "€", JOD: "د.أ" }[currency] || currency || ""
}

export function formatHours(hours) {
	const h = Number(hours || 0)
	if (!h) return "—"
	const whole = Math.floor(h)
	const minutes = Math.round((h - whole) * 60)
	return `${whole}:${String(minutes).padStart(2, "0")}`
}

export function formatNumber(value) {
	const n = Number(value || 0)
	return n.toLocaleString("en-US", { maximumFractionDigits: 2 })
}

export function parseDate(value) {
	if (!value) return null
	const [y, m, d] = String(value).slice(0, 10).split("-").map(Number)
	return new Date(y, m - 1, d)
}

export function toISODate(date) {
	const y = date.getFullYear()
	const m = String(date.getMonth() + 1).padStart(2, "0")
	const d = String(date.getDate()).padStart(2, "0")
	return `${y}-${m}-${d}`
}

export function todayISO() {
	return toISODate(new Date())
}

export function currentPeriod() {
	return todayISO().slice(0, 7)
}

export function addDays(iso, days) {
	const d = parseDate(iso)
	d.setDate(d.getDate() + days)
	return toISODate(d)
}

export function formatDate(value) {
	const d = parseDate(value)
	if (!d) return "—"
	return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`
}

export function formatShortDate(value) {
	const d = parseDate(value)
	if (!d) return "—"
	return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`
}

export function formatLongDate(value) {
	const d = parseDate(value)
	if (!d) return ""
	return `${AR_WEEKDAY[d.getDay()]} ${d.getDate()} ${AR_MONTHS[d.getMonth()]} ${d.getFullYear()}`
}

export function weekdayName(value) {
	const d = parseDate(value)
	return d ? AR_WEEKDAY[d.getDay()] : ""
}

export function formatPeriod(period) {
	if (!period) return ""
	const [y, m] = period.split("-").map(Number)
	return `${AR_MONTHS[m - 1]} ${y}`
}

export function initials(name) {
	return (name || "?")
		.split(" ")
		.filter(Boolean)
		.slice(0, 2)
		.map((p) => p[0])
		.join("")
}

// Attendance row → display status key (Present with late minutes shows as Late).
export function attendanceKey(row) {
	if (!row?.status) return null
	if (row.status === "Present" && Number(row.late_minutes) > 0) return "Late"
	return row.status
}
