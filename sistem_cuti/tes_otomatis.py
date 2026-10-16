"""Pengujian otomatis (jalankan: python tes_otomatis.py). Memakai database sementara."""
import os, io, re, tempfile, openpyxl
import app as A
A.DB_PATH = os.path.join(tempfile.mkdtemp(), "tes.db"); A.init_db()
c = A.app.test_client()
def tok(r): return re.search(r'name="_csrf" value="(\w+)"', r.get_data(as_text=True)).group(1)
def login(cl, u, p):
    cl.get("/logout"); t = tok(cl.get("/login"))
    return cl.post("/login", data={"username": u, "password": p, "_csrf": t}, follow_redirects=True)
def post(cl, url, page, **d):
    t = tok(cl.get(page)); d["_csrf"] = t
    return cl.post(url, data=d, follow_redirects=True)
ok = lambda n, cond: print(("LULUS  " if cond else "GAGAL  ") + n) or (cond or exit(1))

# Excel contoh
wb = openpyxl.Workbook(); ws = wb.active; ws.append(["DAFTAR CUTI"]); ws.append([])
ws.append(["No", "NIP", "Nama", "Golongan", "Unit Kerja", "Hak Cuti", "Cuti Diambil"])
ws.append([1, "199209232025211051", "Pegawai A", "III/a", "Sekretariat", 12, 0])
ws.append([2, "198001012005011002", "Pegawai B", "III/b", "Bidang X", 12, 0])
p = os.path.join(A.DATA_DIR, "contoh.xlsx"); wb.save(p)

adm, a, b = A.app.test_client(), A.app.test_client(), A.app.test_client()
login(adm, "admin", "admin123")
r = adm.post("/admin/import", data={"_csrf": tok(adm.get("/admin/import")), "file": (open(p, "rb"), "x.xlsx")}, content_type="multipart/form-data")
ok("Import: struktur Excel terbaca", "Pegawai A" in r.get_data(as_text=True))
adm.post("/admin/import/proses", data={"_csrf": tok(adm.get("/admin/import"))}, follow_redirects=True)
ok("Import: pegawai masuk", "Pegawai B" in adm.get("/admin/pegawai").get_data(as_text=True))
adm.post("/admin/import/proses", data={"_csrf": tok(adm.get("/admin/import"))}, follow_redirects=True)
ok("Import ulang tidak menggandakan NIP", A.sqlite3.connect(A.DB_PATH).execute("select count(*) from pegawai where role='pegawai'").fetchone()[0] == 2)

TH = A.tahun_aktif() if False else int(A.date.today().year)
login(a, "199209232025211051", "199209232025211051"); login(b, "198001012005011002", "198001012005011002")
ok("Test1: A melihat datanya sendiri", "Pegawai A" in a.get("/dashboard").get_data(as_text=True) and "Pegawai B" not in a.get("/dashboard").get_data(as_text=True))
ok("Test2: A akses PDF kartu B -> 403", a.get("/kartu/3.pdf").status_code == 403)
ok("Test2: A akses admin -> 403", a.get("/admin").status_code == 403 and a.get("/admin/pegawai").status_code == 403)
ok("Tanpa login diarahkan ke login", A.app.test_client().get("/dashboard").status_code == 302)
ok("POST tanpa token CSRF ditolak", a.post("/ajukan", data={}).status_code == 400)

d0 = f"{TH}-10-05"  # Senin? hitung hari kerja 3 hari:
import datetime as dt
senin = dt.date(TH, 10, 1)
while senin.weekday() != 0: senin += dt.timedelta(days=1)
def ajukan(cl, jenis="Cuti Tahunan", m=senin, hari=3, bukti=None):
    d = {"_csrf": tok(cl.get("/ajukan")), "jenis_cuti": jenis, "tanggal_mulai": m.isoformat(),
         "tanggal_selesai": (m + dt.timedelta(days=hari - 1)).isoformat(), "alasan": "tes"}
    if bukti: d["bukti"] = bukti
    return cl.post("/ajukan", data=d, content_type="multipart/form-data", follow_redirects=True)
