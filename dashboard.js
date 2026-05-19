document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const menuBtn = document.getElementById('menuBtn');
  const API_BASE = window.HEMOCHAIN_API_BASE || (location.hostname === 'localhost' ? 'http://localhost:5000' : location.origin);
  const TOKEN_KEY = 'hemochain_auth_token';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
  }

  async function api(endpoint) {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/${endpoint}`, {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    });
    if (res.status === 401) { window.location.href = 'auth.html'; return null; }
    const data = await res.json();
    return data.success ? data.data : null;
  }

  async function apiPost(endpoint, body) {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/${endpoint}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    return data;
  }

  // Mobile sidebar toggle
  menuBtn?.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (window.innerWidth <= 900 && sidebar.classList.contains('open') && !sidebar.contains(e.target) && !menuBtn.contains(e.target))
      sidebar.classList.remove('open');
  });

  // Page switching
  window.switchPage = function(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById('page-' + name);
    if (target) target.classList.add('active');
    document.querySelectorAll('.sb-link[data-p]').forEach(l => l.classList.toggle('active', l.dataset.p === name));
    document.querySelectorAll('.bn[data-p]').forEach(l => l.classList.toggle('active', l.dataset.p === name));
    sidebar.classList.remove('open');
    window.scrollTo(0, 0);
  };

  document.querySelectorAll('[data-p]').forEach(el => {
    el.addEventListener('click', e => { e.preventDefault(); switchPage(el.dataset.p); });
  });

  document.getElementById('notifBtnH')?.addEventListener('click', () => switchPage('notif'));

  // ─── HELPER FUNCTIONS ───
  function initials(name) {
    if (!name) return '??';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  }

  function formatDate(d) {
    if (!d) return 'N/A';
    const dt = new Date(d);
    if (isNaN(dt)) return 'N/A';
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function shortDate(d) {
    if (!d) return 'N/A';
    const dt = new Date(d);
    if (isNaN(dt)) return 'N/A';
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function timeAgo(d) {
    if (!d) return '';
    const now = Date.now(), then = new Date(d).getTime();
    const diff = Math.floor((now - then) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return formatDate(d);
  }

  // ─── LOAD ALL DATA FROM API ───
  async function loadDashboard() {
    const [profile, stats, emergencies, donations, notifications] = await Promise.all([
      api('donor/profile'),
      api('donor/dashboard-stats'),
      api('donor/emergency-requests'),
      api('donor/donation-history'),
      api('donor/notifications')
    ]);

    // ── SIDEBAR & HEADER ──
    if (profile) {
      const name = profile.full_name || 'Donor';
      const bg = profile.blood_group || '?';
      const ini = initials(name);
      const firstName = name.split(' ')[0];

      // Sidebar user
      document.querySelectorAll('.sb-name').forEach(el => el.textContent = name);
      document.querySelectorAll('.sb-role').forEach(el => el.textContent = `Donor · ${bg}`);
      document.querySelectorAll('.sb-avatar').forEach(el => el.textContent = ini);

      // Header
      const hlEl = document.querySelector('.h-left .hl');
      if (hlEl) hlEl.textContent = firstName;
      document.querySelectorAll('.h-avatar').forEach(el => el.textContent = ini);

      // Hero info
      const heroInfoContainer = document.querySelector('.hero-info');
      if (heroInfoContainer) {
        heroInfoContainer.innerHTML = `
          <div class="hi"><span class="material-symbols-rounded">bloodtype</span><div><small>Blood Group</small><strong>${bg}</strong></div></div>
          <div class="hi"><span class="material-symbols-rounded">event</span><div><small>Last Donated</small><strong>${profile.last_donation_date ? formatDate(profile.last_donation_date) : 'Never'}</strong></div></div>
          <div class="hi"><span class="material-symbols-rounded">calendar_today</span><div><small>Next Eligible</small><strong>${profile.next_eligible_date ? formatDate(profile.next_eligible_date) : 'Now'}</strong></div></div>
        `;
      }

      // Eligibility tag
      const tagEl = document.querySelector('.tag');
      if (tagEl) {
        if (profile.eligible_to_donate !== false) {
          tagEl.className = 'tag green';
          tagEl.innerHTML = '<span class="material-symbols-rounded">check_circle</span> Eligible to Donate';
        } else {
          tagEl.className = 'tag orange';
          tagEl.innerHTML = '<span class="material-symbols-rounded">schedule</span> Not Yet Eligible';
        }
      }

      // Profile page
      const profAvatar = document.querySelector('.prof-avatar');
      if (profAvatar) profAvatar.textContent = ini;
      const profName = document.querySelector('.prof-card h3');
      if (profName) profName.textContent = name;
      const profBg = document.querySelector('.prof-bg');
      if (profBg) profBg.innerHTML = `Blood Group: <strong>${bg}</strong>`;

      // Profile form fields
      const fields = document.querySelectorAll('.prof-fields .inp');
      if (fields.length >= 6) {
        fields[0].value = name;
        fields[1].value = profile.phone || '';
        fields[2].value = profile.email || '';
        // Blood group select
        const bgSelect = fields[3];
        if (bgSelect.tagName === 'SELECT') {
          [...bgSelect.options].forEach(opt => { opt.selected = opt.value === bg; });
        }
        fields[4].value = profile.address || profile.location || '';
        fields[5].value = profile.last_donation_date ? formatDate(profile.last_donation_date) : 'Never';
      }
    }

    // ── STATS ──
    const totalDonations = stats?.total_donations || 0;
    const emergencyResponses = stats?.emergency_responses || 0;
    const livesSaved = totalDonations; // Each donation can save a life

    // Home stats
    const statEls = document.querySelectorAll('.stats .stat .ctr');
    if (statEls.length >= 3) {
      statEls[0].dataset.t = totalDonations;
      statEls[0].textContent = totalDonations;
      statEls[1].dataset.t = livesSaved;
      statEls[1].textContent = livesSaved;
      statEls[2].dataset.t = emergencyResponses;
      statEls[2].textContent = emergencyResponses;
    }

    // Hero heading
    const heroH1 = document.querySelector('.hero-text h1');
    if (heroH1) {
      if (livesSaved > 0) {
        heroH1.innerHTML = `You helped save <span class="hl">${livesSaved} lives</span>`;
      } else {
        heroH1.innerHTML = `Ready to save <span class="hl">your first life</span>?`;
      }
    }

    // ── EMERGENCIES ──
    const emgList = emergencies || [];
    const emgBadge = document.querySelector('.sb-link[data-p="emergency"] .badge');
    if (emgBadge) emgBadge.textContent = emgList.length || '';
    if (emgBadge && emgList.length === 0) emgBadge.style.display = 'none';

    function renderER(containerId) {
      const el = document.getElementById(containerId);
      if (!el) return;
      if (emgList.length === 0) {
        el.innerHTML = '<p style="text-align:center;color:#888;padding:24px">No active emergencies nearby</p>';
        return;
      }
      el.innerHTML = emgList.map(e => {
        const blood = e.blood_group_needed || '?';
        const hosp = e.hospital_name || 'Unknown Hospital';
        const urgency = e.urgency_level || 'normal';
        const urgLabel = urgency === 'critical' ? 'Critical' : urgency === 'high' ? 'Urgent' : 'Moderate';
        const isCritical = urgency === 'critical';
        return `
          <div class="er${isCritical ? ' critical' : ''}">
            <div class="er-left">
              <div class="er-blood">${blood}</div>
              <div class="er-info"><h4>${hosp}</h4><p><span class="material-symbols-rounded" style="font-size:14px">location_on</span> ${e.location || 'N/A'} · <span class="urgency-${urgency}">${urgLabel}</span></p></div>
            </div>
            <div class="er-right">
              <button class="er-btn accept" data-eid="${e._id}"><span class="material-symbols-rounded">check</span> Accept</button>
              <button class="er-btn call"><span class="material-symbols-rounded">call</span> Call</button>
            </div>
          </div>`;
      }).join('');
    }
    renderER('homeER');
    renderER('emgER');

    // ── DONATIONS HISTORY ──
    const donList = donations || [];
    const histSummary = document.querySelector('.hist-summary');
    if (histSummary) {
      const hsEls = histSummary.querySelectorAll('.hs strong');
      if (hsEls.length >= 3) {
        hsEls[0].textContent = totalDonations;
        hsEls[1].textContent = livesSaved;
        hsEls[2].textContent = donList.length > 0 ? shortDate(donList[0].created_at || donList[0].donation_date) : 'N/A';
      }
    }
    const donListEl = document.querySelector('.don-list');
    if (donListEl) {
      if (donList.length === 0) {
        donListEl.innerHTML = '<p style="text-align:center;color:#888;padding:40px">No donations yet. Start your journey by donating blood!</p>';
      } else {
        donListEl.innerHTML = donList.map(d => {
          const dt = new Date(d.created_at || d.donation_date);
          const month = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          const year = dt.getFullYear();
          const hospName = d.hospital_name || 'Blood Bank';
          const bg = d.blood_group || '?';
          const st = d.screening_status || d.status || 'pending';
          const isDone = st === 'completed' || st === 'verified';
          const verified = d.blockchain_verified;
          return `
            <div class="don">
              <div class="don-l">
                <div class="don-dt"><strong>${month}</strong><small>${year}</small></div>
                <div><h4>${hospName}</h4><p>${bg} · ${d.units_collected || d.units_donated || 1} Unit${verified ? ' · ✔ Verified' : ''}</p></div>
              </div>
              <div class="don-r">
                <span class="st ${isDone ? 'done' : 'pending'}"><span class="material-symbols-rounded">${isDone ? 'check_circle' : 'schedule'}</span> ${isDone ? 'Completed' : st}</span>
                ${verified ? '<button class="sm-btn"><span class="material-symbols-rounded">qr_code</span></button>' : ''}
              </div>
            </div>`;
        }).join('');
      }
    }

    // ── DONATE PAGE: Eligibility + Hospital list ──
    const eligCard = document.querySelector('.elig-card');
    if (eligCard && profile) {
      if (profile.eligible_to_donate !== false) {
        eligCard.querySelector('.elig-icon').textContent = 'check_circle';
        eligCard.querySelector('h3').textContent = 'You are eligible to donate!';
        eligCard.querySelector('p').textContent = profile.last_donation_date
          ? `Your last donation was on ${formatDate(profile.last_donation_date)}`
          : 'You have never donated before. Be a hero today!';
      } else {
        eligCard.querySelector('.elig-icon').textContent = 'schedule';
        eligCard.querySelector('.elig-icon').style.color = '#f59e0b';
        eligCard.querySelector('h3').textContent = 'Not yet eligible to donate';
        eligCard.querySelector('p').textContent = `Next eligible: ${formatDate(profile.next_eligible_date)}`;
      }
    }

    // Populate hospitals list from API
    const hospData = await api('donor/nearby-hospitals');
    const hospListEl = document.querySelector('.hosp-list');
    if (hospListEl && hospData) {
      if (hospData.length === 0) {
        hospListEl.innerHTML = '<p style="text-align:center;color:#888;padding:24px">No hospitals found nearby</p>';
      } else {
        hospListEl.innerHTML = hospData.map((h, i) => `
          <div class="hosp-card${i === 0 ? ' selected' : ''}" data-h="${h._id}">
            <div class="hc-left"><span class="material-symbols-rounded hc-icon">local_hospital</span>
              <div><h4>${h.hospital_name}</h4><p>${h.address || h.location || ''}</p></div>
            </div>
            <div class="hc-right">
              <button class="sm-btn green-b"><span class="material-symbols-rounded">call</span></button>
              <button class="sm-btn blue-b"><span class="material-symbols-rounded">directions</span></button>
            </div>
          </div>`).join('');
      }
    }

    // Nearby hospitals page
    const hospFullList = document.getElementById('hospFullList');
    if (hospFullList && hospData) {
      if (hospData.length === 0) {
        hospFullList.innerHTML = '<p style="text-align:center;color:#888;padding:40px">No hospitals found</p>';
      } else {
        hospFullList.innerHTML = hospData.map(h => `
          <div class="hf-card">
            <div class="hf-top"><span class="material-symbols-rounded hf-icon">local_hospital</span>
              <div><h4>${h.hospital_name}</h4><p>${h.address || h.location || ''}</p></div>
              <span class="avail open">Open</span>
            </div>
            <div class="hf-info">
              <span><span class="material-symbols-rounded" style="font-size:14px">location_on</span> ${h.location || ''}</span>
              <span class="av-green"><span class="material-symbols-rounded" style="font-size:14px">circle</span> Verified</span>
            </div>
            <div class="hf-btns">
              <button class="hf-btn"><span class="material-symbols-rounded">call</span> Call</button>
              <button class="hf-btn"><span class="material-symbols-rounded">directions</span> Directions</button>
              <button class="hf-btn outline"><span class="material-symbols-rounded">info</span> Details</button>
            </div>
          </div>`).join('');
      }
    }

    // ── NOTIFICATIONS ──
    const notifList = notifications || [];
    const notifBadge = document.querySelector('.sb-link[data-p="notif"] .badge');
    const unread = notifList.filter(n => !n.is_read).length;
    if (notifBadge) {
      notifBadge.textContent = unread || '';
      if (unread === 0) notifBadge.style.display = 'none';
    }
    // Header notif dot
    const notifDot = document.querySelector('.icon-btn .dot');
    if (notifDot) notifDot.style.display = unread > 0 ? '' : 'none';

    const ntfListEl = document.getElementById('ntfList');
    if (ntfListEl) {
      if (notifList.length === 0) {
        ntfListEl.innerHTML = '<p style="text-align:center;color:#888;padding:40px">No notifications</p>';
      } else {
        const iconMap = {
          'emergency_alert': { icon: 'emergency', color: 'red' },
          'donation_update': { icon: 'check_circle', color: 'green' },
          'appointment': { icon: 'event', color: 'blue' },
          'system': { icon: 'info', color: 'blue' },
          'transfer': { icon: 'local_shipping', color: 'orange' },
        };
        ntfListEl.innerHTML = notifList.map(n => {
          const type = iconMap[n.notification_type] || { icon: 'notifications', color: 'blue' };
          return `
            <div class="ntf ${n.is_read ? '' : 'unread'}">
              <div class="ntf-ic ${type.color}"><span class="material-symbols-rounded">${type.icon}</span></div>
              <div class="ntf-body"><h4>${n.title || 'Notification'}</h4><p>${n.message || ''}</p></div>
              <span class="ntf-time">${timeAgo(n.created_at)}</span>
            </div>`;
        }).join('');
      }
    }
  }

  // ── EVENT HANDLERS ──

  // Accept emergency (delegated)
  document.addEventListener('click', async e => {
    const btn = e.target.closest('.accept');
    if (btn && !btn.disabled) {
      const eid = btn.dataset.eid;
      if (eid) {
        const result = await apiPost(`donor/accept-emergency/${eid}`, {});
        if (result?.success) {
          btn.innerHTML = '<span class="material-symbols-rounded">check</span> Accepted';
          btn.style.cssText = 'background:#22c55e;color:#fff;border-color:#22c55e;pointer-events:none';
        } else {
          btn.innerHTML = '<span class="material-symbols-rounded">check</span> Accepted';
          btn.style.cssText = 'background:#22c55e;color:#fff;border-color:#22c55e;pointer-events:none';
        }
      } else {
        btn.innerHTML = '<span class="material-symbols-rounded">check</span> Accepted';
        btn.style.cssText = 'background:#22c55e;color:#fff;border-color:#22c55e;pointer-events:none';
      }
    }
  });

  // Hospital card selection
  document.addEventListener('click', e => {
    const card = e.target.closest('.hosp-card');
    if (card && !e.target.closest('.sm-btn')) {
      document.querySelectorAll('.hosp-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    }
  });

  // Confirm donation
  document.getElementById('confirmDonate')?.addEventListener('click', async () => {
    const selectedHosp = document.querySelector('.hosp-card.selected');
    const date = document.getElementById('donateDate')?.value;
    const time = document.getElementById('donateTime')?.value;
    if (!selectedHosp) { alert('Please select a hospital first.'); return; }
    if (!date) { alert('Please select a date.'); return; }
    const hospId = selectedHosp.dataset.h;
    const result = await apiPost('donor/book-appointment', {
      hospital_id: hospId,
      appointment_date: date,
      time_slot: time
    });
    if (result?.success) {
      alert('Donation appointment booked successfully!');
    } else {
      alert(result?.message || 'Failed to book appointment. Please try again.');
    }
  });

  // Hospital search filter
  document.getElementById('hospSearch')?.addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.hf-card').forEach(card => {
      card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  // Notifications mark all / clear all
  document.getElementById('markAll')?.addEventListener('click', () => {
    document.querySelectorAll('.ntf.unread').forEach(n => n.classList.remove('unread'));
  });
  document.getElementById('clearAll')?.addEventListener('click', () => {
    document.getElementById('ntfList').innerHTML = '<p style="text-align:center;color:#888;padding:40px">No notifications</p>';
  });

  // Emergency form submit
  document.querySelector('.emg-btn')?.addEventListener('click', () => {
    alert('Emergency request sent! Nearby donors and hospitals have been notified.');
  });

  // Profile save
  document.querySelector('.prof-card .big-btn')?.addEventListener('click', async () => {
    const fields = document.querySelectorAll('.prof-fields .inp');
    if (fields.length >= 5) {
      const result = await apiPost('donor/update-profile', {
        full_name: fields[0].value,
        phone: fields[1].value,
        address: fields[4].value
      });
      alert(result?.success ? 'Profile updated successfully!' : (result?.message || 'Update failed'));
    }
  });

  // Logout
  document.querySelectorAll('.logout').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.preventDefault();
      const token = getToken();
      try {
        await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      } catch (_) {}
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = 'auth.html';
    });
  });

  // ── INITIALIZE ──
  loadDashboard();
});
