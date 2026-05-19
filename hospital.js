document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const API = (window.HEMOCHAIN_API_BASE || (location.hostname === 'localhost' ? 'http://localhost:5000' : location.origin)) + '/api';
  const TK = () => localStorage.getItem('hemochain_auth_token') || sessionStorage.getItem('hemochain_auth_token');

  async function get(ep) {
    const r = await fetch(`${API}/${ep}`, { headers: { Authorization: `Bearer ${TK()}` } });
    if (r.status === 401) { location.href = 'auth.html'; return null; }
    const d = await r.json(); return d.success ? d.data : null;
  }

  document.getElementById('menuBtn')?.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (innerWidth <= 900 && sidebar.classList.contains('open') && !sidebar.contains(e.target) && !e.target.closest('.menu-btn')) sidebar.classList.remove('open');
  });

  window.switchPage = name => {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + name)?.classList.add('active');
    document.querySelectorAll('.sb-link[data-p]').forEach(l => l.classList.toggle('active', l.dataset.p === name));
    document.querySelectorAll('.bn[data-p]').forEach(l => l.classList.toggle('active', l.dataset.p === name));
    sidebar.classList.remove('open'); scrollTo(0, 0);
  };
  document.querySelectorAll('[data-p]').forEach(el => el.addEventListener('click', e => { e.preventDefault(); switchPage(el.dataset.p); }));

  const ini = n => (n||'??').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
  const fmtD = d => { if(!d) return 'N/A'; const t=new Date(d); return isNaN(t)?'N/A':t.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}); };
  const ago = d => { if(!d) return ''; const s=Math.floor((Date.now()-new Date(d))/1e3); if(s<60) return 'Just now'; if(s<3600) return Math.floor(s/60)+'m ago'; if(s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago'; };
  const sLbl = { healthy:'Good Stock', good:'Good Stock', low:'Low Stock', critical:'Critical' };

  async function load() {
    const [prof, ov, inv, emg, appt, donors, notifs] = await Promise.all([
      get('hospital/profile'), get('hospital/dashboard-overview'), get('hospital/inventory'),
      get('hospital/emergency-requests'), get('hospital/appointments'), get('hospital/donors'), get('hospital/notifications')
    ]);

    // Sidebar + Header
    if (prof) {
      const nm = prof.hospital_name||'Hospital', i = ini(nm);
      document.querySelectorAll('.sb-name').forEach(e=>e.textContent=nm);
      document.querySelectorAll('.sb-role').forEach(e=>e.textContent=prof.verified_status==='verified'?'Verified Hospital':'Pending');
      document.querySelectorAll('.sb-avatar,.h-avatar').forEach(e=>e.textContent=i);
      const hl = document.querySelector('.h-left .hl'); if(hl) hl.textContent=nm;
      // Profile page
      const pf = document.querySelectorAll('.prof .inp');
      if(pf.length>=4){ pf[0].value=nm; pf[1].value=prof.phone||''; pf[2].value=prof.email||''; pf[3].value=prof.address||''; }
    }

    // Stats
    if (ov) {
      const vals = [ov.total_blood_units||0, ov.active_emergencies||0, ov.total_donors||0, ov.scheduled_appointments||0];
      document.querySelectorAll('.stats .stat .ctr').forEach((e,i) => { if(vals[i]!==undefined){ e.dataset.t=vals[i]; e.textContent=vals[i]; }});
    }

    // Inventory
    const invArr = inv||[];
    function renderInv(id) {
      const el = document.getElementById(id); if(!el) return;
      if(!invArr.length){ el.innerHTML='<p style="text-align:center;color:#888;padding:24px">No inventory data</p>'; return; }
      el.innerHTML = invArr.map(i => {
        const st = i.inventory_status||(i.available_units>=15?'good':i.available_units>=6?'low':'critical');
        return `<div class="inv-card"><div class="inv-bg">${i.blood_group}</div><div class="inv-units">${i.available_units||0}</div><div class="inv-label">units</div><span class="inv-status ${st}">${sLbl[st]||st}</span></div>`;
      }).join('');
    }
    renderInv('homeInv'); renderInv('invFull');

    // Emergencies
    const eList = emg||[];
    const eBadge = document.querySelector('.sb-link[data-p="emergency"] .badge');
    if(eBadge){ eBadge.textContent=eList.length||''; if(!eList.length) eBadge.style.display='none'; }
    function renderEmg(id) {
      const el = document.getElementById(id); if(!el) return;
      if(!eList.length){ el.innerHTML='<p style="text-align:center;color:#888;padding:24px">No active emergencies</p>'; return; }
      el.innerHTML = eList.map(e => {
        const u=e.urgency_level||'normal', l=u==='critical'?'Critical':u==='high'?'Urgent':'Moderate';
        return `<div class="er${u==='critical'?' critical':''}"><div class="er-left"><div class="er-blood">${e.blood_group_needed||'?'}</div><div class="er-info"><h4>${e.units_needed||1} units · ${e.patient_condition||'Patient'}</h4><p><span class="urgency-${u}">${l}</span> · ${ago(e.created_at)}</p></div></div><div class="er-right"><button class="er-btn accept"><span class="material-symbols-rounded">check</span> Approve</button><button class="er-btn call"><span class="material-symbols-rounded">call</span> Contact</button></div></div>`;
      }).join('');
    }
    renderEmg('homeEmg'); renderEmg('emgList');

    // Donors
    const dList = donors||[];
    function renderDonors(q='',bg='') {
      const el = document.getElementById('donorList'); if(!el) return;
      const f = dList.filter(d => ((d.full_name||'').toLowerCase().includes(q.toLowerCase())||(d.blood_group||'').toLowerCase().includes(q.toLowerCase())) && (!bg||d.blood_group===bg));
      if(!f.length){ el.innerHTML='<p style="text-align:center;color:#888;padding:30px">No donors found</p>'; return; }
      el.innerHTML = f.map(d => `<div class="donor"><div class="d-avatar">${ini(d.full_name)}</div><div class="d-info"><h4>${d.full_name||'Unknown'}</h4><p>${d.phone||''} · Last: ${fmtD(d.last_donation_date)}</p></div><div class="d-meta"><span class="d-bg">${d.blood_group||'?'}</span><span class="d-status ${d.eligible_to_donate!==false?'available':'unavailable'}">${d.eligible_to_donate!==false?'Available':'Unavailable'}</span></div><div class="d-btns"><button class="btn-sm-o"><span class="material-symbols-rounded">call</span> Call</button><button class="btn-approve"><span class="material-symbols-rounded">check</span> Approve</button></div></div>`).join('');
    }
    renderDonors();
    document.getElementById('donorSearch')?.addEventListener('input', e => renderDonors(e.target.value, document.getElementById('bgFilter')?.value||''));
    document.getElementById('bgFilter')?.addEventListener('change', e => renderDonors(document.getElementById('donorSearch')?.value||'', e.target.value));

    // Nearby donors
    const nbEl = document.getElementById('nearbyList');
    if(nbEl) {
      const avail = dList.filter(d=>d.eligible_to_donate!==false).slice(0,6);
      nbEl.innerHTML = avail.length ? avail.map(n => `<div class="nb"><div class="nb-top"><div class="nb-av">${ini(n.full_name)}</div><div><h4>${n.full_name}</h4><p>${n.blood_group||'?'} · Available</p></div><span class="nb-dist"><span class="material-symbols-rounded" style="font-size:14px">location_on</span>${n.location||'N/A'}</span></div><div class="nb-btns"><button class="er-btn call"><span class="material-symbols-rounded">call</span> Call</button><button class="er-btn accept"><span class="material-symbols-rounded">send</span> Request</button></div></div>`).join('') : '<p style="text-align:center;color:#888;padding:24px">No nearby donors</p>';
    }

    // Appointments
    const aEl = document.getElementById('apptList');
    if(aEl) {
      const aList = appt||[];
      if(!aList.length){ aEl.innerHTML='<p style="text-align:center;color:#888;padding:30px">No appointments</p>'; }
      else {
        const si={confirmed:'check_circle',pending:'schedule',cancelled:'cancel'}, sl={confirmed:'Confirmed',pending:'Pending',cancelled:'Cancelled'};
        aEl.innerHTML = aList.map(a => { const dt=new Date(a.appointment_date), m=dt.toLocaleDateString('en-US',{month:'short',day:'numeric'}), y=dt.getFullYear(), s=a.appointment_status||'pending';
          return `<div class="appt"><div class="ap-date"><strong>${m}</strong><small>${y}</small></div><div class="ap-info"><h4>${a.donor_name||'Donor'}</h4><p>${a.blood_group||'?'} · ${a.time_slot||''}</p></div><span class="ap-status ${s}"><span class="material-symbols-rounded">${si[s]||'schedule'}</span> ${sl[s]||s}</span><div class="ap-btns"><button class="btn-approve"><span class="material-symbols-rounded">check</span> Approve</button></div></div>`;
        }).join('');
      }
    }

    // Notifications
    const nList = notifs||[], unread = nList.filter(n=>!n.is_read).length;
    const nBadge = document.querySelector('.sb-link[data-p="notif"] .badge');
    if(nBadge){ nBadge.textContent=unread||''; if(!unread) nBadge.style.display='none'; }
    const ntf = document.getElementById('ntfList');
    if(ntf) {
      if(!nList.length) ntf.innerHTML='<p style="text-align:center;color:#888;padding:40px">No notifications</p>';
      else ntf.innerHTML = nList.map(n => {
        const ic = {emergency_alert:{i:'emergency',c:'red'},system:{i:'info',c:'blue'},donation_update:{i:'check_circle',c:'green'}}[n.notification_type]||{i:'notifications',c:'blue'};
        return `<div class="ntf${n.is_read?'':' unread'}"><div class="ntf-ic ${ic.c}"><span class="material-symbols-rounded">${ic.i}</span></div><div class="ntf-body"><h4>${n.title||''}</h4><p>${n.message||''}</p></div><span class="ntf-time">${ago(n.created_at)}</span></div>`;
      }).join('');
    }
  }

  // Event handlers
  document.getElementById('markAll')?.addEventListener('click', () => document.querySelectorAll('.ntf.unread').forEach(n=>n.classList.remove('unread')));
  document.getElementById('clearAll')?.addEventListener('click', () => { document.getElementById('ntfList').innerHTML='<p style="text-align:center;color:#888;padding:40px">No notifications</p>'; });

  const seen = new Set();
  new IntersectionObserver(entries => entries.forEach(entry => {
    if(entry.isIntersecting && !seen.has(entry.target)) { seen.add(entry.target); const el=entry.target, t=+el.dataset.t; let c=0; const s=Math.max(1,Math.ceil(t/30)); const iv=setInterval(()=>{c+=s;if(c>=t){c=t;clearInterval(iv);}el.textContent=c;},50); }
  }), {threshold:.5}).observe && document.querySelectorAll('.ctr').forEach(c => new IntersectionObserver(en => en.forEach(e => { if(e.isIntersecting&&!seen.has(e.target)){seen.add(e.target);const el=e.target,t=+el.dataset.t;let c=0;const s=Math.max(1,Math.ceil(t/30));const iv=setInterval(()=>{c+=s;if(c>=t){c=t;clearInterval(iv);}el.textContent=c;},50);}}),{threshold:.5}).observe(c));

  document.addEventListener('click', e => {
    const b = e.target.closest('.btn-approve');
    if(b&&!b.disabled){b.innerHTML='<span class="material-symbols-rounded">check</span> Approved';b.style.cssText='background:#22c55e;color:#fff;pointer-events:none';}
    const a = e.target.closest('.accept');
    if(a&&!a.disabled){a.innerHTML='<span class="material-symbols-rounded">check</span> Done';a.style.cssText='background:#22c55e;color:#fff;pointer-events:none';}
  });

  // Modals
  const openM=id=>document.getElementById(id)?.classList.add('on'), closeM=id=>document.getElementById(id)?.classList.remove('on');
  document.getElementById('openUpdateStock')?.addEventListener('click',()=>openM('updateStockModal'));
  document.getElementById('openRequestBlood')?.addEventListener('click',()=>openM('requestBloodModal'));
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>closeM(b.dataset.close)));
  document.querySelectorAll('.modal-overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeM(o.id);}));

  function toast(m,err){let t=document.getElementById('appToast');if(!t){t=document.createElement('div');t.id='appToast';t.className='toast';document.body.appendChild(t);}t.innerHTML=`<span class="material-symbols-rounded" style="color:${err?'#ef4444':'#4ade80'}">${err?'error':'check_circle'}</span>${m}`;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000);}
  document.getElementById('confirmUpdateStock')?.addEventListener('click',()=>{closeM('updateStockModal');toast('Stock update request sent!');});
  document.getElementById('confirmRequestBlood')?.addEventListener('click',()=>{closeM('requestBloodModal');toast('Blood request sent!');});
  document.querySelector('.prof .big-btn')?.addEventListener('click',()=>toast('Profile updated!'));

  load();
});
