import { setContext, getContext } from "svelte";

export function indent() {

	let autoDepth = getContext("python-indent") || 0;

	setContext("python-indent", autoDepth + 1);
}

export function getDepth() {
	return getContext("python-indent") || 0;
}