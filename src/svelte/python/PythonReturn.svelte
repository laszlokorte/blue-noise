<script>
	import PythonIndent from "./PythonIndent.svelte";
	import * as R from "ramda";
	let { value } = $props();
</script>

<PythonIndent /><span class="python-kw">return</span> <span>{value}</span><br />
