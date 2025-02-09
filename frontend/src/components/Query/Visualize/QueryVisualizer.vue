<template>
	<div class="flex h-full items-start pt-2">
		<div class="flex h-full w-[18rem] flex-col pr-4">
			<div class="mb-3">
				<div class="mb-2 text-sm tracking-wide text-gray-600">CHART TYPE</div>
				<ChartSelector
					v-if="types?.length > 0"
					:chartTypes="types"
					:invalidTypes="invalidTypes"
					:currentType="chart.type"
					@chartTypeChange="setVizType"
				/>
			</div>

			<div class="flex-1 space-y-3 overflow-y-scroll">
				<div class="mb-2 text-sm tracking-wide text-gray-600">CHART OPTIONS</div>
				<ChartOptions :chartType="chart.type" />
			</div>
		</div>
		<div class="flex h-full w-[calc(100%-18rem)] flex-col space-y-4">
			<div class="flex space-x-2" v-if="chart.component && chart.componentProps">
				<Button
					appearance="white"
					@click="showDashboardDialog = true"
					iconLeft="bookmark"
					:disabled="chart.isDirty"
				>
					Add to Dashboard
				</Button>
				<Button
					v-if="canDownload"
					appearance="white"
					iconLeft="download"
					:disabled="chart.isDirty"
					@click="downloadChart()"
				>
					Download
				</Button>

				<Button
					appearance="primary"
					@click="saveChart"
					:loading="chart.savingDoc"
					:disabled="!chart.isDirty"
				>
					Save
				</Button>
			</div>
			<div class="flex max-h-[30rem] flex-1 items-center justify-center">
				<component
					v-if="chart.component && chart.componentProps"
					ref="eChart"
					:is="chart.component"
					v-bind="chart.componentProps"
				></component>
			</div>
		</div>
	</div>

	<Dialog
		:options="{ title: 'Add to Dashboard' }"
		v-model="showDashboardDialog"
		:dismissable="true"
	>
		<template #body-content>
			<div class="space-y-2 text-gray-600">
				<div class="text-sm font-light text-gray-500">Select a Dashboard</div>
				<Autocomplete
					ref="$autocomplete"
					placeholder="Select a dashboard"
					v-model="toDashboard"
					:options="dashboardOptions"
					:allowCreate="true"
					@createOption="(option) => _createDashboard(option)"
				/>
			</div>
		</template>
		<template #actions>
			<Button appearance="primary" @click="addToDashboard" :loading="addingToDashboard">
				Add
			</Button>
		</template>
	</Dialog>
</template>

<script setup>
import ChartSelector from '@/components/Query/Visualize/ChartSelector.vue'
import ChartOptions from '@/components/Query/Visualize/ChartOptions.vue'

import { computed, inject, nextTick, provide, ref, watch } from 'vue'
import { useChart, types } from '@/utils/charts'
import { useRouter } from 'vue-router'

import Autocomplete from '@/components/Controls/Autocomplete.vue'
import { getDashboardOptions, createDashboard } from '@/utils/dashboard.js'

const query = inject('query')
const chartName = query.charts[0]
const chart = useChart({
	chartID: chartName,
	data: query.results.formattedResult,
})
provide('chart', chart)

const invalidTypes = computed(() => {
	// TODO: change based on data
	return ['Funnel', 'Row']
})
const setVizType = (type) => {
	if (!invalidTypes.value.includes(type)) {
		chart.setType(type)
	}
}

const $notify = inject('$notify')
const saveChart = () => {
	const onSuccess = () => {
		$notify({
			title: 'Chart Saved',
			appearance: 'success',
		})
	}
	chart.updateDoc({ onSuccess })
}

const showDashboardDialog = ref(false)
const toDashboard = ref({})
const dashboardOptions = ref([])
const $autocomplete = ref(null)
watch(showDashboardDialog, async (val) => {
	if (val) {
		await nextTick()
		getDashboardOptions(chartName).then((options) => {
			dashboardOptions.value = options
			setTimeout(() => {
				$autocomplete.value.input.$el.blur()
				$autocomplete.value.input.$el.focus()
			}, 500)
		})
	}
})
const addingToDashboard = computed(() => chart.addToDashboard?.loading)
function addToDashboard() {
	const dashboardName = toDashboard.value.value
	chart.addToDashboard(dashboardName).then(() => {
		$notify({
			title: 'Chart Added to Dashboard',
			appearance: 'success',
		})
		showDashboardDialog.value = false
	})
}

const router = useRouter()
function _createDashboard(newDashboardName) {
	if (!newDashboardName) return router.push('/dashboard')
	createDashboard(newDashboardName).then(({ name, title }) => {
		if (name && title) {
			$notify({
				title: 'Dashboard Created',
				appearance: 'success',
			})
			showDashboardDialog.value = false
			toDashboard.value = {
				value: name,
				label: title,
			}
			addToDashboard()
		}
	})
}

const eChart = ref(null)
const canDownload = computed(() => {
	return eChart.value?.$refs?.eChart?.downloadChart || chart.type == 'Table'
})
function downloadChart() {
	if (canDownload.value) {
		if (chart.type == 'Table') {
			downloadCSV(chart.data)
		} else {
			eChart.value.$refs.eChart.downloadChart()
		}
	}
}

function downloadCSV(data) {
	data[0] = data[0].map((d) => d.split('::')[0])
	const csvString = data.map((row) => row.join(',')).join('\n')
	const blob = new Blob([csvString], { type: 'text/csv' })
	const url = window.URL.createObjectURL(blob)
	const a = document.createElement('a')
	a.setAttribute('hidden', '')
	a.setAttribute('href', url)
	a.setAttribute('download', `${chart.title || 'data'}.csv`)
	document.body.appendChild(a)
	a.click()
	document.body.removeChild(a)
}
</script>
