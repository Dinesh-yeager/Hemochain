document.addEventListener('DOMContentLoaded', () => {

  // === Ticker ===
  const tickerMessages = [
    '<span class="material-symbols-rounded">emergency</span> URGENT: O- blood needed at AIIMS Delhi',
    '<span class="material-symbols-rounded">check_circle</span> 45 units donated today across Mumbai network',
    '<span class="material-symbols-rounded">local_hospital</span> New hospital onboarded: Fortis Healthcare, Bangalore',
    '<span class="material-symbols-rounded">bolt</span> Emergency request fulfilled in 8 minutes — Hyderabad',
    '<span class="material-symbols-rounded">link</span> 12,847 blockchain transactions verified today',
    '<span class="material-symbols-rounded">bloodtype</span> Blood drive scheduled: Chennai — May 25, 2026',
    '<span class="material-symbols-rounded">volunteer_activism</span> 52,300+ lives saved through HemoChain platform',
    '<span class="material-symbols-rounded">dashboard</span> Real-time inventory synced across 1,250 hospitals',
  ];
  const tickerEl = document.getElementById('tickerContent');
  const tickerHTML = tickerMessages.map(m => `<span><span class="pulse-dot"></span>${m}</span>`).join('');
  tickerEl.innerHTML = tickerHTML + tickerHTML;

  // === Navbar Scroll ===
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
    lastScroll = window.scrollY;
  });

  // === Hamburger ===
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('navLinks');
  hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
  navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => navLinks.classList.remove('open')));

  // === Counter Animation ===
  function animateCounters(entries, observer) {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.querySelectorAll('[data-target]').forEach(el => {
        const target = +el.dataset.target;
        const duration = 2000;
        const start = performance.now();
        function update(now) {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.floor(target * eased).toLocaleString();
          if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
      });
      observer.unobserve(entry.target);
    });
  }
  const counterObserver = new IntersectionObserver(animateCounters, { threshold: 0.3 });
  document.querySelectorAll('#statsFloat, .network-stats').forEach(el => counterObserver.observe(el));

  // === Blood Dashboard ===
  const bloodTypes = [
    { type: 'A+', units: 1240, pct: 85, status: 'high' },
    { type: 'A-', units: 320, pct: 45, status: 'medium' },
    { type: 'B+', units: 980, pct: 72, status: 'high' },
    { type: 'B-', units: 180, pct: 28, status: 'low' },
    { type: 'AB+', units: 540, pct: 60, status: 'medium' },
    { type: 'AB-', units: 95, pct: 18, status: 'low' },
    { type: 'O+', units: 1560, pct: 92, status: 'high' },
    { type: 'O-', units: 210, pct: 32, status: 'low' },
  ];
  const bloodGrid = document.getElementById('bloodGrid');
  bloodGrid.innerHTML = bloodTypes.map(b => `
    <div class="blood-card">
      <div class="blood-type">${b.type}</div>
      <div class="blood-units">${b.units} units available</div>
      <div class="blood-bar"><div class="blood-bar-fill" style="width:0%" data-width="${b.pct}%"></div></div>
      <div class="blood-status ${b.status}"><span class="indicator"></span>${b.status === 'high' ? 'Sufficient' : b.status === 'medium' ? 'Moderate' : 'Critical'}</div>
    </div>`).join('');

  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.querySelectorAll('.blood-bar-fill').forEach(bar => {
        setTimeout(() => { bar.style.width = bar.dataset.width; }, 200);
      });
      barObserver.unobserve(entry.target);
    });
  }, { threshold: 0.2 });
  barObserver.observe(bloodGrid);

  // === Matching Visual ===
  const matchVis = document.getElementById('matchingVisual');
  const nodes = [
    { x: 50, y: 50, label: 'A+', color: '#DC143C' },
    { x: 80, y: 30, label: 'O-', color: '#B22222' },
    { x: 20, y: 70, label: 'B+', color: '#DC143C' },
    { x: 70, y: 80, label: 'AB+', color: '#8B0000' },
    { x: 30, y: 25, label: 'O+', color: '#B22222' },
    { x: 85, y: 60, label: 'A-', color: '#DC143C' },
    { x: 15, y: 45, label: 'B-', color: '#8B0000' },
  ];
  const center = { x: 50, y: 50 };
  nodes.forEach((n, i) => {
    const line = document.createElement('div');
    line.className = 'match-line';
    const dx = n.x - center.x, dy = n.y - center.y;
    const len = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    Object.assign(line.style, {
      left: center.x + '%', top: center.y + '%',
      width: len + '%', transform: `rotate(${angle}deg)`,
    });
    matchVis.appendChild(line);
    const node = document.createElement('div');
    node.className = 'match-node';
    node.textContent = n.label;
    node.style.left = `calc(${n.x}% - 28px)`;
    node.style.top = `calc(${n.y}% - 28px)`;
    node.style.animationDelay = `${i * 0.4}s`;
    matchVis.appendChild(node);
  });
  const centerNode = document.createElement('div');
  centerNode.className = 'match-node';
  centerNode.innerHTML = '<span class="material-symbols-rounded" style="font-size:24px;color:#DC143C">smart_toy</span>';
  centerNode.style.cssText = `left:calc(50% - 28px);top:calc(50% - 28px);width:64px;height:64px;font-size:24px;background:linear-gradient(135deg,#fff,#e0e0e0);z-index:2`;
  matchVis.appendChild(centerNode);

  // === Map Dots ===
  const mapDots = document.getElementById('mapDots');
  const locations = [
    [20,30],[35,25],[50,20],[65,35],[80,25],[25,50],[40,45],[55,55],[70,50],[85,45],
    [30,70],[45,65],[60,75],[75,70],[15,40],[90,55],[50,40],[35,60],[65,60],[22,62],
  ];
  locations.forEach(([x, y], i) => {
    const dot = document.createElement('div');
    dot.className = 'map-dot';
    dot.style.left = x + '%';
    dot.style.top = y + '%';
    dot.style.animationDelay = `${i * 0.15}s`;
    mapDots.appendChild(dot);
  });

  // === FAQ ===
  const faqs = [
    ['What is Hemo Chain?', 'Hemo Chain is India\'s first blockchain-powered blood donation platform that connects donors, hospitals, and blood banks through a transparent and secure decentralized network. Every blood unit is tracked from donation to transfusion.'],
    ['How does blockchain ensure blood safety?', 'Blockchain creates an immutable record of each blood unit\'s journey — from the donor\'s medical screening results to storage conditions and final transfusion. This eliminates tampering and ensures complete traceability.'],
    ['Is my personal data secure?', 'Absolutely. We use end-to-end encryption with zero-knowledge proofs. Your medical data is stored on a HIPAA-compliant blockchain, and only authorized healthcare providers can access relevant information.'],
    ['How fast is the emergency matching system?', 'Our AI-powered system matches emergency blood requests with available donors within 60 seconds. GPS-based routing ensures blood reaches the patient in the shortest possible time.'],
    ['Can hospitals integrate with Hemo Chain?', 'Yes! We offer a comprehensive API and dashboard for hospitals and blood banks. Integration takes less than 48 hours, and our team provides full technical support throughout the process.'],
    ['How can I become a donor?', 'Simply register on our platform with your ID verification, complete a brief health questionnaire, and you\'re ready. We\'ll notify you when nearby patients need your blood type.'],
  ];
  const faqGrid = document.getElementById('faqGrid');
  faqGrid.innerHTML = faqs.map(([q, a]) => `
    <div class="faq-item">
      <div class="faq-question"><span>${q}</span><span class="faq-toggle">+</span></div>
      <div class="faq-answer"><p>${a}</p></div>
    </div>`).join('');
  faqGrid.addEventListener('click', e => {
    const item = e.target.closest('.faq-item');
    if (!item) return;
    const wasActive = item.classList.contains('active');
    faqGrid.querySelectorAll('.faq-item').forEach(i => {
      i.classList.remove('active');
      i.querySelector('.faq-answer').style.maxHeight = null;
    });
    if (!wasActive) {
      item.classList.add('active');
      const answer = item.querySelector('.faq-answer');
      answer.style.maxHeight = answer.scrollHeight + 'px';
    }
  });

  // === Blood Wave Canvas ===
  const canvas = document.getElementById('waveCanvas');
  const ctx = canvas.getContext('2d');
  let width, height;
  function resize() {
    width = canvas.width = canvas.offsetWidth;
    height = canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  let time = 0;
  function drawWaves() {
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(0, height);
      for (let x = 0; x <= width; x += 4) {
        const y = height * 0.7 + Math.sin(x * 0.003 + time + i * 0.8) * 30 * (i + 1)
          + Math.sin(x * 0.006 + time * 1.5 + i) * 15;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(width, height);
      ctx.closePath();
      ctx.fillStyle = `rgba(220, 20, 60, ${0.03 - i * 0.008})`;
      ctx.fill();
    }
    time += 0.008;
    requestAnimationFrame(drawWaves);
  }
  drawWaves();

  // === Scroll Reveal ===
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  // === Smooth Scroll ===
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
});
