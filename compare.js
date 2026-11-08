/* Before/after slider: upgrades every two-photo ".twoup" pair into a draggable comparison.
   Opt-in: add data-compare to a .twoup whose two photos were shot from the same spot.
   Without JS (or without the attribute) the two photos simply sit side by side. */
(function () {
  document.querySelectorAll('.twoup[data-compare]').forEach(function (t) {
    var figs = t.querySelectorAll(':scope > figure');
    if (figs.length !== 2 || !figs[0].querySelector('img') || !figs[1].querySelector('img')) return;
    t.classList.add('cmp');
    var range = document.createElement('input');
    range.type = 'range'; range.min = 0; range.max = 100; range.value = 50; range.step = 0.5; range.className = 'cmp-range';
    range.setAttribute('aria-label', 'Drag to compare before and after');
    var handle = document.createElement('div'); handle.className = 'cmp-handle'; handle.setAttribute('aria-hidden', 'true'); handle.innerHTML = '<span></span>';
    var hint = document.createElement('p'); hint.className = 'cmp-hint'; hint.textContent = 'Drag to compare';
    t.appendChild(handle); t.appendChild(hint); t.appendChild(range);
    function set(v) { t.style.setProperty('--cmp', v + '%'); }
    set(50);
    range.addEventListener('input', function () { set(range.value); hint.hidden = true; });
  });
})();
