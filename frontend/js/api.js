async function request(method, url, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  const token = localStorage.getItem('token');
  if (token) opts.headers['Authorization'] = 'Bearer ' + token;
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(API + url, opts);
  if (res.status === 204) return null;

  if (res.status === 401) {
    auth.logout();
    if (typeof updateHeaderAuth === 'function') updateHeaderAuth();
    throw new Error('SESSION_EXPIRED');
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Ошибка сервера');
  return data;
}

const api = {
  // Auth
  register: (d) => request('POST', '/auth/register', d),
  login:    (d) => request('POST', '/auth/login', d),
  me:       ()  => request('GET',  '/auth/me'),

  // Complaints
  updateMe:        (d)  => request('PATCH', '/auth/me', d),
  categories:      ()   => request('GET', '/complaints/categories'),
  recentComplaints:(limit=5) => request('GET', `/complaints/recent?limit=${limit}`),
  mapComplaints:   ()        => request('GET', '/complaints/map'),
  submit:          (d)  => request('POST', '/complaints', d),
  myComplaints:    ()   => request('GET', '/complaints/my'),
  track:           (t)  => request('GET', `/complaints/track/${t}`),
  getComplaint:    (id) => request('GET', `/complaints/${id}`),

  // Admin
  allComplaints:   (params) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', '/admin/complaints' + (q ? '?' + q : ''));
  },
  updateComplaint:  (id, d) => request('PATCH',   `/admin/complaints/${id}`, d),
  deleteComplaint:  (id)    => request('DELETE', `/admin/complaints/${id}`),
  escalate:        (id, r) => request('POST', `/admin/complaints/${id}/escalate?reason=${encodeURIComponent(r)}`),
  adminUsers:      ()      => request('GET', '/admin/users'),
  adminRoute:      (lat, lng, statuses='new,in_progress,escalated') =>
    request('GET', `/admin/route?lat=${lat}&lng=${lng}&statuses=${encodeURIComponent(statuses)}`),

  // Stats & notifications
  stats:           () => request('GET', '/stats'),
  notifications:   () => request('GET', '/notifications'),
  markRead:        (id) => request('POST', `/notifications/${id}/read`),
  markAllRead:     ()   => request('POST', '/notifications/read-all'),
};
