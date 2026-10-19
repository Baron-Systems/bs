<template>
<div class="min-h-screen bg-[var(--bs-page)]">
<div class="flex items-start">
<!-- ═══ Sidebar (desktop) ═══ -->
<aside class="sticky top-0 hidden h-screen w-[264px] shrink-0 flex-col border-e border-slate-200/70 bg-white lg:flex">
	<SidebarBody />
</aside>

<!-- ═══ Main column ═══ -->
<div class="flex min-h-screen min-w-0 flex-1 flex-col">
	<!-- Top bar -->
	<header class="sticky top-0 z-40 h-14 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
		<div class="flex h-full items-center justify-between gap-3 px-4 sm:px-6">
			<div class="flex min-w-0 items-center gap-2">
				<button type="button" @click="drawerOpen = true" class="bs-icon-btn lg:hidden" :aria-label="__('القائمة')">
					<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>
				<nav class="flex min-w-0 items-center gap-2 text-[13px]" aria-label="breadcrumb">
					<span class="hidden text-slate-400 sm:inline">{{ __("خدمات Baron") }}</span>
					<svg v-if="currentService" class="hidden h-3.5 w-3.5 flex-shrink-0 text-slate-300 sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
					<span v-if="currentService" class="truncate font-semibold text-slate-800">{{ currentService.label }}</span>
				</nav>
			</div>
			<div class="flex flex-shrink-0 items-center gap-1.5">
				<div class="hidden items-center gap-2 rounded-full border border-slate-200/80 bg-white py-1 pe-3 ps-1 sm:flex">
					<div class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-[11px] font-bold text-white">
						{{ userInitial }}
					</div>
					<span class="max-w-[160px] truncate text-xs font-semibold text-slate-700">{{ userName }}</span>
				</div>
				<button @click="logout" class="bs-icon-btn hover:!bg-rose-50 hover:!text-rose-600" :aria-label="__('تسجيل الخروج')" :title="__('تسجيل الخروج')">
					<svg class="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
					</svg>
				</button>
			</div>
		</div>
	</header>

	<main class="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-8">
		<router-view />
	</main>
	<footer class="mx-auto w-full max-w-[1400px] px-4 pb-6 text-center text-[11px] font-medium text-slate-400 sm:px-6 lg:px-8">
		{{ __("AL Baron Systems") }} &copy; {{ new Date().getFullYear() }}
	</footer>
</div>
</div>

<!-- ═══ Mobile drawer ═══ -->
<Teleport to="body">
	<Transition
		enter-active-class="transition-opacity duration-200"
		enter-from-class="opacity-0"
		leave-active-class="transition-opacity duration-150"
		leave-to-class="opacity-0"
	>
		<div v-if="drawerOpen" class="fixed inset-0 z-50 lg:hidden" dir="rtl">
			<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]" @click="drawerOpen = false"></div>
			<aside class="absolute inset-y-0 start-0 flex w-[86%] max-w-[300px] flex-col bg-white shadow-2xl">
				<SidebarBody closable @close="drawerOpen = false" />
			</aside>
		</div>
	</Transition>
</Teleport>
</div>
</template>

<script setup>
import ServicesNav from "@/components/ServicesNav.vue"
import { useServices } from "@/data/services"
import { useUserData } from "@/data/user"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import { useRoute } from "vue-router"
import { computed, h, onMounted, ref, watch } from "vue"

const { userName } = useUserData()
const { showError } = useToast()
const route = useRoute()

const { loaded, loading, loadError, services, allServices, navGroups, loadServices } = useServices()

const drawerOpen = ref(false)

const userInitial = computed(() => {
	const name = userName.value || "User"
	const parts = String(name).split(" ").filter(Boolean)
	return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase()
})

const currentService = computed(() =>
	allServices.value.find((s) => s.type === "route" && (s.route === route.name || s.route === route.meta?.navParent))
)

// Sidebar content shared by the desktop rail and the mobile drawer.
const SidebarBody = (props, { emit }) => [
	// Brand
	h("div", { class: "flex h-14 flex-shrink-0 items-center justify-between gap-2 px-4" }, [
		h("div", { class: "flex min-w-0 items-center gap-2.5" }, [
			// App icon (public/favicon.png, served from the build base)
			h("img", {
				src: `${import.meta.env.BASE_URL}favicon.png`,
				alt: "Baron",
				class: "h-10 w-10 flex-shrink-0 object-contain",
				draggable: "false",
			}),
			h("div", { class: "min-w-0 leading-tight" }, [
				h("p", { class: "truncate text-[14px] font-extrabold text-slate-900" }, __("خدمات Baron")),
				h("p", { class: "truncate text-[10px] font-medium text-slate-400" }, __("AL Baron Systems")),
			]),
		]),
		props.closable
			? h("button", { type: "button", class: "bs-icon-btn", "aria-label": __("إغلاق"), onClick: () => emit("close") }, [
				h("svg", { class: "h-5 w-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24" }, [
					h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M6 18L18 6M6 6l12 12" }),
				]),
			])
			: null,
	]),
	// Nav
	h("nav", { class: "flex-1 overflow-y-auto px-3 pb-3 pt-1" }, [
		loading.value && !loaded.value
			? h("div", { class: "space-y-2 pt-4" }, Array.from({ length: 6 }, (_, i) => h("div", { key: i, class: "h-9 animate-pulse rounded-xl bg-slate-100" })))
			: loadError.value
				? h("p", { class: "px-2 pt-6 text-center text-xs text-rose-500" }, loadError.value)
				: [
					h(ServicesNav, { groups: navGroups.value }),
					loaded.value && !navGroups.value.length
						? h("p", { class: "px-2 pt-6 text-center text-xs text-slate-400" }, __("لا توجد خدمات متاحة لك حالياً"))
						: null,
				],
	]),
	// Footer
	h("div", { class: "border-t border-slate-100 px-4 py-3 text-[11px] text-slate-400" }, `${services.value.length} ${__("خدمة متاحة")}`),
]
SidebarBody.props = ["closable"]
SidebarBody.emits = ["close"]

onMounted(async () => {
	await loadServices()
	if (loadError.value) showError(loadError.value)
})

// Close the mobile drawer whenever the route changes
watch(() => route.fullPath, () => {
	drawerOpen.value = false
})

async function logout() {
	await session.logout.submit()
}
</script>
