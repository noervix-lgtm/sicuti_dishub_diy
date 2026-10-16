"""Migrasi non-destruktif: tambah kolom baru jika belum ada."""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

KOLOM_BARU = {
    "pegawai": [
        ("jabatan",      "TEXT DEFAULT ''"),
        ("masa_kerja",   "TEXT DEFAULT ''"),
        ("atasan_nama",  "TEXT DEFAULT ''"),
        ("atasan_nip",   "TEXT DEFAULT ''"),
    ],
    "pengajuan_cuti": [
        ("alamat_cuti",  "TEXT DEFAULT ''"),
        ("telp_cuti",    "TEXT DEFAULT ''"),
    ],
}

PENGATURAN_BARU = [
    ("kepala_nama",    ""),
    ("kepala_nip",     ""),
    ("kepala_jabatan", "Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta"),
]

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

for tabel, kolom_list in KOLOM_BARU.items():
    existing = {r["name"] for r in c.execute(f"PRAGMA table_info({tabel})").fetchall()}
    for kolom, tipe in kolom_list:
        if kolom not in existing:
            c.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {tipe}")
            print(f"  + {tabel}.{kolom} ditambahkan")
        else:
            print(f"  = {tabel}.{kolom} sudah ada, dilewati")

for kunci, nilai_default in PENGATURAN_BARU:
    c.execute("INSERT OR IGNORE INTO pengaturan VALUES(?,?)", (kunci, nilai_default))
    print(f"  + pengaturan[{kunci}] pastikan ada")

c.commit()
c.close()
print("\nMigrasi selesai. Database tidak merusak data lama.")
