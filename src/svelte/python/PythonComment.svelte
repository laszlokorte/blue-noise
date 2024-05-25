<script>
	import PythonIndent from "./PythonIndent.svelte";
	import * as R from "ramda";
	let { text } = $props();
</script>

<PythonIndent /><span class="python-comment"># <span>{text}</span></span><br />
