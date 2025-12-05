import { get, set, collect, foldl } from "partial.lenses";

export function atom(init) {
  let root = $state({
    value: init,
  });

  return root;
}

export function view(opticLense, s) {
  return {
    get value() {
      return get(opticLense, s.value);
    },
    set value(newVal) {
      const transformed = set(opticLense, newVal, s.value);

      if (!(transformed instanceof Error)) {
        s.value = transformed;
      }
    },
  };
}

export function failableView(
  opticLense,
  someAtom,
  autoReset = true,
  errorAtom = atom(null),
  transientAtom = atom(null),
) {
  $effect(() => {
    const changed = someAtom.value;

    untrack(() => {
      errorAtom.value = null;
      transientAtom.value = null;
    });
  });

  return {
    get value() {
      return errorAtom.value !== null
        ? transientAtom.value
        : get(opticLense, someAtom.value);
    },
    set value(newVal) {
      const transformed = set(opticLense, newVal, someAtom.value);

      if (!(transformed instanceof Error)) {
        someAtom.value = transformed;
        transientAtom.value = null;
        errorAtom.value = null;
      } else {
        transientAtom.value = newVal;
        errorAtom.value = transformed;
      }
    },
    get stableValue() {
      return get(opticLense, someAtom.value);
    },
    set stableValue(newVal) {
      const transformed = set(opticLense, newVal, someAtom.value);

      if (!(transformed instanceof Error)) {
        someAtom.value = transformed;

        if (autoReset) {
          transientAtom.value = null;
          errorAtom.value = null;
        }
      }
    },

    get stableAtom() {
      return {
        get value() {
          return get(opticLense, someAtom.value);
        },
        set value(newVal) {
          const transformed = set(opticLense, newVal, someAtom.value);

          if (!(transformed instanceof Error)) {
            someAtom.value = transformed;
            if (autoReset) {
              transientAtom.value = null;
              errorAtom.value = null;
            }
          }
        },
      };
    },

    get error() {
      return errorAtom.value;
    },
    get hasError() {
      return errorAtom.value !== null;
    },
    reset() {
      transientAtom.value = null;
      errorAtom.value = null;
    },
  };
}

export function read(opticLense, s) {
  return {
    get value() {
      return get(opticLense, s.value);
    },

    get all() {
      return collect(opticLense, s.value);
    },

    get allUniq() {
      return [
        ...foldl(
          (a, b) => {
            a.add(b);

            return a;
          },
          new Set(),
          opticLense,
          s.value,
        ),
      ];
    },

    get max() {
      return foldl(
        (a, b) => (b === undefined ? a : Math.max(a, b)),
        -Infinity,
        opticLense,
        s.value,
      );
    },

    get min() {
      return foldl(
        (a, b) => (b === undefined ? a : Math.min(a, b)),
        Infinity,
        opticLense,
        s.value,
      );
    },
  };
}
