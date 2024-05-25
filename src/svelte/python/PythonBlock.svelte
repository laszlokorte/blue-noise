<script>
	import PythonIndent from './PythonIndent.svelte'
	import { indent } from "./python_depth";

	let {children} = $props()

	indent()
</script>

{@render children()}
	