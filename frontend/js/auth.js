const auth = {
  getToken:  () => localStorage.getItem('token'),
  getUser:   () => { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } },
  isLoggedIn:() => !!localStorage.getItem('token'),
  isAdmin:   () => { const u = auth.getUser(); return u && u.is_admin; },

  save(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};
