<script>
	import { onMount } from "svelte";
	import favicon from "/favicon.svg";
	import * as L from "partial.lenses";
	import * as R from "ramda";
	import { atom, view, read, failableView } from "./svatom.svelte.js";
	import { forcePlain } from "./contenteditable.js";
	import { lerp, clamp, PHI } from "./utils.js";
	import rec from "./recording.json";
	import {PythonAssign, PythonComment, PythonDef, PythonWhile, PythonKw, PythonIf, PythonLoop, PythonReturn, PythonSkip} from './python'
	import './python/python.css'

	const recording = atom(rec);
	const focus = atom({});


	const size = $derived(recording.value.globals.height)
	const pixelCount = $derived(recording.value.globals.width * recording.value.globals.height)
	const initialWhite = $derived(recording.value.phases["1"].static.initial_ratio_white.length)
	const remainingCount = $derived(pixelCount - initialWhite)
	const maxPhase1Focus = $derived(recording.value.phases["1"].iteration_count-1)
	const maxPhase2Focus = $derived(recording.value.phases["2"].iteration_count-1)
	const maxPhase3Focus = $derived(recording.value.phases["3"].iteration_count-1)
	const phase1Focus = view(['phase1', L.valueOr(0)], focus)
	const phase2Focus = view(['phase2', L.valueOr(0)], focus)
	const phase3Focus = view(['phase3', L.valueOr(0)], focus)

	const phase2Rank = read(L.iso(x => initialWhite-x, x=> initialWhite-x), phase2Focus)

	const phase1DensestPrev = $derived(phase1Focus.value < 1 ? null : recording.value.phases["1"].iterations['densest'][phase1Focus.value-1])
	const phase1VoidestPrev = $derived(phase1Focus.value < 1 ? null : recording.value.phases["1"].iterations['voidest'][phase1Focus.value-1])
	const phase1Densest = $derived(recording.value.phases["1"].iterations['densest'][phase1Focus.value])
	const phase1Voidest = $derived(recording.value.phases["1"].iterations['voidest'][phase1Focus.value])

	const phase1If1 = $derived(phase1VoidestPrev == phase1Densest && phase1DensestPrev == phase1Voidest)
	const phase1If2 = $derived(phase1Densest == phase1Voidest)

	const phase1DensestCoord = $derived(unravel(phase1Densest, recording.value.globals.width, recording.value.globals.height))
	const phase1VoidestCoord = $derived(unravel(phase1Voidest, recording.value.globals.width, recording.value.globals.height))

	const phase2Densest = $derived(recording.value.phases["2"].iterations['densest'][phase2Focus.value])
	const phase3Voidest = $derived(recording.value.phases["3"].iterations['voidest'][phase3Focus.value])

	const phase2DensestCoord = $derived(unravel(phase2Densest, recording.value.globals.width, recording.value.globals.height))
	const phase3VoidestCoord = $derived(unravel(phase3Voidest, recording.value.globals.width, recording.value.globals.height))


	function unravel(i, w, h) {
		return {
			x: i % w,
			y: Math.floor(i / w),
		};
	}
</script>

