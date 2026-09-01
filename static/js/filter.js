(function () {
  var input = document.getElementById("artist-search");
  var container = document.getElementById("artist-groups");
  var empty = document.getElementById("artist-empty");
  var count = document.getElementById("artist-count");
  var pillsContainer = document.getElementById("genre-pills");
  var favoritesToggle = document.getElementById("favorites-toggle");
  if (!input || !container) return;

  var sections = Array.prototype.slice.call(container.querySelectorAll(".genre-section"));
  var cards = Array.prototype.slice.call(container.querySelectorAll(".artist-card"));
  var pills = pillsContainer ? Array.prototype.slice.call(pillsContainer.querySelectorAll(".pill")) : [];
  var activeGenre = "";
  var favoritesOnly = false;

  function updateCount(visible) {
    if (!count) return;
    count.textContent = visible + " of " + cards.length;
  }

  function applyFilter() {
    var query = input.value.trim().toLowerCase();
    var totalVisible = 0;

    sections.forEach(function (section) {
      var sectionMatchesGenre = activeGenre === "" || section.dataset.genreSection === activeGenre;
      var sectionCards = Array.prototype.slice.call(section.querySelectorAll(".artist-card"));
      var sectionVisible = 0;

      sectionCards.forEach(function (card) {
        var haystack = [
          card.dataset.name || "",
          card.dataset.genres || "",
          card.dataset.location || ""
        ].join(" ");
        var matchesQuery = query === "" || haystack.indexOf(query) !== -1;
        var matchesFavorite = !favoritesOnly || card.dataset.favorite === "true";
        var match = sectionMatchesGenre && matchesQuery && matchesFavorite;
        card.hidden = !match;
        if (match) sectionVisible++;
      });

      section.hidden = sectionVisible === 0;
      totalVisible += sectionVisible;
    });

    empty.hidden = totalVisible !== 0;
    updateCount(totalVisible);
  }

  input.addEventListener("input", applyFilter);

  if (favoritesToggle) {
    favoritesToggle.addEventListener("click", function () {
      favoritesOnly = !favoritesOnly;
      favoritesToggle.classList.toggle("active", favoritesOnly);
      favoritesToggle.dataset.favoritesOnly = String(favoritesOnly);
      applyFilter();
    });
  }

  pills.forEach(function (pill) {
    pill.addEventListener("click", function () {
      activeGenre = pill.dataset.genre || "";
      pills.forEach(function (p) { p.classList.toggle("active", p === pill); });
      applyFilter();
    });
  });

  applyFilter();
})();
