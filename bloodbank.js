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
    const [prof, ov, inv, emg, donations, hospReqs, donors, transfers, notifs] = await Promise.all([
      get('bloodbank/profile'), get('bloodbank/dashboard-overview'), get('bloodbank/inventory'),
      get('bloodbank/emergency-requests'), get('bloodbank/donations'), get('bloodbank/hospital-requests'),
      get('bloodbank/donors'), get('bloodbank/transfers'), get('bloodbank/notifications')
    ]);

    // Sidebar + Header
    if (prof) {
      const nm = prof.bloodbank_name||'Blood Bank', i = ini(nm);
      document.querySelectorAll('.sb-name').forEach(e=>e.textContent=nm);
      document.querySelectorAll('.sb-role').forEach(e=>e.textContent=prof.verified_status==='verified'||prof.verified_status==='approved'?'Verified Blood Bank':'Pending');
      document.querySelectorAll('.sb-avatar,.h-avatar').forEach(e=>e.textContent=i);
      const hl = document.querySelector('.h-left .hl'); if(hl) hl.textContent=nm;
      const pf = document.querySelectorAll('.prof .inp');
      if(pf.length>=4){ pf[0].value=nm; pf[1].value=prof.phone||''; pf[2].value=prof.email||''; pf[3].value=prof.address||''; }
    }

    // Stats
    if (ov) {
      const vals = [ov.total_blood_units||0, ov.active_emergencies||0, ov.pending_hospital_requests||0, ov.donations_today||0];
      document.querySelectorAll('.stats .stat .ctr').forEach((e,i) => { if(vals[i]!==undefined){ e.dataset.t=vals[i]; e.textContent=vals[i]; }});
    }

    // Inventory
    const invArr = inv||[];
    function renderInv(id) {
      const el = document.getElementById(id); if(!el) return;
      if(!invArr.length){ el.innerHTML='<p style="text-align:center;color:#888;padding:24px">No inventory data</p>'; return; }
      const isLarge = el.classList.contains('large');
      el.innerHTML = invArr.map(i => {
        const st = i.inventory_status||(i.available_units>=15?'good':i.available_units>=6?'low':'critical');
        return `<div class="inv-card"><div class="inv-bg">${i.blood_group}</div><div class="inv-units">${i.available_units||0}</div><div class="inv-label">available</div>${isLarge?`<div class="inv-sub">${i.reserved_units||0} reserved · ${i.expiring_units||0} expiring</div>`:''}<span class="inv-status ${st}">${sLbl[st]||st}</span></div>`;
      }).join('');
    }
    renderInv('homeInv'); renderInv('invFull');

    // Home emergencies
    const eList = emg||[];
    const homeEmg = document.getElementById('homeEmg');
    if(homeEmg) {
      if(!eList.length) homeEmg.innerHTML='<p style="text-align:center;color:#888;padding:16px">No emergencies</p>';
      else homeEmg.innerHTML = eList.slice(0,3).map(e => {
        const u=e.urgency_level||'normal';
        return `<div class="er${u==='critical'?' critical':''}"><div class="er-blood">${e.blood_group_needed||'?'}</div><div class="er-info"><h4>${e.hospital_name||'Hospital'} · ${e.units_needed||1} units</h4><p><span class="urgency-${u}">${u==='critical'?'Critical':'Urgent'}</span> · ${ago(e.created_at)}</p></div></div>`;
      }).join('');
    }

    // Home hospital requests
    const hReqs = hospReqs||[];
    const homeReqs = document.getElementById('homeReqs');
    if(homeReqs) {
      if(!hReqs.length) homeReqs.innerHTML='<p style="text-align:center;color:#888;padding:16px">No requests</p>';
      else homeReqs.innerHTML = hReqs.slice(0,3).map(r => `<div class="er"><div class="er-blood">${r.blood_group||'?'}</div><div class="er-info"><h4>${r.hospital_name||'Hospital'} · ${r.units_needed||1} units</h4><p>${ago(r.created_at)}</p></div></div>`).join('');
    }

    // Full emergency list
    const emgFull = document.getElementById('emgFullList');
    if(emgFull) {
      if(!eList.length) emgFull.innerHTML='<p style="text-align:center;color:#888;padding:24px">No emergencies</p>';
      else emgFull.innerHTML = eList.map(e => {
        const u=e.urgency_level||'normal', l=u==='critical'?'Critical':u==='high'?'Urgent':'Normal';
        return `<div class="row${u==='critical'?' critical':''}"><div class="row-ic blood">${e.blood_group_needed||'?'}</div><div class="row-info"><h4>${e.hospital_name||'Hospital'}</h4><p>${e.units_needed||1} units</p></div><div class="row-meta"><span class="urg ${u}"><span class="material-symbols-rounded">${u==='critical'?'priority_high':'warning'}</span>${l}</span><span class="row-time">${ago(e.created_at)}</span></div><div class="row-btns"><button class="btn-sm red"><span class="material-symbols-rounded">local_shipping</span> Dispatch</button><button class="btn-sm blue"><span class="material-symbols-rounded">call</span> Contact</button></div></div>`;
      }).join('');
    }

    // Donations
    const dList = donations||[];
    const donEl = document.getElementById('donationList');
    if(donEl) {
      if(!dList.length) donEl.innerHTML='<p style="text-align:center;color:#888;padding:24px">No donations received</p>';
      else {
        const sMap = {verified:{l:'Verified',i:'check_circle'},testing:{l:'Testing',i:'science'},rejected:{l:'Rejected',i:'cancel'},pending:{l:'Pending',i:'schedule'}};
        donEl.innerHTML = dList.map(d => {
          const s = sMap[d.screening_status||'pending']||sMap.pending;
          return `<div class="row"><div class="row-ic donor">${d.blood_group||'?'}</div><div class="row-info"><h4>${d.donor_name||'Donor'}</h4><p>${d.units_collected||1} unit · ${fmtD(d.created_at)}</p></div><div class="row-meta"><span class="status-badge ${d.screening_status||'pending'}"><span class="material-symbols-rounded">${s.i}</span>${s.l}</span></div><div class="row-btns"><button class="btn-sm green"><span class="material-symbols-rounded">check</span> Approve</button><button class="btn-sm outline"><span class="material-symbols-rounded">info</span> Details</button></div></div>`;
        }).join('');
      }
    }

    // Hospital requests full
    const hrEl = document.getElementById('hospReqList');
    if(hrEl) {
      if(!hReqs.length) hrEl.innerHTML='<p style="text-align:center;color:#888;padding:24px">No hospital requests</p>';
      else hrEl.innerHTML = hReqs.map(r => {
        const u = r.urgency||'normal';
        return `<div class="row"><div class="row-ic hosp"><span class="material-symbols-rounded">local_hospital</span></div><div class="row-info"><h4>${r.hospital_name||'Hospital'}</h4><p>${r.blood_group||'?'} · ${r.units_needed||1} units</p></div><div class="row-meta"><span class="urg ${u}"><span class="material-symbols-rounded">${u==='critical'?'priority_high':'info'}</span>${u==='critical'?'Critical':u==='urgent'?'Urgent':'Normal'}</span><span class="row-time">${ago(r.created_at)}</span></div><div class="row-btns"><button class="btn-sm green"><span class="material-symbols-rounded">check</span> Approve</button><button class="btn-sm red"><span class="material-symbols-rounded">local_shipping</span> Dispatch</button></div></div>`;
      }).join('');
    }

    // Donor records
    const drList = donors||[];
    function renderDonors(q='',bg='') {
      const el = document.getElementById('donorRecList'); if(!el) return;
      const f = drList.filter(d => ((d.full_name||'').toLowerCase().includes(q.toLowerCase())||(d.blood_group||'').toLowerCase().includes(q.toLowerCase())) && (!bg||d.blood_group===bg));
      if(!f.length){ el.innerHTML='<p style="text-align:center;color:#888;padding:30px">No donors found</p>'; return; }
      el.innerHTML = f.map(d => `<div class="row"><div class="row-ic donor">${ini(d.full_name)}</div><div class="row-info"><h4>${d.full_name||'Unknown'}</h4><p>${d.phone||''} · Last: ${fmtD(d.last_donation_date)}</p></div><div class="row-meta"><span style="font-weight:800;color:var(--c);font-size:15px">${d.blood_group||'?'}</span><span class="status-badge ${d.eligible_to_donate!==false?'verified':'rejected'}">${d.eligible_to_donate!==false?'Available':'Unavailable'}</span></div><div class="row-btns"><button class="btn-sm blue"><span class="material-symbols-rounded">call</span> Contact</button></div></div>`).join('');
    }
    renderDonors();
    document.getElementById('drSearch')?.addEventListener('input', e => renderDonors(e.target.value, document.getElementById('drFilter')?.value||''));
    document.getElementById('drFilter')?.addEventListener('change', e => renderDonors(document.getElementById('drSearch')?.value||'', e.target.value));

    // Transfers
    const tList = transfers||[];
    const trEl = document.getElementById('transferList');
    if(trEl) {
      if(!tList.length) trEl.innerHTML='<p style="text-align:center;color:#888;padding:24px">No transfers</p>';
      else {
        const ts = {delivered:{l:'Delivered',i:'check_circle'},dispatched:{l:'In Transit',i:'local_shipping'},pending:{l:'Pending',i:'schedule'}};
        trEl.innerHTML = tList.map(t => {
          const s = ts[t.transfer_status||'pending']||ts.pending;
          return `<div class="row"><div class="row-ic transfer"><span class="material-symbols-rounded">local_shipping</span></div><div class="row-info"><h4>${t.destination_name||t.hospital_name||'Hospital'}</h4><p>${t.blood_group||'?'} · ${t.units_transferred||1} units</p></div><div class="row-meta"><span class="status-badge ${t.transfer_status||'pending'}"><span class="material-symbols-rounded">${s.i}</span>${s.l}</span></div><div class="row-btns"><button class="btn-sm blue"><span class="material-symbols-rounded">map</span> Track</button></div></div>`;
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
        const ic = {emergency_alert:{i:'emergency',c:'red'},system:{i:'info',c:'blue'},donation_update:{i:'volunteer_activism',c:'green'},transfer:{i:'local_shipping',c:'orange'}}[n.notification_type]||{i:'notifications',c:'blue'};
        return `<div class="ntf${n.is_read?'':' unread'}"><div class="ntf-ic ${ic.c}"><span class="material-symbols-rounded">${ic.i}</span></div><div class="ntf-body"><h4>${n.title||''}</h4><p>${n.message||''}</p></div><span class="ntf-time">${ago(n.created_at)}</span></div>`;
      }).join('');
    }
  }

  // Handlers
  document.getElementById('markAll')?.addEventListener('click', () => document.querySelectorAll('.ntf.unread').forEach(n=>n.classList.remove('unread')));
  document.getElementById('clearAll')?.addEventListener('click', () => { document.getElementById('ntfList').innerHTML='<p style="text-align:center;color:#888;padding:40px">No notifications</p>'; });

  const seen = new Set();
  document.querySelectorAll('.ctr').forEach(c => new IntersectionObserver(en => en.forEach(e => { if(e.isIntersecting&&!seen.has(e.target)){seen.add(e.target);const el=e.target,t=+el.dataset.t;let cur=0;const s=Math.max(1,Math.ceil(t/30));const iv=setInterval(()=>{cur+=s;if(cur>=t){cur=t;clearInterval(iv);}el.textContent=cur;},50);}}),{threshold:.5}).observe(c));

  document.addEventListener('click', e => {
    const b = e.target.closest('.btn-sm.green'); if(b&&b.textContent.includes('Approve')){b.innerHTML='<span class="material-symbols-rounded">check</span> Approved';b.style.cssText='background:#22c55e;color:#fff;pointer-events:none';}
    const d = e.target.closest('.btn-sm.red'); if(d&&d.textContent.includes('Dispatch')){d.innerHTML='<span class="material-symbols-rounded">check</span> Dispatched';d.style.cssText='background:#22c55e;color:#fff;pointer-events:none';}
  });

  // Modals
  const openM=id=>document.getElementById(id)?.classList.add('on'), closeM=id=>document.getElementById(id)?.classList.remove('on');
  document.getElementById('openAdd')?.addEventListener('click',()=>openM('addModal'));
  document.getElementById('openUpdate')?.addEventListener('click',()=>openM('updateModal'));
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>closeM(b.dataset.close)));
  document.querySelectorAll('.modal-overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeM(o.id);}));

  function toast(m,err){const t=document.getElementById('appToast');t.innerHTML=`<span class="material-symbols-rounded" style="color:${err?'#ef4444':'#4ade80'}">${err?'error':'check_circle'}</span>${m}`;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000);}
  document.getElementById('confirmAdd')?.addEventListener('click',()=>{closeM('addModal');toast('Stock added!');});
  document.getElementById('confirmUpd')?.addEventListener('click',()=>{closeM('updateModal');toast('Stock updated!');});
  document.querySelector('.prof .big-btn')?.addEventListener('click',()=>toast('Profile updated!'));

  load();
});
