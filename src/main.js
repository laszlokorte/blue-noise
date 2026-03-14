import init from "./svelte/init";

function ready() {
  init(document.getElementById("app-root"));
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", ready);
} else {
  ready();
}
