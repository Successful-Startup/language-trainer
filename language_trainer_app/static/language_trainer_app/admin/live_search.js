(function () {
  "use strict";

  var DEBOUNCE_MS = 450;
  var timer = null;

  function submitSearch() {
    var form = document.getElementById("changelist-search");
    if (form) {
      form.submit();
    }
  }

  function onInput() {
    clearTimeout(timer);
    timer = setTimeout(submitSearch, DEBOUNCE_MS);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("searchbar");
    if (!input) return;
    input.addEventListener("input", onInput);
  });
})();
