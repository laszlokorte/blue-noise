<script>
	let {skip = false, children} = $props();
</script>

<div class:python-skip={skip}>
	{@render children()}
</div>
