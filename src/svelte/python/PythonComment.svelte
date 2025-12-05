<script>
	import PythonIndent from "./PythonIndent.svelte";
	import * as R from "ramda";
	let { text, noselect = false } = $props();
</script>

<span class:python-noselect={noselect}><PythonIndent /><span class="python-comment"># <span>{text}</span></span><br /></span>
