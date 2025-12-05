<script>
	import { getDepth } from "./python_depth";

	import * as R from "ramda";

	let {children} = $props();

	let depth = getDepth();
</script>

<div style:margin-left={`${2*depth}em`}>
	{@render children()}
</div>
