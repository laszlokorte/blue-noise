<script>

	import PythonIndent from './PythonIndent.svelte'
	import * as R from "ramda";
	import { indent } from "./python_depth";
    import PythonBlock from './PythonBlock.svelte';

	let {name, params, children} = $props()
</script>

<PythonIndent /><span class="python-kw">def</span> 
<span>{name}</span><span class="python-paren">(</span>{#each params as p, i}{#if i>0}<span class="python-comma">,&nbsp;</span>{/if}{p}{/each}<span class="python-paren">)</span>:<br>
<PythonBlock>
	{@render children()}
</PythonBlock>
