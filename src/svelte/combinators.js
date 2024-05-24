import * as R from "ramda";

export const B1 = R.curry((a, b, c, d) => {
	return a(b(d))(c(d));
});

export const expect = (message, pred) => (v) => {
	if (pred(v)) {
		return v;
	} else {
		throw new Error(message);
	}
};