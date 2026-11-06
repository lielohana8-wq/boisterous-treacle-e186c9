/* Booking form availability: the owner blocks days and time windows in the admin calendar;
   this hides them on every "inspection-request" form. Fails open — if the function is
   unreachable the form behaves exactly as before. */
(function () {
  var forms = document.querySelectorAll('form[name="inspection-request"]');
  if (!forms.length) return;
  var A = null;
  function iso(d) { return d.toISOString().slice(0, 10); }
  function dayAt(n) { var d = new Date(); d.setHours(12, 0, 0, 0); d.setDate(d.getDate() + n); return d; }
  function blockedWindows(day) { return (A && A.blocked && A.blocked[day]) || []; }
  function dayClosed(day) {
    if (!A) return false;
    var w = blockedWindows(day); if (w.indexOf('all') > -1) return true;
    var wd = new Date(day + 'T12:00:00').getDay();
    return (A.closed_weekdays || []).map(Number).indexOf(wd) > -1;
  }
  function firstOpen(from) {
    for (var i = 0; i < 120; i++) { var d = iso(dayAt(from + i)); if (!dayClosed(d)) return d; }
    return null;
  }
  function note(form, text) {
    var n = form.querySelector('[data-avail-note]');
    if (!n) { n = document.createElement('p'); n.className = 'fine'; n.setAttribute('data-avail-note', ''); n.setAttribute('aria-live', 'polite'); n.style.margin = '-6px 0 0'; n.style.color = '#A93F13';
      var d = form.querySelector('[name=visit_date]'); if (d && d.parentNode) d.parentNode.appendChild(n); else return; }
    n.textContent = text || ''; n.hidden = !text;
  }
  function apply(form) {
    var date = form.querySelector('[name=visit_date]'); if (!date) return;
    var lead = (A && A.lead_days) || 0, max = (A && A.max_days) || 60;
    date.min = iso(dayAt(lead)); date.max = iso(dayAt(max));
    var day = date.value;
    if (day && dayClosed(day)) {
      var next = firstOpen(Math.max(lead, 1));
      if (next) { date.value = next; day = next; note(form, 'That day is full — we moved you to the next open day, ' + new Date(next + 'T12:00:00').toLocaleDateString('en-CA', { weekday: 'long', month: 'long', day: 'numeric' }) + '.'); }
    } else note(form, '');
    var blocked = blockedWindows(day);
    form.querySelectorAll('input[name=visit_time]').forEach(function (r) {
      var off = blocked.indexOf(r.value) > -1 || (blocked.indexOf('all') > -1 && r.value.indexOf('First available') < 0);
      r.disabled = off; if (off && r.checked) r.checked = false;
      var lab = r.closest('label'); if (lab) { lab.style.opacity = off ? '.42' : ''; lab.title = off ? 'Not available on that day' : ''; }
    });
    form.querySelectorAll('select[name=visit_time] option').forEach(function (o) {
      var off = blocked.indexOf(o.value) > -1; o.disabled = off; if (off && o.selected) o.selected = false;
    });
  }
  function run() { forms.forEach(function (f) { apply(f); var d = f.querySelector('[name=visit_date]'); if (d && !d.dataset.avail) { d.dataset.avail = '1'; d.addEventListener('change', function () { apply(f); }); } }); }
  var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  if (ctl) setTimeout(function () { ctl.abort(); }, 4000);
  fetch('/.netlify/functions/availability', { signal: ctl && ctl.signal }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (a) { if (a && a.blocked) { A = a; run(); } }).catch(function () {});
})();
