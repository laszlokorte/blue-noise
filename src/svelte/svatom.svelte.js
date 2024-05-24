import { get, set, collect, foldl } from 'partial.lenses'

export function atom(init) {
	let root = $state({
		value: init
	})

	return root
}

export function view(opticLense, s) {
	return {
		get value() {
			return get(opticLense, s.value)
		},
		set value(newVal) {
			const transformed = set(opticLense, newVal, s.value)
			
			if (!(transformed instanceof Error)) {
				s.value = transformed
			}
		}
	}
}

export function failableView(opticLense, s, fastValid) {
	let currentInvalidValue = $state(null)
	let currentError = $state(null)

	return {
		get value() {
			return !$state.is(currentError, null) ? currentInvalidValue : get(opticLense, s.value)
		},
		set value(newVal) {
			newVal = fastValid(newVal)
			const transformed = set(opticLense, newVal, s.value)
			
			if (!(transformed instanceof Error)) {
				s.value = transformed
				currentInvalidValue = null
				currentError = null
			} else {
				currentInvalidValue = newVal
				currentError = transformed
			}
		},
		get error() {
			return currentError
		},
		get hasError() {
			return currentError !== null
		},
		reset() {
			currentInvalidValue = null
			currentError = null
		}
	}
}

export function read(opticLense, s) {
	return {
		get value() {
			return get(opticLense, s.value)
		},

		get all() {
			return collect(opticLense, s.value)
		},

		get allUniq() {
			return [...foldl((a, b) => {
							a.add(b)
			
							return a
						}, new Set(), opticLense, s.value)]
		},

		get max() {
			return foldl((a,b) => b===undefined?a:Math.max(a,b), -Infinity, opticLense, s.value)
		},

		get min() {
			return foldl((a,b) => b===undefined?a:Math.min(a,b), Infinity, opticLense, s.value)
		},
	}
}