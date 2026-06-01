/* ═══════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════ */
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function fmtDate(s) {
  if (!s) return '—';
  return new Date(s).toLocaleString('ru-RU',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
}
function statusBadge(s) {
  const c = STATUS_CFG[s] || { label: s, cls: 's-new' };
  return `<span class="status-badge ${c.cls}">${c.label}</span>`;
}
function colorOf(email) {
  const palette = ['#2563EB','#7C3AED','#059669','#DC2626','#D97706','#0E7490'];
  let h = 0; for (let i=0; i<email.length; i++) h = email.charCodeAt(i)+((h<<5)-h);
  return palette[Math.abs(h)%palette.length];
}
function initials(user) {
  return ((user.full_name||'?')[0]).toUpperCase();
}

/* ═══════════════════════════════════════════════════════
   SESSION ERROR HANDLER
═══════════════════════════════════════════════════════ */
function handleApiError(e, fallbackMsg) {
  if (e.message === 'SESSION_EXPIRED') {
    showToast('warning', 'Сессия истекла', 'Войдите снова');
    openAuthModal('login');
  } else {
    showToast('error', e.message || fallbackMsg || 'Ошибка сервера');
  }
}

/* ═══════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════ */
function showToast(type, title, desc='') {
  const icons = { success:'✅', warning:'⚠️', error:'❌', info:'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<div class="toast-icon">${icons[type]||'ℹ️'}</div>
    <div class="toast-text"><div class="toast-title">${esc(title)}</div>
    ${desc?`<div class="toast-desc">${esc(desc)}</div>`:''}</div>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(()=>{ el.style.animation='toastIn .3s ease reverse'; setTimeout(()=>el.remove(),300); },3500);
}

/* ═══════════════════════════════════════════════════════
   SCROLL / HEADER
═══════════════════════════════════════════════════════ */
function initScrollEvents() {
  const header = document.getElementById('header');
  const btn = document.getElementById('scrollTop');
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    header.classList.toggle('scrolled', y > 20);
    btn.classList.toggle('visible', y > 400);
    const ids = ['how','submit','map-section','tracker','statistics','faq'];
    let active = '';
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.getBoundingClientRect().top < 120) active = id;
    });
    document.querySelectorAll('nav a[data-section]').forEach(a => {
      a.classList.toggle('active', a.dataset.section === active);
    });
  });
}

/* ═══════════════════════════════════════════════════════
   COUNTERS ANIMATION
═══════════════════════════════════════════════════════ */
function animateCounter(el, target, dur=2000) {
  let v=0; const step=target/(dur/16);
  const t = setInterval(()=>{ v=Math.min(v+step,target); el.textContent=Math.floor(v).toLocaleString('ru'); if(v>=target)clearInterval(t); },16);
}
function initCounters(stats) {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      obs.unobserve(e.target);
      document.getElementById('hero-cnt-1').textContent = (stats.total_complaints||0).toLocaleString('ru');
      document.getElementById('hero-cnt-2').textContent = (stats.resolution_rate||0)+'%';
      animateCounter(document.getElementById('m1'), stats.total_complaints||0);
      animateCounter(document.getElementById('m2'), stats.resolution_rate||0);
      animateCounter(document.getElementById('m3'), 54200);
      animateCounter(document.getElementById('m4'), 6);
    });
  },{threshold:.3});
  obs.observe(document.getElementById('metrics'));
}

