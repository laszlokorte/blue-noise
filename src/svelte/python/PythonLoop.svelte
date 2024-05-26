<script>
	import PythonIndent from './PythonIndent.svelte'
	import * as R from "ramda";
	import { indent, getDepth } from "./python_depth";
    import PythonBlock from './PythonBlock.svelte';

	let {iter, collection, children, iterations = null, focus = atom(0)} = $props();
</script>

{#if iterations !== null}
<span class="python-noselect"><PythonIndent /><span class="python-comment">
	 <span class="python-slider"># <input type="range" max={iterations} bind:value={focus.value} min="0"></span>
</span><br></span>
{/if}
<PythonIndent /><span class="python-kw">for</span> <span>{iter}</span> <span class="python-kw">in</span> <span>{collection}</span><span class="python-colon">:</span>
{#if iterations !== null}
<span class="python-comment python-noselect">
	 # (Iteration #{focus.value}) <span class="python-slider"></span>
</span>
{/if}
<br>
<PythonBlock>
	{@render children()}
</PythonBlock>


