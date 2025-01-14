import {
	Button,
	FeatherIcon,
	Input,
	onOutsideClickDirective,
	Popover,
	Dialog,
	ErrorMessage,
	Dropdown,
} from 'frappe-ui'
import Checkbox from '@/components/Controls/Checkbox.vue'
import Autocomplete from '@/components/Controls/Autocomplete.vue'

import utils from './utils'
import auth from './utils/auth'
import { createToast } from './utils/toasts'
import dayjs from './utils/dayjs'

export function registerGlobalComponents(app) {
	app.component('Input', Input)
	app.component('Button', Button)
	app.component('Dialog', Dialog)
	app.component('Popover', Popover)
	app.component('Checkbox', Checkbox)
	app.component('Dropdown', Dropdown)
	app.component('Autocomplete', Autocomplete)
	app.component('ErrorMessage', ErrorMessage)
	app.component('FeatherIcon', FeatherIcon)
	app.directive('on-outside-click', onOutsideClickDirective)
}

export function registerControllers(app) {
	app.provide('$auth', auth)
	app.provide('$utils', utils)
	app.provide('$dayjs', dayjs)
	app.provide('$notify', createToast)

	if (import.meta.env.DEV) {
		window.$auth = auth
		window.$utils = utils
		window.$dayjs = dayjs
		window.$notify = createToast
	}
}
