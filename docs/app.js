/* simak web companion. Stars and notes live in localStorage on this device;
   nothing is sent anywhere. */
(function () {
  var data = window.SIMAK_DATA;
  var content = document.getElementById('content');
  var footer = document.getElementById('footer');
  var tab = 'day1';

  document.getElementById('event-line').textContent =
    data.event.name + ' · ' + data.event.dates + ' · ' + data.event.venue;

  footer.innerHTML =
    'Agenda from <a href="' + data.event.source + '">' + data.event.source +
    '</a>, checked ' + data.event.checked + '. The schedule is subject to change. ' +
    data.event.note +
    '<br>The Guide tab is interpretation and suggestions, not the organizers\' descriptions. ' +
    'Stars and notes stay in this browser on this device. ' +
    'Source: <a href="https://github.com/irvan-putra/simak">github.com/irvan-putra/simak</a>.';

  function star(id) { return localStorage.getItem('simak:star:' + id) === '1'; }
  function note(id) { return localStorage.getItem('simak:note:' + id) || ''; }

  function sessionCard(s) {
    var el = document.createElement('section');
    el.className = 'session' + (s.kind === 'break' ? ' break' : '');

    var top = document.createElement('div');
    top.className = 'top';
    var time = document.createElement('span');
    time.className = 'time';
    time.textContent = s.start + ' - ' + s.end;
    var starBtn = document.createElement('button');
    starBtn.className = 'toggle' + (star(s.id) ? ' on' : '');
    starBtn.textContent = star(s.id) ? '★' : '☆';
    starBtn.setAttribute('aria-label', 'Star this session');
    starBtn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var on = !star(s.id);
      localStorage.setItem('simak:star:' + s.id, on ? '1' : '0');
      starBtn.className = 'toggle' + (on ? ' on' : '');
      starBtn.textContent = on ? '★' : '☆';
    });
    top.appendChild(time);
    top.appendChild(starBtn);
    el.appendChild(top);

    var h = document.createElement('h2');
    h.textContent = s.title;
    el.appendChild(h);

    if (s.speaker) {
      var sp = document.createElement('p');
      sp.className = 'speaker';
      sp.textContent = s.speaker;
      el.appendChild(sp);
    }

    var kind = document.createElement('span');
    kind.className = 'kind';
    kind.textContent = s.kind;
    el.appendChild(kind);

    var area = document.createElement('textarea');
    area.placeholder = 'Your note for this session (stays on this device)';
    area.value = note(s.id);
    area.style.display = 'none';
    area.addEventListener('input', function () {
      localStorage.setItem('simak:note:' + s.id, area.value);
    });
    area.addEventListener('click', function (ev) { ev.stopPropagation(); });
    el.appendChild(area);

    el.addEventListener('click', function () {
      area.style.display = area.style.display === 'none' ? 'block' : 'none';
    });
    return el;
  }

  function renderDay(dayId) {
    content.innerHTML = '';
    var day = null;
    data.days.forEach(function (d) { if (d.id === dayId) day = d; });
    if (!day) return;
    var label = document.createElement('p');
    label.style.cssText = 'color:var(--ink-soft);font-size:13px;margin:6px 4px;';
    label.textContent = day.label + ' · ' + day.date + ' (WIB)';
    content.appendChild(label);
    day.sessions.forEach(function (s) {
      // a legacy card only appears while it still carries saved state
      if (s.kind === 'legacy' && !star(s.id) && !note(s.id)) return;
      content.appendChild(sessionCard(s));
    });
  }

  function renderGuide() {
    content.innerHTML = '';
    var wrap = document.createElement('div');
    wrap.className = 'guide';

    var about = document.createElement('p');
    about.textContent = data.guide.about;
    wrap.appendChild(about);

    data.guide.sections.forEach(function (sec) {
      var h = document.createElement('h2');
      h.textContent = sec.title;
      wrap.appendChild(h);
      var ul = document.createElement('ul');
      sec.bullets.forEach(function (b) {
        var li = document.createElement('li');
        li.textContent = b;
        ul.appendChild(li);
      });
      wrap.appendChild(ul);
    });
    content.appendChild(wrap);
  }

  function render() {
    document.querySelectorAll('#tabs button').forEach(function (b) {
      b.className = b.dataset.tab === tab ? 'active' : '';
    });
    if (tab === 'guide') renderGuide(); else renderDay(tab);
  }

  document.getElementById('tabs').addEventListener('click', function (ev) {
    if (ev.target.dataset && ev.target.dataset.tab) {
      tab = ev.target.dataset.tab;
      render();
    }
  });

  render();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).catch(function () { /* offline cache optional */ });
    // A new service worker (new cache name) means fresh assets are ready;
    // reload once so the page renders them instead of the old cache's copy.
    var swReloaded = false;
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (swReloaded) return;
      swReloaded = true;
      location.reload();
    });
  }
})();
