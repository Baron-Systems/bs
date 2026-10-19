// Shared chart theme for the Decision Center analytics page.
// Categorical order is validated (CVD + normal-vision) — assign in order, never cycle.

export const SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
export const OTHER = "#c3c2b7"

// Status colors — only when the color *means* good / bad
export const STATUS = {
	good: "#0ca30c",
	warning: "#fab219",
	serious: "#ec835a",
	critical: "#d03b3b",
}

export const INK = {
	primary: "#0b0b0b",
	secondary: "#52514e",
	muted: "#898781",
	grid: "#eeede8",
	axis: "#c3c2b7",
}

export const FONT = "Cairo, system-ui, -apple-system, 'Segoe UI', sans-serif"

export function alpha(hex, a) {
	const n = parseInt(hex.slice(1), 16)
	return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}

export const compactNumber = (v) =>
	Number(v).toLocaleString("en-US", { notation: "compact", maximumFractionDigits: 1 })

export function tooltip(extra = {}) {
	return {
		rtl: true,
		backgroundColor: "#ffffff",
		titleColor: INK.primary,
		bodyColor: INK.secondary,
		footerColor: INK.muted,
		borderColor: "rgba(11,11,11,0.10)",
		borderWidth: 1,
		padding: 12,
		cornerRadius: 10,
		boxPadding: 6,
		usePointStyle: true,
		titleFont: { family: FONT, weight: "700", size: 12 },
		bodyFont: { family: FONT, size: 12 },
		footerFont: { family: FONT, size: 11, weight: "500" },
		...extra,
	}
}

export const legend = {
	position: "top",
	align: "end",
	rtl: true,
	labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 8, boxHeight: 8, padding: 14, color: INK.secondary, font: { family: FONT, size: 11 } },
}

export function valueAxis(extra = {}) {
	return {
		beginAtZero: true,
		border: { display: false },
		grid: { color: INK.grid, drawTicks: false },
		ticks: { color: INK.muted, padding: 8, font: { family: FONT, size: 10 }, callback: compactNumber },
		...extra,
	}
}

export function categoryAxis(extra = {}) {
	return {
		border: { color: INK.axis },
		grid: { display: false },
		ticks: { color: INK.muted, padding: 6, maxRotation: 0, autoSkipPadding: 12, font: { family: FONT, size: 10 } },
		...extra,
	}
}

export const barStyle = {
	borderRadius: { topLeft: 4, topRight: 4 },
	borderSkipped: "start",
	maxBarThickness: 26,
	categoryPercentage: 0.72,
	barPercentage: 0.9,
}

export const lineStyle = {
	borderWidth: 2,
	tension: 0.35,
	pointRadius: 0,
	pointHoverRadius: 5,
	pointHoverBorderWidth: 2,
	pointHoverBorderColor: "#ffffff",
}
