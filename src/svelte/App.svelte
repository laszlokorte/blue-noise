<script>
	import { onMount } from "svelte";
	import favicon from "/favicon.svg";
	import * as L from "partial.lenses";
	import * as R from "ramda";
	import { atom, view, read, failableView } from "./svatom.svelte.js";
	import { forcePlain } from "./contenteditable.js";
	import { lerp, clamp, PHI } from "./utils.js";
	import recordUrl from "/steps/recording.json?url";

	const loadedRecording = atom(null);
	const focus = atom({});
	const seeking = atom({});

	onMount(async () => {
		let recordJson = await fetch(recordUrl);
		let record = await recordJson.json();

		loadedRecording.value = record;
	});

	function getImageUrl(phase, step, name) {
		const u = new URL(
			`../../public/steps/p0${phase}-s0${step}-${name}.png`,
			import.meta.url,
		);
		return u.href;
	}

	function getVideoUrl(phase, step, name) {
		const u = new URL(
			`../../public/steps/p0${phase}-s0${step}-${name}.mp4`,
			import.meta.url,
		);
		return u.href;
	}

	function unravel(i, w, h) {
		return {
			x: i % w,
			y: Math.floor(i / w),
		};
	}

	const phase_images = {
		"1": {
			name: "Phase 1",
			intro: "This phase is the only point at which the algorithm is non-deterministic by generating white noise.",
			code: `shape = (size, size)
ranks = np.zeros(shape)

initial_white_noise = np.random.rand(size, size)
placed_pixels = initial_white_noise >= (1-initial_ratio)
count_placed = np.sum(placed_pixels)
count_remaining = placed_pixels.size - count_placed`,
			iter_code: `prev_swap = None

# Phase 1: Place intial
while True:
    blurred = gaussian(placed_pixels)
    densest = (blurred * placed_pixels).argmax()
    voidest = (blurred + placed_pixels).argmin()

    if prev_swap == (voidest, densest):
        break
    if densest == voidest:
        break

    densest_coord = np.unravel_index(densest, shape)
    voidest_coord = np.unravel_index(voidest, shape)

    placed_pixels[densest_coord] = False
    placed_pixels[voidest_coord] = True

    prev_swap = (densest, voidest)`,
			start: [
				{
					name: "initial_white_noise",
					varname: "initial_white_noise",
					step: 1,
					comment: "Initial Uniform White Noise",
				},
				{
					name: "initial_ratio_white",
					varname: "placed_pixels",
					step: 2,
					comment:
						"threshold: all values below 0.9 to 0, all others to 1",
				},
			],
			iter: [
				{
					name: "before-swap",
					varname: "placed_pixels",
					step: 3,
					markers: [],
					comment: "binary image at the begin of the iteration",
				},
				{
					name: "blurred",
					varname: "blurred",
					step: 3,
					markers: [],
					comment: "binary image gets blurred via guassian",
				},
				{
					name: "blurred_dense_masked",
					varname: "blurred * placed_pixels",
					step: 3,
					markers: [
						{
							key: "densest",
							color: "magenta",
							varname: "densest",
						},
					],
					comment:
						"blurred images gets masked. brightest pixel is selected",
				},
				{
					name: "blurred_voidest_offset",
					varname: "blurred + placed_pixels",
					step: 3,
					markers: [
						{
							key: "voidest",
							color: "magenta",
							varname: "voidest",
						},
					],
					comment:
						"blurred images gets added to the binary image, then darkest pixel is selected",
				},
				{
					name: "after-swap",
					varname: "placed_pixels",
					step: 3,
					markers: [
						{
							key: "densest",
							color: "#ff3333",
							varname: "densest",
						},
						{
							key: "voidest",
							color: "#aaffaa",
							varname: "voidest",
						},
					],
					comment: "darkest and brightest pixels are swapped",
				},
			],
		},
		"2": {
			name: "Phase 2",
			intro: "The goal of this phase is to assign distinct intensitiy value to all of the already placed pixels. Pixels that are close together must get most different values. This is achieved to iterated through the pixels from densest to sparsest region.",
			code: `placed_but_not_ranked = placed_pixels.copy()`,
			start: [
				{
					name: "initial",
					varname: "placed_pixels",
					step: 0,
					comment: "Initial binary mask of already placed pixels",
				},
			],
			iter_code: `for rank in range(count_placed, 0, -1):
	blurred = gaussian(placed_but_not_ranked)
	densest = (blurred * placed_but_not_ranked).argmax()
	densest_coord = np.unravel_index(densest, shape)

	placed_but_not_ranked[densest_coord] = False
	ranks[densest_coord] = rank`,
			iter: [
				{
					name: "before-remove",
					varname: "placed_pixels",
					step: 1,
					markers: [],
					comment: "remaining pixels at the begin of the iteration",
				},
				{
					name: "blurred",
					varname: "blurred",
					step: 1,
					markers: [],
					comment: "Image gets blurred",
				},
				{
					name: "blurred_dense_masked",
					varname: "(blurred * placed_but_not_ranked)",
					step: 1,
					markers: [
						{
							key: "densest",
							color: "magenta",
							varname: "densest",
						},
					],
					comment:
						"Blurred image is masked with binary mask, brightest pixel is selected",
				},
				// {
				// 	name: "blurred_dense_restricted",
				// 	step: 1,
				// 	markers: ["voidest"],
				// },
				{
					name: "after-remove",
					varname: "placed_pixels",
					step: 1,
					markers: [
						{
							key: "densest",
							varname: "densest",
							color: "#ff3333",
						},
					],
					comment: "Brightest pixel is removed from the mask",
				},
				{
					name: "after-ranks",
					varname: "ranks",
					step: 1,
					markers: [
						{
							key: "densest",
							color: "#ffcc00",
							varname: "densest",
						},
					],
					comment: "Rank value is assigned to the selected pixel",
				},
			],
		},
		"3": {
			name: "Phase 3",
			intro: "Up until now, only a few pixel have been placed in the image. The remaining task is to place the remaining pixels until each pixel in the image is set. This is is done in increase order from sparsest to densest region.",
			start: [
				{
					step: 0,
					name: "initial",
					varname: "placed_pixels",
					comment: "Initial binary mask of already placed pixels",
				},
			],
			iter_code: `for rank in range(count_remaining):
	blurred = gaussian(placed_pixels)
	voidest = (blurred + placed_pixels).argmin()
	voidest_coord = np.unravel_index(voidest, shape)

	placed_pixels[voidest_coord] = True
	ranks[voidest_coord] = count_placed + rank`,
			iter: [
				{
					name: "before-new",
					varname: "placed_pixels",
					step: 1,
					markers: [],
					comment:
						"Already placed pixel at the start of the iteration",
				},
				{
					name: "blurred",
					varname: "blurred",
					step: 1,
					markers: [],
					comment:
						"Mask of already placed pixels is blurred to find sparsest region",
				},
				{
					name: "blurred_voidest_offset",
					varname: "blurred + placed_pixels",
					step: 1,
					markers: [
						{
							key: "voidest",
							varname: "voidest",
							color: "magenta",
						},
					],
					comment:
						"Blurred image is offset by mask, the darkest pixel is selected",
				},
				{
					name: "after-new",
					varname: "placed_pixels",
					step: 1,
					markers: [
						{
							key: "voidest",
							color: "#aaffaa",
							varname: "voidest",
						},
					],
					comment: "Pixel is added to mask",
				},
				{
					name: "after-ranks",
					varname: "ranks",
					step: 1,
					markers: [
						{
							key: "voidest",
							color: "#ffcc00",
							varname: "voidest",
						},
					],
					comment: "Next rank is assigned to selected Pixel",
				},
			],
		},
		"5": {
			name: "Results",
			intro: "The final image can be further processed. For example only the pixel with intensities below 10% can be selected:",
			code: `psd = np.abs(spec*np.conj(spec))
log_psd = np.log(psd+eps)
log_psd[size//2,size//2] = 0 # set DC frequency to 0
psd[size//2,size//2] = 0 # set DC frequency to 0`,
			start: [
				{
					step: 0,
					name: "result",
					varname: "ranks",
					comment:
						"Resulting image, each pixel has a distinct intensity andsimilar intensities are not close to each other.",
				},
				{
					step: 0,
					name: "psd",
					varname: "psd",
					comment:
						"The Power-Spectral-Density(PSD) of the resulting image has a black spot at the center. That is, the resutling image does not contain any lower frequencies. This is the primary characteristic for blue noise.",
				},
				{
					step: 0,
					name: "log-psd",
					varname: "log_psd",
					comment:
						"The logarithm of the PSD also shows a dark region at the low frequencies.",
				},
			],
		},
		"6": {
			name: "Thresholding",
			intro: "The final image can be further processed. For example only the pixel with intensities below 10% can be selected:",
			code: `thres = space < 0.9
thres_spec = fftshift(fft2(thres))
thres_psd = np.abs(thres_spec*np.conj(thres_spec))
log_thres_psd = np.log(thres_psd+eps)
log_thres_psd[size//2,size//2] = 0 # set DC frequency to 0
thres_psd[size//2,size//2] = 0 # set DC frequency to 0`,
			start: [
				{
					step: 1,
					name: "thresholded",
					comment:
						"Notice how evenly the selected pixels are distributed across the image.",
				},
				{
					step: 1,
					name: "thresholded-psd",
					comment:
						"When looking at the psd of the thresholded result, we can still see the dark spot. I.e. the thresholden does not disrupt the blue-noise-chracteristic.",
				},
				{
					step: 1,
					name: "thresholded-log-psd",
					comment:
						"The logarithm of the PSD also keeps its dark region.",
				},
			],
		},
	};

	$inspect(loadedRecording.value);
