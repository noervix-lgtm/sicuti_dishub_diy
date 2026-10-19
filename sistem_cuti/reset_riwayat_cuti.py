#!/usr/bin/env python3
"""Skrip untuk mengosongkan riwayat cuti dan mengembalikan saldo cuti ke keadaan awal."""
import os
import sys
import math
import shutil
import sqlite3
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
BACKUP_PATH = os.path.join(BASE_DIR, "database_sebelum_reset.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads", "bukti_cuti")

def main():
    parser = argparse.ArgumentParser(description="Kosongkan riwayat cuti dan kembalikan saldo cuti.")
    parser.add_argument("--ya", action="store_true", help="Lewati konfirmasi interaktif")
    args = parser.parse_args()

    from db_config import get_db, DB_TYPE

    # 1. Hitung dan tampilkan status data saat ini
    con = get_db()
    cur = con.cursor()

    c_pengajuan = cur.execute("SELECT COUNT(*) FROM pengajuan_cuti").fetchone()[0]
    c_dokumen = cur.execute("SELECT COUNT(*) FROM dokumen_cuti").fetchone()[0]

    files_bukti = []
    if os.path.exists(UPLOADS_DIR):
        files_bukti = [f for f in os.listdir(UPLOADS_DIR) if os.path.isfile(os.path.join(UPLOADS_DIR, f))]
    c_files = len(files_bukti)

    print("=" * 60)
    print("STATUS DATA RIWAYAT CUTI SAAT INI")
    print("=" * 60)
    print(f"- Jumlah baris pengajuan_cuti : {c_pengajuan}")
    print(f"- Jumlah baris dokumen_cuti   : {c_dokumen}")
    print(f"- Jumlah file di bukti_cuti/  : {c_files}")
    print("=" * 60)

    # 2. Minta konfirmasi (ketik 'YA' untuk lanjut)
    if not args.ya:
        konfirmasi = input("Ketik 'YA' untuk melanjutkan reset (selain itu akan dibatalkan): ").strip()
        if konfirmasi != "YA":
            print("Reset dibatalkan. Tidak ada data yang diubah.")
            con.close()
            sys.exit(0)

    # 3. Cadangkan database jika SQLite
    con.close()
    if DB_TYPE == "sqlite" and os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"Cadangan database berhasil dibuat: {os.path.basename(BACKUP_PATH)}")

    con = get_db()
    cur = con.cursor()

    # 4. Hapus data dokumen_cuti dan pengajuan_cuti, lalu reset sequence
    cur.execute("DELETE FROM dokumen_cuti")
    cur.execute("DELETE FROM pengajuan_cuti")
    if DB_TYPE == "sqlite":
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('pengajuan_cuti', 'dokumen_cuti')")
    else:
        cur.execute("ALTER TABLE pengajuan_cuti AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE dokumen_cuti AUTO_INCREMENT = 1")

    # 5. Hitung ulang saldo setiap baris di jatah_cuti
    rows_jatah = cur.execute("SELECT id, jatah_dasar, tambahan_dari_tahun_sebelumnya, digunakan_awal FROM jatah_cuti").fetchall()
    for r in rows_jatah:
        total_jatah = r["jatah_dasar"] + r["tambahan_dari_tahun_sebelumnya"]
        total_digunakan = r["digunakan_awal"]
        sisa_cuti = total_jatah - r["digunakan_awal"]
        carry = math.ceil(max(sisa_cuti, 0) / 2)
        cur.execute("""UPDATE jatah_cuti SET
            total_jatah = ?,
            total_digunakan = ?,
            sisa_cuti = ?,
            cuti_dibawa_ke_tahun_berikutnya = ?
            WHERE id = ?""", (total_jatah, total_digunakan, sisa_cuti, carry, r["id"]))

    # 6. Commit lalu VACUUM
    con.commit()
    cur.execute("VACUUM")
    con.close()

    # 7. Hapus semua file di dalam folder uploads/bukti_cuti/ (folder tetap dibiarkan ada)
    if os.path.exists(UPLOADS_DIR):
        for f in os.listdir(UPLOADS_DIR):
            file_path = os.path.join(UPLOADS_DIR, f)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Gagal menghapus file {f}: {e}")
            elif os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Gagal menghapus folder {f}: {e}")

    # 8. Cetak pesan selesai
    print("Selesai. Riwayat cuti kosong, saldo cuti kembali ke awal.")

if __name__ == "__main__":
    main()
