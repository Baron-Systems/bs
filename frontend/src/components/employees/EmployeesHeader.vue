<template>
	<PageHeader :eyebrow="__('الموظفون')" :title="title" :subtitle="subtitle">
		<template #actions>
			<select
				v-if="showCompany && companies.length > 1"
				:value="company"
				class="bs-input !w-auto min-w-[170px] !py-2"
				@change="onCompany($event.target.value)"
			>
				<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
			</select>
			<slot name="actions" />
		</template>
	</PageHeader>
</template>

<script setup>
import PageHeader from "@/components/ui/PageHeader.vue"
import { useEmployeeCompany } from "@/composables/useEmployeeCompany"

defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: "" },
	// Kept for backwards compatibility with existing callers (no longer rendered)
	icon: { type: String, default: "" },
	gradient: { type: String, default: "" },
	showCompany: { type: Boolean, default: true },
})
const emit = defineEmits(["company-change"])

const { companies, company, setCompany } = useEmployeeCompany()

function onCompany(value) {
	setCompany(value)
	emit("company-change", value)
}
</script>
