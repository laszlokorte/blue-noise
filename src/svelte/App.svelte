<script>
	import { onMount } from "svelte";
	import favicon from "/favicon.svg";
	import * as L from "partial.lenses";
	import * as R from "ramda";
	import { atom, view, read, failableView } from "./svatom.svelte.js";
	import { forcePlain } from "./contenteditable.js";
	import { lerp, clamp, PHI } from "./utils.js";
	import rec from "../steps/recording.json";
	import {PythonAssign, PythonComment, PythonDef, PythonIndented, PythonWhile, PythonKw, PythonIf, PythonLoop, PythonReturn, PythonSkip} from './python'
	import './python/python.css'
	import Bitmap from './Bitmap.svelte'

	import initialWhiteImage from '../steps/p01-s01-initial_white_noise.png'
	import initialWhiteRatio from '../steps/p01-s02-initial_ratio_white.png'
	import p1Placed from '../steps/p01-s03-before-swap.png'
	import p1PlacedAfter from '../steps/p01-s03-after-swap.png'
	import p1Blurred from '../steps/p01-s03-blurred.png'
	import p1Masked from '../steps/p01-s03-blurred_dense_masked.png'
	import p1Offset from '../steps/p01-s03-blurred_voidest_offset.png'
	import resultImageGrey from '../steps/p05-s00-result.png'
	import resultImageHsv from '../steps/p05-s00-result-hsv.png'
	import psdImage from '../steps/p05-s00-psd.png'
	import logPsdImage from '../steps/p05-s00-log-psd.png'
	import resultThresImage from '../steps/p05-s01-thresholded.png'
	import psdThresImage from '../steps/p05-s01-thresholded-psd.png'
	import logPsdThresImage from '../steps/p05-s01-thresholded-log-psd.png'
	import p2PlacedBefore from '../steps/p02-s01-before-remove.png'
	import p2Blurred from '../steps/p02-s01-blurred.png'
	import p2Masked from '../steps/p02-s01-blurred_dense_masked.png'
	import p2RanksGrey from '../steps/p02-s01-after-ranks.png'
	import p2RanksHsv from '../steps/p02-s01-after-ranks-hsv.png'
	import p3placed from '../steps/p03-s01-before-new.png'
	import p3blurred from '../steps/p03-s01-blurred.png'
	import p3blurredOffset from '../steps/p03-s01-blurred_voidest_offset.png'
	import p3RanksGrey from '../steps/p03-s01-after-ranks.png'
	import p3RanksHsv from '../steps/p03-s01-after-ranks-hsv.png'

	const recording = atom(rec);
	const focus = atom({});
	const hsvScale = atom(true);
	const markerColors = atom({})

	const densestColor = view(['densestColor', L.valueOr('#ff00ff')], markerColors)
	const voidestColor = view(['voidestColor', L.valueOr('#00ffff')], markerColors)
	const removeColor = view(['removeColor', L.valueOr('#ff7777')], markerColors)
	const addColor = view(['addColor', L.valueOr('#aaffaa')], markerColors)
	const rankColor = view(['rankColor', L.valueOr('#ffaa00')], markerColors)


	const p2Ranks = $derived(hsvScale.value ? p2RanksHsv : p2RanksGrey)
	const p3Ranks = $derived(hsvScale.value ? p3RanksHsv : p3RanksGrey)
	const resultImage = $derived(hsvScale.value ? resultImageHsv : resultImageGrey)

	const size = $derived(recording.value.globals.height)
	const pixelCount = $derived(recording.value.globals.width * recording.value.globals.height)
	const initialWhite = $derived(recording.value.phases["1"].static.initial_ratio_white.map(([y,x]) => ({x,y})))
	const initialWhiteCount = $derived(recording.value.phases["1"].static.initial_ratio_white.length)
	const remainingCount = $derived(pixelCount - initialWhiteCount)
	const maxPhase1Focus = $derived(recording.value.phases["1"].iteration_count-1)
	const maxPhase2Focus = $derived(recording.value.phases["2"].iteration_count-1)
	const maxPhase3Focus = $derived(recording.value.phases["3"].iteration_count-1)
	const phase1Focus = view(['phase1', L.valueOr(0)], focus)
	const phase2Focus = view(['phase2', L.valueOr(0)], focus)
	const phase3Focus = view(['phase3', L.valueOr(0)], focus)

	const phase2Rank = read(L.iso(x => initialWhiteCount-x, x=> initialWhiteCount-x), phase2Focus)

	const phase1DensestPrev = $derived(phase1Focus.value < 1 ? null : recording.value.phases["1"].iterations['densest'][phase1Focus.value-1])
	const phase1VoidestPrev = $derived(phase1Focus.value < 1 ? null : recording.value.phases["1"].iterations['voidest'][phase1Focus.value-1])
	const phase1Densest = $derived(recording.value.phases["1"].iterations['densest'][phase1Focus.value])
	const phase1Voidest = $derived(recording.value.phases["1"].iterations['voidest'][phase1Focus.value])

	const phase1If1 = $derived(phase1VoidestPrev == phase1Densest && phase1DensestPrev == phase1Voidest)
	const phase1If2 = $derived(phase1Densest == phase1Voidest)

	const phase1DensestCoord = $derived(unravel(phase1Densest, recording.value.globals.width, recording.value.globals.height))
	const phase1VoidestCoord = $derived(unravel(phase1Voidest, recording.value.globals.width, recording.value.globals.height))
	const phase1Direction = $derived({x: phase1VoidestCoord.x - phase1DensestCoord.x, y: phase1VoidestCoord.y - phase1DensestCoord.y})
	const phase1DirectionCenter = $derived({x: (phase1VoidestCoord.x + phase1DensestCoord.x)/2, y: (phase1VoidestCoord.y + phase1DensestCoord.y)/2})
	const phase1DirectionLength = $derived(Math.sqrt(phase1Direction.x*phase1Direction.x + phase1Direction.y*phase1Direction.y))
	const phase1DirectionNormed = $derived({x: phase1Direction.x/phase1DirectionLength, y: phase1Direction.y/phase1DirectionLength})

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

		<p>
			<a href="https://www.youtube.com/watch?v=ORsTjpy5CH8" target="_blank">Video Demo</a>
		</p>

		<p>
			This is an interactive demonstration of the <a target="_blank" href="https://ieeexplore.ieee.org/document/3288/">Void and Cluster</a> algorithm for generating blue noise. <a target="_blank" href="http://momentsingraphics.de/BlueNoise.html">There are</a> already <a target="_blank" href="https://observablehq.com/@bensimonds/mitchells-best-candidate-algorithm">plenty of</a> excellent explorations on <a target="_blank" href="https://blog.demofox.org/2019/06/25/generating-blue-noise-textures-with-void-and-cluster/">how</a> <a target="_blank" href="https://www.youtube.com/watch?v=tethAU66xaA">and why</a> to generate <a target="_blank" href="https://en.wikipedia.org/wiki/Colors_of_noise">blue noise</a>, <a target="_blank" href="https://blog.demofox.org/2017/10/25/transmuting-white-noise-to-blue-red-green-purple/">and noises of other color</a>. The <em>Void and Cluster</em> algorithm is one of <a target="_blank" href="https://blog.demofox.org/2017/10/20/generating-blue-noise-sample-points-with-mitchells-best-candidate-algorithm/">several promiment algorithms</a>. <a target="_blank" href="https://blog.demofox.org/2018/08/12/not-all-blue-noise-is-created-equal/">Some advantages</a> over other algorithms are that the blue noise is of very good quality and that only the first step in the algorithm is non-deterministic.
		</p>

		<h3>This page</h3>

		<p>
			The goal of this page is to provide additional insight by visualizing the core idea of this algorithm.
		</p>
		<p>
			This insight might be used to better unstand the algorithm itself, for example to recognize potential performance improvements. But it might also be used as source of inspiration on how to design a custom algorithm.
		</p>
		<p>
			The algorithm below is implemented in python using numpy. In this regard it can also be used as a case-study on how a sophisticated algorithm (that may <a target="_blank" href="https://github.com/Atrix256/VoidAndCluster/blob/master/generatebn_void_cluster.cpp">take multiple hundred lines in C++</a>) can be written very succinctly when relying on higher level concepts, such as convolution and rank-polymorphism.
		</p>

		<h3>Blue Noise</h3>

		<p>A sequence of random numbers is called <em>blue noise</em> if succeeding numbers are very likely to be very different. This is in contrast to white noise, where each number would be completely unrelated to each other number in the squence. In a white noise sequency it would neither be surprising for the similar numbers occur right next to each other, nor would it be surprising for two succeeding values to be quite far appart. In blue noise neighbors are expected to be different. The opposite would be red noise, where neighboring values are expected to be at least similar.</p>

		<p>
			The characteristic check if a sequence is <em>blue noise</em> is to compute its <a target="_blank" href="https://en.wikipedia.org/wiki/Spectral_density#Power_spectral_density">Power spectral density</a> (the magnitude-square of its Fourier Transform) and then to check that it contains only high frequencies.
		</p>

		<h3>The algorithm</h3>

		<p>
			When generating 2D blue noise, as in the example below, the goal is to assign each pixel in the image a distinct intensity value, such that the intensity difference of neighboring pixels gets maximized.
		</p>

		<p>
			Read the code below and drag the sliders above the <code>for</code> and <code>while</code> loops to inspect the intermediate results.
		</p>

		<p>
			The <code>rank</code> image is better viewed on a rainbow scale to make the low intensity more visible.
		</p>

		<details>
			<summary>&hellip;or read the natural language explanation</summary>

			<p>The algorithm consists of multiple phases. </p>
		<ol>
			<li>
				<p><strong>Initilization</strong> (the only non-deterministic step, because of the <code>random()</code> call):</p>
				<ul>
					<li>Allocate an all-zero output image (<code>ranks</code>)</li>
					<li>Generate white noise (<code>initial_white_noise</code>)</li>
					<li>Threshold the white noise to select a random subset (~10%) of pixels, as binary image (<code>placed_pixels </code>)</li>
				</ul>
			</li>
			<li>
				<strong>Phase1: Spreading</strong>
				<p>
					The randomly <code>placed_pixels</code> might be clustered in some areas and sparse in some other areas. This a because a un-correlated(white noise) random generator is used. To spread the pixels more evenly:
				</p>
				<ul>
					<li>Blur the <code>placed_pixels</code> with a gaussian filter to estimate the density across the image</li>
					<li>Move a <code>placed_pixel</code> from the highest densesity area to the most void empty position</li>
					<li>&hellip;repeat until dense and void areas converge</li>
				</ul>
			</li>
			<li>
				<strong>Phase 2: Assign distinct intensities to pixels</strong>
				<p>
					The random subset of <code>placed_pixels</code> is now spread as far as possible across the image.
					<br>Next we assign each of them a distinct intensity value (starting at 0) by iterating through the set in descending order:
				</p>
				<ul>
					<li>Blur the <code>placed_pixels</code></li>
					<li>Select the pixel with highest density</li>
					<li>Assign a new intensity value to this pixel</li>
					<li>Repeat until each pixel in <code>placed_pixels</code> has been processed</li>
				</ul>
			</li>
			<li>
				<strong>Phase 3: Add remaining pixels</strong>
				<p>
					Up until now only a subset of the pixels (~10%) have been processed. To generate the remaining 90% of pixels:
				</p>
				<ul>
					<li>Blur the <code>placed_pixels</code></li>
					<li>Select the empty pixel with lowest density</li>
					<li>Add this pixel to the <code>placed_pixels</code></li>
					<li>Assign this pixel the next available intensity (<code>rank</code>) value in the output image</li>
					<li>&hellip;repeat until no more pixels left.</li>
				</ul>
			</li>
		</ol>
			
		</details>

	</header>

	<div style:display="none">
		<input type="color" id="input-densestColor" bind:value={densestColor.value} />
		<input type="color" id="input-voidestColor" bind:value={voidestColor.value} />
		<input type="color" id="input-removeColor" bind:value={removeColor.value} />
		<input type="color" id="input-addColor" bind:value={addColor.value} />
		<input type="color" id="input-rankColor" bind:value={rankColor.value} />
	</div>

	<div class="code-snippet">
		<span class="python-kw">import</span> numpy <span class="python-kw">as</span> np<br>
		<span class="python-kw">from</span> skimage.filters <span class="python-kw">import</span> gaussian<br><br>
		<PythonDef name="blueNoise" params={['size','sigma=2.0','initial_ratio=0.1']}>

			<PythonComment text="Init: Place some initial pixels based off thresholded white noise" />
			<PythonAssign left="shape" currentValue="({size}, {size})">
				{#snippet subRight()}
				(size, size)
				{/snippet}
			</PythonAssign>
			<PythonAssign left="ranks" right="np.zeros(shape)" />


			<PythonAssign left="initial_white_noise" right="np.random.rand(size, size)"  />


			<PythonAssign left="placed_pixels" right="initial_white_noise >= (1-initial_ratio)" />


			<div class="media-row">
				<PythonIndented>
					<div class="row">
						<figure>
						<div class="stack">
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect x="-2" y="-2" width={size+4} height={size+4} />
							</svg>
						</div>
						<figcaption>
							{@render scaleSwitch()}
							<code>ranks</code>
						</figcaption>
					</figure>
						<figure>
						<div class="stack">
							<img src={initialWhiteImage} alt="" class="stacked-image" />
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
							</svg>
						</div>
						<figcaption>
							<code>initial_white_noise</code>
						</figcaption>
					</figure>
						<figure>
						<div class="stack">
							<img src={initialWhiteRatio} alt="" class="stacked-image" />

							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
							</svg>
						</div>
						<figcaption>
							<code>placed_pixels</code>
						</figcaption>
					</figure>
					</div>
				</PythonIndented>
			</div>

			<PythonAssign left="count_placed" right="np.sum(placed_pixels)" currentValue={initialWhiteCount} />

			<PythonAssign left="count_remaining" right="placed_pixels.size - count_placed" currentValue={remainingCount} />

			<br>
			<PythonComment text="Phase 1: Spread white pixels more evenly. Swap between dense and void areas" />
			<PythonAssign left="prev_swap" right="None" />

			<PythonWhile condition="True" iterations={maxPhase1Focus} focus={phase1Focus}>
				{#if phase1DensestPrev == null}
				<PythonComment noselect text="prev_swap = None" />
				{:else}
				<PythonComment noselect text="prev_swap = ({phase1DensestPrev}, {phase1VoidestPrev})" />
				{/if}

				<PythonAssign left="blurred" right="gaussian(placed_pixels, sigma)" />
				<PythonAssign left="densest" right="(blurred * placed_pixels).argmax()" currentValue={phase1Densest} />
				<PythonAssign left="voidest" right="(blurred + placed_pixels).argmin()" currentValue={phase1Voidest} />

				<PythonAssign left="densest_coord" right="np.unravel_index(densest, shape)" currentValue='({phase1DensestCoord.x}, {phase1DensestCoord.y})'>
					{#snippet marker()}
					<label class="color-picker-label" for="input-densestColor">
					<svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={densestColor.value} />
					</svg>
					</label>
					{/snippet}
				</PythonAssign>
				<PythonAssign left="voidest_coord" right="np.unravel_index(voidest, shape)" currentValue='({phase1VoidestCoord.x}, {phase1VoidestCoord.y})'>
					{#snippet marker()}
					<label class="color-picker-label" for="input-voidestColor">
					<svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={voidestColor.value} />
					</svg>
					</label>
					{/snippet}
				</PythonAssign>

				<div class="media-row">
					<PythonIndented>
						<div class="row">
							<figure>
						<div class="stack">
							<div class="stacked-sprite" style:--sprite-index={phase1Focus.value}>
							<img src={p1Placed} alt="" class="stacked-sprite-image" />
							</div>

							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
							</svg>
						</div>
						<figcaption>
							<code>placed_pixels</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase1Focus.value}>
							<img src={p1Blurred} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>blurred</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase1Focus.value}>
							<img src={p1Masked} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect class="pixel-marker" x={phase1DensestCoord.x-1} y={phase1DensestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={densestColor.value} />
							</svg>
						</div>
						<figcaption>
							<code>blurred * <br>placed_pixels</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase1Focus.value}>
							<img src={p1Offset} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">

								<rect class="pixel-marker" x={phase1VoidestCoord.x-1} y={phase1VoidestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={voidestColor.value} />

							</svg>
						</div>
						<figcaption>
							<code>blurred + <br>placed_pixels</code>
						</figcaption>
						</div>
					</PythonIndented>
				</div>

				<PythonComment text="detect cycle" />
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
						<PythonAssign left="placed_pixels[densest_coord]" right="False">
							{#snippet marker()}
							 &nbsp;set <label class="color-picker-label" for="input-removeColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
								<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={removeColor.value} />
							</svg></label> to False
							{/snippet}
						</PythonAssign>
						<PythonAssign left="placed_pixels[voidest_coord]" right="True">
							{#snippet marker()}
							&nbsp;set
							<label class="color-picker-label" for="input-addColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
								<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={addColor.value} />
							</svg></label> to True
							{/snippet}
						</PythonAssign>


						<div class="media-row">
							<PythonIndented>
								<div class="row">
									<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase1Focus.value}>
							<img src={p1PlacedAfter} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect class="pixel-marker" x={phase1DensestCoord.x-1} y={phase1DensestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={removeColor.value} />


								<rect class="pixel-marker" x={phase1VoidestCoord.x-1} y={phase1VoidestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={addColor.value} />


								<path d="M{phase1DensestCoord.x+0.5} {phase1DensestCoord.y+0.5} Q {phase1DirectionCenter.x+phase1DirectionNormed.y*5} {phase1DirectionCenter.y-phase1DirectionNormed.x*5} {phase1VoidestCoord.x+0.5} {phase1VoidestCoord.y+0.5}" stroke={"pink"} stroke-width="3px" vector-effect="non-scaling-stroke" fill="none" />
							</svg>
						</div>
						<figcaption>
							<code>placed_pixels</code>
						</figcaption>
					</figure>
								</div>
							</PythonIndented>
						</div>

						<PythonAssign left="prev_swap" right="(densest, voidest)" />
					</PythonSkip>
				</PythonSkip>
			</PythonWhile>


			<br>
			<PythonComment text="Phase 2: Rank pixels by density" />


			<PythonAssign left="not_ranked" right="placed_pixels.copy()" />

			<PythonLoop iter="rank" collection="range(count_placed, 0, -1)" iterations={maxPhase2Focus} focus={phase2Focus}>
				<PythonComment noselect text="rank = {phase2Rank.value}" />

				<PythonAssign left="blurred" right="gaussian(not_ranked, sigma)" />
				<PythonAssign left="densest" right="(blurred * not_ranked).argmax()" currentValue={phase2Densest} />
				<PythonAssign left="densest_coord" right="np.unravel_index(densest, shape)" currentValue='({phase2DensestCoord.x}, {phase2DensestCoord.y})'>
					{#snippet marker()}
					<label class="color-picker-label" for="input-densestColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={densestColor.value} />
					</svg></label>
					{/snippet}
				</PythonAssign>
				<br>
				<PythonAssign left="not_ranked[densest_coord]" right="False">

					{#snippet marker()}
					&nbsp;set
					<label class="color-picker-label" for="input-removeColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={removeColor.value} />
					</svg></label> to False
					{/snippet}
				</PythonAssign>
				<PythonAssign left="ranks[densest_coord]" right="rank" currentValue={phase2Rank.value}>
					{#snippet marker()}
					&nbsp;set
					<label class="color-picker-label" for="input-rankColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={rankColor.value} />
					</svg></label> to
					{/snippet}
				</PythonAssign>

				<div class="media-row">
					<PythonIndented>
						<div class="row">
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase2Focus.value}>
							<img src={p2PlacedBefore} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								
								<rect class="pixel-marker" x={phase2DensestCoord.x-1} y={phase2DensestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={removeColor.value} />

							</svg>
						</div>
						<figcaption>
							<code>not_ranked</code>

						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase2Focus.value}>
							<img src={p2Blurred} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>blurred</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase2Focus.value}>
							<img src={p2Masked} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">

								<rect class="pixel-marker" x={phase2DensestCoord.x-1} y={phase2DensestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={densestColor.value} />

							</svg>
						</div>
						<figcaption>
							<code>blurred * <br>not_ranked</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase2Focus.value}>
							<img src={p2Ranks} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect class="pixel-marker" x={phase2DensestCoord.x-1} y={phase2DensestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={rankColor.value} />

							</svg>
						</div>
						<figcaption>
							{@render scaleSwitch()}
							<code>ranks</code>
						</figcaption>
					</figure>
						</div>
					</PythonIndented>
				</div>


			</PythonLoop>
			<br>

			<PythonComment text="Phase 3: Fill up remaining pixels from the sparsest areas"/>
			<PythonLoop iter="rank" collection="range(count_remaining)"  iterations={maxPhase3Focus} focus={phase3Focus}>
				<PythonComment text="rank = {phase3Focus.value}" />

				<PythonAssign left="blurred" right="gaussian(placed_pixels, sigma)" />
				<PythonAssign left="voidest" right="(blurred + placed_pixels).argmin()" currentValue={phase3Voidest} />
				<PythonAssign left="voidest_coord" right="np.unravel_index(voidest, shape)" currentValue='({phase3VoidestCoord.x}, {phase3VoidestCoord.y})'>

					{#snippet marker()}
					<label class="color-picker-label" for="input-voidestColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={voidestColor.value} />
					</svg></label> =
					{/snippet}
				</PythonAssign>
				<br>
				<PythonAssign left="placed_pixels[voidest_coord]" right="True">
					{#snippet marker()}
					&nbsp;set
					<label class="color-picker-label" for="input-addColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={addColor.value} />
					</svg></label> to True
					{/snippet}
				</PythonAssign>
				<PythonAssign left="ranks[voidest_coord]" right="count_placed + rank">
					{#snippet marker()}
					&nbsp;set
					<label class="color-picker-label" for="input-rankColor"><svg viewBox="-2 -2 5 5" style:width="1.3em" style:height="1.3em" style:vertical-align="top">
						<rect class="pixel-marker" x={0} y={0} width="2" height="2" fill="none" stroke-width="0.5" stroke={rankColor.value} />
					</svg></label> to {initialWhiteCount + phase3Focus.value}
					{/snippet}
				</PythonAssign>

				<div class="media-row">
					<PythonIndented>
						<div class="row">
							<figure>
						<div class="stack">

							<div class="stacked-sprite" style:--sprite-index={phase3Focus.value}>
							<img src={p3placed} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								
								<rect class="pixel-marker" x={phase3VoidestCoord.x-1} y={phase3VoidestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={addColor.value} />

							</svg>
						</div>
						<figcaption>
							<code>placed_pixels</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">
							<div class="stacked-sprite" style:--sprite-index={phase3Focus.value}>
							<img src={p3blurred} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>blurred</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">
							<div class="stacked-sprite" style:--sprite-index={phase3Focus.value}>
							<img src={p3blurredOffset} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect class="pixel-marker" x={phase3VoidestCoord.x-1} y={phase3VoidestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={voidestColor.value} />
							</svg>
						</div>
						<figcaption>
							<code>blurred + <br> placed_pixels</code>
						</figcaption>
					</figure>
							<figure>
						<div class="stack">
							<div class="stacked-sprite" style:--sprite-index={phase3Focus.value}>
							<img src={p3Ranks} alt="" class="stacked-sprite-image" />
							</div>
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg">
								<rect class="pixel-marker" x={phase3VoidestCoord.x-1} y={phase3VoidestCoord.y-1} width="3" height="3" fill="none" stroke-width="0.5" stroke={rankColor.value} />
							</svg>
						</div>
						<figcaption>
							{@render scaleSwitch()}
							<code>ranks</code>
						</figcaption>
					</figure>
						</div>
					</PythonIndented>
				</div>
			</PythonLoop>
			<PythonReturn value="ranks"/>
		</PythonDef>
		<br>
	</div>
	<h2>Results</h2>

	<p>
		The resulting image has a the intensity values evenly spread across in space. Everywhere in the image are both dark and light pixels.
	</p>
	<p>
		The verify the characteristic <a target="_blank" href="https://en.wikipedia.org/wiki/Spectral_density#Power_spectral_density">Power spectral density</a> we can compute the fourier transform and observe the dark spot around the the low frequencies:
	</p>

	<div class="code-snippet">
		result = blueNoise({size})<br>
		spec = fftshift(fft2(result))<br>
    	psd = np.abs(spec * np.conj(spec))<br>
    	log_psd = np.log(psd)

		<div class="media-row">
			<PythonIndented>
				<div class="row centered">
					<figure>
						<div class="stack">
							<img src={resultImage} class="stacked-image" alt="" />
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							{@render scaleSwitch()}
							<code>result</code>
						</figcaption>
					</figure>

					<figure>
						<div class="stack">
							<img src={psdImage} class="stacked-image" alt="" />

							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>psd</code>
						</figcaption>
					</figure>

					<figure>
						<div class="stack">
							<img src={logPsdImage} class="stacked-image" alt="" />

							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>log_psd</code>
						</figcaption>
					</figure>
				</div>
			</PythonIndented>
		</div>
	</div>
	
	<h2>Threshold</h2>

	<p>
		Depending on the quality of the blue noise the image might processed even further while maintaining the blue noise property. Below the resulting image is thresholded to generate a new binary image of evenly distributed white spots. This is basically a similar image as the intermediate result of phase 1 (10% of white pixels evenly spaced).
	</p>

	<p>
		When inspecting the power spectral density we can also observe the dark spot at the low frequencies. <a target="_blank" href="https://blog.demofox.org/2018/08/12/not-all-blue-noise-is-created-equal/">This is not always the case when post-processing a blue noise signal.</a>
	</p>

	<div class="code-snippet">
		threshold = result &ge; 0.9<br>
		threshold_spec = fftshift(fft2(threshold))<br>
    	threshold_psd = np.abs(threshold_spec * np.conj(threshold_spec))<br>
    	threshold_log_psd = np.log(threshold_psd)

		<div class="media-row">
			<PythonIndented>
				<div class="row centered">
					<figure>
						<div class="stack">
							<img src={resultThresImage} class="stacked-image" alt="" />
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>threshold</code>
						</figcaption>
					</figure>

					<figure>
						<div class="stack">
							<img src={psdThresImage} class="stacked-image" alt="" />
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>threshold_psd</code>
						</figcaption>
					</figure>

					<figure>
						<div class="stack">
							<img src={logPsdThresImage} class="stacked-image" alt="" />
							<svg viewBox="-2 -2 {size+4} {size+4}" class="stacked-svg"></svg>
						</div>
						<figcaption>
							<code>threshold_log_psd</code>
						</figcaption>
					</figure>
				</div>
			</PythonIndented>
		</div>
	</div>

	<h2>References</h2>

	<ul>
		<li><a target="_blank" href="https://blog.demofox.org/2018/08/12/not-all-blue-noise-is-created-equal/">Not All Blue Noise is Created Equal</a></li>
		<li><a target="_blank" href="https://blog.demofox.org/2019/06/25/generating-blue-noise-textures-with-void-and-cluster/">Generating Blue Noise Textures With Void And Cluster</a></li>
		<li><a target="_blank" href="http://momentsingraphics.de/BlueNoise.html">Free blue noise textures</a></li>
		<li><a target="_blank" href="https://dl.acm.org/doi/10.1145/127719.122736">Mitchell's Best Candidate Algorithm</a></li>
		<li><a target="_blank" href="https://ieeexplore.ieee.org/document/3288/">Dithering with blue noise</a></li>
		<li><a target="_blank" href="https://blog.demofox.org/2017/10/20/generating-blue-noise-sample-points-with-mitchells-best-candidate-algorithm/">Generating Blue Noise Sample Points With Mitchell’s Best Candidate Algorithm</a></li>
		<li><a target="_blank" href="https://blog.demofox.org/2017/10/25/transmuting-white-noise-to-blue-red-green-purple/">Transmuting White Noise To Blue, Red, Green, Purple</a></li>
		<li><a target="_blank" href="https://observablehq.com/@bensimonds/mitchells-best-candidate-algorithm">Mitchell's Best Candidate Algorithm</a></li>
	</ul>

	<footer>
		<a target="_blank" href="https://tools.laszlokorte.de" title="More educational tools"
			>More educational tools</a
		>
	</footer>
</section>

{#snippet scaleSwitch()}
<div class="switch">
	<label class="switch-option" class:active={hsvScale.value==false}><input type="radio" value={false} bind:group={hsvScale.value} /> Grayscale</label>
	<label class="switch-option" class:active={hsvScale.value==true}><input value={true} type="radio" bind:group={hsvScale.value} /> Rainbow</label>
</div>
{/snippet}

<style>

	figure {
		margin: 0;
		padding: 0;
	}
	figcaption {
		text-align: center;
	}
	.bitmap {
		image-rendering: pixelated;
	}
	.stack {
		display: grid;
		grid-template-columns: 100%;
		grid-template-rows: 100%;
		border: 1px solid gray;
		box-sizing: content-box;
		max-width: 192px;
		max-height: 192px;
		overflow: hidden;
		aspect-ratio: 1;
	}

	.stack :global(> *) {
		grid-area: 1 / 1;
		align-self: stretch;
		justify-self: stretch;
	}

	.stacked-video {
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		display: block;
	}

	.stacked-image {
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		display: block;
		image-rendering: pixelated;
	}

	.stacked-svg {
		pointer-events: none;
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		display: block;
	}

	.stacked-sprite {
		pointer-events: none;
		width: 100%;
		height: 100%;
		max-width: 100%;
		max-height: 100%;
		display: grid;
		overflow: hidden;
	}

	.stacked-sprite-image {
		width: 100%;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
		display: block;
	}

	.seeking {
		outline: pink 2px solid;
	}

	.pixel-marker {
		shape-rendering: crispEdges;
		vector-effect: non-scaling-stroke;
		stroke-width: 2px;
	}

	.unseekable {
		opacity: 0.2;
	}



	.stacked-sprite-image {
		margin-top: calc(-100% * var(--sprite-index,0 ));
	}

	.svg {
		width: 100%;
		background: #eee;
	}

	.row {
		display: flex;
		gap: 1em;
	}

	.centered {
		justify-content: center;
	}

	:global(.python-skip) .media-row {
		display: none;
	}

	.switch input {
		display: none;
	}

	.switch {
		display: flex;
		justify-content: center;
		gap: 1px;
		font-size: 0.8em;
	}

	.switch-option {
		color: #fff;
		padding: 0.1em 0.6em;
		cursor: pointer;
		color: #aaa;
	}


	.switch-option.active {
		background: gray;
		color: #b0e2f5;
	}

	.media-row {
		user-select: none;
		margin: 0.5em 0;
		padding: 0.8em 0;
		background: #0003;
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
		max-width: 80em;
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

	.color-picker-label {
		cursor: pointer;
	}

	.error-message {
		padding: 1em;
		color: #aa0000;
		background: #ffdddd;
	}

	ul {
		padding: 0;
		margin: 0.5em 0;
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

	p code, li code {
		background: #333;
		color: #fff;
		display: inline-block;
		padding: 1px 2px;
	}
</style>
