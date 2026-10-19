"""Modul adapter database untuk Sistem Cuti Dishub.
Mendukung MySQL (Laragon) dengan fallback ke SQLite jika diperlukan.
"""
import os
import re
import sqlite3
import pymysql

# Konfigurasi Koneksi Database MySQL (Laragon)
DB_TYPE = os.environ.get("DB_TYPE", "mysql")  # 'mysql' atau 'sqlite'
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "sicuti_dishub")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(BASE_DIR, "database.db")

# Unified IntegrityError
IntegrityError = (sqlite3.IntegrityError, pymysql.MySQLError)

MYSQL_TABLE_SCHEMAS = [
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

class Row(dict):
    """Wrapper baris hasil query yang mendukung akses:
    - Dict key: row['nama']
    - Index tuple: row[0]
    - Method get: row.get('nama', default)
    - Konversi dict: dict(row)
    """
    def __init__(self, description, values):
        super().__init__()
        self._values = tuple(values)
        self._cols = [d[0] for d in description] if description else []
        for col, val in zip(self._cols, values):
            self[col] = val

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    def keys(self):
        return self._cols


class MySQLCursorWrapper:
    """Wrapper kursor PyMySQL agar kompatibel dengan cursor SQLite."""
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
        self.rowcount = 0
        self.description = None

    def _prepare_query(self, query):
        q = query
        # Normalisasi SQLite syntax -> MySQL syntax
        if "INSERT OR IGNORE" in q:
            q = q.replace("INSERT OR IGNORE", "INSERT IGNORE")
        if "INSERT OR REPLACE" in q:
            q = q.replace("INSERT OR REPLACE", "REPLACE")
        if "PRAGMA foreign_keys" in q:
            q = "SET FOREIGN_KEY_CHECKS=1"
        if "PRAGMA table_info" in q:
            m = re.search(r"PRAGMA\s+table_info\((.*?)\)", q, re.I)
            if m:
                tbl = m.group(1).strip()
                q = f"SELECT COLUMN_NAME as name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{tbl}'"
        # Ganti placeholder SQLite (?) menjadi MySQL (%s)
        q = q.replace("?", "%s")
        return q

    def execute(self, query, args=None):
        q = self._prepare_query(query)
        if args is not None:
            self.cursor.execute(q, args)
        else:
            self.cursor.execute(q)
        self.lastrowid = self.cursor.lastrowid
        self.rowcount = self.cursor.rowcount
        self.description = self.cursor.description
        return self

    def executemany(self, query, args_list):
        q = self._prepare_query(query)
        self.cursor.executemany(q, args_list)
        self.lastrowid = self.cursor.lastrowid
        self.rowcount = self.cursor.rowcount
        self.description = self.cursor.description
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return Row(self.description, row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [Row(self.description, r) for r in rows]

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def close(self):
        self.cursor.close()


class MySQLConnectionWrapper:
    """Wrapper koneksi PyMySQL agar menyediakan antarmuka seperti sqlite3.Connection."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return MySQLCursorWrapper(self.conn.cursor())

    def execute(self, query, args=None):
        cur = self.cursor()
        cur.execute(query, args)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db():
    """Mengembalikan koneksi database yang siap digunakan."""
    import sys
    app_mod = sys.modules.get("app")
    custom_sqlite = getattr(app_mod, "DB_PATH", None) if app_mod else None

    # Jika sedang dalam test dengan custom sqlite DB_PATH, langsung gunakan SQLite
    if custom_sqlite and custom_sqlite != SQLITE_DB:
        conn = sqlite3.connect(custom_sqlite)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    if DB_TYPE == "mysql":
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                port=MYSQL_PORT,
                database=MYSQL_DB,
                charset="utf8mb4",
                autocommit=False
            )
            return MySQLConnectionWrapper(conn)
        except Exception:
            # Fallback ke SQLite jika koneksi MySQL gagal
            pass

    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
