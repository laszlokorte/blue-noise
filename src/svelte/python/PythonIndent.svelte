<script>
	import { getDepth } from "./python_depth";

	import * as R from "ramda";

	let depth = getDepth();
</script>

<span class="indent" style:width={`${depth}em`}
	>{@html R.join("", R.repeat("&nbsp;", depth * 2))}</span
>

<style>
</style>
