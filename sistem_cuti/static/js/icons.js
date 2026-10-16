/**
 * SICUTI - Sistem Cuti Pegawai Dishub DIY
 * Modern SVG Icons Helper (No external CDN, pure DOM API)
 */
(function() {
  const SVG_NS = "http://www.w3.org/2000/svg";

  const ICONS = {
    "dashboard": [
      ["rect", { x: 3, y: 3, width: 7, height: 7, rx: 1 }],
      ["rect", { x: 14, y: 3, width: 7, height: 7, rx: 1 }],
      ["rect", { x: 14, y: 14, width: 7, height: 7, rx: 1 }],
      ["rect", { x: 3, y: 14, width: 7, height: 7, rx: 1 }]
    ],
    "file-text": [
      ["path", { d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" }],
      ["polyline", { points: "14 2 14 8 20 8" }],
      ["line", { x1: 16, y1: 13, x2: 8, y2: 13 }],
      ["line", { x1: 16, y1: 17, x2: 8, y2: 17 }],
      ["polyline", { points: "10 9 9 9 8 9" }]
    ],
    "history": [
      ["circle", { cx: 12, cy: 12, r: 10 }],
      ["polyline", { points: "12 6 12 12 16 14" }]
    ],
    "users": [
      ["path", { d: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" }],
      ["circle", { cx: 9, cy: 7, r: 4 }],
      ["path", { d: "M23 21v-2a4 4 0 0 0-3-3.87" }],
      ["path", { d: "M16 3.13a4 4 0 0 1 0 7.75" }]
    ],
    "user": [
      ["path", { d: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" }],
      ["circle", { cx: 12, cy: 7, r: 4 }]
    ],
    "id-card": [
      ["rect", { x: 2, y: 5, width: 20, height: 14, rx: 2 }],
      ["line", { x1: 2, y1: 10, x2: 22, y2: 10 }],
      ["circle", { cx: 7, cy: 15, r: 1 }],
      ["line", { x1: 12, y1: 15, x2: 18, y2: 15 }]
    ],
    "calendar": [
      ["rect", { x: 3, y: 4, width: 18, height: 18, rx: 2, ry: 2 }],
      ["line", { x1: 16, y1: 2, x2: 16, y2: 6 }],
      ["line", { x1: 8, y1: 2, x2: 8, y2: 6 }],
      ["line", { x1: 3, y1: 10, x2: 21, y2: 10 }]
    ],
    "settings": [
      ["circle", { cx: 12, cy: 12, r: 3 }],
      ["path", { d: "M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" }]
    ],
    "upload": [
      ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" }],
      ["polyline", { points: "17 8 12 3 7 8" }],
      ["line", { x1: 12, y1: 3, x2: 12, y2: 15 }]
    ],
    "download": [
      ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" }],
      ["polyline", { points: "7 10 12 15 17 10" }],
      ["line", { x1: 12, y1: 15, x2: 12, y2: 3 }]
    ],
    "printer": [
      ["polyline", { points: "6 9 6 2 18 2 18 9" }],
      ["path", { d: "M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" }],
      ["rect", { x: 6, y: 14, width: 12, height: 8, rx: 1 }]
    ],
    "plus": [
      ["line", { x1: 12, y1: 5, x2: 12, y2: 19 }],
      ["line", { x1: 5, y1: 12, x2: 19, y2: 12 }]
    ],
    "save": [
      ["path", { d: "M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" }],
      ["polyline", { points: "17 21 17 13 7 13 7 21" }],
      ["polyline", { points: "7 3 7 8 15 8" }]
    ],
    "check": [
      ["polyline", { points: "20 6 9 17 4 12" }]
    ],
    "x": [
      ["line", { x1: 18, y1: 6, x2: 6, y2: 18 }],
      ["line", { x1: 6, y1: 6, x2: 18, y2: 18 }]
    ],
    "trash": [
      ["polyline", { points: "3 6 5 6 21 6" }],
      ["path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" }],
      ["line", { x1: 10, y1: 11, x2: 10, y2: 17 }],
      ["line", { x1: 14, y1: 11, x2: 14, y2: 17 }]
    ],
    "send": [
      ["line", { x1: 22, y1: 2, x2: 11, y2: 13 }],
      ["polygon", { points: "22 2 15 22 11 13 2 9 22 2" }]
    ],
    "search": [
      ["circle", { cx: 11, cy: 11, r: 8 }],
      ["line", { x1: 21, y1: 21, x2: 16.65, y2: 16.65 }]
    ],
    "log-in": [
      ["path", { d: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" }],
      ["polyline", { points: "10 17 15 12 10 7" }],
      ["line", { x1: 15, y1: 12, x2: 3, y2: 12 }]
    ],
    "log-out": [
      ["path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" }],
      ["polyline", { points: "16 17 21 12 16 7" }],
      ["line", { x1: 21, y1: 12, x2: 9, y2: 12 }]
    ],
    "key": [
      ["path", { d: "M21 2l-2 2m-1.5 1.5L14 9l-2-2-7 7a3 3 0 1 0 4.24 4.24l7-7-2-2 3.5-3.5M19 5l2 2" }]
    ],
    "arrow-left": [
      ["line", { x1: 19, y1: 12, x2: 5, y2: 12 }],
      ["polyline", { points: "12 19 5 12 12 5" }]
    ],
    "bell": [
      ["path", { d: "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" }],
      ["path", { d: "M13.73 21a2 2 0 0 1-3.46 0" }]
    ],
    "clock": [
      ["circle", { cx: 12, cy: 12, r: 10 }],
      ["polyline", { points: "12 6 12 12 16 14" }]
    ],
    "check-circle": [
      ["path", { d: "M22 11.08V12a10 10 0 1 1-5.93-9.14" }],
      ["polyline", { points: "22 4 12 14.01 9 11.01" }]
    ],
    "x-circle": [
      ["circle", { cx: 12, cy: 12, r: 10 }],
      ["line", { x1: 15, y1: 9, x2: 9, y2: 15 }],
      ["line", { x1: 9, y1: 9, x2: 15, y2: 15 }]
    ],
    "layers": [
      ["polygon", { points: "12 2 2 7 12 12 22 7 12 2" }],
      ["polyline", { points: "2 17 12 22 22 17" }],
      ["polyline", { points: "2 12 12 17 22 12" }]
    ],
    "edit": [
      ["path", { d: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" }],
      ["path", { d: "M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" }]
    ],
    "refresh-cw": [
      ["polyline", { points: "23 4 23 10 17 10" }],
      ["polyline", { points: "1 20 1 14 7 14" }],
      ["path", { d: "M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" }]
    ]
  };

  // Helper untuk membuat elemen SVG dengan DOM API (aman, tanpa innerHTML)
  function icon(name, extraClass) {
    const def = ICONS[name];
    if (!def) return null;

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin="round");
    svg.setAttribute("class", extraClass ? `ic ${extraClass}` : "ic");
    svg.setAttribute("aria-hidden", "true");

    for (let i = 0; i < def.length; i++) {
      const tag = def[i][0];
      const attrs = def[i][1];
      const el = document.createElementNS(SVG_NS, tag);
      for (const key in attrs) {
        if (Object.prototype.hasOwnProperty.call(attrs, key)) {
          el.setAttribute(key, attrs[key]);
        }
      }
      svg.appendChild(el);
    }
    return svg;
  }

  // Ekspos icon function secara global
  window.icon = icon;

  // Keyword mapping untuk tombol otomatis
  const BUTTON_KEYWORDS = [
    { kw: "simpan", icon: "save" },
    { kw: "tambah", icon: "plus" },
    { kw: "cetak", icon: "printer" },
    { kw: "download", icon: "download" },
    { kw: "unduh", icon: "download" },
    { kw: "import", icon: "upload" },
    { kw: "unggah", icon: "upload" },
    { kw: "setuju", icon: "check" },
    { kw: "terima", icon: "check" },
    { kw: "tolak", icon: "x" },
    { kw: "hapus", icon: "trash" },
    { kw: "ajukan", icon: "send" },
    { kw: "kelola", icon: "edit" },
    { kw: "kembali", icon: "arrow-left" },
    { kw: "masuk", icon: "log-in" },
    { kw: "keluar", icon: "log-out" },
    { kw: "reset", icon: "refresh-cw" },
    { kw: "cari", icon: "search" },
    { kw: "filter", icon: "search" }
  ];

  function initIcons() {
    // 1. Render data-icon elements
    document.querySelectorAll("[data-icon]").forEach(el => {
      const name = el.getAttribute("data-icon");
      if (!name) return;
      // Jika sudah memiliki svg di dalamnya, lewati
      if (el.querySelector("svg.ic")) return;
      const icEl = icon(name);
      if (icEl) {
        el.insertBefore(icEl, el.firstChild);
      }
    });

    // 2. Otomatis tambahkan ikon ke .btn yang belum memiliki ikon
    document.querySelectorAll(".btn").forEach(btn => {
      // Lewati tombol yang sudah memiliki svg, img, atau i, atau tombol dismiss
      if (btn.querySelector("svg, img, i") || btn.classList.contains("btn-close")) return;

      const text = (btn.textContent || "").trim().toLowerCase();
      if (!text) return;

      for (let i = 0; i < BUTTON_KEYWORDS.length; i++) {
        const item = BUTTON_KEYWORDS[i];
        if (text.includes(item.kw)) {
          const icEl = icon(item.icon, "btn-ic");
          if (icEl) {
            btn.insertBefore(icEl, btn.firstChild);
          }
          break;
        }
      }
    });

    // 3. Tambahkan gelembung ikon pada .stat
    document.querySelectorAll(".stat").forEach(stat => {
      if (stat.querySelector(".stat-icon")) return;

      const labelEl = stat.querySelector(".stat-label");
      const text = ((labelEl ? labelEl.textContent : "") + " " + (stat.className || "")).toLowerCase();

      let iconName = "layers";
      if (text.includes("menunggu")) {
        iconName = "clock";
      } else if (text.includes("disetujui") || text.includes("setuju")) {
        iconName = "check-circle";
      } else if (text.includes("ditolak") || text.includes("tolak")) {
        iconName = "x-circle";
      } else if (text.includes("sisa")) {
        iconName = "calendar";
      } else if (text.includes("pegawai")) {
        iconName = "users";
      } else if (text.includes("total") || text.includes("jatah") || text.includes("digunakan")) {
        iconName = "layers";
      }

      const bubble = document.createElement("div");
      bubble.className = "stat-icon";
      const icEl = icon(iconName);
      if (icEl) {
        bubble.appendChild(icEl);
      }

      // Bungkus konten teks stat jika belum terbungkus agar layout flex rapi
      stat.insertBefore(bubble, stat.firstChild);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initIcons);
  } else {
    initIcons();
  }
})();