ajukan(a)
ok("Test3: muncul di dashboard admin", "Pengajuan Cuti Baru (1)" in adm.get("/admin").get_data(as_text=True))
ok("Jatah belum berkurang saat Menunggu", "<div class=\"n\">0 hari" in a.get("/dashboard").get_data(as_text=True))
with A.app.app_context():
    ok("Akhir pekan tidak dihitung (Jumat-Senin = 2 hari)", A.hitung_hari(senin - dt.timedelta(days=3), senin) == 2)
ok("B tidak bisa buka pengajuan A", b.get("/pengajuan/1").status_code == 403)
adm.post("/admin/pengajuan/1/proses", data={"_csrf": tok(adm.get("/pengajuan/1")), "aksi": "setuju"}, follow_redirects=True)
dsh = a.get("/dashboard").get_data(as_text=True)
ok("Test4: disetujui, terpakai 3 hari, sisa 9", "3 hari" in dsh and "9 hari" in dsh)
r = adm.post("/admin/pengajuan/1/proses", data={"_csrf": tok(adm.get("/admin/pegawai")), "aksi": "setuju"}, follow_redirects=True)
ok("Test8: setuju kedua kali tidak mengurangi lagi", "9 hari" in a.get("/dashboard").get_data(as_text=True) and "sudah diproses" in r.get_data(as_text=True))
ajukan(a, m=senin + dt.timedelta(days=7), hari=1)
adm.post("/admin/pengajuan/2/proses", data={"_csrf": tok(adm.get("/pengajuan/2")), "aksi": "tolak", "catatan": "x"}, follow_redirects=True)
ok("Test5: ditolak, jatah tetap 9", "9 hari" in a.get("/dashboard").get_data(as_text=True))
r = ajukan(a, "Cuti Sakit"); ok("Cuti sakit tanpa bukti ditolak", "wajib melampirkan" in r.get_data(as_text=True))
r = ajukan(a, "Cuti Sakit", m=senin + dt.timedelta(days=14), hari=1, bukti=(io.BytesIO(b"MZ\x90 bukan pdf"), "evil.pdf"))
ok("Upload file palsu/berbahaya ditolak", "tidak sesuai" in r.get_data(as_text=True))
r = ajukan(a, "Cuti Sakit", m=senin + dt.timedelta(days=14), hari=1, bukti=(io.BytesIO(b"%PDF-1.4 ok"), "surat.pdf"))
ok("Upload PDF sah diterima", "berhasil dikirim" in r.get_data(as_text=True))
ok("Admin bisa unduh bukti", adm.get("/bukti/1").status_code == 200)
ok("B tidak bisa unduh bukti A", b.get("/bukti/1").status_code == 403)
# Test 6: tahun baru
r = post(adm, "/admin/tahun-baru", "/admin/tahun-baru", konfirmasi=str(TH + 1))
cn = A.sqlite3.connect(A.DB_PATH)
ok("Test6: A 2027 = 12 + ceil(9/2)=5 -> 17", cn.execute("select total_jatah from jatah_cuti where pegawai_id=2 and tahun=?", (TH+1,)).fetchone()[0] == 17)
ok("Test6: B 2027 = 12 + 6 = 18", cn.execute("select total_jatah from jatah_cuti where pegawai_id=3 and tahun=?", (TH+1,)).fetchone()[0] == 18)
ok("Data tahun lama tetap ada", cn.execute("select count(*) from jatah_cuti where tahun=?", (TH,)).fetchone()[0] == 2)
r = post(adm, "/admin/tahun-baru", "/admin/tahun-baru", konfirmasi=str(TH + 1))
ok("Tahun baru tidak bisa dibuat dua kali", "ditolak" in r.get_data(as_text=True) or cn.execute("select count(*) from jatah_cuti where tahun=?", (TH+1,)).fetchone()[0] == 2)
r = adm.get(f"/kartu/2.pdf?tahun={TH}")
ok("Test7: PDF kartu cuti terbentuk", r.status_code == 200 and r.data[:4] == b"%PDF")
open(os.path.join(A.BASE, "pdf", "contoh_kartu.pdf"), "wb").write(r.data)
ok("Pegawai A bisa cetak kartunya sendiri", a.get("/kartu-saya", follow_redirects=True).status_code == 200)
print("\nSEMUA PENGUJIAN LULUS")
