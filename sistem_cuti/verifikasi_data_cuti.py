#!/usr/bin/env python3
"""
Skrip verifikasi menyeluruh untuk memastikan data baru cuti 2026 di MySQL dan SQLite 100% akurat.
"""
import os
import sys
import sqlite3
import pymysql

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from db_config import (
    SQLITE_DB, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
)
from data_cuti_baru_60 import DATA_BARU_60

def verify_instance(conn, is_mysql=True):
    name = "MySQL (sicuti_dishub)" if is_mysql else "SQLite (database.db)"
    print(f"\nVerifikasi {name}:")
    cur = conn.cursor()

    # 1. Total pegawai aktif role pegawai
    if is_mysql:
        cur.execute("SELECT COUNT(*) AS c FROM pegawai WHERE role='pegawai' AND aktif=1")
        total_aktif = cur.fetchone()["c"]
    else:
        cur.execute("SELECT COUNT(*) AS c FROM pegawai WHERE role='pegawai' AND aktif=1")
        total_aktif = cur.fetchone()[0]

    print(f"  - Total pegawai aktif: {total_aktif} (harus 60)")
    assert total_aktif == 60, f"Error: Total aktif {total_aktif} != 60"

    # 2. Periksa setiap data pegawai dan sisa cuti
    mismatches = []
    for item in DATA_BARU_60:
        nip = item["nip"]
        param = "%s" if is_mysql else "?"
        sql = f"""
            SELECT p.id, p.nip, p.nama, p.golongan, p.jabatan, p.aktif,
                   j.jatah_dasar, j.tambahan_dari_tahun_sebelumnya, j.total_jatah,
                   j.digunakan_awal, j.total_digunakan, j.sisa_cuti
            FROM pegawai p
            LEFT JOIN jatah_cuti j ON p.id = j.pegawai_id AND j.tahun = 2026
            WHERE p.nip = {param}
        """
        cur.execute(sql, (nip,))
        if is_mysql:
            row = cur.fetchone()
        else:
            cols = [d[0] for d in cur.description]
            r = cur.fetchone()
            row = dict(zip(cols, r)) if r else None

        if not row:
            mismatches.append(f"NIP {nip} tidak ditemukan!")
            continue

        if row["nama"] != item["nama"]:
            mismatches.append(f"Nama beda untuk {nip}: DB '{row['nama']}' vs Target '{item['nama']}'")
        if row["golongan"] != item["golongan"]:
            mismatches.append(f"Golongan beda untuk {nip}: DB '{row['golongan']}' vs Target '{item['golongan']}'")
        if row["jabatan"] != item["jabatan"]:
            mismatches.append(f"Jabatan beda untuk {nip}: DB '{row['jabatan']}' vs Target '{item['jabatan']}'")
        if row["sisa_cuti"] != item["sisa_cuti"]:
            mismatches.append(f"Sisa cuti beda untuk {nip}: DB {row['sisa_cuti']} vs Target {item['sisa_cuti']}")

    if mismatches:
        print(f"  [GAGAL] Ditemukan {len(mismatches)} ketidaksesuaian:")
        for m in mismatches[:10]:
            print("    *", m)
        return False
    else:
        print(f"  [OK] Seluruh 60 data pegawai dan sisa cuti di {name} COCOK 100%!")
        return True

def test_recalc_idempotency():
    """Uji apakah memanggil recalc() mempertahankan nilai sisa_cuti sesuai target"""
    print("\nUji Idempotensi recalc() dengan app.py...")
    from app import app, recalc
    with app.app_context():
        from app import db
        for item in DATA_BARU_60:
            p = db().execute("SELECT id FROM pegawai WHERE nip=?", (item["nip"],)).fetchone()
            if not p:
                print(f"Pegawai {item['nip']} tidak ada di context!")
                continue
            recalc(p["id"], 2026)
            j = db().execute("SELECT sisa_cuti FROM jatah_cuti WHERE pegawai_id=? AND tahun=2026", (p["id"],)).fetchone()
            assert j["sisa_cuti"] == item["sisa_cuti"], f"Recalc mengubah sisa_cuti {j['sisa_cuti']} != {item['sisa_cuti']} for {item['nip']}"
        db().commit()
    print("  [OK] Seluruh sisa_cuti setelah pemanggilan fungsi recalc() tetap tepat 100%!")

def main():
    print("=" * 70)
    print("MEMULAI VERIFIKASI DATA")
    print("=" * 70)

    # Verifikasi MySQL
    mysql_conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        port=MYSQL_PORT,
        database=MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    ok_mysql = verify_instance(mysql_conn, is_mysql=True)
    mysql_conn.close()

    # Verifikasi SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    ok_sqlite = verify_instance(sqlite_conn, is_mysql=False)
    sqlite_conn.close()

    # Uji recalc di context app
    test_recalc_idempotency()

    if ok_mysql and ok_sqlite:
        print("\n" + "=" * 70)
        print("SEMUA VERIFIKASI BERHASIL 100%!")
        print("=" * 70)

if __name__ == "__main__":
    main()
