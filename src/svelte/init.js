import { mount } from 'svelte';
import App from './App.svelte';

export default function(domRoot) {
	mount(App, {
		target: domRoot
	});
}