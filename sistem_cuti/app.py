"""Sistem Informasi Pengelolaan Cuti Pegawai - aplikasi lokal (Flask + SQLite)."""
import os, io, re, math, secrets, sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from flask import (Flask, g, render_template, request, redirect, url_for, session,
                   flash, abort, send_file, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "database.db")
UPLOAD_DIR = os.path.join(BASE, "uploads", "bukti_cuti")
DATA_DIR = os.path.join(BASE, "data")
for d in (UPLOAD_DIR, DATA_DIR, os.path.join(BASE, "pdf")):
    os.makedirs(d, exist_ok=True)

JATAH_DASAR = 12
# nama: (memotong jatah tahunan?, wajib bukti?)
JENIS_CUTI = {
    "Cuti Tahunan": (1, 0),
    "Cuti Sakit": (0, 1),
    "Cuti Besar": (0, 0),
    "Cuti Melahirkan": (0, 1),
    "Cuti Karena Alasan Penting": (0, 1),
    "Cuti di Luar Tanggungan Negara": (0, 0),
}
EXT_OK = {"pdf", "jpg", "jpeg", "png"}
BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024
_kp = os.path.join(DATA_DIR, "secret.key")
if not os.path.exists(_kp):
    open(_kp, "w").write(secrets.token_hex(32))
app.secret_key = open(_kp).read().strip()

from db_config import get_db, IntegrityError, DB_TYPE, MYSQL_TABLE_SCHEMAS

# ---------------------------------------------------------------- database
def db():
    if "db" not in g:
        g.db = get_db()
    return g.db

