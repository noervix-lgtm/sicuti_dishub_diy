"""Script migrasi data dari SQLite (database.db) ke MySQL Laragon (sicuti_dishub)"""
import sqlite3
import pymysql
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(BASE_DIR, "database.db")

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "port": 3306,
    "database": "sicuti_dishub",
    "charset": "utf8mb4"
}

TABLE_SCHEMAS = [
    """CREATE TABLE IF NOT EXISTS pegawai (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nip VARCHAR(50) UNIQUE,
        nama VARCHAR(255) NOT NULL,
        golongan VARCHAR(50) DEFAULT '',
        unit_kerja VARCHAR(255) DEFAULT '',
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'pegawai',
        aktif INT DEFAULT 1,
        jabatan VARCHAR(255) DEFAULT '',
        masa_kerja VARCHAR(100) DEFAULT '',
        atasan_nama VARCHAR(255) DEFAULT '',
        atasan_nip VARCHAR(50) DEFAULT '',
        kelas_jabatan VARCHAR(50) DEFAULT '',
        tmt_kerja VARCHAR(50) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS jatah_cuti (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pegawai_id INT NOT NULL,
        tahun INT NOT NULL,
        jatah_dasar INT NOT NULL DEFAULT 12,
        tambahan_dari_tahun_sebelumnya INT NOT NULL DEFAULT 0,
        total_jatah INT NOT NULL DEFAULT 12,
        digunakan_awal INT NOT NULL DEFAULT 0,
        total_digunakan INT NOT NULL DEFAULT 0,
        sisa_cuti INT NOT NULL DEFAULT 12,
        cuti_dibawa_ke_tahun_berikutnya INT NOT NULL DEFAULT 0,
        UNIQUE KEY uq_pegawai_tahun (pegawai_id, tahun),
        CONSTRAINT fk_jatah_pegawai FOREIGN KEY (pegawai_id) REFERENCES pegawai(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS pengajuan_cuti (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pegawai_id INT NOT NULL,
        jenis_cuti VARCHAR(100) NOT NULL,
        tanggal_mulai VARCHAR(20) NOT NULL,
        tanggal_selesai VARCHAR(20) NOT NULL,
        jumlah_hari INT NOT NULL,
        alasan TEXT,
        status VARCHAR(50) NOT NULL DEFAULT 'Menunggu',
        tanggal_pengajuan VARCHAR(20) NOT NULL,
        memotong_jatah INT NOT NULL DEFAULT 1,
        catatan_admin TEXT,
        nomor_surat VARCHAR(100) DEFAULT '',
        tanggal_surat VARCHAR(20) DEFAULT '',
        diproses_oleh INT,
        tanggal_proses VARCHAR(20),
        alamat_cuti TEXT,
        telp_cuti VARCHAR(50) DEFAULT '',
        CONSTRAINT fk_pengajuan_pegawai FOREIGN KEY (pegawai_id) REFERENCES pegawai(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS dokumen_cuti (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pengajuan_id INT NOT NULL,
        nama_file VARCHAR(255) NOT NULL,
        path_file VARCHAR(255) NOT NULL,
        CONSTRAINT fk_dokumen_pengajuan FOREIGN KEY (pengajuan_id) REFERENCES pengajuan_cuti(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS hari_libur (
        tanggal VARCHAR(20) PRIMARY KEY,
        keterangan VARCHAR(255) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS pengaturan (
        kunci VARCHAR(100) PRIMARY KEY,
        nilai TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
]

def migrate():
    print(f"Membuka database SQLite: {SQLITE_DB}...")
    s_conn = sqlite3.connect(SQLITE_DB)
    s_conn.row_factory = sqlite3.Row

    print("Menghubungkan ke MySQL Laragon...")
    m_conn = pymysql.connect(**MYSQL_CONFIG)

    with m_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0;")
        for schema in TABLE_SCHEMAS:
            cur.execute(schema)
        m_conn.commit()
        print("Tabel-tabel MySQL berhasil dibuat.")

        # Tabel yang akan dimigrasikan secara berurutan
        tables = ["pegawai", "jatah_cuti", "pengajuan_cuti", "dokumen_cuti", "hari_libur", "pengaturan"]
        for tbl in tables:
            # Ambil kolom dari sqlite
            s_rows = s_conn.execute(f"SELECT * FROM {tbl}").fetchall()
            if not s_rows:
                print(f"- {tbl}: 0 baris (kosong)")
                continue

            cols = s_rows[0].keys()
            col_names = ", ".join([f"`{c}`" for c in cols])
            placeholders = ", ".join(["%s"] * len(cols))
            insert_sql = f"REPLACE INTO `{tbl}` ({col_names}) VALUES ({placeholders})"

            data = []
            for r in s_rows:
                row_data = [r[c] for c in cols]
                data.append(row_data)

            cur.executemany(insert_sql, data)
            m_conn.commit()
            print(f"- {tbl}: {len(data)} baris berhasil dipindahkan ke MySQL!")

        cur.execute("SET FOREIGN_KEY_CHECKS=1;")
        m_conn.commit()

    s_conn.close()
    m_conn.close()
    print("\nMigrasi ke MySQL Laragon selesai dengan sukses!")

if __name__ == "__main__":
    migrate()
