(function () {
  const API_BASE = window.HEMOCHAIN_API_BASE || (location.hostname === "localhost" ? "http://localhost:5000" : location.origin);
  const SESSION_KEY = "hemochain_super_admin_session";
  const TOKEN_KEY = "hemochain_auth_token";
  const REFRESH_TOKEN_KEY = "hemochain_refresh_token";
  const ROLE_KEY = "hemochain_auth_role";
  const USER_KEY = "hemochain_auth_user";
  const THEME_KEY = "hemochain_admin_theme";

  const $ = (s, sc = document) => sc.querySelector(s);
  const $$ = (s, sc = document) => Array.from(sc.querySelectorAll(s));

  function showToast(m) { const t = $("#toast"); if (!t) return; t.textContent = m; t.classList.add("show"); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => t.classList.remove("show"), 2600); }
  function hasSession() { return getStored(SESSION_KEY) === "active" && getStored(ROLE_KEY) === "admin" && Boolean(getStored(TOKEN_KEY)); }
  function getStored(k) { return localStorage.getItem(k) || sessionStorage.getItem(k); }
  function getToken() { return getStored(TOKEN_KEY); }

  function setSession(remember, data) {
    const store = remember ? localStorage : sessionStorage;
    const other = remember ? sessionStorage : localStorage;
    store.setItem(SESSION_KEY, "active"); store.setItem(TOKEN_KEY, data.token);
    store.setItem(REFRESH_TOKEN_KEY, data.refresh_token || ""); store.setItem(ROLE_KEY, data.role);
    store.setItem(USER_KEY, JSON.stringify(data.user || {}));
    [SESSION_KEY, TOKEN_KEY, REFRESH_TOKEN_KEY, ROLE_KEY, USER_KEY].forEach(k => other.removeItem(k));
  }
  function clearSession() { [localStorage, sessionStorage].forEach(s => [SESSION_KEY, TOKEN_KEY, REFRESH_TOKEN_KEY, ROLE_KEY, USER_KEY].forEach(k => s.removeItem(k))); }

  async function api(ep) {
    const r = await fetch(`${API_BASE}/api/${ep}`, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (r.status === 401) { clearSession(); location.replace("./"); return null; }
    const d = await r.json(); return d.success ? d.data : null;
  }

  const ago = d => { if(!d) return ''; const s=Math.floor((Date.now()-new Date(d))/1e3); if(s<60) return 'Just now'; if(s<3600) return Math.floor(s/60)+' min ago'; if(s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago'; };

  function initLogin() {
    const form = $("#adminLoginForm"); if (!form) return;
    if (hasSession()) { location.replace("./dashboard.html"); return; }
    const pw = $("#adminPassword"), toggle = $("#passwordToggle"), error = $("#loginError");
    toggle?.addEventListener("click", () => { const v = pw.type === "text"; pw.type = v ? "password" : "text"; toggle.querySelector(".material-symbols-rounded").textContent = v ? "visibility" : "visibility_off"; });
    $("#forgotPassword")?.addEventListener("click", () => showToast("Password reset workflow is ready."));
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const email = $("#adminEmail").value.trim().toLowerCase(), password = pw.value, remember = $("#rememberAdmin").checked;
      const btn = $(".login-action"); if(btn) { btn.disabled = true; btn.innerHTML = '<span class="material-symbols-rounded">progress_activity</span> Verifying...'; }
      try {
        const r = await fetch(`${API_BASE}/api/auth/admin/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data.success) { error?.classList.add("show"); $("#errTxt").textContent = data.message || "Invalid Credentials"; pw.focus(); return; }
        error?.classList.remove("show"); setSession(remember, data);
        showToast("Verified. Opening dashboard..."); setTimeout(() => location.assign("./dashboard.html"), 420);
      } catch (_) { error?.classList.add("show"); $("#errTxt").textContent = "Unable to reach API."; }
      finally { if(btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-rounded">login</span> Sign In'; } }
    });
  }

  function initDashboard() {
    if (!document.body.classList.contains("admin-app-page")) return;
    if (!hasSession()) { location.replace("./"); return; }

    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme === "dark") { document.body.classList.add("dark"); $("#themeToggle .material-symbols-rounded").textContent = "light_mode"; }

    const viewTitle = $("#viewTitle"), viewSubtitle = $("#viewSubtitle"), search = $("#globalSearch");
    function closeMobileSidebar() { document.body.classList.remove("sidebar-open"); }
    function setView(target) {
      const view = $(`#${target}View`); if (!view) return;
      $$(".view").forEach(i => i.classList.remove("active")); view.classList.add("active");
      $$(".nav-link[data-target]").forEach(l => l.classList.toggle("active", l.dataset.target === target));
      viewTitle.textContent = view.dataset.title || "Dashboard"; viewSubtitle.textContent = view.dataset.subtitle || "";
      if (search) search.value = ""; filterVisibleView(""); closeMobileSidebar();
    }
    function filterVisibleView(term) {
      const av = $(".view.active"); if (!av) return; const q = term.trim().toLowerCase();
      $$("[data-search]", av).forEach(i => i.classList.toggle("is-hidden", Boolean(q) && !i.dataset.search.toLowerCase().includes(q)));
      $$("tbody tr", av).forEach(r => { const t = `${r.dataset.search||""} ${r.textContent}`.toLowerCase(); r.classList.toggle("is-hidden", Boolean(q) && !t.includes(q)); });
    }
    $$(".nav-link[data-target]").forEach(b => b.addEventListener("click", () => setView(b.dataset.target)));
    $$("[data-target-shortcut]").forEach(b => b.addEventListener("click", () => { setView(b.dataset.targetShortcut); $("#profileMenu")?.classList.remove("open"); }));
    search?.addEventListener("input", () => filterVisibleView(search.value));
    $("#roleFilter")?.addEventListener("change", e => { const v = e.target.value; $$("#usersTable tbody tr").forEach(r => { r.classList.toggle("is-hidden", v !== "all" && r.dataset.role !== v); }); });
    $("#collapseSidebar")?.addEventListener("click", () => { document.body.classList.toggle("collapsed"); $("#collapseSidebar .material-symbols-rounded").textContent = document.body.classList.contains("collapsed") ? "left_panel_open" : "left_panel_close"; });
    $("#mobileMenu")?.addEventListener("click", () => document.body.classList.add("sidebar-open"));
    $("#mobileScrim")?.addEventListener("click", closeMobileSidebar);
    $("#themeToggle")?.addEventListener("click", () => { const d = document.body.classList.toggle("dark"); localStorage.setItem(THEME_KEY, d ? "dark" : "light"); $("#themeToggle .material-symbols-rounded").textContent = d ? "light_mode" : "dark_mode"; });
    $("#profileToggle")?.addEventListener("click", () => $("#profileMenu")?.classList.toggle("open"));
    document.addEventListener("click", e => { const m = $("#profileMenu"), t = $("#profileToggle"); if (m && t && !m.contains(e.target) && !t.contains(e.target)) m.classList.remove("open"); });
    const drawer = $("#notificationDrawer");
    $("#notificationsToggle")?.addEventListener("click", () => drawer?.classList.add("open"));
    $("#closeNotifications")?.addEventListener("click", () => drawer?.classList.remove("open"));

    async function logout() {
      const token = getToken();
      if (token) { try { await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", headers: { Authorization: `Bearer ${token}` } }); } catch (_) {} }
      clearSession(); showToast("Signed out."); setTimeout(() => location.replace("./"), 350);
    }
    $("#logoutButton")?.addEventListener("click", logout);
    $("#profileLogout")?.addEventListener("click", logout);

    $$("[data-export]").forEach(b => b.addEventListener("click", () => showToast(`${b.dataset.export} export generated.`)));

    // ── LOAD LIVE DATA ──
    loadAdminData();
  }

  async function loadAdminData() {
    const [overview, donors, facilities, emergencies, inventory, reports, notifs, blockchain, chainInfo] = await Promise.all([
      api("admin/dashboard-overview"), api("admin/donors"), api("admin/facilities"),
      api("admin/global-emergencies"), api("admin/inventory"), api("admin/reports"),
      api("admin/notifications"), api("blockchain/logs"), api("blockchain/chain-info")
    ]);

    // ── DASHBOARD COUNTERS ──
    if (overview) {
      const counters = $$(".counter");
      const vals = [overview.total_registered_donors||0, overview.verified_hospitals||0, overview.registered_bloodbanks||0, overview.active_emergencies||0, overview.total_blood_units||0, overview.total_donations_processed||0];
      counters.forEach((c, i) => { if (vals[i] !== undefined) { c.dataset.count = vals[i]; c.textContent = '0'; } });
      // Animate
      counters.forEach(c => { const t = Number(c.dataset.count||"0"), dur = 1100, st = performance.now();
        function tick(now) { const p = Math.min((now-st)/dur,1), e = 1-Math.pow(1-p,3); c.textContent = Math.round(t*e).toLocaleString("en-IN"); if(p<1) requestAnimationFrame(tick); }
        requestAnimationFrame(tick);
      });
      // Emergency counts
      const ec = overview.active_emergencies||0;
      const topEc = $("#topEmergencyCount"); if(topEc) topEc.textContent = ec;
      const sideEc = $("#sideEmergencyCount"); if(sideEc) sideEc.textContent = ec;
      // Signal cards
      const signals = $$(".signal-card");
      if (signals[0]) signals[0].querySelector("p").textContent = `${overview.total_blood_units||0} units available`;
      if (signals[1]) signals[1].querySelector("p").textContent = `${overview.verified_hospitals||0} verified facilities`;
      if (signals[2]) signals[2].querySelector("p").textContent = `${overview.total_registered_donors||0} registered donors`;
    }

    // ── SIDEBAR ADMIN INFO ──
    const profile = await api("admin/profile");
    if (profile) {
      const nm = profile.admin_name || "Super Admin", ini = nm.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
      $$(".avatar").forEach(a => { if(a.closest('.admin-mini')||a.closest('.profile-button')) a.textContent = ini; });
      const nameEl = $(".admin-mini strong"); if(nameEl) nameEl.textContent = nm;
      $(".profile-copy").textContent = nm;
    }

    // ── USERS TABLE ──
    const usersBody = $("#usersTable tbody");
    if (usersBody) {
      const allUsers = [];
      (donors||[]).forEach(d => allUsers.push({ name: d.full_name, loc: d.location||d.address||'', role: 'donor', status: d.verification_status==='suspended'?'Blocked':'Active', verified: d.verification_status==='verified', id: d._id, time: ago(d.updated_at||d.created_at) }));
      (facilities||[]).filter(f=>f.entity_type==='hospital').forEach(h => allUsers.push({ name: h.hospital_name, loc: h.location||h.address||'', role: 'hospital', status: h.verified_status==='suspended'?'Blocked':'Active', verified: h.verified_status==='verified', id: h._id, time: ago(h.updated_at||h.created_at) }));
      (facilities||[]).filter(f=>f.entity_type==='bloodbank').forEach(b => allUsers.push({ name: b.bloodbank_name, loc: b.location||b.address||'', role: 'blood bank', status: b.verified_status==='suspended'?'Blocked':'Active', verified: b.verified_status==='verified', id: b._id, time: ago(b.updated_at||b.created_at) }));
      if (allUsers.length) {
        usersBody.innerHTML = allUsers.map(u => `<tr data-role="${u.role}" data-search="${u.name} ${u.role} ${u.status}"><td><strong>${u.name}</strong><span>${u.loc}</span></td><td>${u.role.charAt(0).toUpperCase()+u.role.slice(1)}</td><td><span class="status ${u.status==='Active'?'success':'danger'}">${u.status}</span></td><td>${u.time}</td><td><span class="${u.verified?'verified-pill':'status warning'}">${u.verified?'Verified':'Pending'}</span></td><td class="table-actions"><button>Edit</button><button class="toggle-suspend">${u.status==='Blocked'?'Unblock':'Suspend'}</button><button>View Profile</button></td></tr>`).join('');
        $$(".toggle-suspend").forEach(b => b.addEventListener("click", () => { const r=b.closest("tr"), s=$(".status",r), blocked=b.textContent.trim()==="Suspend"; b.textContent=blocked?"Unblock":"Suspend"; s.textContent=blocked?"Blocked":"Active"; s.classList.toggle("success",!blocked); s.classList.toggle("danger",blocked); showToast(blocked?"User suspended.":"User restored."); }));
      } else { usersBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;color:#888">No users found</td></tr>'; }
    }

    // ── DONORS VIEW ──
    const donorCards = $$(".management-card strong", $("#donorsView"));
    if (donorCards.length >= 3 && donors) {
      const eligible = (donors||[]).filter(d=>d.eligible_to_donate!==false).length;
      donorCards[0].textContent = eligible;
      donorCards[1].textContent = overview?.total_donations_processed || 0;
      donorCards[2].textContent = donors.length ? Math.round((donors.filter(d=>d.emergency_responses>0).length/donors.length)*100)+'%' : '0%';
    }
    const donorTbody = $$("#donorsView table tbody");
    if (donorTbody.length && donors) {
      donorTbody[0].innerHTML = (donors||[]).length ? donors.map(d => `<tr data-search="${d.full_name} ${d.blood_group}"><td><strong>${d.full_name||'Unknown'}</strong><span>${d.location||''}</span></td><td>${d.blood_group||'?'}</td><td><span class="status ${d.eligible_to_donate!==false?'success':'danger'}">${d.eligible_to_donate!==false?'Eligible':'Deferred'}</span></td><td>${ago(d.last_donation_date)||'Never'}</td><td><span class="${d.verification_status==='verified'?'verified-pill':'status warning'}">${d.verification_status==='verified'?'Verified':'Pending'}</span></td><td class="table-actions"><button>View Profile</button><button>Activity Logs</button></td></tr>`).join('') : '<tr><td colspan="6" style="text-align:center;padding:30px;color:#888">No donors</td></tr>';
    }

    // ── HOSPITALS VIEW ──
    const hospGrid = $$("#hospitalsView .facility-grid");
    if (hospGrid.length) {
      const hosps = (facilities||[]).filter(f=>f.entity_type==='hospital');
      hospGrid[0].innerHTML = hosps.length ? hosps.map(h => `<article class="facility-card" data-search="${h.hospital_name} ${h.verified_status}"><div><span class="material-symbols-rounded">local_hospital</span><strong>${h.hospital_name}</strong><p>${h.location||h.address||''}</p></div><span class="status ${h.verified_status==='verified'?'success':'warning'}">${h.verified_status==='verified'?'Verified':h.verified_status||'Pending'}</span></article>`).join('') : '<p style="text-align:center;color:#888;padding:40px">No hospitals registered</p>';
    }

    // ── BLOOD BANKS VIEW ──
    const bbGrid = $$("#bloodbanksView .facility-grid");
    if (bbGrid.length) {
      const bbs = (facilities||[]).filter(f=>f.entity_type==='bloodbank');
      bbGrid[0].innerHTML = bbs.length ? bbs.map(b => `<article class="facility-card" data-search="${b.bloodbank_name} ${b.verified_status}"><div><span class="material-symbols-rounded">inventory_2</span><strong>${b.bloodbank_name}</strong><p>${b.location||b.address||''}</p></div><span class="status ${b.verified_status==='verified'||b.verified_status==='approved'?'success':'warning'}">${b.verified_status||'Pending'}</span></article>`).join('') : '<p style="text-align:center;color:#888;padding:40px">No blood banks registered</p>';
    }

    // ── EMERGENCY VIEW ──
    const emgBoard = $(".emergency-board");
    if (emgBoard) {
      const eList = emergencies || [];
      if (!eList.length) { emgBoard.innerHTML = '<p style="text-align:center;color:#888;padding:40px">No active emergencies</p>'; }
      else {
        emgBoard.innerHTML = eList.map(e => {
          const u = e.urgency_level||'normal', cls = u==='critical'?'critical':u==='high'?'urgent':'moderate';
          return `<article class="request-card ${cls}" data-search="${e.hospital_name} ${e.blood_group_needed} ${u}"><div class="request-main"><span class="priority">${u.charAt(0).toUpperCase()+u.slice(1)}</span><h3>${e.hospital_name||'Hospital'}</h3><p><strong>${e.blood_group_needed||'?'}</strong> blood needed - ${e.units_needed||1} units</p></div><div class="request-actions"><button>Approve</button><button>Close Request</button></div></article>`;
        }).join('');
        $$(".request-actions button").forEach(b => b.addEventListener("click", () => { if(b.textContent==="Close Request"){b.closest(".request-card").classList.add("is-hidden");showToast("Emergency closed.");} else showToast(`${b.textContent} action queued.`); }));
      }
    }

    // ── INVENTORY VIEW ──
    const invGrid = $(".inventory-grid");
    if (invGrid) {
      const inv = inventory || [];
      if (!inv.length) { invGrid.innerHTML = '<p style="text-align:center;color:#888;padding:40px">No blood inventory data</p>'; }
      else {
        invGrid.innerHTML = inv.map(i => {
          const st = i.inventory_status||(i.available_units>=15?'healthy':i.available_units>=6?'low':'critical');
          return `<article class="inventory-card ${st}" data-search="${i.blood_group} ${st}"><strong>${i.blood_group}</strong><span>${i.available_units||0} units</span><p>${st.charAt(0).toUpperCase()+st.slice(1)}${i.facility_name?' · '+i.facility_name:''}</p></article>`;
        }).join('');
      }
    }

    // ── BLOCKCHAIN VERIFICATION VIEW ──
    const vCards = $$(".verification-card");
    if (vCards.length >= 3) {
      const bLogs = blockchain || [], ci = chainInfo || {};
      vCards[0].querySelector("p").textContent = `${bLogs.length} verified records on ${ci.total_blocks||0} blocks.`;
      vCards[0].querySelector(".status").textContent = ci.chain_initialized ? "Operational" : "Offline";
      vCards[2].querySelector("p").textContent = `${bLogs.length} secure transaction logs stored.`;
    }

    // ── NOTIFICATIONS VIEW ──
    const nList = $$("#notificationsView .notification-list");
    if (nList.length) {
      const ns = notifs || [];
      if (!ns.length) { nList[0].innerHTML = '<p style="text-align:center;color:#888;padding:40px">No notifications</p>'; }
      else {
        nList[0].innerHTML = ns.map(n => {
          const cls = n.notification_type==='emergency_alert'?'critical':n.notification_type==='system'?'neutral':'success';
          const icon = {emergency_alert:'emergency',system:'cloud_sync',donation_update:'check_circle'}[n.notification_type]||'notifications';
          return `<article class="notification-item ${cls}" data-search="${n.title} ${n.message}"><span class="material-symbols-rounded">${icon}</span><div><strong>${n.title||''}</strong><p>${n.message||''}</p><small>${ago(n.created_at)}</small></div></article>`;
        }).join('');
      }
    }

    // ── NOTIFICATION DRAWER ──
    const drawerList = $(".notification-drawer .notification-list");
    if (drawerList) {
      const ns = notifs || [];
      if (!ns.length) { drawerList.innerHTML = '<p style="text-align:center;color:#888;padding:20px">No notifications</p>'; }
      else {
        drawerList.innerHTML = ns.slice(0, 5).map(n => {
          const cls = n.notification_type==='emergency_alert'?'critical':'neutral';
          const icon = {emergency_alert:'emergency',system:'cloud_done'}[n.notification_type]||'notifications';
          return `<article class="notification-item ${cls}"><span class="material-symbols-rounded">${icon}</span><div><strong>${n.title||''}</strong><p>${n.message||''}</p><small>${ago(n.created_at)}</small></div></article>`;
        }).join('');
      }
    }

    // ── REPORTS VIEW (update with live stats) ──
    if (reports) {
      const rCards = $$(".report-card p");
      if(rCards[0]) rCards[0].textContent = `${reports.total_registered_donors||0} registrations, eligibility tracking.`;
      if(rCards[1]) rCards[1].textContent = `${reports.total_emergencies||0} total, ${reports.resolved_emergencies||0} resolved.`;
      if(rCards[2]) rCards[2].textContent = `${reports.total_blood_units_available||0} units, ${reports.expiring_units||0} expiring.`;
      if(rCards[3]) rCards[3].textContent = `${overview?.verified_hospitals||0} hospitals, verification tracking.`;
      if(rCards[4]) rCards[4].textContent = `${reports.total_donations_processed||0} donations, ${reports.verified_donations||0} verified.`;
    }
  }

  initLogin();
  initDashboard();
})();