@app.teardown_appcontext
def close_db(_):
    c = g.pop("db", None)
    if c: c.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS pegawai(
 id INTEGER PRIMARY KEY AUTOINCREMENT, nip TEXT UNIQUE, nama TEXT NOT NULL,
 golongan TEXT DEFAULT '', unit_kerja TEXT DEFAULT '', username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'pegawai', aktif INTEGER DEFAULT 1,
 jabatan TEXT DEFAULT '', masa_kerja TEXT DEFAULT '', atasan_nama TEXT DEFAULT '', atasan_nip TEXT DEFAULT '',
 kelas_jabatan TEXT DEFAULT '', tmt_kerja TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS jatah_cuti(
 id INTEGER PRIMARY KEY AUTOINCREMENT, pegawai_id INTEGER NOT NULL REFERENCES pegawai(id),
 tahun INTEGER NOT NULL, jatah_dasar INTEGER NOT NULL DEFAULT 12,
 tambahan_dari_tahun_sebelumnya INTEGER NOT NULL DEFAULT 0,
 total_jatah INTEGER NOT NULL DEFAULT 12, digunakan_awal INTEGER NOT NULL DEFAULT 0,
 total_digunakan INTEGER NOT NULL DEFAULT 0, sisa_cuti INTEGER NOT NULL DEFAULT 12,
 cuti_dibawa_ke_tahun_berikutnya INTEGER NOT NULL DEFAULT 0, UNIQUE(pegawai_id,tahun));
CREATE TABLE IF NOT EXISTS pengajuan_cuti(
 id INTEGER PRIMARY KEY AUTOINCREMENT, pegawai_id INTEGER NOT NULL REFERENCES pegawai(id),
 jenis_cuti TEXT NOT NULL, tanggal_mulai TEXT NOT NULL, tanggal_selesai TEXT NOT NULL,
 jumlah_hari INTEGER NOT NULL, alasan TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Menunggu',
 tanggal_pengajuan TEXT NOT NULL, memotong_jatah INTEGER NOT NULL DEFAULT 1,
 catatan_admin TEXT DEFAULT '', nomor_surat TEXT DEFAULT '', tanggal_surat TEXT DEFAULT '',
 diproses_oleh INTEGER, tanggal_proses TEXT,
 alamat_cuti TEXT DEFAULT '', telp_cuti TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS dokumen_cuti(
 id INTEGER PRIMARY KEY AUTOINCREMENT, pengajuan_id INTEGER NOT NULL REFERENCES pengajuan_cuti(id),
 nama_file TEXT NOT NULL, path_file TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hari_libur(tanggal TEXT PRIMARY KEY, keterangan TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS pengaturan(kunci TEXT PRIMARY KEY, nilai TEXT);
"""

def init_db():
    c = get_db()
    if isinstance(c, sqlite3.Connection) or DB_TYPE == "sqlite":
        c.executescript(SCHEMA)
    else:
        for sch in MYSQL_TABLE_SCHEMAS:
            c.execute(sch)
    kolom_baru = {
        "pegawai": [("jabatan", "VARCHAR(255) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                    ("masa_kerja", "VARCHAR(100) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                    ("atasan_nama", "VARCHAR(255) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                    ("atasan_nip", "VARCHAR(50) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                    ("kelas_jabatan", "VARCHAR(50) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                    ("tmt_kerja", "VARCHAR(50) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''")],
        "pengajuan_cuti": [("alamat_cuti", "TEXT"),
                          ("telp_cuti", "VARCHAR(50) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                          ("nomor_surat", "VARCHAR(100) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''"),
                          ("tanggal_surat", "VARCHAR(20) DEFAULT ''" if DB_TYPE == "mysql" else "TEXT DEFAULT ''")]
    }
    for tbl, kols in kolom_baru.items():
        existing = {r["name"] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()}
        for kol, tipe in kols:
            if kol not in existing:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN {kol} {tipe}")

    for k, v in {"tahun_aktif": str(date.today().year), "instansi": "DINAS PERHUBUNGAN DIY",
                 "kepala_nama": "", "kepala_nip": "",
                 "kepala_jabatan": "Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta"}.items():
        c.execute("INSERT OR IGNORE INTO pengaturan VALUES(?,?)", (k, v))
    if not c.execute("SELECT 1 FROM pegawai WHERE role='admin'").fetchone():
        c.execute("INSERT INTO pegawai(nip,nama,username,password_hash,role) VALUES(?,?,?,?,'admin')",
                  (None, "Administrator", "admin", generate_password_hash("admin123")))
    c.commit(); c.close()

def get_set(k):
    r = db().execute("SELECT nilai FROM pengaturan WHERE kunci=?", (k,)).fetchone()
    return r["nilai"] if r else ""

def set_set(k, v):
    db().execute("INSERT OR REPLACE INTO pengaturan VALUES(?,?)", (k, v))

# ---------------------------------------------------------------- logika cuti
def tgl(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def fmt(s):
    if not s or s == "-": return "-"
    try:
        d = tgl(s) if isinstance(s, str) else s
        return f"{d.day} {BULAN[d.month]} {d.year}"
    except Exception:
        return str(s)
app.jinja_env.filters["tgl"] = fmt

def hitung_masa_kerja(tmt, hari_ini=None):
    """Hitung selisih bulan antara hari ini dan tmt_kerja.
    Kembalikan teks '05 Tahun 10 Bulan' (tahun dan bulan 2 digit).
    Jika tmt kosong, kembalikan string kosong.
    """
    if not tmt:
        return ""
    try:
        if isinstance(tmt, (datetime, date)):
            d_tmt = tmt if isinstance(tmt, date) else tmt.date()
        else:
            s = str(tmt).strip()[:10]
            if len(s) == 7:
                s = s + "-01"
            d_tmt = datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return ""

    if hari_ini is None:
        hari_ini = date.today()
    elif isinstance(hari_ini, str):
        try:
            hari_ini = datetime.strptime(hari_ini[:10], "%Y-%m-%d").date()
        except Exception:
            hari_ini = date.today()
    elif isinstance(hari_ini, datetime):
        hari_ini = hari_ini.date()

    total_bulan = (hari_ini.year - d_tmt.year) * 12 + (hari_ini.month - d_tmt.month)
    if total_bulan < 0:
        total_bulan = 0
    th = total_bulan // 12
    bl = total_bulan % 12
    return f"{th:02d} Tahun {bl:02d} Bulan"

def masa_kerja_pegawai(row):
    """Pakai hasil hitung otomatis; jika tmt_kerja kosong, pakai teks masa_kerja lama."""
    if not row:
        return ""
    tmt = ""
    lama = ""
    if isinstance(row, dict):
        tmt = row.get("tmt_kerja") or ""
        lama = row.get("masa_kerja") or ""
    else:
        try:
            tmt = row["tmt_kerja"] or ""
        except (KeyError, IndexError, TypeError):
            tmt = ""
        try:
            lama = row["masa_kerja"] or ""
        except (KeyError, IndexError, TypeError):
            lama = ""
    if tmt:
        hasil = hitung_masa_kerja(tmt)
        if hasil:
            return hasil
    return str(lama or "")

app.jinja_env.filters["masa_kerja"] = masa_kerja_pegawai

def hitung_hari(mulai, selesai):
    """Hari kerja (Senin-Jumat) dikurangi hari libur yang terdaftar."""
    libur = {r["tanggal"] for r in db().execute("SELECT tanggal FROM hari_libur")}
    n, d = 0, mulai
    while d <= selesai:
        if d.weekday() < 5 and d.isoformat() not in libur:
            n += 1
        d += timedelta(days=1)
    return n

def ensure_jatah(pid, tahun):
    r = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid, tahun)).fetchone()
    if not r:
        db().execute("INSERT INTO jatah_cuti(pegawai_id,tahun,jatah_dasar,total_jatah,sisa_cuti) VALUES(?,?,?,?,?)",
                     (pid, tahun, JATAH_DASAR, JATAH_DASAR, JATAH_DASAR))
    recalc(pid, tahun)
    return db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid, tahun)).fetchone()

def recalc(pid, tahun):
    """Hitung ulang dari data: aman dari pengurangan ganda (idempoten)."""
    r = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid, tahun)).fetchone()
    if not r: return
    pakai = db().execute("""SELECT COALESCE(SUM(jumlah_hari),0) s FROM pengajuan_cuti
        WHERE pegawai_id=? AND status='Disetujui' AND memotong_jatah=1
        AND substr(tanggal_mulai,1,4)=?""", (pid, str(tahun))).fetchone()["s"]
    total = r["jatah_dasar"] + r["tambahan_dari_tahun_sebelumnya"]
    digunakan = r["digunakan_awal"] + pakai
    sisa = total - digunakan
    carry = math.ceil(max(sisa, 0) / 2)
    db().execute("""UPDATE jatah_cuti SET total_jatah=?, total_digunakan=?, sisa_cuti=?,
        cuti_dibawa_ke_tahun_berikutnya=? WHERE id=?""", (total, digunakan, sisa, carry, r["id"]))

def tahun_aktif():
    return int(get_set("tahun_aktif"))

# ---------------------------------------------------------------- keamanan
@app.before_request
def csrf_dan_user():
    g.user = None
    if "uid" in session:
        g.user = db().execute("SELECT * FROM pegawai WHERE id=? AND aktif=1", (session["uid"],)).fetchone()
        if not g.user: session.clear()
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    if request.method == "POST":
        if not secrets.compare_digest(request.form.get("_csrf", ""), session["csrf"]):
            abort(400, "Token keamanan tidak valid. Muat ulang halaman.")

@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "SAMEORIGIN"
    r.headers["Cache-Control"] = "no-store"
    return r

@app.context_processor
def ctx():
    n = 0
    if g.get("user") and g.user["role"] == "admin":
        n = db().execute("SELECT COUNT(*) c FROM pengajuan_cuti WHERE status='Menunggu'").fetchone()["c"]
    return dict(csrf=session.get("csrf", ""), user=g.get("user"), notif=n,
                instansi=get_set("instansi") if g.get("user") else "",
                get_setting=get_set)

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not g.user: return redirect(url_for("login"))
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not g.user: return redirect(url_for("login"))
        if g.user["role"] != "admin": abort(403)
        return f(*a, **k)
    return w

def boleh_akses(pegawai_id):
    return g.user["role"] == "admin" or g.user["id"] == pegawai_id

# ---------------------------------------------------------------- login
@app.route("/")
def index():
    if not g.user: return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard" if g.user["role"] == "admin" else "dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM pegawai WHERE username=? AND aktif=1",
                         (request.form["username"].strip(),)).fetchone()
        if u and check_password_hash(u["password_hash"], request.form["password"]):
            session.clear(); session["uid"] = u["id"]; session["csrf"] = secrets.token_hex(16)
            return redirect(url_for("index"))
        flash("Username atau password salah.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/ganti-password", methods=["GET", "POST"])
@login_required
def ganti_password():
    if request.method == "POST":
        if not check_password_hash(g.user["password_hash"], request.form["lama"]):
            flash("Password lama salah.", "danger")
        elif len(request.form["baru"]) < 6 or request.form["baru"] != request.form["ulang"]:
            flash("Password baru minimal 6 karakter dan harus sama dengan pengulangan.", "danger")
        else:
            db().execute("UPDATE pegawai SET password_hash=? WHERE id=?",
                         (generate_password_hash(request.form["baru"]), g.user["id"]))
            db().commit(); flash("Password berhasil diganti.", "success")
            return redirect(url_for("index"))
    return render_template("ganti_password.html")

# ---------------------------------------------------------------- pegawai
@app.route("/dashboard")
@login_required
def dashboard():
    if g.user["role"] == "admin": return redirect(url_for("admin_dashboard"))
    th = tahun_aktif()
    j = ensure_jatah(g.user["id"], th); db().commit()
    riwayat = db().execute("SELECT * FROM pengajuan_cuti WHERE pegawai_id=? ORDER BY id DESC", (g.user["id"],)).fetchall()
    return render_template("dashboard_pegawai.html", j=j, tahun=th, riwayat=riwayat)

@app.route("/api/hitung-hari")
@login_required
def api_hitung():
    try:
        m, s = tgl(request.args["mulai"]), tgl(request.args["selesai"])
        return jsonify(hari=hitung_hari(m, s) if s >= m else 0)
    except Exception:
        return jsonify(hari=0)

def simpan_bukti(file, pengajuan_id):
    nama = file.filename or ""
    ext = nama.rsplit(".", 1)[-1].lower() if "." in nama else ""
    if ext not in EXT_OK: raise ValueError("Bukti harus berformat PDF, JPG, atau PNG.")
    head = file.stream.read(8); file.stream.seek(0)
    ok = (ext == "pdf" and head.startswith(b"%PDF")) or (ext in ("jpg", "jpeg") and head[:3] == b"\xff\xd8\xff") \
        or (ext == "png" and head.startswith(b"\x89PNG"))
    if not ok: raise ValueError("Isi file tidak sesuai dengan ekstensinya.")
    acak = f"{secrets.token_hex(16)}.{ext}"
    file.save(os.path.join(UPLOAD_DIR, acak))
    db().execute("INSERT INTO dokumen_cuti(pengajuan_id,nama_file,path_file) VALUES(?,?,?)",
                 (pengajuan_id, os.path.basename(nama)[:120], acak))

@app.route("/ajukan", methods=["GET", "POST"])
@login_required
def ajukan():
    if g.user["role"] == "admin": abort(403)
    if request.method == "POST":
        try:
            jenis = request.form["jenis_cuti"]
            if jenis not in JENIS_CUTI: raise ValueError("Jenis cuti tidak valid.")
            m, s = tgl(request.form["tanggal_mulai"]), tgl(request.form["tanggal_selesai"])
            if s < m: raise ValueError("Tanggal selesai tidak boleh sebelum tanggal mulai.")
            if m.year != s.year: raise ValueError("Cuti tidak boleh melewati pergantian tahun. Ajukan terpisah per tahun.")
            hari = hitung_hari(m, s)
            if hari < 1: raise ValueError("Rentang tanggal tidak mengandung hari kerja.")
            potong, wajib = JENIS_CUTI[jenis]
            f = request.files.get("bukti")
            ada = f and f.filename
            if wajib and not ada: raise ValueError(f"{jenis} wajib melampirkan bukti.")
            if potong:
                j = ensure_jatah(g.user["id"], m.year)
                if not j:
                    raise ValueError(f"Jatah cuti tahun {m.year} belum tersedia.")
                menunggu = db().execute("""SELECT COALESCE(SUM(jumlah_hari),0) s FROM pengajuan_cuti WHERE pegawai_id=?
                    AND status='Menunggu' AND memotong_jatah=1 AND substr(tanggal_mulai,1,4)=?""",
                    (g.user["id"], str(m.year))).fetchone()["s"]
                if hari + menunggu > j["sisa_cuti"]:
                    raise ValueError(f"Sisa cuti ({j['sisa_cuti']} hari, dikurangi pengajuan menunggu {menunggu} hari) tidak cukup.")
            cur = db().execute("""INSERT INTO pengajuan_cuti(pegawai_id,jenis_cuti,tanggal_mulai,tanggal_selesai,
                jumlah_hari,alasan,status,tanggal_pengajuan,memotong_jatah,alamat_cuti,telp_cuti) VALUES(?,?,?,?,?,?,'Menunggu',?,?,?,?)""",
                (g.user["id"], jenis, m.isoformat(), s.isoformat(), hari, request.form.get("alasan", "").strip()[:500],
                 datetime.now().strftime("%Y-%m-%d %H:%M"), potong,
                 request.form.get("alamat_cuti", "").strip()[:300],
                 request.form.get("telp_cuti", "").strip()[:30]))
            if ada: simpan_bukti(f, cur.lastrowid)
            db().commit()
            flash("Pengajuan cuti berhasil dikirim dan menunggu persetujuan admin.", "success")
            return redirect(url_for("dashboard"))
        except (ValueError, KeyError) as e:
            db().rollback(); flash(str(e), "danger")
        except Exception as e:
            db().rollback(); flash(f"Terjadi kesalahan: {str(e)}", "danger")
    return render_template("ajukan.html", jenis=JENIS_CUTI)

@app.route("/pengajuan/<int:pid>")
@login_required
def detail(pid):
    p = db().execute("""SELECT c.*, e.nama, e.nip, e.golongan, e.unit_kerja FROM pengajuan_cuti c
        JOIN pegawai e ON e.id=c.pegawai_id WHERE c.id=?""", (pid,)).fetchone()
    if not p: abort(404)
    if not boleh_akses(p["pegawai_id"]): abort(403)
    dok = db().execute("SELECT * FROM dokumen_cuti WHERE pengajuan_id=?", (pid,)).fetchall()
    return render_template("detail.html", p=p, dok=dok, wajib=JENIS_CUTI.get(p["jenis_cuti"], (0, 0))[1])

@app.route("/bukti/<int:did>")
@login_required
def bukti(did):
    d = db().execute("""SELECT d.*, c.pegawai_id FROM dokumen_cuti d JOIN pengajuan_cuti c ON c.id=d.pengajuan_id
        WHERE d.id=?""", (did,)).fetchone()
    if not d: abort(404)
    if not boleh_akses(d["pegawai_id"]): abort(403)
    return send_file(os.path.join(UPLOAD_DIR, d["path_file"]), download_name=d["nama_file"])

# ---------------------------------------------------------------- admin
@app.route("/admin")
@admin_required
def admin_dashboard():
    q = lambda sql: db().execute(sql).fetchone()[0]
    st = dict(pegawai=q("SELECT COUNT(*) FROM pegawai WHERE role='pegawai' AND aktif=1"),
              total=q("SELECT COUNT(*) FROM pengajuan_cuti"),
              menunggu=q("SELECT COUNT(*) FROM pengajuan_cuti WHERE status='Menunggu'"),
              setuju=q("SELECT COUNT(*) FROM pengajuan_cuti WHERE status='Disetujui'"),
              tolak=q("SELECT COUNT(*) FROM pengajuan_cuti WHERE status='Ditolak'"))
    baru = db().execute("""SELECT c.*, e.nama, e.nip FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
        WHERE c.status='Menunggu' ORDER BY c.id DESC LIMIT 10""").fetchall()
    return render_template("dashboard_admin.html", st=st, baru=baru)

@app.route("/admin/notif")
@admin_required
def admin_notif():
    return jsonify(n=db().execute("SELECT COUNT(*) c FROM pengajuan_cuti WHERE status='Menunggu'").fetchone()["c"])

@app.route("/admin/pengajuan")
@admin_required
def admin_pengajuan():
    st = request.args.get("status", "")
    sql = "SELECT c.*, e.nama, e.nip FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id"
    args = ()
    if st in ("Menunggu", "Disetujui", "Ditolak"):
        sql += " WHERE c.status=?"; args = (st,)
    rows = db().execute(sql + " ORDER BY c.id DESC", args).fetchall()
    return render_template("admin_pengajuan.html", rows=rows, st=st)

@app.route("/admin/pengajuan/<int:pid>/proses", methods=["POST"])
@admin_required
def proses(pid):
    aksi = request.form.get("aksi")
    try:
        try:
            db().execute("BEGIN IMMEDIATE")
        except Exception:
            pass
        p = db().execute("SELECT * FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
        if not p or p["status"] != "Menunggu":   # cegah pemrosesan ganda
            db().rollback(); flash("Pengajuan ini sudah diproses sebelumnya.", "warning")
            return redirect(url_for("detail", pid=pid))
        th = int(p["tanggal_mulai"][:4])
        if aksi == "setuju":
            if p["memotong_jatah"]:
                j = ensure_jatah(p["pegawai_id"], th)
                if p["jumlah_hari"] > j["sisa_cuti"]:
                    db().rollback(); flash(f"Sisa cuti pegawai ({j['sisa_cuti']} hari) tidak cukup.", "danger")
                    return redirect(url_for("detail", pid=pid))
            status = "Disetujui"
        elif aksi == "tolak":
            status = "Ditolak"
        else:
            db().rollback(); abort(400)
        db().execute("""UPDATE pengajuan_cuti SET status=?, catatan_admin=?, nomor_surat=?, tanggal_surat=?,
            diproses_oleh=?, tanggal_proses=? WHERE id=?""",
            (status, request.form.get("catatan", "").strip()[:500], request.form.get("nomor_surat", "").strip()[:100],
             request.form.get("tanggal_surat", ""), g.user["id"], datetime.now().strftime("%Y-%m-%d %H:%M"), pid))
        ensure_jatah(p["pegawai_id"], th)
        db().commit(); flash(f"Pengajuan {status.lower()}.", "success")
        return redirect(url_for("admin_pengajuan"))
    except Exception as e:
        db().rollback()
        import logging
        logging.exception("Gagal memproses pengajuan cuti:")
        flash(f"Terjadi kesalahan saat memproses pengajuan: {e}", "danger")
        return redirect(url_for("detail", pid=pid))

@app.route("/admin/pengajuan/<int:pid>/surat", methods=["POST"])
@admin_required
def admin_update_surat(pid):
    p = db().execute("SELECT * FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
    if not p: abort(404)
    nomor = request.form.get("nomor_surat", "").strip()[:100]
    tanggal = request.form.get("tanggal_surat", "").strip()
    db().execute("UPDATE pengajuan_cuti SET nomor_surat=?, tanggal_surat=? WHERE id=?",
                 (nomor, tanggal, pid))
    db().commit()
    flash("Nomor dan tanggal surat izin berhasil disimpan.", "success")
    return redirect(url_for("detail", pid=pid))

@app.route("/admin/pengajuan/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_pengajuan_edit(pid):
    p = db().execute("""SELECT c.*, e.nama, e.nip, e.unit_kerja, e.jabatan, e.atasan_nama, e.atasan_nip
        FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
        WHERE c.id=?""", (pid,)).fetchone()
    if not p:
        abort(404)

    th_asal = int(p["tanggal_mulai"][:4])
    j_asal = ensure_jatah(p["pegawai_id"], th_asal)
    dok = db().execute("SELECT * FROM dokumen_cuti WHERE pengajuan_id=?", (pid,)).fetchall()

    if request.method == "POST":
        try:
            jenis = request.form.get("jenis_cuti", "").strip()
            if jenis not in JENIS_CUTI:
                raise ValueError("Jenis cuti tidak valid.")

            status_baru = request.form.get("status", "").strip()
            if status_baru not in ("Menunggu", "Disetujui", "Ditolak"):
                raise ValueError("Status pengajuan tidak valid (harus Menunggu, Disetujui, atau Ditolak).")

            m_val = request.form.get("tanggal_mulai", "").strip()
            s_val = request.form.get("tanggal_selesai", "").strip()
            if not m_val or not s_val:
                raise ValueError("Tanggal mulai dan tanggal selesai wajib diisi.")

            m, s = tgl(m_val), tgl(s_val)
            if s < m:
                raise ValueError("Tanggal selesai tidak boleh sebelum tanggal mulai.")
            if m.year != s.year:
                raise ValueError("Cuti tidak boleh melewati pergantian tahun. Ajukan terpisah per tahun.")

            lama_input = request.form.get("jumlah_hari", "").strip()
            if lama_input:
                try:
                    hari = int(lama_input)
                except ValueError:
                    raise ValueError("Lama cuti harus berupa angka bulat.")
            else:
                hari = hitung_hari(m, s)

            if hari < 1:
                raise ValueError("Lama cuti minimal 1 hari kerja.")

            potong, wajib = JENIS_CUTI[jenis]

            f = request.files.get("bukti")
            ada_upload = f and f.filename
            cur_dok_count = len(dok)
            if wajib and not ada_upload and cur_dok_count == 0:
                raise ValueError(f"{jenis} wajib melampirkan bukti / dokumen pendukung.")

            th_baru = m.year
            j_baru = ensure_jatah(p["pegawai_id"], th_baru)

            if potong:
                disetujui_lain = db().execute("""SELECT COALESCE(SUM(jumlah_hari),0) s FROM pengajuan_cuti
                    WHERE pegawai_id=? AND status='Disetujui' AND memotong_jatah=1
                    AND substr(tanggal_mulai,1,4)=? AND id!=?""",
                    (p["pegawai_id"], str(th_baru), pid)).fetchone()["s"]

                menunggu_lain = db().execute("""SELECT COALESCE(SUM(jumlah_hari),0) s FROM pengajuan_cuti
                    WHERE pegawai_id=? AND status='Menunggu' AND memotong_jatah=1
                    AND substr(tanggal_mulai,1,4)=? AND id!=?""",
                    (p["pegawai_id"], str(th_baru), pid)).fetchone()["s"]

                hak_total = j_baru["jatah_dasar"] + j_baru["tambahan_dari_tahun_sebelumnya"]
                sisa_tersedia = hak_total - j_baru["digunakan_awal"] - disetujui_lain

                if status_baru == "Disetujui":
                    if hari > sisa_tersedia:
                        raise ValueError(f"Sisa cuti pegawai ({sisa_tersedia} hari) tidak mencukupi untuk disetujui ({hari} hari). Kuota tidak boleh minus.")
                elif status_baru == "Menunggu":
                    if hari + menunggu_lain > sisa_tersedia:
                        raise ValueError(f"Sisa cuti pegawai ({sisa_tersedia} hari, dikurangi pengajuan menunggu lainnya {menunggu_lain} hari) tidak mencukupi.")

            alasan = request.form.get("alasan", "").strip()[:500]
            alamat_cuti = request.form.get("alamat_cuti", "").strip()[:300]
            telp_cuti = request.form.get("telp_cuti", "").strip()[:30]
            nomor_surat = request.form.get("nomor_surat", "").strip()[:100]
            tanggal_surat = request.form.get("tanggal_surat", "").strip()[:20]
            catatan_admin = request.form.get("catatan_admin", "").strip()[:500]

            diproses_oleh = g.user["id"] if status_baru in ("Disetujui", "Ditolak") else p["diproses_oleh"]
            tgl_proses = datetime.now().strftime("%Y-%m-%d %H:%M") if status_baru in ("Disetujui", "Ditolak") else p["tanggal_proses"]

            db().execute("""UPDATE pengajuan_cuti SET
                jenis_cuti=?, tanggal_mulai=?, tanggal_selesai=?, jumlah_hari=?,
                alasan=?, status=?, memotong_jatah=?, catatan_admin=?,
                nomor_surat=?, tanggal_surat=?, alamat_cuti=?, telp_cuti=?,
                diproses_oleh=?, tanggal_proses=?
                WHERE id=?""",
                (jenis, m.isoformat(), s.isoformat(), hari,
                 alasan, status_baru, potong, catatan_admin,
                 nomor_surat, tanggal_surat, alamat_cuti, telp_cuti,
                 diproses_oleh, tgl_proses, pid))

            if ada_upload:
                simpan_bukti(f, pid)

            recalc(p["pegawai_id"], th_baru)
            if th_asal != th_baru:
                ensure_jatah(p["pegawai_id"], th_asal)
                recalc(p["pegawai_id"], th_asal)

            db().commit()
            flash("Pengajuan cuti berhasil diperbarui.", "success")

            next_url = request.form.get("next", "").strip()
            if next_url and next_url.startswith("/admin"):
                return redirect(next_url)
            return redirect(url_for("admin_riwayat", tahun=th_baru))

        except (ValueError, KeyError) as e:
            db().rollback()
            flash(str(e), "danger")
            p_edit = dict(p)
            p_edit.update({
                "jenis_cuti": request.form.get("jenis_cuti", p["jenis_cuti"]),
                "status": request.form.get("status", p["status"]),
                "tanggal_mulai": request.form.get("tanggal_mulai", p["tanggal_mulai"]),
                "tanggal_selesai": request.form.get("tanggal_selesai", p["tanggal_selesai"]),
                "jumlah_hari": request.form.get("jumlah_hari", p["jumlah_hari"]),
                "alasan": request.form.get("alasan", p["alasan"]),
                "alamat_cuti": request.form.get("alamat_cuti", p["alamat_cuti"]),
                "telp_cuti": request.form.get("telp_cuti", p["telp_cuti"]),
                "nomor_surat": request.form.get("nomor_surat", p["nomor_surat"]),
                "tanggal_surat": request.form.get("tanggal_surat", p["tanggal_surat"]),
                "catatan_admin": request.form.get("catatan_admin", p["catatan_admin"]),
            })
            return render_template("admin_pengajuan_edit.html", p=p_edit, dok=dok, jenis=JENIS_CUTI,
                                   j=j_asal, next_url=request.form.get("next", ""))

    next_url = request.args.get("next", "")
    return render_template("admin_pengajuan_edit.html", p=p, dok=dok, jenis=JENIS_CUTI,
                           j=j_asal, next_url=next_url)

@app.route("/admin/pengajuan/<int:pid>/hapus", methods=["POST"])
@admin_required
def admin_pengajuan_hapus(pid):
    p = db().execute("SELECT * FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    pid_peg = p["pegawai_id"]
    th = int(p["tanggal_mulai"][:4])

    # Hapus dokumen pendukung dari tabel referensi saja (tanpa menghapus file fisik di uploads)
    db().execute("DELETE FROM dokumen_cuti WHERE pengajuan_id=?", (pid,))

    # Hapus pengajuan cuti
    db().execute("DELETE FROM pengajuan_cuti WHERE id=?", (pid,))

    # Sinkronisasi / perbarui saldo pegawai
    ensure_jatah(pid_peg, th)
    recalc(pid_peg, th)
    db().commit()

    flash("Pengajuan cuti berhasil dihapus.", "success")
    next_url = request.form.get("next", "").strip()
    if next_url and next_url.startswith("/admin"):
        return redirect(next_url)
    return redirect(url_for("admin_riwayat", tahun=th))


@app.route("/admin/pegawai", methods=["GET", "POST"])
@admin_required
def admin_pegawai():
    if request.method == "POST":
        try:
            nip, nama = request.form["nip"].strip(), request.form["nama"].strip()
            if not nip or not nama: raise ValueError("NIP dan nama wajib diisi.")
            cur = db().execute("INSERT INTO pegawai(nip,nama,golongan,unit_kerja,username,password_hash) VALUES(?,?,?,?,?,?)",
                (nip, nama, request.form["golongan"].strip(), request.form["unit_kerja"].strip(), nip,
                 generate_password_hash(nip)))
            ensure_jatah(cur.lastrowid, tahun_aktif()); db().commit()
            flash("Pegawai ditambahkan. Username dan password awal = NIP.", "success")
        except IntegrityError:
            db().rollback(); flash("NIP/username sudah terdaftar.", "danger")
        except ValueError as e:
            flash(str(e), "danger")
    rows = db().execute("""SELECT e.*, j.total_jatah, j.total_digunakan, j.sisa_cuti FROM pegawai e
        LEFT JOIN jatah_cuti j ON j.pegawai_id=e.id AND j.tahun=? WHERE e.role='pegawai' ORDER BY e.nama""",
        (tahun_aktif(),)).fetchall()
    return render_template("admin_pegawai.html", rows=rows, tahun=tahun_aktif())

@app.route("/admin/pegawai/<int:pid>", methods=["GET", "POST"])
@admin_required
def admin_pegawai_edit(pid):
    e = db().execute("SELECT * FROM pegawai WHERE id=? AND role='pegawai'", (pid,)).fetchone()
    if not e: abort(404)
    if request.method == "POST":
        a = request.form.get("aksi")
        if a == "reset":
            db().execute("UPDATE pegawai SET password_hash=? WHERE id=?", (generate_password_hash(e["nip"] or "123456"), pid))
            flash("Password direset menjadi NIP.", "success")
        else:
            tmt_val = request.form.get("tmt_kerja", "").strip()[:10]
            if len(tmt_val) == 7:
                tmt_val += "-01"
            db().execute("""UPDATE pegawai SET nama=?, golongan=?, unit_kerja=?,
                jabatan=?, kelas_jabatan=?, masa_kerja=?, tmt_kerja=?, atasan_nama=?, atasan_nip=?, aktif=? WHERE id=?""",
                (request.form["nama"].strip(), request.form.get("golongan", "").strip(), request.form.get("unit_kerja", "").strip(),
                 request.form.get("jabatan", "").strip(), request.form.get("kelas_jabatan", "").strip(),
                 request.form.get("masa_kerja", "").strip(), tmt_val,
                 request.form.get("atasan_nama", "").strip(), request.form.get("atasan_nip", "").strip(),
                 1 if request.form.get("aktif") else 0, pid))
            flash("Data pegawai disimpan.", "success")
        db().commit(); return redirect(url_for("admin_pegawai_edit", pid=pid))
    jt = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? ORDER BY tahun DESC", (pid,)).fetchall()
    return render_template("admin_pegawai_edit.html", e=e, jt=jt)

@app.route("/admin/riwayat")
@admin_required
def admin_riwayat():
    th = request.args.get("tahun", type=int) or tahun_aktif()
    rows = db().execute("""SELECT c.*, e.nama, e.nip FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
        WHERE substr(c.tanggal_mulai,1,4)=? ORDER BY e.nama, c.tanggal_mulai""", (str(th),)).fetchall()
    return render_template("admin_riwayat.html", rows=rows, th=th)

@app.route("/admin/kartu")
@admin_required
def admin_kartu():
    rows = db().execute("""SELECT e.*, j.total_jatah, j.total_digunakan, j.sisa_cuti FROM pegawai e
        LEFT JOIN jatah_cuti j ON j.pegawai_id=e.id AND j.tahun=? WHERE e.role='pegawai' ORDER BY e.nama""",
        (tahun_aktif(),)).fetchall()
    return render_template("admin_kartu.html", rows=rows, tahun=tahun_aktif())

@app.route("/admin/pegawai/<int:pid>/formulir")
@admin_required
def admin_pegawai_formulir(pid):
    return redirect(url_for("kartu_pdf", pid=pid))

@app.route("/admin/tahun-baru", methods=["GET", "POST"])
@admin_required
def tahun_baru():
    lama = tahun_aktif(); baru = lama + 1
    if request.method == "POST":
        if request.form.get("konfirmasi", "").strip() != str(baru):
            flash(f"Ketik {baru} untuk konfirmasi.", "danger")
        else:
            try:
                db().execute("BEGIN IMMEDIATE")
            except Exception:
                pass
            if db().execute("SELECT 1 FROM jatah_cuti WHERE tahun=?", (baru,)).fetchone():
                db().rollback(); flash(f"Tahun {baru} sudah pernah dibuat.", "warning")
                return redirect(url_for("tahun_baru"))
            for e in db().execute("SELECT id FROM pegawai WHERE role='pegawai' AND aktif=1").fetchall():
                prev = ensure_jatah(e["id"], lama)
                carry = prev["cuti_dibawa_ke_tahun_berikutnya"]
                db().execute("""INSERT INTO jatah_cuti(pegawai_id,tahun,jatah_dasar,tambahan_dari_tahun_sebelumnya,
                    total_jatah,sisa_cuti) VALUES(?,?,?,?,?,?)""",
                    (e["id"], baru, JATAH_DASAR, carry, JATAH_DASAR + carry, JATAH_DASAR + carry))
            set_set("tahun_aktif", str(baru)); db().commit()
            flash(f"Tahun cuti {baru} berhasil dibuat.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("tahun_baru.html", lama=lama, baru=baru,
        sudah=bool(db().execute("SELECT 1 FROM jatah_cuti WHERE tahun=?", (baru,)).fetchone()))

@app.route("/admin/libur", methods=["GET", "POST"])
@admin_required
def admin_libur():
    if request.method == "POST":
        if request.form.get("hapus"):
            db().execute("DELETE FROM hari_libur WHERE tanggal=?", (request.form["hapus"],))
        elif request.form.get("tanggal"):
            db().execute("INSERT OR REPLACE INTO hari_libur VALUES(?,?)", (request.form["tanggal"], request.form.get("ket", "")[:100]))
        db().commit(); return redirect(url_for("admin_libur"))
    return render_template("admin_libur.html", rows=db().execute("SELECT * FROM hari_libur ORDER BY tanggal").fetchall())

@app.route("/admin/pengaturan", methods=["GET", "POST"])
@admin_required
def admin_pengaturan():
    if request.method == "POST":
        for k in ("instansi", "kepala_nama", "kepala_nip", "kepala_jabatan"):
            if k in request.form:
                set_set(k, request.form[k].strip()[:200])
        db().commit()
        flash("Pengaturan disimpan.", "success")
    return render_template("admin_pengaturan.html")


# ---------------------------------------------------------------- formulir + kartu PDF (2 halaman)
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, NextPageTemplate,
                                PageBreak, Table, TableStyle, Paragraph, Spacer)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def _buat_formulir_flowables(p, j, j_prev, instansi, kepala_nama, kepala_nip, kepala_jabatan):
    """Menghasilkan flowables Halaman 1 Formulir Permintaan dan Pemberian Cuti A4 Portrait."""
    # Pastikan p adalah dict agar .get() bisa digunakan (sqlite3.Row tidak mendukung .get())
    if not isinstance(p, dict):
        p = dict(p)
    p["masa_kerja"] = masa_kerja_pegawai(p)
    W = 186 * mm

    def PS(name, **kw):
        defaults = dict(fontName="Times-Roman", fontSize=8, leading=10)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    sN      = PS("fN")
    sNBold  = PS("fNBold",  fontName="Times-Bold")
    sNCen   = PS("fNCen",   alignment=TA_CENTER)
    sNCenB  = PS("fNCenB",  fontName="Times-Bold", alignment=TA_CENTER)
    sOptHdr = PS("fOptHdr", fontName="Times-Bold", fontSize=7.5, leading=9, alignment=TA_CENTER)
    sTitle  = PS("fTitle",  fontName="Times-Bold", fontSize=10, leading=12, alignment=TA_CENTER)
    sNomor  = PS("fNomor",  fontName="Times-Bold", fontSize=8.5, leading=11, alignment=TA_CENTER)
    sSec    = PS("fSec",    fontName="Times-Bold", fontSize=8, leading=10)

    TS_BOX = [
        ("GRID",          (0,0), (-1,-1), 0.5, colors.black),
        ("FONTNAME",      (0,0), (-1,-1), "Times-Roman"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 1.5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
        ("LEFTPADDING",   (0,0), (-1,-1), 3),
        ("RIGHTPADDING",  (0,0), (-1,-1), 3),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]

    el = []

    # 1. Header Kanan Atas
    tgl_surat_str = fmt(p["tanggal_surat"]) if p.get("tanggal_surat") else "........................................"
    t_top = Table([
        ["", Paragraph(f"Yogyakarta, {tgl_surat_str}<br/>Kepada Yth.<br/>Kepala Dinas Perhubungan<br/>Daerah Istimewa Yogyakarta<br/>di Y O G Y A K A R T A", sN)]
    ], colWidths=[96*mm, 90*mm])
    t_top.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    el.append(t_top)
    el.append(Spacer(1, 1.5*mm))

    # Judul & NOMOR
    no_surat = p.get("nomor_surat") or ""
    txt_no = f"NOMOR {no_surat}" if no_surat else "NOMOR ...................................................."
    el.append(Paragraph("<b>FORMULIR PERMINTAAN DAN PEMBERIAN CUTI</b>", sTitle))
    el.append(Paragraph(txt_no, sNomor))
    el.append(Spacer(1, 2*mm))

    # I. DATA PEGAWAI
    data_pegawai = [
        [Paragraph("<b>I. DATA PEGAWAI</b>", sSec), "", "", ""],
        [Paragraph("Nama", sN), Paragraph(p["nama"], sNBold),
         Paragraph("NIP", sN), Paragraph(p.get("nip") or "-", sN)],
        [Paragraph("Jabatan", sN), Paragraph(p.get("jabatan") or "-", sN),
         Paragraph("Masa Kerja", sN), Paragraph(p.get("masa_kerja") or "-", sN)],
        [Paragraph("Unit Kerja", sN), Paragraph(p.get("unit_kerja") or instansi, sN), "", ""],
    ]
    t1 = Table(data_pegawai, colWidths=[24*mm, 69*mm, 24*mm, 69*mm])
    ts1 = list(TS_BOX) + [
        ("SPAN", (0,0), (3,0)),
        ("SPAN", (1,3), (3,3)),
    ]
    t1.setStyle(TableStyle(ts1))
    el.append(t1)
    el.append(Spacer(1, 1.5*mm))

    # II. JENIS CUTI YANG DIAMBIL (Kiri: 1, 2, 3; Kanan: 4, 5, 6)
    jenis_ini = p["jenis_cuti"]
    v_tahunan = "V" if jenis_ini == "Cuti Tahunan" else ""
    v_sakit   = "V" if jenis_ini == "Cuti Sakit" else ""
    v_penting = "V" if jenis_ini == "Cuti Karena Alasan Penting" else ""
    v_besar   = "V" if jenis_ini == "Cuti Besar" else ""
    v_lahir   = "V" if jenis_ini == "Cuti Melahirkan" else ""
    v_cltn    = "V" if jenis_ini == "Cuti di Luar Tanggungan Negara" else ""

    data_jenis = [
        [Paragraph("<b>II. JENIS CUTI YANG DIAMBIL</b>", sSec), "", "", "", "", ""],
        [Paragraph("1. Cuti Tahunan", sN), Paragraph(v_tahunan, sNCenB), "",
         Paragraph("4. Cuti Besar", sN), Paragraph(v_besar, sNCenB), ""],
        [Paragraph("2. Cuti Sakit", sN), Paragraph(v_sakit, sNCenB), "",
         Paragraph("5. Cuti Melahirkan", sN), Paragraph(v_lahir, sNCenB), ""],
        [Paragraph("3. Cuti Karena Alasan Penting", sN), Paragraph(v_penting, sNCenB), "",
         Paragraph("6. Cuti di Luar Tanggungan Negara", sN), Paragraph(v_cltn, sNCenB), ""],
    ]
    t2 = Table(data_jenis, colWidths=[68*mm, 15*mm, 10*mm, 68*mm, 15*mm, 10*mm])
    ts2 = list(TS_BOX) + [
        ("SPAN", (0,0), (5,0)),
        ("SPAN", (1,1), (2,1)),
        ("SPAN", (1,2), (2,2)),
        ("SPAN", (1,3), (2,3)),
        ("SPAN", (4,1), (5,1)),
        ("SPAN", (4,2), (5,2)),
        ("SPAN", (4,3), (5,3)),
    ]
    t2.setStyle(TableStyle(ts2))
    el.append(t2)
    el.append(Spacer(1, 1.5*mm))

    # III. ALASAN CUTI
    alasan_txt = p.get("alasan") or "........................................................................................................................"
    data_alasan = [
        [Paragraph("<b>III. ALASAN CUTI</b>", sSec)],
        [Paragraph(alasan_txt, sN)],
    ]
    t3 = Table(data_alasan, colWidths=[W])
    ts3 = list(TS_BOX) + [
        ("TOPPADDING", (0,1), (0,1), 3),
        ("BOTTOMPADDING", (0,1), (0,1), 3),
    ]
    t3.setStyle(TableStyle(ts3))
    el.append(t3)
    el.append(Spacer(1, 1.5*mm))

    # IV. LAMANYA CUTI: "Selama <n> hari, mulai tanggal <mulai> s.d <selesai>"
    if p.get("tanggal_mulai") and p.get("jumlah_hari"):
        tgl_mulai_str = fmt(p["tanggal_mulai"])
        tgl_selesai_str = fmt(p.get("tanggal_selesai") or p["tanggal_mulai"])
        lama_txt = f"{p['jumlah_hari']} hari"
    else:
        lama_txt = "....... hari"
        tgl_mulai_str = "........................................"
        tgl_selesai_str = "........................................"
    data_lama = [
        [Paragraph("<b>IV. LAMANYA CUTI</b>", sSec), "", "", "", "", ""],
        [Paragraph("Selama", sN), Paragraph(lama_txt, sNCenB),
         Paragraph("mulai tanggal", sN), Paragraph(tgl_mulai_str, sNCenB),
         Paragraph("s.d.", sNCen), Paragraph(tgl_selesai_str, sNCenB)],
    ]
    t4 = Table(data_lama, colWidths=[20*mm, 26*mm, 30*mm, 45*mm, 16*mm, 49*mm])
    ts4 = list(TS_BOX) + [
        ("SPAN", (0,0), (5,0)),
    ]
    t4.setStyle(TableStyle(ts4))
    el.append(t4)
    el.append(Spacer(1, 1.5*mm))

    # V. CATATAN CUTI
    sisa_n1 = str(j_prev["sisa_cuti"]) if j_prev else (str(j["tambahan_dari_tahun_sebelumnya"] * 2) if j["tambahan_dari_tahun_sebelumnya"] else "0")
    sisa_n  = str(j["jatah_dasar"])

    data_catatan = [
        [Paragraph("<b>V. CATATAN CUTI***</b>", sSec), "", "", "", ""],
        [Paragraph("<b>1. CUTI TAHUNAN</b>", sNBold), "", "", Paragraph("<b>2. CUTI BESAR</b>", sN), ""],
        [Paragraph("Tahun", sNCenB), Paragraph("Sisa", sNCenB), Paragraph("Keterangan", sNCenB),
         Paragraph("<b>3. CUTI SAKIT</b>", sN), ""],
        [Paragraph("N-2", sNCen), Paragraph("", sNCen), Paragraph("", sN),
         Paragraph("<b>4. CUTI MELAHIRKAN</b>", sN), ""],
        [Paragraph("N-1", sNCen), Paragraph(sisa_n1, sNCen), Paragraph("", sN),
         Paragraph("<b>5. CUTI KARENA ALASAN PENTING</b>", sN), ""],
        [Paragraph("N", sNCen), Paragraph(sisa_n, sNCen), Paragraph("", sN),
         Paragraph("<b>6. CUTI DI LUAR TANGGUNGAN NEGARA</b>", sN), ""],
    ]
    t5 = Table(data_catatan, colWidths=[18*mm, 18*mm, 57*mm, 83*mm, 10*mm])
    ts5 = list(TS_BOX) + [
        ("SPAN", (0,0), (4,0)),
        ("SPAN", (0,1), (2,1)),
        ("SPAN", (3,1), (4,1)),
        ("SPAN", (3,2), (4,2)),
        ("SPAN", (3,3), (4,3)),
        ("SPAN", (3,4), (4,4)),
        ("SPAN", (3,5), (4,5)),
    ]
    t5.setStyle(TableStyle(ts5))
    el.append(t5)
    el.append(Spacer(1, 1.5*mm))

    # Lebar kolom tanda tangan terpadu untuk Seksi VI, VII, dan VIII: diperbesar menjadi 86 mm (sebelumnya 70 mm)
    w_ttd = 86 * mm
    w_almt_total = W - w_ttd                 # 100 mm untuk area data kontak (Alamat & No HP)
    w_telp_lbl = 16 * mm                     # label TELP.
    w_telp_val = w_almt_total - w_telp_lbl   # 84 mm untuk isian nomor telepon
    col_w_opt = (W - w_ttd) / 4.0            # 25 mm per kolom opsi persetujuan (DISETUJUI, PERUBAHAN, DITANGGUHKAN, TIDAK DISETUJUI)

    # VI. ALAMAT SELAMA MENJALANKAN CUTI
    almt = p.get("alamat_cuti") or ".................................................................................."
    telp = p.get("telp_cuti")   or "........................................................"
    # Kolom pemohon: ruang tanda tangan murni (Hormat saya, ruang ttd, nama, NIP) tanpa campur nomor HP
    txt_pemohon = (
        "Hormat saya,<br/>"
        "<br/><br/><br/><br/><br/><br/>"
        f"<b>{p['nama']}</b><br/>"
        f"NIP. {p.get('nip') or '-'}"
    )
    data_alamat = [
        [Paragraph("<b>VI. ALAMAT SELAMA MENJALANKAN CUTI</b>", sSec), "", ""],
        [
            Paragraph(f"{almt}", sN),
            "",
            Paragraph(txt_pemohon, sNCen)
        ],
        [
            Paragraph("TELP.", sNBold),
            Paragraph(f"{telp}", sN),
            ""
        ]
    ]
    t6 = Table(data_alamat, colWidths=[w_telp_lbl, w_telp_val, w_ttd])
    ts6 = list(TS_BOX) + [
        ("SPAN", (0,0), (2,0)),
        ("SPAN", (0,1), (1,1)),
        ("SPAN", (2,1), (2,2)),
        ("VALIGN", (0,1), (1,1), "TOP"),
        ("VALIGN", (0,2), (1,2), "MIDDLE"),
        ("VALIGN", (2,1), (2,2), "TOP"),
        ("TOPPADDING", (0,1), (1,1), 3),
        ("BOTTOMPADDING", (0,1), (1,1), 3),
        ("TOPPADDING", (0,2), (1,2), 2),
        ("BOTTOMPADDING", (0,2), (1,2), 2),
        ("TOPPADDING", (2,1), (2,2), 3),
        ("BOTTOMPADDING", (2,1), (2,2), 4),
    ]
    t6.setStyle(TableStyle(ts6))
    el.append(t6)
    el.append(Spacer(1, 1.5*mm))

    # VII & VIII: Status persetujuan & keputusan
    st = p.get("status") or "Menunggu"
    v_setuju = "V" if st == "Disetujui" else ""
    v_tolak  = "V" if st == "Ditolak" else ""

    # VII. PERTIMBANGAN ATASAN LANGSUNG
    atasan_nama_str = p.get("atasan_nama") or ""
    atasan_nip_str  = p.get("atasan_nip")  or ""
    if atasan_nama_str:
        txt_atasan_ttd = (
            f"Atasan Langsung,"
            f"<br/><br/><br/><br/><br/><br/><br/>"
            f"<b>{atasan_nama_str}</b>"
            f"<br/>NIP. {atasan_nip_str}"
        )
    else:
        txt_atasan_ttd = (
            "Atasan Langsung,"
            "<br/><br/><br/><br/><br/><br/><br/>"
            "( .................................................... )"
            "<br/>NIP. ...................................................."
        )
    data_atasan = [
        [Paragraph("<b>VII. PERTIMBANGAN ATASAN LANGSUNG</b>", sSec), "", "", "", ""],
        [Paragraph("DISETUJUI", sOptHdr), Paragraph("PERUBAHAN", sOptHdr),
         Paragraph("DITANGGUHKAN", sOptHdr), Paragraph("TIDAK<br/>DISETUJUI", sOptHdr),
         Paragraph(txt_atasan_ttd, sNCen)],
        [Paragraph(v_setuju, sNCenB), Paragraph("", sNCenB), Paragraph("", sNCenB), Paragraph(v_tolak, sNCenB), ""]
    ]
    t7 = Table(data_atasan, colWidths=[col_w_opt, col_w_opt, col_w_opt, col_w_opt, w_ttd])
    ts7 = list(TS_BOX) + [
        ("SPAN", (0,0), (4,0)),
        ("SPAN", (4,1), (4,2)),
        ("VALIGN", (0,1), (-1,-1), "MIDDLE"),
        ("VALIGN", (4,1), (4,2), "TOP"),
        ("LEFTPADDING", (0,1), (3,1), 1),
        ("RIGHTPADDING", (0,1), (3,1), 1),
        ("TOPPADDING", (4,1), (4,2), 3),
        ("BOTTOMPADDING", (4,1), (4,2), 4),
        ("BOTTOMPADDING", (0,2), (3,2), 10),
    ]
    t7.setStyle(TableStyle(ts7))
    el.append(t7)
    el.append(Spacer(1, 1.5*mm))

    # VIII. KEPUTUSAN PEJABAT YANG BERWENANG MEMBERIKAN CUTI
    # Kolom Kepala Dinas menyediakan ruang tanda tangan dan cap dinas yang lapang dan bersih.
    kadin_nama_str = kepala_nama or ""
    kadin_nip_str  = kepala_nip  or ""
    if kadin_nama_str:
        txt_kadin_ttd = (
            f"{kepala_jabatan},<br/>"
            f"<br/><br/><br/><br/><br/><br/><br/>"
            f"<b>{kadin_nama_str}</b><br/>"
            f"NIP. {kadin_nip_str}"
        )
    else:
        txt_kadin_ttd = (
            f"{kepala_jabatan},<br/>"
            f"<br/><br/><br/><br/><br/><br/><br/>"
            "( .................................................... )<br/>"
            "NIP. ...................................................."
        )
    data_pejabat = [
        [Paragraph("<b>VIII. KEPUTUSAN PEJABAT YANG BERWENANG MEMBERIKAN CUTI</b>", sSec), "", "", "", ""],
        [Paragraph("DISETUJUI", sOptHdr), Paragraph("PERUBAHAN", sOptHdr),
         Paragraph("DITANGGUHKAN", sOptHdr), Paragraph("TIDAK<br/>DISETUJUI", sOptHdr),
         Paragraph(txt_kadin_ttd, sNCen)],
        [Paragraph(v_setuju, sNCenB), Paragraph("", sNCenB), Paragraph("", sNCenB), Paragraph(v_tolak, sNCenB), ""]
    ]
    t8 = Table(data_pejabat, colWidths=[col_w_opt, col_w_opt, col_w_opt, col_w_opt, w_ttd])
    ts8 = list(TS_BOX) + [
        ("SPAN", (0,0), (4,0)),
        ("SPAN", (4,1), (4,2)),
        ("VALIGN", (0,1), (-1,-1), "MIDDLE"),
        ("VALIGN", (4,1), (4,2), "TOP"),
        ("LEFTPADDING", (0,1), (3,1), 1),
        ("RIGHTPADDING", (0,1), (3,1), 1),
        ("TOPPADDING", (4,1), (4,2), 3),
        ("BOTTOMPADDING", (4,1), (4,2), 5),
        ("BOTTOMPADDING", (0,2), (3,2), 10),
    ]
    t8.setStyle(TableStyle(ts8))
    el.append(t8)

    return el

def _tambahkan_lampiran_ke_pdf(base_pdf_buf, dok_rows):
    """Jika ada berkas lampiran (surat dokter / foto surat izin / dokumen PDF),
    gabungkan ke dalam PDF di halaman-halaman berikutnya setelah Formulir & Kartu Cuti.
    """
    if not dok_rows:
        return base_pdf_buf

    valid_doks = []
    for d in dok_rows:
        fpath = os.path.join(UPLOAD_DIR, d["path_file"])
        if os.path.exists(fpath):
            valid_doks.append((d, fpath))

    if not valid_doks:
        return base_pdf_buf

    try:
        from pypdf import PdfWriter, PdfReader
        from PIL import Image as PILImage
        from reportlab.pdfgen import canvas

        writer = PdfWriter()
        base_reader = PdfReader(base_pdf_buf)
        for page in base_reader.pages:
            writer.add_page(page)

        for d, fpath in valid_doks:
            ext = d["path_file"].rsplit(".", 1)[-1].lower() if "." in d["path_file"] else ""
            if ext == "pdf":
                try:
                    att_reader = PdfReader(fpath)
                    for page in att_reader.pages:
                        writer.add_page(page)
                except Exception:
                    pass
            elif ext in ("jpg", "jpeg", "png"):
                try:
                    img_buf = io.BytesIO()
                    can = canvas.Canvas(img_buf, pagesize=A4)
                    wP, hP = A4
                    margin = 28

                    # Header keterangan lampiran
                    can.setFont("Helvetica-Bold", 10)
                    can.setFillColorRGB(0.17, 0.16, 0.39)
                    can.drawString(margin, hP - 26, "LAMPIRAN DOKUMEN / SURAT IZIN")
                    can.setFont("Helvetica", 8)
                    can.setFillColorRGB(0.4, 0.4, 0.4)
                    can.drawString(margin, hP - 38, f"Nama berkas: {d['nama_file']}")

                    with PILImage.open(fpath) as pil_img:
                        orig_w, orig_h = pil_img.size

                    avail_w = wP - (2 * margin)
                    avail_h = hP - 48 - margin

                    scale = min(avail_w / orig_w, avail_h / orig_h)
                    new_w = orig_w * scale
                    new_h = orig_h * scale
                    x = margin + (avail_w - new_w) / 2
                    y = margin + (avail_h - new_h) / 2

                    can.drawImage(fpath, x, y, width=new_w, height=new_h)
                    can.showPage()
                    can.save()
                    img_buf.seek(0)

                    att_reader = PdfReader(img_buf)
                    for page in att_reader.pages:
                        writer.add_page(page)
                except Exception:
                    pass

        out_buf = io.BytesIO()
        writer.write(out_buf)
        out_buf.seek(0)
        return out_buf
    except Exception:
        base_pdf_buf.seek(0)
        return base_pdf_buf

def _buat_formulir_kartu_pegawai(pid, th=None, pengajuan_id=None):
    """Hasilkan buffer PDF (Hal 1: Formulir Permintaan dan Pemberian Cuti Portrait,
    Hal 2: Kartu Cuti PNS Model Fe.03 Landscape, Hal 3+: Lampiran foto surat izin/dokter jika ada)
    untuk seorang pegawai. Sesuai format berkas SURAT_CUTI_UMUM.
    """
    e = db().execute("SELECT * FROM pegawai WHERE id=? AND role='pegawai'", (pid,)).fetchone()
    if not e:
        return None, None, None

    if th is None:
        th = tahun_aktif()

    p = None
    if pengajuan_id:
        p = db().execute("""SELECT c.*, e.nama, e.nip, e.golongan, e.unit_kerja,
            e.jabatan, e.masa_kerja, e.kelas_jabatan, e.tmt_kerja, e.atasan_nama, e.atasan_nip
            FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
            WHERE c.id=?""", (pengajuan_id,)).fetchone()
    if not p:
        p = db().execute("""SELECT c.*, e.nama, e.nip, e.golongan, e.unit_kerja,
            e.jabatan, e.masa_kerja, e.kelas_jabatan, e.tmt_kerja, e.atasan_nama, e.atasan_nip
            FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
            WHERE e.id=? ORDER BY c.id DESC LIMIT 1""", (pid,)).fetchone()

    if p:
        p = dict(p)
        if p.get("tanggal_mulai"):
            try: th = int(p["tanggal_mulai"][:4])
            except Exception: pass
    else:
        p = {
            "id": 0,
            "pegawai_id": e["id"],
            "nama": e["nama"],
            "nip": e["nip"] or "",
            "golongan": e["golongan"] or "",
            "unit_kerja": e["unit_kerja"] or "",
            "jabatan": e["jabatan"] or "",
            "masa_kerja": e["masa_kerja"] or "",
            "kelas_jabatan": e["kelas_jabatan"] or "",
            "tmt_kerja": e["tmt_kerja"] or "",
            "atasan_nama": e["atasan_nama"] or "",
            "atasan_nip": e["atasan_nip"] or "",
            "tanggal_surat": "",
            "nomor_surat": "",
            "jenis_cuti": "Cuti Tahunan",
            "alasan": "",
            "tanggal_mulai": "",
            "tanggal_selesai": "",
            "jumlah_hari": 0,
            "alamat_cuti": "",
            "telp_cuti": "",
            "status": "Menunggu"
        }

    dok_rows = []
    if pengajuan_id:
        dok_rows = list(db().execute("SELECT * FROM dokumen_cuti WHERE pengajuan_id=? ORDER BY id ASC", (pengajuan_id,)).fetchall())
    elif p and p.get("id"):
        dok_rows = list(db().execute("""SELECT d.* FROM dokumen_cuti d
            JOIN pengajuan_cuti c ON c.id=d.pengajuan_id
            WHERE c.pegawai_id=? AND (c.id=? OR (c.status='Disetujui' AND substr(c.tanggal_mulai,1,4)=?))
            ORDER BY c.id DESC, d.id ASC""", (pid, p["id"], str(th))).fetchall())

    j = ensure_jatah(pid, th); db().commit()
    j_prev = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid, th - 1)).fetchone()

    instansi       = get_set("instansi") or "DINAS PERHUBUNGAN DIY"
    kepala_nama    = get_set("kepala_nama") or ""
    kepala_nip     = get_set("kepala_nip") or ""
    kepala_jabatan = get_set("kepala_jabatan") or "Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta"

    el1 = _buat_formulir_flowables(p, j, j_prev, instansi, kepala_nama, kepala_nip, kepala_jabatan)

    # Hal 2: Kartu Cuti Fe.03
    rows_kartu = list(db().execute("""SELECT * FROM pengajuan_cuti
        WHERE pegawai_id=? AND jenis_cuti='Cuti Tahunan' AND status='Disetujui'
        AND substr(tanggal_mulai,1,4)=?
        ORDER BY tanggal_mulai ASC, id ASC""", (pid, str(th))).fetchall())
    el2 = _buat_kartu_flowables(e, j, rows_kartu, th, instansi, j_prev, compact=True)

    buf = io.BytesIO()

    # Halaman 1: A4 Portrait; Halaman 2: A4 Landscape
    wL, hL = landscape(A4)   # lebar ≈ 841.9 pt, tinggi ≈ 595.3 pt
    wP, hP = A4               # lebar ≈ 595.3 pt, tinggi ≈ 841.9 pt

    def page_fn_portrait(canvas, doc):
        canvas.setPageSize(A4)

    def page_fn_landscape(canvas, doc):
        canvas.setPageSize(landscape(A4))

    class TwoPageDoc(BaseDocTemplate):
        def __init__(self, b):
            super().__init__(b, leftMargin=12*mm, rightMargin=12*mm, topMargin=10*mm, bottomMargin=8*mm)
            f1 = Frame(12*mm, 8*mm, wP-24*mm, hP-18*mm, id="p1",
                       topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            f2 = Frame(15*mm, 10*mm, wL-30*mm, hL-22*mm, id="p2",
                       topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            self.addPageTemplates([
                PageTemplate(id="P1", frames=[f1], onPage=page_fn_portrait),
                PageTemplate(id="P2", frames=[f2], onPage=page_fn_landscape),
            ])

    story = el1 + [NextPageTemplate("P2"), PageBreak()] + el2
    doc2 = TwoPageDoc(buf)
    doc2.build(story)
    buf.seek(0)

    buf = _tambahkan_lampiran_ke_pdf(buf, dok_rows)

    return buf, e, p

def _buat_formulir_kartu(pengajuan_id):
    """Hasilkan buffer PDF 2 halaman A4:
    Hal 1 – Formulir Permintaan dan Pemberian Cuti
    Hal 2 – Kartu Cuti PNS (Model Fe.03)
    """
    p_row = db().execute("SELECT pegawai_id FROM pengajuan_cuti WHERE id=?", (pengajuan_id,)).fetchone()
    if not p_row:
        return None, None
    buf, e, p = _buat_formulir_kartu_pegawai(p_row["pegawai_id"], pengajuan_id=pengajuan_id)
    return buf, p

@app.route("/pengajuan/<int:pid>/formulir.pdf")
@login_required
def formulir_tunggal_pdf(pid):
    """Cetak Formulir Permintaan dan Pemberian Cuti (1 halaman A4 Portrait)."""
    p_check = db().execute("SELECT pegawai_id FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
    if not p_check:
        abort(404)
    if not boleh_akses(p_check["pegawai_id"]):
        abort(403)

    p = db().execute("""SELECT c.*, e.nama, e.nip, e.golongan, e.unit_kerja,
        e.jabatan, e.masa_kerja, e.kelas_jabatan, e.tmt_kerja, e.atasan_nama, e.atasan_nip
        FROM pengajuan_cuti c JOIN pegawai e ON e.id=c.pegawai_id
        WHERE c.id=?""", (pid,)).fetchone()
    if not p:
        abort(404)

    pid_peg = p["pegawai_id"]
    th = int(p["tanggal_mulai"][:4])
    j = ensure_jatah(pid_peg, th); db().commit()
    j_prev = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid_peg, th - 1)).fetchone()

    instansi       = get_set("instansi") or "DINAS PERHUBUNGAN DIY"
    kepala_nama    = get_set("kepala_nama") or ""
    kepala_nip     = get_set("kepala_nip") or ""
    kepala_jabatan = get_set("kepala_jabatan") or "Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=12*mm, rightMargin=12*mm,
                            topMargin=10*mm, bottomMargin=8*mm, title=f"Formulir Cuti {p['nama']}")
    el = _buat_formulir_flowables(p, j, j_prev, instansi, kepala_nama, kepala_nip, kepala_jabatan)
    doc.build(el)
    buf.seek(0)
    fname = f"Formulir_Cuti_{(p['nip'] or 'PNS').replace('/', '_')}_{p['tanggal_mulai'][:10]}.pdf"
    return send_file(buf, mimetype="application/pdf", download_name=fname,
                     as_attachment=request.args.get("unduh") == "1")

@app.route("/formulir/<int:pid>.pdf")
@login_required
def formulir_pdf(pid):
    """Cetak Formulir Permintaan & Pemberian Cuti + Kartu Cuti (2 halaman A4 Portrait)."""
    p_check = db().execute("SELECT pegawai_id FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
    if not p_check:
        abort(404)
    if not boleh_akses(p_check["pegawai_id"]):
        abort(403)
    buf, p = _buat_formulir_kartu(pid)
    if not buf:
        abort(404)
    fname = f"FormCuti_{(p['nip'] or 'PNS').replace('/', '_')}_{p['tanggal_mulai'][:10]}.pdf"
    return send_file(buf, mimetype="application/pdf", download_name=fname,
                     as_attachment=request.args.get("unduh") == "1")

@app.route("/pengajuan/<int:pid>/cetak-gabungan.pdf")
@login_required
def cetak_gabungan_pdf(pid):
    """Cetak SATU file PDF A4 berisi 2 halaman:
    Halaman 1: Formulir Permintaan dan Pemberian Cuti pengajuan itu
    Halaman 2: Kartu Cuti Fe.03 pegawai itu
    """
    p_check = db().execute("SELECT pegawai_id FROM pengajuan_cuti WHERE id=?", (pid,)).fetchone()
    if not p_check:
        abort(404)
    if not boleh_akses(p_check["pegawai_id"]):
        abort(403)
    buf, p = _buat_formulir_kartu(pid)
    if not buf:
        abort(404)
    fname = f"Formulir_Kartu_{(p['nip'] or 'PNS').replace('/', '_')}_{p['tanggal_mulai'][:10]}.pdf"
    return send_file(buf, mimetype="application/pdf", download_name=fname,
                     as_attachment=request.args.get("unduh") == "1")


# ---------------------------------------------------------------- import Excel
KUNCI = {"nip": ["nip"], "nama": ["nama"], "golongan": ["golongan", "gol", "pangkat"],
         "unit_kerja": ["unit", "bagian", "bidang"], "hak": ["hak", "jatah"],
         "diambil": ["diambil", "digunakan", "terpakai"], "sisa": ["sisa"], "tahun": ["tahun"]}

def baca_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    hasil = []
    for ws in wb.worksheets:
        hdr = None
        for r in range(1, min(ws.max_row, 20) + 1):
            vals = [str(c.value or "").strip().lower() for c in ws[r]]
            if any(v == "nip" or v.startswith("nip") for v in vals):
                hdr = r; break
        if not hdr: continue
        kolom = {}
        heads = [str(c.value or "").strip() for c in ws[hdr]]
        for i, h in enumerate(heads):
            for k, kws in KUNCI.items():
                if k not in kolom and any(w in h.lower() for w in kws): kolom[k] = i
        for row in ws.iter_rows(min_row=hdr + 1, values_only=True):
            nip = re.sub(r"\D", "", str(row[kolom["nip"]] or "")) if "nip" in kolom else ""
            if len(nip) < 8: continue
            d = {k: row[i] for k, i in kolom.items()}
            d["nip"] = nip; hasil.append(d)
        hasil_hdr = (ws.title, heads, kolom)
        hasil.append(("__info__", hasil_hdr))
    return hasil

def angka(v):
    try: return int(float(str(v).replace(",", ".")))
    except Exception: return None

@app.route("/admin/import", methods=["GET", "POST"])
@admin_required
def admin_import():
    prev = None
    if request.method == "POST":
        f = request.files.get("file")
        if f and f.filename.lower().endswith((".xlsx", ".xlsm")):
            f.save(os.path.join(DATA_DIR, "import_tmp.xlsx"))
            data = baca_excel(os.path.join(DATA_DIR, "import_tmp.xlsx"))
            info = [d[1] for d in data if isinstance(d, tuple)]
            rows = [d for d in data if isinstance(d, dict)]
            prev = dict(info=info, rows=rows[:10], total=len(rows))
        else:
            flash("Pilih file Excel (.xlsx).", "danger")
    return render_template("admin_import.html", prev=prev)

@app.route("/admin/import/proses", methods=["POST"])
@admin_required
def admin_import_proses():
    path = os.path.join(DATA_DIR, "import_tmp.xlsx")
    if not os.path.exists(path): abort(400)
    rows = [d for d in baca_excel(path) if isinstance(d, dict)]
    th, baru, lewat = tahun_aktif(), 0, 0
    if request.form.get("kosongkan") == "ya":
        for t in ("dokumen_cuti", "pengajuan_cuti", "jatah_cuti"): db().execute(f"DELETE FROM {t}")
        db().execute("DELETE FROM pegawai WHERE role='pegawai'")
    for d in rows:
        nama = str(d.get("nama") or "").strip()
        if not nama: continue
        if db().execute("SELECT 1 FROM pegawai WHERE nip=?", (d["nip"],)).fetchone(): lewat += 1; continue
        cur = db().execute("INSERT INTO pegawai(nip,nama,golongan,unit_kerja,username,password_hash) VALUES(?,?,?,?,?,?)",
            (d["nip"], nama, str(d.get("golongan") or "").strip(), str(d.get("unit_kerja") or "").strip(), d["nip"],
             generate_password_hash(d["nip"])))
        ensure_jatah(cur.lastrowid, th)
        hak, amb = angka(d.get("hak")), angka(d.get("diambil"))
        tambahan = max((hak or JATAH_DASAR) - JATAH_DASAR, 0)
        db().execute("""UPDATE jatah_cuti SET tambahan_dari_tahun_sebelumnya=?, digunakan_awal=? WHERE pegawai_id=? AND tahun=?""",
                     (tambahan, amb or 0, cur.lastrowid, th))
        recalc(cur.lastrowid, th); baru += 1
    db().commit()
    flash(f"Import selesai: {baru} pegawai baru, {lewat} dilewati (NIP sudah ada). Password awal = NIP.", "success")
    return redirect(url_for("admin_pegawai"))

# ---------------------------------------------------------------- kartu cuti PDF (Model Fe.03)
def format_rentang_tanggal(m_str, s_str, jumlah_hari=None):
    if not m_str: return "-"
    d1 = tgl(m_str) if isinstance(m_str, str) else m_str
    if not s_str or m_str == s_str:
        return f"{d1.day} {BULAN[d1.month]} {d1.year}"
    d2 = tgl(s_str) if isinstance(s_str, str) else s_str

    is_dan = False
    if jumlah_hari is not None and jumlah_hari > 0:
        hari_kerja = hitung_hari(d1, d2)
        if hari_kerja > jumlah_hari:
            is_dan = True

    if is_dan:
        if d1.year == d2.year and d1.month == d2.month:
            return f"{d1.day} dan {d2.day} {BULAN[d1.month]} {d1.year}"
        elif d1.year == d2.year:
            return f"{d1.day} {BULAN[d1.month]} dan {d2.day} {BULAN[d2.month]} {d1.year}"
        else:
            return f"{d1.day} {BULAN[d1.month]} {d1.year} dan {d2.day} {BULAN[d2.month]} {d2.year}"

    if d1.year == d2.year and d1.month == d2.month:
        return f"{d1.day} s.d {d2.day} {BULAN[d1.month]} {d1.year}"
    elif d1.year == d2.year:
        return f"{d1.day} {BULAN[d1.month]} s.d {d2.day} {BULAN[d2.month]} {d1.year}"
    else:
        return f"{d1.day} {BULAN[d1.month]} {d1.year} s.d {d2.day} {BULAN[d2.month]} {d2.year}"

def _buat_kartu_flowables(e, j, rows, th, instansi, j_prev=None, compact=False):
    """Menghasilkan elemen flowables Kartu Cuti Pegawai Negeri Sipil (Model Fe.03) A4 Portrait.
    compact=True: mode ringkas untuk landscape (baris lebih kecil, minimal padding).
    """
    W = 180 * mm

    def PS(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=8, leading=10)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    sModel   = PS("fe_model", fontSize=8.5, leading=10, alignment=TA_RIGHT)
    sTitle   = PS("fe_title", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER)
    sIdLabel = PS("fe_id_lbl", fontName="Helvetica-Bold", fontSize=8.5, leading=11)
    sIdVal   = PS("fe_id_val", fontName="Helvetica", fontSize=8.5, leading=11)
    sIdTh    = PS("fe_id_th", fontName="Helvetica-Bold", fontSize=9.5, leading=11, alignment=TA_RIGHT)

    sHdr     = PS("fe_hdr", fontName="Helvetica-Bold", fontSize=7.5, leading=9, alignment=TA_CENTER)
    sHdrNum  = PS("fe_hdr_num", fontName="Helvetica", fontSize=7, leading=8, alignment=TA_CENTER)
    sCellL   = PS("fe_cell_l", fontName="Helvetica", fontSize=7.5, leading=9.5, alignment=TA_LEFT)
    sCellC   = PS("fe_cell_c", fontName="Helvetica", fontSize=7.5, leading=9.5, alignment=TA_CENTER)

    el = []

    # 1. Judul & Model Fe.03
    t_top = Table([
        ["", Paragraph("Model: Fe.03", sModel)],
        [Paragraph("<b>KARTU CUTI PEGAWAI NEGERI SIPIL</b>", sTitle), ""]
    ], colWidths=[W - 35*mm, 35*mm])
    t_top.setStyle(TableStyle([
        ("SPAN", (0, 1), (1, 1)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    el.append(t_top)
    el.append(Spacer(1, 2.5*mm))

    # 2. Blok Identitas
    ident_data = [
        [Paragraph("INSTANSI", sIdLabel), Paragraph(":", sIdLabel), Paragraph(instansi, sIdVal), ""],
        [Paragraph("UNIT KERJA", sIdLabel), Paragraph(":", sIdLabel), Paragraph(e["unit_kerja"] or "-", sIdVal), ""],
        [Paragraph("NAMA", sIdLabel), Paragraph(":", sIdLabel), Paragraph(e["nama"], sIdVal), ""],
        [Paragraph("NIP", sIdLabel), Paragraph(":", sIdLabel), Paragraph(e["nip"] or "-", sIdVal), Paragraph(f"TH. {th}", sIdTh)],
    ]
    t_ident = Table(ident_data, colWidths=[24*mm, 4*mm, 112*mm, 40*mm])
    t_ident.setStyle(TableStyle([
        ("SPAN", (2, 0), (3, 0)),
        ("SPAN", (2, 1), (3, 1)),
        ("SPAN", (2, 2), (3, 2)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    el.append(t_ident)
    el.append(Spacer(1, 3*mm))

    # 3. Tabel Cuti 8 Kolom berborder penuh
    col_w = [8*mm, 36*mm, 24*mm, 34*mm, 15*mm, 27*mm, 21*mm, 15*mm]

    hdr0 = [
        Paragraph("NO", sHdr),
        Paragraph("JENIS CUTI", sHdr),
        Paragraph("KEPUTUSAN/SURAT IZIN<br/>PEMBERIAN IZIN", sHdr), "",
        Paragraph("LAMA<br/>CUTI", sHdr),
        Paragraph("MULAI S/D<br/>TANGGAL", sHdr),
        Paragraph("KETERANGAN", sHdr),
        Paragraph("PARAF PEJABAT<br/>KEPEGAWAIAN", sHdr),
    ]
    hdr1 = [
        "", "",
        Paragraph("PEJABAT", sHdr),
        Paragraph("NOMOR &amp;<br/>TANGGAL", sHdr),
        "", "", "", ""
    ]
    hdr2 = [Paragraph(str(i), sHdrNum) for i in range(1, 9)]

    t_data = [hdr0, hdr1, hdr2]

    # Baris Pertama: Saldo Awal Tahun
    sisa_th_lalu = j_prev["sisa_cuti"] if j_prev else (j["tambahan_dari_tahun_sebelumnya"] * 2 if j["tambahan_dari_tahun_sebelumnya"] else 0)
    txt_jc_awal = f"Cuti Tahunan TH. {th-1}<br/>Sisa: {sisa_th_lalu} hr"
    txt_ket_awal = f"Awal {th}: {j['jatah_dasar']} hr<br/>Sisa {th-1}: {j['tambahan_dari_tahun_sebelumnya']} hr<br/>Cuti Th {th}: {j['total_jatah']} hr"

    row_awal = [
        "",
        Paragraph(txt_jc_awal, sCellL),
        "", "", "", "",
        Paragraph(txt_ket_awal, sCellL),
        ""
    ]
    t_data.append(row_awal)

    # Baris Cuti Tahunan Berstatus Disetujui
    hak_total = j["total_jatah"]
    sisa_berjalan = hak_total - j["digunakan_awal"]

    for r in rows:
        sisa_sebelum = sisa_berjalan
        ambil = r["jumlah_hari"]
        sisa_sesudah = sisa_sebelum - ambil
        sisa_berjalan = sisa_sesudah

        txt_jc = f"Cuti Tahunan TH. {th}<br/>Sisa: {sisa_sebelum} hr"
        pejabat = ""
        no_surat = r["nomor_surat"] or ""
        tgl_surat = fmt(r["tanggal_surat"]) if r["tanggal_surat"] else ""
        if no_surat and tgl_surat:
            no_tgl = f"{no_surat}<br/>{tgl_surat}"
        elif no_surat:
            no_tgl = no_surat
        elif tgl_surat:
            no_tgl = tgl_surat
        else:
            no_tgl = ""

        lama_txt = f"{ambil} hari"
        tgl_txt = format_rentang_tanggal(r["tanggal_mulai"], r["tanggal_selesai"], ambil)
        ket_txt = f"Hak cuti {sisa_sebelum} Hr<br/>Ambil {ambil} Hr<br/>Sisa {sisa_sesudah} Hr"

        t_data.append([
            "",
            Paragraph(txt_jc, sCellL),
            Paragraph(pejabat, sCellC),
            Paragraph(no_tgl, sCellC),
            Paragraph(lama_txt, sCellC),
            Paragraph(tgl_txt, sCellC),
            Paragraph(ket_txt, sCellL),
            ""
        ])

    # Baris kosong: portrait 10 baris, landscape (compact) minimal 5 baris
    min_rows = 5 if compact else 10
    while len(t_data) - 3 < min_rows:
        t_data.append(["", "", "", "", "", "", "", ""])

    num_data_rows = len(t_data) - 3
    row_h = 14 * mm if compact else 17.5 * mm
    row_heights = [8*mm, 8*mm, 4.5*mm] + [row_h] * num_data_rows

    t_table = Table(t_data, colWidths=col_w, rowHeights=row_heights)
    t_style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (3, 0)),
        ("SPAN", (4, 0), (4, 1)),
        ("SPAN", (5, 0), (5, 1)),
        ("SPAN", (6, 0), (6, 1)),
        ("SPAN", (7, 0), (7, 1)),
        ("SPAN", (6, 3), (7, 3)),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("ALIGN", (0, 2), (-1, 2), "CENTER"),
    ]
    t_table.setStyle(TableStyle(t_style))
    el.append(t_table)
    return el

@app.route("/kartu/<int:pid>.pdf")
@login_required
def kartu_pdf(pid):
    if not boleh_akses(pid): abort(403)
    e = db().execute("SELECT * FROM pegawai WHERE id=? AND role='pegawai'", (pid,)).fetchone()
    if not e: abort(404)
    th = request.args.get("tahun", type=int) or tahun_aktif()

    # Opsi jika hanya ingin Kartu Cuti 1 Halaman
    if request.args.get("hanya_kartu") == "1":
        j = ensure_jatah(pid, th); db().commit()
        j_prev = db().execute("SELECT * FROM jatah_cuti WHERE pegawai_id=? AND tahun=?", (pid, th - 1)).fetchone()
        instansi = get_set("instansi") or "DINAS PERHUBUNGAN DIY"

        rows = db().execute("""SELECT * FROM pengajuan_cuti
            WHERE pegawai_id=? AND jenis_cuti='Cuti Tahunan' AND status='Disetujui'
            AND substr(tanggal_mulai,1,4)=?
            ORDER BY tanggal_mulai ASC, id ASC""", (pid, str(th))).fetchall()

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=12*mm, bottomMargin=10*mm, title=f"Kartu Cuti {e['nama']} {th}")
        el = _buat_kartu_flowables(e, j, rows, th, instansi, j_prev)
        doc.build(el)
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", download_name=f"Kartu_Cuti_{e['nip']}_{th}.pdf",
                         as_attachment=request.args.get("unduh") == "1")

    # Sesuai berkas SURAT_CUTI_UMUM: Cetak Dokumen Cuti mencakup Formulir Permintaan & Pemberian Cuti + Kartu Cuti PNS
    buf, e_obj, p_obj = _buat_formulir_kartu_pegawai(pid, th=th)
    if not buf: abort(404)
    fname = f"Formulir_Kartu_{(e['nip'] or 'PNS').replace('/', '_')}_{th}.pdf"
    return send_file(buf, mimetype="application/pdf", download_name=fname,
                     as_attachment=request.args.get("unduh") == "1")


@app.route("/kartu-saya")
@login_required
def kartu_saya():
    if g.user["role"] == "admin": return redirect(url_for("admin_kartu"))
    return redirect(url_for("kartu_pdf", pid=g.user["id"]))

@app.route("/formulir-saya")
@login_required
def formulir_saya():
    if g.user["role"] == "admin": return redirect(url_for("admin_kartu"))
    return redirect(url_for("kartu_pdf", pid=g.user["id"]))

@app.errorhandler(403)
def e403(_): return render_template("error.html", kode=403, pesan="Anda tidak memiliki akses ke halaman ini."), 403
@app.errorhandler(404)
def e404(_): return render_template("error.html", kode=404, pesan="Halaman tidak ditemukan."), 404
@app.errorhandler(400)
def e400(e): return render_template("error.html", kode=400, pesan=getattr(e, "description", "Permintaan tidak valid.")), 400
@app.errorhandler(413)
def e413(_): return render_template("error.html", kode=413, pesan="Ukuran file terlalu besar (maks. 5 MB)."), 413
@app.errorhandler(500)
def e500(_): return render_template("error.html", kode=500, pesan="Terjadi kesalahan pada server. Silakan coba lagi."), 500

init_db()
if __name__ == "__main__":
    import socket, threading, webbrowser
    port = 5000
    while port < 5010:  # cari port yang kosong jika 5000 dipakai program lain
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0: break
        port += 1

    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    url_local = f"http://127.0.0.1:{port}"
    url_lan = f"http://{local_ip}:{port}"
    print("\n" + "=" * 60)
    print(" SISTEM CUTI DISHUB DIY TELAH BERJALAN")
    print("=" * 60)
    print(f" * Akses di laptop/PC ini    : {url_local}")
    print(f" * Akses dari perangkat lain : {url_lan}")
    print("=" * 60)
    print(" Tutup jendela ini untuk menghentikan server.\n")

    threading.Timer(1.5, lambda: webbrowser.open(url_local)).start()
    app.run(host="0.0.0.0", port=port, debug=False)
