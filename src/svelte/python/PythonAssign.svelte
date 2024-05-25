<script>
	import PythonIndent from "./PythonIndent.svelte";
	import * as R from "ramda";
	let { left, right, op = "=", subRight, currentValue = null } = $props();
</script>

<PythonIndent /><span>{left}</span>
<span class="python-op">{op}</span> <span>{#if subRight}
	{@render subRight()}
	{:else}
	{right}
{/if}</span>
{#if currentValue !== null}
<span class="python-comment"># {left} = {currentValue}</span>
{/if}
<br />
