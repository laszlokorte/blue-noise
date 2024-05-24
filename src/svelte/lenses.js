import * as L from "partial.lenses";

export const lindex = (xtra) =>
	L.lens(
		(a) =>
			Array(a + xtra)
				.fill(0)
				.map((_, i) => i),
		(c, a) => c.length - xtra,
	);