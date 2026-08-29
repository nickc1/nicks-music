(function () {
  var input = document.getElementById("artist-search");
  var grid = document.getElementById("artist-grid");
  var empty = document.getElementById("artist-empty");
  var count = document.getElementById("artist-count");
  var pillsContainer = document.getElementById("genre-pills");
  if (!input || !grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".artist-card"));
  var pills = pillsContainer ? Array.prototype.slice.call(pillsContainer.querySelectorAll(".pill")) : [];
  var activeGenre = "";

  function updateCount(visible) {
    if (!count) return;
    count.textContent = visible + " of " + cards.length;
  }

  function applyFilter() {
    var query = input.value.trim().toLowerCase();
    var visible = 0;

    cards.forEach(function (card) {
      var genres = (card.dataset.genres || "").split(",");
      var haystack = [
        card.dataset.name || "",
        card.dataset.genres || "",
        card.dataset.location || ""
      ].join(" ");

      var matchesQuery = query === "" || haystack.indexOf(query) !== -1;
      var matchesGenre = activeGenre === "" || genres.indexOf(activeGenre) !== -1;
      var match = matchesQuery && matchesGenre;

      card.hidden = !match;
      if (match) visible++;
    });

    empty.hidden = visible !== 0;
    updateCount(visible);
  }

  input.addEventListener("input", applyFilter);

  pills.forEach(function (pill) {
    pill.addEventListener("click", function () {
      activeGenre = pill.dataset.genre || "";
      pills.forEach(function (p) { p.classList.toggle("active", p === pill); });
      applyFilter();
    });
  });

  applyFilter();
})();