<section>
	<header>
		<h1>
			<img src={favicon} class="icon" alt="Icon" />Generate Blue Noise
		</h1>
	</header>


	<div class="code-snippet">
		<PythonComment text="This is the python function that you would need to write" />
		<PythonDef name="blueNoise" params={['size','sigma=2.0']}>
			<PythonComment text="Setup" />

			<PythonAssign left="shape" currentValue="({size}, {size})">
				{#snippet subRight()}
				(size, size)
				{/snippet}
			</PythonAssign>
			<PythonAssign left="ranks" right="np.zeros(shape)" />


			<PythonAssign left="initial_white_noise" right="np.random.rand(size, size)"  />
			<PythonAssign left="placed_pixels" right="initial_white_noise >= (1-initial_ratio)" />
			<PythonAssign left="count_placed" right="np.sum(placed_pixels)" currentValue={initialWhite} />

			<PythonAssign left="count_remaining" right="placed_pixels.size - count_placed" currentValue={remainingCount} />

			<br>
			<PythonComment text="Phase 1: Place intial" />
			<PythonAssign left="prev_swap" right="None" />

			<PythonWhile condition="True" iterations={maxPhase1Focus} focus={phase1Focus}>
				{#if phase1DensestPrev == null}
				<PythonComment text="prev_swap = None" />
				{:else}
				<PythonComment text="prev_swap = ({phase1DensestPrev}, {phase1VoidestPrev})" />
				{/if}

				<PythonAssign left="blurred" right="gaussian(placed_pixels, sigma)" />
				<PythonAssign left="densest" right="(blurred * placed_pixels).argmax()" currentValue={phase1Densest} />
				<PythonAssign left="voidest" right="(blurred + placed_pixels).argmin()" currentValue={phase1Voidest} />
				<PythonIf condition="prev_swap == (voidest, densest)" currentValue={phase1If1}>
					<PythonSkip skip={!phase1If1}>
						<PythonKw token="break" />
					</PythonSkip>
				</PythonIf>

				<PythonSkip skip={phase1If1}>

					<PythonIf condition="densest == voidest" currentValue={phase1If2}>
						<PythonSkip skip={!phase1If2}>
							<PythonKw token="break" />
						</PythonSkip>
					</PythonIf>
					<PythonSkip skip={phase1If2}>
						<PythonAssign left="densest_coord" right="np.unravel_index(densest, shape)" currentValue='({phase1DensestCoord.x}, {phase1DensestCoord.y})' />
						<PythonAssign left="voidest_coord" right="np.unravel_index(voidest, shape)" currentValue='({phase1VoidestCoord.x}, {phase1VoidestCoord.y})' />


						<PythonAssign left="placed_pixels[densest_coord]" right="False" />
						<PythonAssign left="placed_pixels[voidest_coord]" right="True" />

						<PythonAssign left="prev_swap" right="(densest, voidest)" />
					</PythonSkip>
				</PythonSkip>
			</PythonWhile>


			<br>
			<PythonComment text="Phase 2: Rank pixels by density" />


			<PythonAssign left="placed_but_not_ranked" right="placed_pixels.copy()" />

			<PythonLoop iter="rank" collection="range(count_placed, 0, -1)" iterations={maxPhase2Focus} focus={phase2Focus}>
				<PythonComment text="rank = {phase2Rank.value}" />

				<PythonAssign left="blurred" right="gaussian(placed_but_not_ranked, sigma)" />
				<PythonAssign left="densest" right="(blurred * placed_but_not_ranked).argmax()" currentValue={phase2Densest} />
				<PythonAssign left="densest_coord" right="np.unravel_index(densest, shape)" currentValue='({phase2DensestCoord.x}, {phase2DensestCoord.y})' />
				<PythonAssign left="placed_but_not_ranked[densest_coord]" right="False" />
				<PythonAssign left="ranks[densest_coord]" right="rank" currentValue={phase2Rank.value} />
			</PythonLoop>
			<br>

			<PythonComment text="Phase 3: Fill up remaining pixels from the sparsest areas"/>
			<PythonLoop iter="rank" collection="range(count_remaining)"  iterations={maxPhase3Focus} focus={phase3Focus}>
				<PythonComment text="rank = {phase3Focus.value}" />

				<PythonAssign left="blurred" right="gaussian(placed_pixels, sigma)" />
				<PythonAssign left="voidest" right="(blurred + placed_pixels).argmin()" currentValue={phase3Voidest} />
				<PythonAssign left="voidest_coord" right="np.unravel_index(voidest, shape)" currentValue='({phase3VoidestCoord.x}, {phase3VoidestCoord.y})' />

				<PythonAssign left="placed_pixels[voidest_coord]" right="True" />
				<PythonAssign left="ranks[voidest_coord]" right="count_placed + rank" />
			</PythonLoop>
			<br>
			<PythonReturn value="ranks"/>

		</PythonDef>
	</div>

	<footer>
		<a href="https://tools.laszlokorte.de" title="More educational tools"
			>More educational tools</a
		>
	</footer>
</section>

<style>
	.bitmap {
		image-rendering: pixelated;
	}
	.stack {
		display: grid;
		grid-template-columns: max-content;
		grid-template-rows: max-content;
		padding: 0.5em;
	}

	.stack > * {
		grid-area: 1 / 1;
		align-self: stretch;
		justify-self: stretch;
	}

	.stacked-video {
		width: 100%;
		height: 100%;
		max-width: 15em;
		max-height: 15em;
		display: block;
	}

	.seeking {
		outline: pink 2px solid;
	}

	.unseekable {
		opacity: 0.2;
	}

	.stacked-svg {
		pointer-events: none;
		width: 100%;
		height: 100%;
		max-width: 15em;
		max-height: 15em;
		display: block;
	}

	.svg {
		width: 100%;
		background: #eee;
	}

	.row {
		display: flex;
		gap: 1em;
	}

	header {
		margin: 2em 0;
	}

	details {
		padding: 0.5em 1em;
		transition: background 0.08s ease;
	}

	details[open] {
		background: #fefaf0;
	}

	summary {
		padding: 0.4em 0;
		cursor: pointer;
		user-select: none;
	}

	summary > span {
		text-decoration: underline;
	}

	hr {
		background: none;
		border: none;
		border-top: 1px solid #333;
	}

	footer {
		text-align: center;
		padding: 2em;
		border-top: 1px solid #aaa;
		margin-top: 2em;
	}

	.icon {
		height: 2em;
		width: 2em;
		display: inline-block;
		vertical-align: middle;
		margin: 0 0.5em 0 0;
	}

	h1 {
		margin: 0;
	}

	section {
		margin: 0 auto 3em;
		max-width: 65em;
		font-family: monospace;
	}

	.code-snippet {
		display: block;
		background: #333;
		color: #fff;
		padding: 1em;
		font-family: monospace;
		font-size: 1.1em;
		line-height: 1.7;
		white-space: nowrap;
	}

	a {
		color: #15218d;
	}

	.code-template {
		background: #15218d;
		color: #fff;
		padding: 1em;
		font-size: 2em;
		font-family: monospace;
		display: grid;
		grid-template-columns: auto auto auto;
		justify-content: start;
		align-items: baseline;
	}

	.code-template-start {
		grid-column: 1;
	}

	.code-template-content {
		grid-column: 2;
	}

	.code-template-end {
		grid-column: 3;
	}

	.code-template-prompt {
		grid-column: 2;
		grid-row: 2;
		text-align: center;
		align-items: center;
		font-size: 0.5em;
		color: #cceeff;
		user-select: none;
	}

	.code-placeholder {
		min-width: 1em;
		display: inline-block;
		background: #cceeff;
		color: #000;
		padding: 0.2em 0.4em;
		margin: 0.2em;
	}

	.syntax-error {
		color: #aa0000;
		outline: #aa0000 3px solid;
		background: #ffdddd;
	}

	.error-message {
		padding: 1em;
		color: #aa0000;
		background: #ffdddd;
	}

	ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		gap: 0.5em;
		flex-direction: column;
	}

	pre {
		white-space: pre-wrap;
		background: #333;
		color: #fff;
		overflow: auto;
		resize: vertical;
		padding: 1em;
		box-sizing: border-box;
	}

	textarea {
		white-space: pre-wrap;
		background: #ffffee;
		color: #000;
		width: 100%;
		min-height: 10em;
		border: 0;
		resize: vertical;
		padding: 1em;
		box-sizing: border-box;
	}

	.number-picker {
		display: flex;
		align-items: center;
		gap: 1em;
	}

	input[type="range"] {
		padding: 1em;
		margin: 0;
	}

	input[type="text"] {
		margin: 0;
	}

	.phantom {
		visibility: hidden;
	}

	.controls {
		display: flex;
		margin: 1em 0;
	}

	button {
		border: none;
		background: #2541ad;
		color: #fff;
		padding: 0.3em 0.5em;
		display: inline-block;
		font: inherit;
		cursor: pointer;
	}

	button:hover {
		background: #2562ad;
	}

	button:active {
		background: #252aad;
	}

	button:focus-visible {
		outline: 3px solid #4daace;
	}

	.button-bar {
		display: flex;
		gap: 0.2em;
		margin: 4px 0;
		align-items: baseline;
	}

	.button-bar-intro {
		padding-right: 0.5em;
	}
</style>
