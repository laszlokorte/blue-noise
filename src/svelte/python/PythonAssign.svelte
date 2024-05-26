<script>
	import PythonIndent from "./PythonIndent.svelte";
	import * as R from "ramda";
	let { left, right, op = "=", subRight, marker, currentValue = null } = $props();
</script>

<PythonIndent /><span>{left}</span>
<span class="python-op">{op}</span> <span>{#if subRight}
	{@render subRight()}
	{:else}
	{right}
{/if}</span>

{#if currentValue !== null}
<span class="python-comment"># =>

{#if marker !== null}
{@render marker()}{/if}{currentValue}</span>
{/if}
<br />
