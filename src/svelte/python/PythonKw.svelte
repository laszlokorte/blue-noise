<script>
	import PythonIndent from './PythonIndent.svelte'
	import * as R from "ramda";
	import { indent, getDepth } from "./python_depth";
    import PythonBlock from './PythonBlock.svelte';

	let {token} = $props();
</script>

<PythonIndent /><span class="python-kw">{token}</span><br>