/* ═══════════════════════════════════════════════════════
   LIVE FEED
═══════════════════════════════════════════════════════ */
function renderLiveFeed() {
  const el = document.getElementById('live-feed');
  if (!el) return;
  el.innerHTML = LIVE_FEED.map(it=>`
    <div class="live-item">
      <div class="live-avatar" style="background:${it.bg}">${it.icon}</div>
      <div><div class="live-text">${it.text}</div><div class="live-time">${it.time}</div></div>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════
   CATEGORIES (from API)
═══════════════════════════════════════════════════════ */
let _categories = [];

async function loadCategoriesIntoForm() {
  try {
    _categories = await api.categories();
    renderCategoryGrid();
    renderCategorySelect();
  } catch(e) { showToast('error','Ошибка загрузки категорий'); }
}

function renderCategoryGrid() {
  const grid = document.getElementById('categoryGrid');
  if (!grid || !_categories.length) return;
  grid.innerHTML = _categories.map(c => {
    const m = CAT_META[c.id] || {icon:'🏠',color:'#64748B',hint:''};
    return `<div class="cat-tile" data-catid="${c.id}" onclick="selectCatTile(this)">
      <div class="cat-tile-icon">${m.icon}</div>
      <div class="cat-tile-name">${esc(c.name)}</div>
      <div class="cat-tile-count">${m.hint}</div>
    </div>`;
  }).join('');
}

function renderCategorySelect() {
  const sel = document.getElementById('complaint-category');
  if (!sel) return;
  sel.innerHTML = '<option value="">— Выберите категорию —</option>' +
    _categories.map(c=>`<option value="${c.id}">${(CAT_META[c.id]||{icon:''}).icon} ${esc(c.name)}</option>`).join('');
}

function renderQuickCategories() {
  const grid = document.getElementById('quick-categories-grid');
  if (!grid || !_categories.length) return;
  grid.innerHTML = _categories.slice(0,8).map(c => {
    const m = CAT_META[c.id]||{icon:'🏠'};
    return `<a class="quick-cat" href="#submit" onclick="quickCat(${c.id})">
      <div class="quick-cat-icon">${m.icon}</div>
      <div class="quick-cat-name">${esc(c.name)}</div>
    </a>`;
  }).join('');
}

function quickCat(id) {
  scrollToForm();
  setTimeout(()=>{ preselectCategory(id); }, 300);
}

function preselectCategory(id) {
  document.querySelectorAll('.cat-tile').forEach(t=>t.classList.toggle('selected', parseInt(t.dataset.catid)===id));
  _state.catId = id;
  document.getElementById('step1Next').disabled = false;
  // Also update select
  const sel = document.getElementById('complaint-category');
  if (sel) sel.value = id;
}

/* ═══════════════════════════════════════════════════════
   MULTI-STEP FORM
═══════════════════════════════════════════════════════ */
const _state = { catId: null, urgency: 'medium', step: 1 };

function selectCatTile(el) {
  document.querySelectorAll('.cat-tile').forEach(t=>t.classList.remove('selected'));
  el.classList.add('selected');
  _state.catId = parseInt(el.dataset.catid);
  document.getElementById('step1Next').disabled = false;
}

function selectCatInStep2(id) {
  // Update hidden catId from dropdown
  _state.catId = parseInt(id);
}

function selectUrgency(el, level) {
  document.querySelectorAll('.urgency-item').forEach(i=>i.className='urgency-item');
  el.classList.add('sel-'+level);
  _state.urgency = level;
  const priMap = {low:'low',med:'medium',high:'high'};
  _state.priority = priMap[level]||'medium';
}

function goStep(n) {
  if (n===2 && !_state.catId) { showToast('warning','Выберите категорию'); return; }
  if (n===3) {
    const city = document.getElementById('f-city').value.trim();
    const addr = document.getElementById('f-street').value.trim();
    const desc = document.getElementById('f-desc').value.trim();
    if (!city||!addr||!desc) { showToast('warning','Заполните поля','Укажите город, улицу и описание'); return; }
  }
  document.querySelectorAll('.form-step').forEach(s=>s.classList.remove('active'));
  document.getElementById('step'+n).classList.add('active');
  _state.step = n;
  updateProgress(n);
  document.getElementById('submit').scrollIntoView({behavior:'smooth',block:'start'});
}

function updateProgress(n) {
  for (let i=1;i<=4;i++) {
    const circle = document.getElementById('pc'+i);
    const label  = document.getElementById('pl'+i);
    const conn   = document.getElementById('conn'+i);
    circle.className = 'step-circle'+(i<n?' done':i===n?' active':'');
    circle.textContent = i<n ? '✓' : i;
    label.className = 'step-label'+(i<=n?' active':'');
    if (conn) conn.className = 'step-connector'+(i<n?' done':'');
  }
}

function previewPhotos(input) {
  const c = document.getElementById('photoPreviews');
  c.innerHTML = '';
  Array.from(input.files).slice(0,5).forEach(f=>{
    const r = new FileReader();
    r.onload = e => {
      const img = document.createElement('img');
      img.src = e.target.result;
      img.className = 'photo-preview';
      c.appendChild(img);
    };
    r.readAsDataURL(f);
  });
}

async function submitComplaint() {
  if (!auth.isLoggedIn()) {
    sessionStorage.setItem('afterLogin','submit');
    openAuthModal('login');
    showToast('info','Необходима авторизация','Войдите чтобы подать жалобу');
    return;
  }
  const name  = document.getElementById('f-name').value.trim();
  const phone = document.getElementById('f-phone').value.trim();
  if (!name||!phone) { showToast('warning','Укажите контакты','Имя и телефон обязательны'); return; }

  const btn = document.getElementById('btnSubmit');
  btn.disabled = true; btn.textContent = 'Отправка...';
  try {
    const city   = document.getElementById('f-city').value.trim();
    const street = document.getElementById('f-street').value.trim();
    const address = city + ', ' + street;

    // Геокодирование адреса
    let lat = null, lng = null;
    try {
      const q = encodeURIComponent(address);
      const geo = await fetch(`https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=1`,
        {headers:{'User-Agent':'Zhalobi/1.0'}});
      const gd = await geo.json();
      if (gd.length) { lat = gd[0].lat; lng = gd[0].lon; }
    } catch(_) {}

    const complaint = await api.submit({
      category_id:   _state.catId,
      title:         city + ' — ' + street,
      description:   document.getElementById('f-desc').value.trim(),
      address,
      priority:      _state.priority || 'medium',
      contact_phone: document.getElementById('f-phone').value.trim() || null,
      lat, lng,
    });

    // Добавляем метку на карту сразу если карта уже открыта
    if (_map && lat && lng) {
      addMapPin({
        lat: parseFloat(lat), lng: parseFloat(lng),
        cat: _state.catId || 8,
        status: 'new',
        title: complaint.title || (city + ' — ' + street),
        addr: address,
        district: '',
        id: complaint.id,
      });
    }

    showSuccessStep(complaint);
    showToast('success','Жалоба зарегистрирована!','Номер: '+complaint.ticket_number);
  } catch(e) {
    showToast('error', e.message||'Ошибка при отправке');
  } finally {
    btn.disabled = false; btn.textContent = 'Отправить обращение →';
  }
}

function showSuccessStep(c) {
  document.getElementById('ticketNumber').textContent = c.ticket_number;
  document.getElementById('ticketDate').textContent = fmtDate(c.created_at);
  document.getElementById('ticketCat').textContent = (CAT_META[c.category_id]||{icon:'🏠'}).icon + ' ' + (c.category?.name||'');
  const dead = {low:'10 раб. дней',medium:'3 раб. дня',high:'24 часа',critical:'Немедленно'};
  document.getElementById('ticketDeadline').textContent = dead[c.priority]||'10 раб. дней';
  goStep(4);
}

function copyTicket() {
  const t = document.getElementById('ticketNumber').textContent;
  navigator.clipboard.writeText(t).catch(()=>{});
  showToast('success','Скопировано!', t);
}

function trackFromSuccess() {
  const t = document.getElementById('ticketNumber').textContent;
  document.getElementById('trackerInput').value = t;
  document.getElementById('tracker').scrollIntoView({behavior:'smooth'});
  setTimeout(searchComplaint, 400);
}

function resetForm() {
  _state.catId=null; _state.urgency='medium'; _state.step=1;
  document.querySelectorAll('.form-step').forEach(s=>s.classList.remove('active'));
  document.getElementById('step1').classList.add('active');
  document.querySelectorAll('.cat-tile').forEach(t=>t.classList.remove('selected'));
  document.querySelectorAll('.urgency-item').forEach(t=>t.className='urgency-item');
  document.getElementById('step1Next').disabled=true;
  document.getElementById('photoPreviews').innerHTML='';
  ['f-city','f-street','f-desc','f-name','f-phone','f-email'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.value='';
  });
  updateProgress(1);
  document.getElementById('charCount').textContent='0';
}

function scrollToForm() {
  if (document.getElementById('cabinet').classList.contains('active')) closeCabinet();
  setTimeout(()=>document.getElementById('submit').scrollIntoView({behavior:'smooth'}),300);
}

/* ═══════════════════════════════════════════════════════
   TRACKER
═══════════════════════════════════════════════════════ */
async function searchComplaint() {
  const ticket = document.getElementById('trackerInput').value.trim().toUpperCase();
  const el = document.getElementById('trackerResult');
  if (!ticket) { el.innerHTML=''; return; }
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const c = await api.track(ticket);
    const m = CAT_META[c.category.id]||{icon:'🏠',color:'#2563EB'};
    el.innerHTML = `<div style="background:var(--primary-light);border-radius:12px;padding:16px;cursor:pointer" onclick="openModal(${c.id})">
      <div style="font-size:15px;font-weight:700;margin-bottom:6px">${m.icon} ${esc(c.category.name)}</div>
      <div style="font-size:13px;color:var(--muted);margin-bottom:8px">📍 ${esc(c.address)}</div>
      <div style="font-size:14px;margin-bottom:10px">${esc(c.title)}</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        ${statusBadge(c.status)}
        <span style="font-size:12px;color:var(--primary);font-weight:600">Подробнее →</span>
      </div>
    </div>`;
  } catch(e) {
    el.innerHTML = `<div style="background:#FEE2E2;border-radius:10px;padding:12px 16px;font-size:13px;color:#991B1B">
      ✗ Обращение не найдено. Проверьте номер.
    </div>`;
  }
}

document.addEventListener('keydown', e => {
  if (e.key==='Enter' && document.activeElement===document.getElementById('trackerInput')) searchComplaint();
});

/* ═══════════════════════════════════════════════════════
   TIMELINE MODAL
═══════════════════════════════════════════════════════ */
async function openModal(id) {
  const user = auth.getUser();
  let complaint;
  try {
    if (user) complaint = await api.getComplaint(id);
    else {
      const res = await api.track(''); // fallback — try track by id
      complaint = null;
    }
  } catch(e) { complaint = null; }

  if (!complaint) {
    showToast('info','Войдите для просмотра деталей');
    return;
  }

  const m = CAT_META[complaint.category.id]||{icon:'🏠'};
  const isDone = complaint.status==='resolved'||complaint.status==='closed';

  // Этапы жизненного цикла
  const STAGES = [
    {key:'new',       label:'Новое',        color:'#2563EB'},
    {key:'in_progress',label:'В работе',    color:'#F59E0B'},
    {key:'escalated', label:'Эскалировано', color:'#EF4444'},
    {key:'resolved',  label:'Решено',       color:'#10B981'},
    {key:'closed',    label:'Закрыто',      color:'#64748B'},
  ];
  const curIdx = STAGES.findIndex(s=>s.key===complaint.status);
  const cur = STAGES[curIdx]||STAGES[0];

  // Найти даты этапов из событий
  const events = complaint.events||[];
  const stageDate = key => {
    const ev = events.find(e=>e.new_status===key||(key==='new'&&e.event_type==='created'));
    return ev ? fmtDate(ev.created_at).split(',')[0] : '';
  };

  // Шапка
  document.getElementById('modalTitle').innerHTML = esc(complaint.ticket_number);
  document.getElementById('modalSubtitle').innerHTML =
    `${m.icon} <b>${esc(complaint.category.name)}</b> &nbsp;·&nbsp; 📍 ${esc(complaint.address)} &nbsp;·&nbsp; 📅 ${fmtDate(complaint.created_at)}`;

  // Описание + прогресс
  document.getElementById('modalDesc').innerHTML = `
    <div class="mc-body">
      <div class="mc-title">${esc(complaint.title)}</div>
      <div class="mc-desc">${esc(complaint.description)}</div>
    </div>
    <div class="mc-stages">
      <div class="mc-stages-header">
        <span class="mc-stages-lbl">Этап</span>
        <span class="mc-stages-cur" style="color:${cur.color}">${cur.label}</span>
        <span class="mc-stages-progress">${curIdx+1} / ${STAGES.length}</span>
      </div>
      <div class="mc-track">
        ${STAGES.map((s,i)=>`
          <div class="mc-stage-wrap">
            <div class="mc-dot ${i<curIdx?'mc-done':i===curIdx?'mc-active':''}" style="${i<=curIdx?`background:${s.color};border-color:${s.color}`:''}"></div>
            <div class="mc-stage-label">${s.label}</div>
            ${stageDate(s.key)?`<div class="mc-stage-date">${stageDate(s.key)}</div>`:''}
          </div>
          ${i<STAGES.length-1?`<div class="mc-line ${i<curIdx?'mc-done':''}" style="${i<curIdx?`background:${STAGES[i+1].color}`:''}"></div>`:''}
        `).join('')}
      </div>
    </div>`;

  // Заявитель (только админ)
  const applicantEl = document.getElementById('modalApplicant');
  if(applicantEl) {
    if(user?.is_admin && complaint.user) {
      const u = complaint.user;
      applicantEl.innerHTML = `
        <div class="modal-applicant-row">
          <span class="modal-applicant-lbl">Заявитель</span>
          <span class="modal-applicant-name">${esc(u.full_name||'—')}</span>
          <a class="modal-applicant-link" href="mailto:${esc(u.email)}">${esc(u.email)}</a>
          <span class="modal-applicant-phone">${esc(complaint.contact_phone||u.phone||'—')}</span>
        </div>`;
    } else { applicantEl.innerHTML=''; }
  }

  // История
  const evLabels={created:'Зарегистрировано',status_changed:'Изменён статус',escalated:'Эскалация',assigned:'Назначен исполнитель'};
  document.getElementById('modalTimeline').innerHTML = `
    <div class="mc-history-title">История событий</div>
    <div class="timeline">` +
    (events.length ? events.slice().reverse().map((ev,i)=>{
      const cls = i===0 && !isDone ? 'current' : 'done';
      return `<div class="tl-item ${cls}">
        <div class="tl-date">${fmtDate(ev.created_at)}</div>
        <div class="tl-title">${evLabels[ev.event_type]||ev.event_type}${ev.new_status?` ${statusBadge(ev.new_status)}`:''}</div>
        ${ev.comment?`<div class="tl-desc">${esc(ev.comment)}</div>`:''}
      </div>`;
    }).join('') : '<div class="tl-item done"><div class="tl-title">Обращение принято</div></div>')
    + '</div>';

  const ratingEl = document.getElementById('modalRating');
  if(ratingEl) ratingEl.style.display = isDone ? '' : 'none';

  document.getElementById('timelineModal').classList.add('open');
  document.body.style.overflow='hidden';
}

function closeModal() {
  document.getElementById('timelineModal').classList.remove('open');
  document.body.style.overflow='';
}

document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeModal(); });

let _rating=0;
function setRating(v) {
  _rating=v;
  document.querySelectorAll('.star').forEach((s,i)=>s.classList.toggle('active',i<v));
  showToast('success','Оценка принята','Спасибо за обратную связь!');
}

/* ═══════════════════════════════════════════════════════
   MAP
═══════════════════════════════════════════════════════ */
let _map, _markers=[];

async function initMap() {
  _map = L.map('map',{zoomControl:false}).setView([55.75,37.62],12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{
    attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>',
    subdomains:'abcd',maxZoom:19
  }).addTo(_map);
  L.control.zoom({position:'topright'}).addTo(_map);
  _map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');

  try {
    const complaints = await api.mapComplaints();
    complaints.forEach(c => {
      const district = MAP_DEMO.find(d => d.addr === c.address)?.district || '';
      addMapPin({
        lat: parseFloat(c.lat), lng: parseFloat(c.lng),
        cat: c.category?.id || 8,
        status: c.status,
        title: c.title,
        addr: c.address,
        district,
        id: c.id,
      });
    });
    renderDistrictStats(complaints);
  } catch(e) {
    MAP_DEMO.forEach(c => addMapPin(c));
    renderDistrictStats();
  }
}

function addMapPin(c) {
  const colors = {new:'#2563EB',in_progress:'#F59E0B',resolved:'#10B981',escalated:'#EF4444',closed:'#94A3B8'};
  const color = colors[c.status]||colors.new;
  const m = CAT_META[c.cat]||{icon:'🏠'};
  const pulse = c.status==='new' ? `<div class="map-pin-pulse" style="border-color:${color}"></div>` : '';
  const icon = L.divIcon({
    html:`<div class="map-pin-wrap">
      ${pulse}
      <div class="map-pin-circle" style="background:${color};box-shadow:0 4px 14px ${color}60">${m.icon}</div>
      <div class="map-pin-tail" style="border-top-color:${color}"></div>
    </div>`,
    className:'',iconSize:[40,52],iconAnchor:[20,52]
  });
  const status_labels = {new:'Новое',in_progress:'В работе',resolved:'Решено',escalated:'Эскалировано',closed:'Закрыто'};
  const marker = L.marker([c.lat,c.lng],{icon})
    .addTo(_map)
    .bindPopup(`<div class="map-popup">
      <div class="map-popup-head" style="border-left:3px solid ${color}">
        <span class="map-popup-icon">${m.icon}</span>
        <span class="map-popup-title">${c.title}</span>
      </div>
      <div class="map-popup-addr">📍 ${c.addr}</div>
      <span class="map-popup-badge" style="background:${color}18;color:${color}">${status_labels[c.status]||c.status}</span>
    </div>`,{maxWidth:260,className:'modern-popup'});
  marker._fs = c.status; marker._fc = c.cat;
  _markers.push(marker);
}

function renderDistrictStats(apiComplaints) {
  const el = document.getElementById('districtList');
  if (!el) return;
  const byDistrict = {};
  const source = apiComplaints
    ? apiComplaints.map(c => ({
        district: MAP_DEMO.find(d => d.addr === c.address)?.district || 'Другое',
        status: c.status,
      }))
    : MAP_DEMO;
  source.forEach(c => {
    const d = c.district || 'Прочие';
    if (!byDistrict[d]) byDistrict[d] = {total:0,new:0,in_progress:0,escalated:0,resolved:0};
    byDistrict[d].total++;
    byDistrict[d][c.status] = (byDistrict[d][c.status]||0)+1;
  });
  const rows = Object.entries(byDistrict)
    .map(([name,s])=>({name,...s,open:(s.new||0)+(s.in_progress||0)+(s.escalated||0)}))
    .sort((a,b)=>b.open-a.open);
  const maxOpen = rows[0]?.open || 1;
  const heat   = n => n>=3?'#EF4444':n>=2?'#F59E0B':n===1?'#2563EB':'#10B981';
  const icon   = n => n>=3?'🔴':n>=2?'🟠':n===1?'🔵':'🟢';
  const label  = n => n>=3?'Критично':n>=2?'Высокий':n===1?'Средний':'Норма';
  const parts  = d => [
    d.new        ? `${d.new} нов.`        : '',
    d.in_progress? `${d.in_progress} в работе` : '',
    d.resolved   ? `${d.resolved} решено`  : '',
  ].filter(Boolean).join(' · ');

  el.innerHTML = `
    <div class="district-legend">
      <span>🔴 Критично</span><span>🟠 Высокий</span><span>🔵 Средний</span><span>🟢 Норма</span>
    </div>
    ${rows.map((d,i)=>`
    <div class="district-item" onclick="focusDistrict('${d.name}')">
      <div class="district-rank" style="background:${heat(d.open)}18;color:${heat(d.open)}">${i+1}</div>
      <div class="district-info">
        <div class="district-name-row">
          <span class="district-sev-icon">${icon(d.open)}</span>
          <span class="district-name">${d.name}</span>
        </div>
        <div class="district-bar-track">
          <div class="district-bar" style="width:${Math.round(d.open/maxOpen*100)}%;background:${heat(d.open)}"></div>
        </div>
        <div class="district-breakdown">${parts(d)}</div>
      </div>
      <div class="district-open-badge">
        <div class="district-open-num" style="color:${heat(d.open)}">${d.open}</div>
        <div class="district-open-lbl">не решено</div>
      </div>
    </div>`).join('')}`;
}

function focusDistrict(name) {
  const c = MAP_DEMO.find(x=>x.district===name);
  if(c && _map) _map.setView([c.lat, c.lng], 14, {animate:true});
  document.querySelectorAll('.district-item').forEach(el=>{
    el.classList.toggle('district-item--active', el.querySelector('.district-name')?.textContent===name);
  });
}

function filterMap(btn, filter) {
  document.querySelectorAll('.map-filter').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  _markers.forEach(m=>{
    let show=true;
    if(filter!=='all') {
      if(['new','in_progress','resolved'].includes(filter)) show = m._fs===filter;
      else show = m._fc===parseInt(filter);
    }
    show ? m.addTo(_map) : _map.removeLayer(m);
  });
}

/* ═══════════════════════════════════════════════════════
   STATS + CHARTS
═══════════════════════════════════════════════════════ */
async function loadStats() {
  try {
    const s = await api.stats();
    document.getElementById('hero-cnt-1').textContent = (s.total_complaints||0).toLocaleString('ru');
    document.getElementById('hero-cnt-2').textContent = (s.resolution_rate||0)+'%';
    document.getElementById('m1').textContent = (s.total_complaints||0).toLocaleString('ru');
    document.getElementById('m2').textContent = (s.resolution_rate||0);
    document.getElementById('m3').textContent = (54200).toLocaleString('ru');
    document.getElementById('m4').textContent = 6;

    const setEl = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
    setEl('stat-total',   s.total_complaints||0);
    setEl('stat-rate',    (s.resolution_rate||0)+'%');
    setEl('stat-resolved', s.resolved_complaints||0);
    setEl('stat-auto',    s.auto_processed_count||0);

    // stats page numbers
    const sv = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'&nbsp;');
    const sts = document.getElementById('sn-total');   if(sts) sts.innerHTML = sv(s.total_complaints||0);
    const sr  = document.getElementById('sn-rate');    if(sr)  sr.textContent = (s.resolution_rate||0)+'%';

    return s;
  } catch(e) { return {}; }
}

function renderCharts() {
  const catCtx = document.getElementById('catChart');
  if (catCtx) new Chart(catCtx,{type:'doughnut',data:{
    labels:['Водоснабжение','Отопление','Электроэнергия','Лифты','Мусор','Дороги','Освещение','Другое'],
    datasets:[{data:[2341,1892,987,654,1122,3401,778,512],
      backgroundColor:['#2563EB','#DC2626','#D97706','#7C3AED','#059669','#92400E','#0E7490','#64748B'],
      borderWidth:0,hoverOffset:8}]
  },options:{responsive:true,plugins:{legend:{position:'right',labels:{font:{size:11}}}},cutout:'60%'}});

  const timeCtx = document.getElementById('timeChart');
  if (timeCtx) new Chart(timeCtx,{type:'line',data:{
    labels:['Июнь','Июль','Авг','Сен','Окт','Нов'],
    datasets:[
      {label:'Подано',data:[1420,1890,2100,1780,2450,2847],borderColor:'#2563EB',backgroundColor:'rgba(37,99,235,.1)',tension:.4,fill:true},
      {label:'Решено',data:[1200,1650,1900,1590,2100,2310],borderColor:'#10B981',backgroundColor:'rgba(16,185,129,.1)',tension:.4,fill:true}
    ]
  },options:{responsive:true,plugins:{legend:{position:'top'}},scales:{y:{beginAtZero:true}}}});

  const resCtx = document.getElementById('resolveChart');
  if (resCtx) new Chart(resCtx,{type:'bar',data:{
    labels:['Аварийные','Лифты','Вода','Тепло','Электро','Мусор','Дороги'],
    datasets:[{label:'Дней',data:[1,3,5,6,4,7,12],
      backgroundColor:['#EF4444','#7C3AED','#2563EB','#DC2626','#D97706','#059669','#92400E'],
      borderRadius:6}]
  },options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,title:{display:true,text:'Дни'}}}}});
}

/* ═══════════════════════════════════════════════════════
   FAQ
═══════════════════════════════════════════════════════ */
function renderFAQ() {
  const el = document.getElementById('faqGrid');
  if (!el) return;
  el.innerHTML = FAQ_DATA.map(f=>`<div class="faq-item">
    <div class="faq-question" onclick="toggleFAQ(this)">
      ${esc(f.q)}<span class="faq-arrow">⌄</span>
    </div>
    <div class="faq-answer">${esc(f.a)}</div>
  </div>`).join('');
}

function toggleFAQ(el) {
  const item=el.parentElement;
  const was=item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(i=>i.classList.remove('open'));
  if(!was) item.classList.add('open');
}

/* ═══════════════════════════════════════════════════════
   AUTH MODAL
═══════════════════════════════════════════════════════ */
function openAuthModal(tab) {
  document.getElementById('authModal').classList.add('open');
  document.body.style.overflow='hidden';
  switchAuthTab(tab||'login');
}
function closeAuthModal() {
  document.getElementById('authModal').classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('authModal').addEventListener('click',function(e){
  if(e.target===this) closeAuthModal();
});
function switchAuthTab(tab) {
  ['login','register'].forEach(t=>{
    document.getElementById('authStep-'+t).classList.toggle('active',t===tab);
    document.getElementById('authTab-'+t).classList.toggle('active',t===tab);
  });
}
function togglePass(id, icon) {
  const inp=document.getElementById(id);
  inp.type = inp.type==='password'?'text':'password';
  icon.textContent = inp.type==='password'?'👁':'🙈';
}
function checkPassStrength(v) {
  const fill=document.getElementById('passStrFill');
  if(!fill) return;
  let s=0; if(v.length>=6)s++; if(v.length>=10)s++; if(/[A-Z]/.test(v)&&/[0-9]/.test(v))s++;
  fill.style.width=['0','40%','70%','100%'][s];
  fill.style.background=['#E2E8F0','#EF4444','#F59E0B','#10B981'][s];
}

async function submitLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const pass  = document.getElementById('loginPass').value;
  const eErr  = document.getElementById('loginEmailErr');
  const pErr  = document.getElementById('loginPassErr');
  eErr.textContent=''; pErr.textContent='';
  let ok=true;
  if(!email||!/\S+@\S+\.\S+/.test(email)){eErr.textContent='Введите корректный email';document.getElementById('loginEmail').classList.add('error');ok=false;}
  else document.getElementById('loginEmail').classList.remove('error');
  if(pass.length<6){pErr.textContent='Пароль минимум 6 символов';document.getElementById('loginPass').classList.add('error');ok=false;}
  else document.getElementById('loginPass').classList.remove('error');
  if(!ok) return;
  const btn = document.getElementById('btnLogin');
  btn.disabled=true; btn.textContent='Вход...';
  try {
    const data = await api.login({email,password:pass});
    auth.save(data.access_token, data.user);
    closeAuthModal();
    updateHeaderAuth();
    showToast('success','Добро пожаловать!', data.user.full_name);
    const redir = sessionStorage.getItem('afterLogin');
    sessionStorage.removeItem('afterLogin');
    if(redir==='submit') scrollToForm();
    else if(redir==='cabinet') openCabinet('profile');
  } catch(e) {
    showToast('error', e.message||'Ошибка входа');
  } finally { btn.disabled=false; btn.textContent='Войти в аккаунт'; }
}

async function submitRegister() {
  const name    = document.getElementById('regName').value.trim();
  const email   = document.getElementById('regEmail').value.trim();
  const phone   = document.getElementById('regPhone').value.trim();
  const pass    = document.getElementById('regPass').value;
  const confirm = document.getElementById('regPassConfirm').value;
  ['regNameErr','regEmailErr','regPassErr','regConfirmErr'].forEach(id=>{
    document.getElementById(id).textContent='';
  });
  let ok=true;
  if(!name){document.getElementById('regNameErr').textContent='Введите имя';ok=false;}
  if(!email||!/\S+@\S+\.\S+/.test(email)){document.getElementById('regEmailErr').textContent='Введите корректный email';ok=false;}
  if(pass.length<6){document.getElementById('regPassErr').textContent='Минимум 6 символов';ok=false;}
  if(pass!==confirm){document.getElementById('regConfirmErr').textContent='Пароли не совпадают';ok=false;}
  if(!document.getElementById('regAgree').checked){showToast('warning','Необходимо согласие');ok=false;}
  if(!ok) return;
  const btn = document.getElementById('btnRegister');
  btn.disabled=true; btn.textContent='Регистрация...';
  try {
    const data = await api.register({
      email, password: pass, full_name: name, phone: phone||null
    });
    auth.save(data.access_token, data.user);
    closeAuthModal();
    updateHeaderAuth();
    showToast('success','Аккаунт создан!','Добро пожаловать, '+data.user.full_name);
    openCabinet('profile');
  } catch(e) {
    showToast('error', e.message||'Ошибка регистрации');
  } finally { btn.disabled=false; btn.textContent='Создать аккаунт'; }
}

/* ═══════════════════════════════════════════════════════
   HEADER AUTH STATE
═══════════════════════════════════════════════════════ */
function updateHeaderAuth() {
  const user = auth.getUser();
  const loggedIn = !!user;
  document.getElementById('loginBtn').style.display    = loggedIn?'none':'';
  document.getElementById('registerBtn').style.display = loggedIn?'none':'';
  document.getElementById('userMenuWrap').style.display = loggedIn?'':'none';
  document.getElementById('notifBtn').style.display     = loggedIn?'':'none';
  if (!loggedIn) return;
  const isAdmin = user.is_admin;
  const ini = initials(user);
  const col = isAdmin ? 'linear-gradient(135deg,#7C3AED,#2563EB)' : colorOf(user.email);
  const av = document.getElementById('headerAvatar');
  av.textContent = isAdmin?'🛡️':ini; av.style.background=col;
  document.getElementById('headerName').textContent = isAdmin?'Администратор':user.full_name.split(' ')[0];
  document.getElementById('dropdownName').innerHTML = user.full_name + (isAdmin?'&nbsp;<span class="admin-badge">Admin</span>':'');
  document.getElementById('dropdownEmail').textContent = user.email;
  document.getElementById('adminDropdownItem').style.display = isAdmin?'':'none';
  document.getElementById('notifDot').style.display = '';
  document.getElementById('dropdownNotifBadge').style.display = '';
  loadNotifCount();
}

async function loadNotifCount() {
  if (!auth.isLoggedIn()) return;
  try {
    const list = await api.notifications();
    const cnt = list.filter(n=>!n.is_read).length;
    const dot = document.getElementById('notifDot');
    const badge = document.getElementById('dropdownNotifBadge');
    if(dot) dot.style.display = cnt?'':'none';
    if(badge){ badge.textContent=cnt; badge.style.display=cnt?'':'none'; }
  } catch(_){}
}

function toggleUserDropdown() {
  document.getElementById('userDropdown').classList.toggle('open');
}
document.addEventListener('click', e=>{
  const w = document.getElementById('userMenuWrap');
  if(w&&!w.contains(e.target)) document.getElementById('userDropdown').classList.remove('open');
});

function doLogout() {
  auth.logout();
  document.getElementById('userDropdown').classList.remove('open');
  updateHeaderAuth();
  if(document.getElementById('cabinet').classList.contains('active')) closeCabinet();
  showToast('info','Вы вышли из аккаунта');
}

/* ═══════════════════════════════════════════════════════
   CABINET
═══════════════════════════════════════════════════════ */
function openCabinet(tab) {
  if(!auth.isLoggedIn()){
    sessionStorage.setItem('afterLogin','cabinet');
    openAuthModal('login');
    return;
  }
  document.getElementById('userDropdown').classList.remove('open');
  document.getElementById('mainPage').classList.add('hidden');
  document.getElementById('cabinet').classList.add('active');
  window.scrollTo({top:0,behavior:'instant'});
  fillCabinetUI();
  switchCabinetTab(tab||'profile');
}

function closeCabinet() {
  document.getElementById('cabinet').classList.remove('active');
  document.getElementById('mainPage').classList.remove('hidden');
  sessionStorage.removeItem('cabinetTab');
  history.replaceState(null, '', window.location.pathname);
  window.scrollTo({top:0,behavior:'smooth'});
}

function fillCabinetUI() {
  const user = auth.getUser();
  if(!user) return;
  const isAdmin = user.is_admin;
  const ini = initials(user);
  const col = isAdmin?'linear-gradient(135deg,#7C3AED,#2563EB)':colorOf(user.email);
  const setAv = (id, txt, bg) => { const el=document.getElementById(id); if(el){el.textContent=txt;el.style.background=bg;} };

  setAv('cabinetTopAvatar', isAdmin?'🛡️':ini, col);
  setAv('sidebarAv', isAdmin?'🛡️':ini, col);
  setAv('profileBigAv', ini, 'rgba(255,255,255,.25)');
  document.getElementById('cabinetTopName').textContent = isAdmin?'Администратор':user.full_name.split(' ')[0];
  document.getElementById('sidebarName').textContent = user.full_name;
  const nameParts = (user.full_name||'').trim().split(/\s+/);
  document.getElementById('cabinetWelcomeName').textContent = nameParts[1] || nameParts[0] || '';
  document.getElementById('profileHeaderName').textContent = user.full_name;
  document.getElementById('profileHeaderEmail').textContent = user.email;
  document.getElementById('profileHeaderSince').textContent = 'На платформе с ' + fmtDate(user.created_at);
  document.getElementById('pfName').textContent = user.full_name;
  document.getElementById('pfEmail').textContent = user.email;
  document.getElementById('pfPhone').textContent = user.phone||'Не указан';

  const np = (user.full_name||'').trim().split(/\s+/);
  const elLast = document.getElementById('setFLast');
  const elFirst = document.getElementById('setFFirst');
  const elMiddle = document.getElementById('setFMiddle');
  if(elLast)   elLast.value   = np[0]||'';
  if(elFirst)  elFirst.value  = np[1]||'';
  if(elMiddle) elMiddle.value = np[2]||'';
  document.getElementById('setFPhone').value = user.phone||'';

  document.getElementById('adminNavItem').style.display = isAdmin?'':'none';
}

function switchCabinetTab(tab) {
  document.querySelectorAll('.cabinet-nav-item').forEach(i=>i.classList.toggle('active',i.dataset.tab===tab));
  document.querySelectorAll('.cabinet-tab').forEach(t=>t.classList.toggle('active',t.id==='ctab-'+tab));
  sessionStorage.setItem('cabinetTab', tab);
  history.replaceState(null, '', '#cabinet/' + tab);
  if(tab==='complaints') loadMyComplaints();
  if(tab==='notifications') loadCabinetNotifs();
  if(tab==='admin') loadAdminPanel();
}

async function loadMyComplaints(filter='all') {
  const el=document.getElementById('myComplaintsList');
  el.innerHTML='<div class="spinner"></div>';
  try {
    let list = await api.myComplaints();
    if(filter!=='all') list = list.filter(c=>c.status===filter);
    if(!list.length){
      el.innerHTML='<div class="empty-state"><div class="ei">📋</div><p>Нет обращений</p><button class="btn btn-primary btn-sm" onclick="scrollToForm()">+ Новая жалоба</button></div>';
      return;
    }
    document.getElementById('compBadge').textContent = list.length;
    el.innerHTML = list.map(c=>{
      const m = c.category ? CAT_META[c.category.id]||{icon:'🏠',color:'#2563EB'} : {icon:'🏠',color:'#2563EB'};
      return `<div class="complaint-card status-${c.status}" onclick="openModal(${c.id})">
        <div class="complaint-header">
          <div class="complaint-cat-icon" style="background:${m.color}22">${m.icon}</div>
          <div class="complaint-meta">
            <div class="complaint-title">${esc(c.title)}</div>
            <div class="complaint-addr">📍 ${esc(c.address)}</div>
          </div>
          <div class="complaint-status">${statusBadge(c.status)}</div>
        </div>
        <div style="font-size:13px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(c.description)}</div>
        <div class="complaint-footer"><span>📅 ${fmtDate(c.created_at)} • #${c.ticket_number}</span><button class="action-btn">Подробнее →</button></div>
      </div>`;
    }).join('');
  } catch(e){ el.innerHTML='<div class="empty-state"><p>Ошибка загрузки</p></div>'; }
}

function filterMyComplaints(btn, filter) {
  document.querySelectorAll('.cabinet-filter-row .cabinet-filter').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  loadMyComplaints(filter);
}

async function loadCabinetNotifs() {
  const el=document.getElementById('notifListCabinet');
  el.innerHTML='<div class="spinner"></div>';
  try {
    const list = await api.notifications();
    if(!list.length){ el.innerHTML='<div class="empty-state"><div class="ei">🔔</div><p>Нет уведомлений</p></div>'; return; }
    const badge=document.getElementById('notifBadgeSidebar');
    const unread=list.filter(n=>!n.is_read).length;
    if(badge){badge.textContent=unread;badge.style.display=unread?'':'none';}
    const icons={success:'✅',warning:'⚠️',info:'📬',error:'❌'};
    const bgs  ={success:'#D1FAE5',warning:'#FEF3C7',info:'#DBEAFE',error:'#FEE2E2'};
    el.innerHTML=list.map(n=>`<div class="notif-item ${n.is_read?'':'unread'}" onclick="readNotif(${n.id},this)">
      <div class="notif-item-icon" style="background:${bgs[n.notification_type]||'#DBEAFE'}">${icons[n.notification_type]||'📬'}</div>
      <div style="flex:1">
        <div class="notif-item-title">${esc(n.message)}</div>
        <div class="notif-item-time">${fmtDate(n.created_at)}</div>
      </div>
      ${n.is_read?'':'<div class="unread-dot"></div>'}
    </div>`).join('');
  } catch(e){ el.innerHTML='<div class="empty-state"><p>Ошибка загрузки</p></div>'; }
}

async function readNotif(id, el) {
  el.classList.remove('unread');
  el.querySelector('.unread-dot')?.remove();
  await api.markRead(id).catch(()=>{});
  loadNotifCount();
}

async function markAllRead() {
  await api.markAllRead().catch(()=>{});
  document.querySelectorAll('#notifListCabinet .notif-item').forEach(el=>{
    el.classList.remove('unread');
    el.querySelector('.unread-dot')?.remove();
  });
  loadNotifCount();
  showToast('success','Всё прочитано');
}

async function saveProfile() {
  const user = auth.getUser();
  if(!user) return;
  const fLast   = document.getElementById('setFLast')?.value.trim()   || '';
  const fFirst  = document.getElementById('setFFirst')?.value.trim()  || '';
  const fMiddle = document.getElementById('setFMiddle')?.value.trim() || '';
  const joined  = [fLast, fFirst, fMiddle].filter(Boolean).join(' ');
  const phone   = document.getElementById('setFPhone').value.trim();
  try {
    const updated = await api.updateMe({
      full_name: joined || user.full_name,
      phone: phone || user.phone || '',
    });
    user.full_name = updated.full_name;
    user.phone     = updated.phone;
    auth.save(auth.getToken(), user);
    updateHeaderAuth();
    fillCabinetUI();
    showToast('success','Профиль обновлён');
  } catch(e) {
    showToast('error','Ошибка сохранения');
  }
}

function changePassword() {
  const n = document.getElementById('setNewPass').value;
  const c = document.getElementById('setConfPass').value;
  if(n.length<6){showToast('warning','Минимум 6 символов');return;}
  if(n!==c){showToast('error','Пароли не совпадают');return;}
  ['setNewPass','setConfPass'].forEach(id=>{document.getElementById(id).value='';});
  showToast('success','Пароль изменён');
}

/* ═══════════════════════════════════════════════════════
   ADMIN PANEL
═══════════════════════════════════════════════════════ */
let _adminAll=[], _adminFilter='all';

async function loadAdminPanel() {
  const kpiEl=id=>document.getElementById(id);
  try {
    const [stats, complaints, users] = await Promise.all([
      api.stats(), api.allComplaints({}), api.adminUsers()
    ]);
    // KPIs
    kpiEl('kpi-total')    && (kpiEl('kpi-total').textContent    = stats.total_complaints||0);
    kpiEl('kpi-new')      && (kpiEl('kpi-new').textContent      = stats.new_complaints||0);
    kpiEl('kpi-inprog')   && (kpiEl('kpi-inprog').textContent   = stats.in_progress_complaints||0);
    kpiEl('kpi-escalated')&& (kpiEl('kpi-escalated').textContent= stats.escalated_complaints||0);
    kpiEl('kpi-resolved') && (kpiEl('kpi-resolved').textContent = stats.resolved_complaints||0);
    kpiEl('kpi-rate')     && (kpiEl('kpi-rate').textContent     = (stats.resolution_rate||0)+'%');
    kpiEl('kpi-auto')     && (kpiEl('kpi-auto').textContent     = stats.auto_processed_count||0);
    _adminAll = complaints;
    renderAdminTable('');
    renderAdminUsers(users);
  } catch(e){ showToast('error','Ошибка загрузки администратора'); }
}

function renderAdminTable(q) {
  const body = document.getElementById('adminTBody');
  if(!body) return;
  let items = [..._adminAll];
  if(_adminFilter!=='all') items=items.filter(c=>c.status===_adminFilter);
  if(q){ const ql=q.toLowerCase(); items=items.filter(c=>c.ticket_number.toLowerCase().includes(ql)||c.title.toLowerCase().includes(ql)||c.address.toLowerCase().includes(ql)); }
  if(!items.length){ body.innerHTML='<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--muted)">Ничего не найдено</td></tr>'; return; }
  body.innerHTML = items.slice(0,30).map(c=>{
    const m = c.category?CAT_META[c.category.id]||{icon:'🏠'}:{icon:'🏠'};
    return `<tr>
      <td style="font-weight:700;font-size:12px;white-space:nowrap">${esc(c.ticket_number)}</td>
      <td style="max-width:220px">
        <div style="font-weight:600;font-size:13px;color:var(--primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer" title="${esc(c.title)}" onclick="openModal(${c.id})">${esc(c.title)}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px">${m.icon} ${esc(c.category?.name||'')}</div>
      </td>
      <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-size:12px" title="${esc(c.address)}">${esc(c.address)}</td>
      <td>${statusBadge(c.status)}</td>
      <td>${fmtDate(c.created_at)}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <select class="status-select s-${c.status}" onchange="adminStatus(${c.id},this.value,this)">
            ${Object.entries(STATUS_CFG).map(([val,cfg])=>`<option value="${val}"${c.status===val?' selected':''}>${cfg.label}</option>`).join('')}
          </select>
          <button class="admin-del-btn" onclick="adminDelete(${c.id})" title="Удалить жалобу">−</button>
        </div>
      </td>
    </tr>`;
  }).join('');
}

function renderAdminUsers(users) {
  const body=document.getElementById('adminUBody');
  if(!body) return;
  body.innerHTML = users.map(u=>{
    const ini=initials(u);
    const col=u.is_admin?'linear-gradient(135deg,#7C3AED,#2563EB)':colorOf(u.email);
    return `<tr>
      <td><div style="display:flex;align-items:center;gap:10px">
        <div class="avatar-circle" style="width:32px;height:32px;font-size:12px;background:${col}">${u.is_admin?'🛡️':ini}</div>
        <div style="font-weight:600">${esc(u.full_name)}</div>
      </div></td>
      <td style="color:var(--muted)">${esc(u.email)}</td>
      <td>${u.is_admin?'<span class="admin-badge">Admin</span>':'Пользователь'}</td>
      <td>${fmtDate(u.created_at)}</td>
    </tr>`;
  }).join('');
}

async function adminDelete(id) {
  const c = _adminAll.find(x=>x.id===id);
  if(!confirm(`Удалить жалобу ${c?.ticket_number||'#'+id}? Это действие необратимо.`)) return;
  try {
    await api.deleteComplaint(id);
    _adminAll = _adminAll.filter(x=>x.id!==id);
    renderAdminTable(document.getElementById('adminSearch')?.value||'');
    showToast('success','Жалоба удалена');
  } catch(e){ showToast('error', e.message||'Ошибка удаления'); }
}

async function adminStatus(id, status, selectEl) {
  const prev = _adminAll.find(x=>x.id===id)?.status;
  try {
    await api.updateComplaint(id,{status,comment:'Изменено администратором'});
    const c=_adminAll.find(x=>x.id===id);
    if(c) c.status=status;
    if(selectEl){
      selectEl.className='status-select s-'+status;
    }
    // re-render only if active filter would hide updated row
    if(_adminFilter!=='all' && _adminFilter!==status){
      renderAdminTable(document.getElementById('adminSearch')?.value||'');
    }
    showToast('success','Статус обновлён');
  } catch(e){
    // revert select on error
    if(selectEl && prev) selectEl.value=prev;
    showToast('error',e.message);
  }
}

async function adminEsc(id) {
  try {
    await api.escalate(id,'Ручная эскалация администратором');
    const c=_adminAll.find(x=>x.id===id); if(c) c.status='escalated';
    renderAdminTable(document.getElementById('adminSearch')?.value||'');
    showToast('warning','Жалоба эскалирована');
  } catch(e){ showToast('error',e.message); }
}

function adminFilterStatus(val) {
  _adminFilter=val;
  renderAdminTable(document.getElementById('adminSearch')?.value||'');
}

function adminSearchFn(q) { renderAdminTable(q); }

function adminExport() {
  const rows=[['Номер','Категория','Адрес','Статус','Дата']];
  _adminAll.forEach(c=>rows.push([c.ticket_number,c.category?.name||'',c.address,c.status,fmtDate(c.created_at)]));
  const csv=rows.map(r=>r.join(';')).join('\n');
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,﻿'+encodeURIComponent(csv);
  a.download='zhalobi_export.csv'; a.click();
  showToast('success','Экспорт готов');
}

/* ═══════════════════════════════════════════════════════
   ROUTE OPTIMIZER
═══════════════════════════════════════════════════════ */
let _routeMap = null;

async function buildRoute() {
  const btn = document.getElementById('buildRouteBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Геолокация...';

  try {
    const coords = await new Promise(resolve => {
      if (!navigator.geolocation) {
        resolve({ latitude: 55.7558, longitude: 37.6173 });
        return;
      }
      navigator.geolocation.getCurrentPosition(
        p => resolve({ latitude: p.coords.latitude, longitude: p.coords.longitude }),
        () => resolve({ latitude: 55.7558, longitude: 37.6173 }),
        { timeout: 6000 }
      );
    });

    btn.textContent = '⏳ Оптимизация...';
    const statuses = document.getElementById('routeStatusFilter').value;
    const data = await api.adminRoute(coords.latitude, coords.longitude, statuses);
    renderRouteResult(data, coords.latitude, coords.longitude);
  } catch(e) {
    showToast('error', e.message || 'Ошибка построения маршрута');
  } finally {
    btn.disabled = false;
    btn.textContent = '📍 Построить маршрут';
  }
}

function renderRouteResult(data, startLat, startLng) {
  document.getElementById('routeEmpty').style.display = 'none';
  document.getElementById('routeResult').style.display = '';

  document.getElementById('routeSummary').innerHTML = `
    <span>📍 <b>${data.count}</b> ${data.count===1?'точка':data.count<5?'точки':'точек'}</span>
    <span>📏 <b>${data.total_km} км</b> суммарно</span>
    <span style="color:var(--muted);font-size:11px">Алгоритм: Greedy Nearest Neighbor</span>
  `;

  if (_routeMap) { _routeMap.remove(); _routeMap = null; }
  _routeMap = L.map('routeMapCanvas', { zoomControl: false }).setView([startLat, startLng], 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd', maxZoom: 19
  }).addTo(_routeMap);
  L.control.zoom({ position: 'topright' }).addTo(_routeMap);
  _routeMap.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');

  const STATUS_COLOR = { new:'#2563EB', in_progress:'#F59E0B', escalated:'#EF4444', resolved:'#10B981' };

  const startIcon = L.divIcon({
    html: `<div style="width:34px;height:34px;background:#10B981;border:3px solid white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 2px 8px rgba(0,0,0,.3)">🏁</div>`,
    className:'', iconSize:[34,34], iconAnchor:[17,17]
  });
  L.marker([startLat, startLng], { icon: startIcon })
    .addTo(_routeMap)
    .bindPopup('<b>Точка старта</b>');

  const latlngs = [[startLat, startLng]];

  data.route.forEach((stop, i) => {
    const color = STATUS_COLOR[stop.status] || '#64748B';
    const icon = L.divIcon({
      html: `<div style="width:28px;height:28px;background:${color};border:2.5px solid white;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:800;box-shadow:0 2px 6px rgba(0,0,0,.3)">${i+1}</div>`,
      className:'', iconSize:[28,28], iconAnchor:[14,14]
    });
    L.marker([parseFloat(stop.lat), parseFloat(stop.lng)], { icon })
      .addTo(_routeMap)
      .bindPopup(`<b>#${i+1} ${esc(stop.ticket_number)}</b><br>${esc(stop.title)}<br>📍 ${esc(stop.address)}<br><small>+${stop.dist_km} км от предыдущей точки</small>`);
    latlngs.push([parseFloat(stop.lat), parseFloat(stop.lng)]);
  });

  L.polyline(latlngs, { color:'#2563EB', weight:2.5, dashArray:'8 5', opacity:.75 }).addTo(_routeMap);
  if (latlngs.length > 1) _routeMap.fitBounds(L.latLngBounds(latlngs), { padding:[36, 36] });

  const listEl = document.getElementById('routeListEl');
  if (!data.route.length) {
    listEl.innerHTML = '<div style="text-align:center;padding:16px;color:var(--muted)">Нет активных жалоб с координатами по выбранным статусам</div>';
    return;
  }

  const STATUS_LABEL = { new:'Новое', in_progress:'В работе', escalated:'Эскалировано', resolved:'Решено' };
  listEl.innerHTML = data.route.map((stop, i) => {
    const color = STATUS_COLOR[stop.status] || '#64748B';
    return `<div class="route-item" onclick="openModal(${stop.id})">
      <div class="route-num" style="background:${color}">${i+1}</div>
      <div class="route-info">
        <div class="route-title">${esc(stop.ticket_number)} — ${esc(stop.title)}</div>
        <div class="route-addr">📍 ${esc(stop.address)} · ${esc(stop.category)} · ${STATUS_LABEL[stop.status]||stop.status}</div>
      </div>
      <div class="route-dist">+${stop.dist_km} км</div>
    </div>`;
  }).join('');
}

