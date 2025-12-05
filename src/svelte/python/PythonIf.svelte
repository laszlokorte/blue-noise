<script>
	import PythonIndent from './PythonIndent.svelte'
	import * as R from "ramda";
	import { indent, getDepth } from "./python_depth";
    import PythonBlock from './PythonBlock.svelte';

	let {condition, collection, children, currentValue} = $props();
</script>

<PythonIndent /><span class="python-kw">if</span> <span>{condition}</span><span class="python-colon">:</span>
<span class="python-comment python-noselect"> # {currentValue ? "✅ True":"❌ False"}</span>
<br>
<PythonBlock>
	{@render children()}
</PythonBlock>


