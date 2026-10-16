// Hitung jumlah hari otomatis pada form pengajuan
function hitungHari(){
  const m=document.getElementById('mulai'), s=document.getElementById('selesai'), o=document.getElementById('hari');
  if(!m||!m.value||!s.value){return}
  fetch('/api/hitung-hari?mulai='+encodeURIComponent(m.value)+'&selesai='+encodeURIComponent(s.value))
    .then(r=>r.json())
    .then(d=>{ if(o) o.value=d.hari+' hari kerja'; });
}

// Navigasi responsif sidebar mobile
function toggleSidebar(){
  const sb=document.getElementById('sidebar');
  const ov=document.getElementById('sidebar-overlay');
  if(sb) sb.classList.toggle('open');
  if(ov) ov.classList.toggle('visible');
}

function closeSidebar(){
  const sb=document.getElementById('sidebar');
  const ov=document.getElementById('sidebar-overlay');
  if(sb) sb.classList.remove('open');
  if(ov) ov.classList.remove('visible');
}

document.addEventListener('DOMContentLoaded',()=>{
  ['mulai','selesai'].forEach(i=>{
    const e=document.getElementById(i);
    if(e) e.addEventListener('change',hitungHari);
  });
  // Notifikasi admin: perbarui otomatis tiap 15 detik
  const b=document.getElementById('notif-badge');
  if(b){
    setInterval(()=>{
      fetch('/admin/notif')
        .then(r=>r.json())
        .then(d=>{
          b.textContent=d.n;
          b.style.display=d.n>0?'inline-block':'none';
        })
        .catch(()=>{});
    },15000);
  }
});
