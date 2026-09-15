(function () {
  "use strict";

  // Navigation mobile
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("mainNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Galerie produit : bascule d'image
  document.querySelectorAll(".gallery-thumbs").forEach(function (gallery) {
    gallery.addEventListener("click", function (e) {
      var thumbs = gallery.querySelectorAll("img");
      thumbs.forEach(function (t) { t.classList.remove("active"); });
      var img = e.target.closest("img");
      if (!img) return;
      img.classList.add("active");
      var main = document.querySelector(".gallery-main img");
      if (main) main.src = img.dataset.full;
    });
  });

  // Onglets description / caractéristiques / avis
  document.querySelectorAll(".tab-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var container = btn.closest(".pdp-sections");
      if (!container) return;
      container.querySelectorAll(".tab-btn").forEach(function (b) { b.classList.remove("active"); });
      container.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("active"); });
      btn.classList.add("active");
      var target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  // Confirmation automatique de la suppression de quantité
  document.querySelectorAll(".qty-input").forEach(function (input) {
    input.addEventListener("change", function () {
      var form = this.closest("form");
      if (form) form.requestSubmit ? form.requestSubmit() : form.submit();
    });
  });
})();