<template>
<div class="flex flex-col gap-1">
<div v-for="group in groups" :key="group.id">
<template v-if="group.collapsible">
<button
type="button"
@click="toggleGroup(group.id)"
class="mt-1 flex w-full items-center justify-between rounded-xl px-3 py-2 text-[13px] transition-colors"
:class="isGroupActive(group) ? 'font-semibold text-slate-900' : 'font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900'"
>
<span class="truncate">{{ group.title }}</span>
<svg
class="h-4 w-4 flex-shrink-0 text-slate-400 transition-transform duration-200"
:class="isExpanded(group.id) ? 'rotate-180' : ''"
fill="none"
stroke="currentColor"
viewBox="0 0 24 24"
>
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
</svg>
</button>
<ul v-show="isExpanded(group.id)" class="mt-0.5 space-y-0.5 border-s border-slate-200 ms-4 ps-2">
<li v-for="item in group.items" :key="item.id">
<NavItem :item="item" :active="isActive(item)" />
</li>
</ul>
</template>
<template v-else>
<p class="px-3 pb-1.5 pt-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">{{ group.title }}</p>
<ul class="space-y-0.5">
<li v-for="item in group.items" :key="item.id">
<NavItem :item="item" :active="isActive(item)" />
</li>
</ul>
</template>
</div>
</div>
</template>

<script setup>
import { computed, h, ref, resolveComponent } from "vue"
import { useRoute } from "vue-router"

const props = defineProps({
	groups: { type: Array, default: () => [] },
})

const route = useRoute()
const manualExpanded = ref(new Set())

// One nav row — router link or external link, with icon and active state.
const NavItem = (p) => {
	const { item, active } = p
	const isLink = item.type === "link"
	const RouterLink = resolveComponent("RouterLink")
	const icon = h(
		"span",
		{
			class: [
				"flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg transition-colors",
				active ? "bg-white text-blue-600 shadow-sm" : "text-slate-400 group-hover:text-slate-600",
			],
		},
		[
			h(
				"svg",
				{ class: "h-[18px] w-[18px]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24" },
				(item.paths || []).map((d) =>
					h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "1.8", d })
				)
			),
		]
	)
	const label = h("span", { class: "truncate" }, item.label)
	const cls = [
		"group flex items-center gap-2.5 rounded-xl px-1.5 py-1 text-[13px] transition-colors",
		active ? "bg-blue-50 font-semibold text-blue-700" : "font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900",
	]
	return isLink
		? h("a", { href: item.route, class: cls }, [icon, label])
		: h(RouterLink, { to: { name: item.route }, class: cls }, () => [icon, label])
}
NavItem.props = ["item", "active"]

const activeGroupIds = computed(() => {
	const ids = new Set()
	for (const group of props.groups) {
		if (group.collapsible && group.items?.some((item) => isActive(item))) {
			ids.add(group.id)
		}
	}
	return ids
})

// Sub-pages (e.g. an employee profile) can light up their parent entry via meta.navParent
const isActive = (item) => item.type !== "link" && (route.name === item.route || route.meta?.navParent === item.route)
const isGroupActive = (group) => group.items?.some((item) => isActive(item))
const isExpanded = (groupId) => activeGroupIds.value.has(groupId) || manualExpanded.value.has(groupId)

function toggleGroup(groupId) {
	const next = new Set(manualExpanded.value)
	if (next.has(groupId)) {
		next.delete(groupId)
	} else {
		next.add(groupId)
	}
	manualExpanded.value = next
}
</script>