/* ═══════════════════════════════════════════════════════
   HELP PANEL
═══════════════════════════════════════════════════════ */
function toggleHelp() {
  document.getElementById('helpPanel').classList.toggle('open');
}
document.addEventListener('click', e=>{
  const p=document.getElementById('helpPanel');
  if(p.classList.contains('open')&&!e.target.closest('.floating-help')) p.classList.remove('open');
});

/* ═══════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  // Auth
  if(auth.isLoggedIn()) updateHeaderAuth();

  // Restore cabinet state on reload (sessionStorage primary, URL hash fallback)
  if(auth.isLoggedIn()) {
    const savedTab = sessionStorage.getItem('cabinetTab');
    const hashMatch = window.location.hash.match(/^#cabinet\/(.+)$/);
    const tab = savedTab || (hashMatch && hashMatch[1]);
    if(tab) openCabinet(tab);
  }

  // Load stats
  const stats = await loadStats();
  initCounters(stats);

  // Categories
  await loadCategoriesIntoForm();
  renderQuickCategories();

  // UI
  renderLiveFeed();
  renderFAQ();
  initScrollEvents();
  renderCharts();

  // Desc counter
  const desc=document.getElementById('f-desc');
  if(desc) desc.addEventListener('input',()=>document.getElementById('charCount').textContent=desc.value.length);

  // Map (lazy)
  const obs=new IntersectionObserver(entries=>{
    if(entries[0].isIntersecting){ initMap(); obs.disconnect(); }
  },{threshold:.1});
  const mapEl=document.getElementById('map');
  if(mapEl) obs.observe(mapEl);

  // Complaints live list — только для авторизованных
  const listEl = document.getElementById('complaintsList');
  if(listEl) {
    if(!auth.isLoggedIn()) {
      listEl.innerHTML = `<div style="text-align:center;padding:32px 16px;color:var(--muted)">
        <div style="font-size:36px;margin-bottom:12px">🔒</div>
        <div style="font-weight:600;color:#0F172A;margin-bottom:6px">Войдите, чтобы видеть обращения</div>
        <div style="font-size:13px;margin-bottom:16px">Список актуальных жалоб доступен зарегистрированным пользователям</div>
        <button class="btn btn-primary btn-sm" onclick="openAuthModal('login')" style="border:none">Войти</button>
      </div>`;
    } else {
      try {
        const recent = await api.recentComplaints(5);
        if(recent.length) {
          listEl.innerHTML = recent.map(c=>{
            const m = c.category?CAT_META[c.category.id]||{icon:'🏠',color:'#2563EB'}:{icon:'🏠',color:'#2563EB'};
            return `<div class="complaint-card status-${c.status}" onclick="openModal(${c.id})">
              <div class="complaint-header">
                <div class="complaint-cat-icon" style="background:${m.color}22">${m.icon}</div>
                <div class="complaint-meta">
                  <div class="complaint-title">${esc(c.title)}</div>
                  <div class="complaint-addr">📍 ${esc(c.address)}</div>
                </div>
                ${statusBadge(c.status)}
              </div>
              <div class="complaint-progress"><div class="progress-bar"><div class="progress-fill" style="width:${(STATUS_CFG[c.status]||{progress:10}).progress}%;background:${c.status==='escalated'?'#EF4444':c.status==='resolved'||c.status==='closed'?'#10B981':'#2563EB'}"></div></div></div>
              <div class="complaint-footer"><span>📅 ${fmtDate(c.created_at)} • #${c.ticket_number}</span><button class="action-btn">Подробнее →</button></div>
            </div>`;
          }).join('');
        }
      } catch(_){}
    }
  }
});
