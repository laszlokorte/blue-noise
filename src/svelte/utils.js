
export function clamp(min, max) {
	return (v) => Math.max(min, Math.min(max, v))
}

export function lerp(a, b, t) {
	return a*(1-t) + b*t
}

function phi(n) { // do not surpass n >= 79 due to JavaScript's 32 bit integer limitation regarding decimal precision
    let ratios = [1, 1, 2], i = 2;
    let fs = fib(n, true);
    while (i < n - 1) {
        ratios.push((fs[i + 1] / fs[i]));
        i++;
    }
    return ratios;
}

function fib(n, isSeq) {// accuracy is lost after n > 79
    let Fn = 0, i = 2;
    let Fn_1 = 1, Fn_2 = 1;
    let seq = [Fn_1, Fn_2]; // Fibonacci sequence always starts with 1, 1
    while( i < n) {
        Fn = Fn_1 + Fn_2;
        var prevFn_1 = Fn_1;
        Fn_1 = Fn;
        Fn_2 = prevFn_1;
        seq. push(Fn);
        i++;
    }
    if (isSeq) {
        return seq;
    }
    return Fn;
}

export const PHI = fib(70, false)/fib(69, false)
