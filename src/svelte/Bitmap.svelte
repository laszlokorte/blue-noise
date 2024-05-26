<script>
	import {onMount} from 'svelte'

	let {width, height, padding=2, pixels=[]} = $props()
	let canvas = $state()

	$effect(() => {
		const ctx = canvas.getContext("2d")

		ctx.rect(padding,padding,width,height);
		ctx.fillStyle='black'
		ctx.fill()

		ctx.beginPath()
		for(let p=0;p<pixels.length;p++) {
			ctx.rect(padding+pixels[p].x,padding+pixels[p].y,1,1);
		}
		ctx.fillStyle='white'
		ctx.fill()
	})
</script>

<canvas bind:this={canvas} width={width+2*padding} height={height+2*padding}></canvas>

<style>
	canvas {
		display: block;
		image-rendering: pixelated;
	}
</style>