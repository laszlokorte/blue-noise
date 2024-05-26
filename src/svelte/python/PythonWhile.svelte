<script>
	import PythonIndent from './PythonIndent.svelte'
	import * as R from "ramda";
	import { indent, getDepth } from "./python_depth";
    import PythonBlock from './PythonBlock.svelte';
    import {atom} from '../svatom.svelte.js'

	let {condition, collection, children, iterations = null, focus = atom(0)} = $props();


</script>

{#if iterations !== null}<br>
<PythonIndent /><span class="python-comment">
	<span class="python-slider"># <input type="range" max={iterations} bind:value={focus.value} min="0"></span>
</span><br>
{/if}
<PythonIndent /><span class="python-kw">while</span> <span>{condition}</span><span class="python-colon">:</span>
{#if iterations !== null}
<span class="python-comment">
	# (Iteration #{focus.value})
</span>
{/if}
<br>
<PythonBlock>
	{@render children()}
</PythonBlock>