</script>

<section>
	<header>
		<h1>
			<img src={favicon} class="icon" alt="Icon" />Generate Blue Noise
		</h1>
	</header>

	{#if loadedRecording.value !== null}
		{@const size = view(
			["globals", L.pick({ x: "width", y: "height" })],
			loadedRecording,
		)}
		<div>
			{#each Object.keys(phase_images) as p (p)}
				<h2>{phase_images[p].name}</h2>
				<p>{phase_images[p].intro}</p>
				{#if phase_images[p].code}
					<pre class="code-snippet">{phase_images[p].code}</pre>
				{/if}
				{@const iterations = read(
					["phases", p, L.values, "length"],
					loadedRecording,
				)}

				{@const f = view(
					[
						`phase${p}`,
						L.valueOr(0),
						L.normalize(clamp(0, iterations.min - 1)),
					],
					focus,
				)}
				{@const videoTimeInteger = view(
					L.lens(
						(x) => Math.floor(x),
						(y) => Math.floor(y),
					),
					f,
				)}
				{@const videoTimeReadonly = view(
					L.lens(
						(x) => x,
						(x, y) => y,
					),
					f,
				)}
				<div class="row">
					{#each phase_images[p].start as pi}
						<div>
							<div class="stack">
								<img
									class="bitmap"
									src={getImageUrl(p, pi.step, pi.name)}
									alt=""
								/><svg
									viewBox="0 0 {size.value.x} {size.value.y}"
									width="200"
									height="200"
								>
								</svg>
							</div>
							<div style="text-align: center;">
								<code>{pi.varname}</code>
							</div>
							<div>
								{pi.comment}
							</div>
						</div>
					{/each}
				</div>

				{#if phase_images[p].iter}
					{#if phase_images[p].iter_code}
						<pre class="code-snippet">{phase_images[p]
								.iter_code}</pre>
					{/if}
					<label class="number-picker">
						Iteration
						<input
							type="range"
							min="0"
							max={iterations.min - 1}
							bind:value={videoTimeInteger.value}
						/>
						<span> {videoTimeInteger.value}</span>
						<button
							onclick={() => {
								videoTimeInteger.value -= 1;
							}}
							type="button">Prev</button
						>
						<button
							onclick={() => {
								videoTimeInteger.value += 1;
							}}
							type="button">Next</button
						>
					</label>
					<div class="row">
						{#each phase_images[p].iter as pi}
							{@const seekable = atom(false)}
							{@const thisSeeking = view(
								[L.prop(p), L.prop(pi.name), L.valueOr(false)],
								seeking,
							)}
							<div>
								<div class="stack">
									<video
										autobuffer
										class:unseekable={!seekable.value}
										disablePictureInPicture
										class="stacked-video bitmap"
										bind:currentTime={videoTimeReadonly.value}
										bind:seeking={thisSeeking.value}
										bind:seekable={seekable.value}
									>
										<source
											src={getVideoUrl(
												p,
												pi.step,
												pi.name,
											)}
										/>
									</video>
									<svg
										viewBox="0 0 {size.value.x} {size.value
											.y}"
										width="200"
										height="200"
										class="stacked-svg"
									>
										{#each pi.markers as m, i (m.key)}
											{@const xy = unravel(
												loadedRecording.value.phases[p][
													m.key
												][videoTimeInteger.value],
												size.value.x,
												size.value.y,
											)}
											<rect
												rx="0.3"
												ry="0.3"
												x={xy.x - 1}
												y={xy.y - 1}
												fill="none"
												width="3"
												height="3"
												stroke-width="2"
												stroke={m.color}
												opacity="0.3"
											></rect>
											<rect
												rx="0.3"
												ry="0.3"
												x={xy.x - 1}
												y={xy.y - 1}
												fill="none"
												width="3"
												height="3"
												stroke-width="0.5"
												stroke={m.color}
											></rect>
										{/each}
									</svg>
								</div>
								<div style="text-align: center;">
									<code>{pi.varname}</code>
								</div>
								{#each pi.markers as m, i (m.key)}
									{@const xy = unravel(
										loadedRecording.value.phases[p][m.key][
											videoTimeInteger.value
										],
										size.value.x,
										size.value.y,
									)}
									<code
										style:padding="0.3em"
										style:background="#333"
										style:color={m.color}
										>{m.varname} = ({xy.x}, {xy.y})</code
									><br />
								{/each}
								<div>
									{pi.comment}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			{/each}
		</div>
	{/if}

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
		max-width: 60em;
	}

	.code-snippet {
		display: block;
		background: #333;
		color: #fff;
		padding: 1em;
		font-family: monospace;
		font-size: 1.1em;
		line-height: 1.4;
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