function renderNav(active) {
    const user = JSON.parse(localStorage.getItem('jansetu_user') || 'null');
    const items = user && user.role !== 'citizen'
        ? [['dashboard', 'Dashboard'], ['exceptions', 'Exceptions'], ['audit', 'Audit Log'], ['matches', 'Identity Matches']]
        : [];
    const nav = document.createElement('div');
    nav.innerHTML = `
    <style>
      .jsnav { background:#0f1b3d; color:#fff; padding:0 24px; display:flex; align-items:center;
               justify-content:space-between; height:56px; font-family:system-ui,sans-serif; }
      .jsnav .brand { font-weight:700; font-size:17px; }
      .jsnav .tabs { display:flex; gap:4px; }
      .jsnav .tabs button { background:none; border:none; color:#b8c2e0; padding:8px 14px;
                            font-size:14px; cursor:pointer; border-radius:6px; }
      .jsnav .tabs button.active { background:#1a2a5e; color:#fff; }
      .jsnav .right { font-size:13px; color:#b8c2e0; display:flex; align-items:center; gap:12px; }
      .jsnav .right a { color:#b8c2e0; text-decoration:none; }
      footer.jsfoot { text-align:center; color:#999; font-size:12px; padding:20px; font-family:system-ui,sans-serif; }
      footer.jsfoot a { color:#666; margin:0 6px; }
    </style>
    <div class="jsnav">
      <div class="brand">SetuCare</div>
      <div class="tabs">${items.map(([id, label]) =>
        `<button class="${id === active ? 'active' : ''}" onclick="location.href='/static/${id}.html'">${label}</button>`).join('')}</div>
      <div class="right">
        <span>${user ? user.label : ''}</span>
        <a href="#" onclick="localStorage.removeItem('jansetu_user'); location.href='/static/login.html'">Logout</a>
      </div>
    </div>`;
    document.body.prepend(nav);
}
function renderFooter() {
    const f = document.createElement('footer');
    f.className = 'jsfoot';
    f.innerHTML = `SetuCare — hackathon prototype, not a real government service.
    <a href="/static/about.html">About &amp; Privacy</a>`;
    document.body.appendChild(f);
}