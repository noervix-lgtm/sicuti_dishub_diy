"""Data lengkap 60 pegawai berdasarkan dokumen PDF terbaru:
Halaman 1 (1-45): NIP & NAMA
Halaman 2 (46-60): NIP & NAMA
Halaman 3 (1-45): GOLONGAN, JABATAN, SISA CUTI
Halaman 4 (46-60): GOLONGAN, JABATAN, SISA CUTI
"""

DATA_BARU_60 = [
    {
        "no": 1,
        "nip": "196905021991022002",
        "nama": "CHRESTINA ERNI WIDYASTUTI S.E., M.Si.",
        "golongan": "Pembina Utama Muda/IV/c",
        "jabatan": "Kepala Dinas Perhubungan",
        "sisa_cuti": 18
    },
    {
        "no": 2,
        "nip": "197207201998032003",
        "nama": "ETIK ESTIMAYASTI S.E., M.Si.",
        "golongan": "Pembina Tk. I/IV/b",
        "jabatan": "Sekretaris",
        "sisa_cuti": 18
    },
    {
        "no": 3,
        "nip": "198908152015021002",
        "nama": "MUHAMMAD SYAIFUL NAZAR S.S.T. (T.D), M.Sc.",
        "golongan": "Penata/III/c",
        "jabatan": "Kepala Subbagian Program",
        "sisa_cuti": 12
    },
    {
        "no": 4,
        "nip": "199503212025042002",
        "nama": "RIZKY NUR ZHAFIRAH, S.Kom.",
        "golongan": "Penata Muda/III/a",
        "jabatan": "Penata Kelola Sistem dan Teknologi Informasi",
        "sisa_cuti": 11
    },
    {
        "no": 5,
        "nip": "199612102020121008",
        "nama": "LALU ANUGERAH KEVIN ALGINOLA, S.S.T(TD).",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 16
    },
    {
        "no": 6,
        "nip": "199502262022021001",
        "nama": "MUHAMMAD PANDU SATRIO, S.Tr.Tra",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 16
    },
    {
        "no": 7,
        "nip": "197505131999032003",
        "nama": "AYU KUSUMA NURHAYANTI S.E.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Subbagian Keuangan",
        "sisa_cuti": 10
    },
    {
        "no": 8,
        "nip": "200005252022012006",
        "nama": "FATIN AZZAHRA MEIDA, A.Md.Ak.",
        "golongan": "Pengatur Tk. I/II/d",
        "jabatan": "Pengolah Data dan Informasi",
        "sisa_cuti": 6
    },
    {
        "no": 9,
        "nip": "197211281998032004",
        "nama": "FARISTIN HERAWATI, S.E.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 12
    },
    {
        "no": 10,
        "nip": "196902201991031006",
        "nama": "SUPARJANA",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 7
    },
    {
        "no": 11,
        "nip": "196906081991032005",
        "nama": "SRI PURWANINGSIH",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 10
    },
    {
        "no": 12,
        "nip": "197907082009121003",
        "nama": "QURNIAWAN YULIANTO ST",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Subbagian Umum",
        "sisa_cuti": 15
    },
    {
        "no": 13,
        "nip": "198502272010122002",
        "nama": "FEBRI YULIASTUTI, S.Pd.T",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 11
    },
    {
        "no": 14,
        "nip": "196902012007011017",
        "nama": "HENDAR SUNARTO, S.I.P.",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 12
    },
    {
        "no": 15,
        "nip": "198207052012121001",
        "nama": "HARTANTO, S.Ak.",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 13
    },
    {
        "no": 16,
        "nip": "198101152009122002",
        "nama": "DIAN PERMATA SARI, S.E., M.M",
        "golongan": "Pembina/IV/a",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 16
    },
    {
        "no": 17,
        "nip": "197305212005011005",
        "nama": "RIZKI BUDI UTOMO S.T., M.T.",
        "golongan": "Pembina Tk. I/IV/b",
        "jabatan": "Kepala Bidang Angkutan",
        "sisa_cuti": 18
    },
    {
        "no": 18,
        "nip": "198806112011012010",
        "nama": "YUNI KARUNIAWATI S.Si.T., M.M.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Seksi Angkutan Perkotaan",
        "sisa_cuti": 15
    },
    {
        "no": 19,
        "nip": "198710022010121002",
        "nama": "ADITYA AJI MUSTOFA, M.Sc.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 13
    },
    {
        "no": 20,
        "nip": "199804222022022002",
        "nama": "PRELLA PUSPITANING WITRI ARDY, S.Tr.Tra",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 9
    },
    {
        "no": 21,
        "nip": "198810212011011007",
        "nama": "AGHA PERDANA PUTRO S.SiT., M.T.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Seksi Angkutan Tidak Dalam Trayek dan Antar Wilayah",
        "sisa_cuti": 18
    },
    {
        "no": 22,
        "nip": "199703162020121010",
        "nama": "ANUGRAH TRI SAPUTRA, S.S.T. (TD), M.T.",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 6
    },
    {
        "no": 23,
        "nip": "197607301998032002",
        "nama": "WINDIARTI DWI LESTARI, S.Si.T., M.Si.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 7
    },
    {
        "no": 24,
        "nip": "198307062006041002",
        "nama": "WULAN SAPTO NUGROHO S.Si.T., M.T.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Kepala Bidang Lalu Lintas",
        "sisa_cuti": 17
    },
    {
        "no": 25,
        "nip": "197004241991012001",
        "nama": "RISTINI S.E.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Seksi Manajemen dan Rekayasa Lalu Lintas",
        "sisa_cuti": 4
    },
    {
        "no": 26,
        "nip": "199003052015021003",
        "nama": "FAKHRUDIN SETIAWAN, S.S.T (TD)",
        "golongan": "Penata/III/c",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 12
    },
    {
        "no": 27,
        "nip": "199612242020121011",
        "nama": "LAGA BROVI MANGGALA, S.S.T (TD)",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 16
    },
    {
        "no": 28,
        "nip": "198105122005011009",
        "nama": "TAUFAN ABDI SOELAIMAN S.T., M.Sc.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Kepala Seksi Teknologi Transportasi",
        "sisa_cuti": 6
    },
    {
        "no": 29,
        "nip": "197003191999031001",
        "nama": "FREDERICUS ISMULYATNO GUNO T, A.Md",
        "golongan": "Penata/III/c",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 16
    },
    {
        "no": 30,
        "nip": "198310142006041006",
        "nama": "ADI DARMAWAN HARIADI, S.T., M.Ec.Dev.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 15
    },
    {
        "no": 31,
        "nip": "197407141999031005",
        "nama": "LAZUARDI S.Si.T., M.M.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Kepala Seksi Pengendalian Operasional Lalu Lintas",
        "sisa_cuti": 16
    },
    {
        "no": 32,
        "nip": "196909091992021003",
        "nama": "CATUR PRIYO PAMUNGKAS, S.H",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 17
    },
    {
        "no": 33,
        "nip": "198404302011011009",
        "nama": "APRINANTO, S.Tr., M.M",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 13
    },
    {
        "no": 34,
        "nip": "197802142005011001",
        "nama": "VALENTINUS BUDI SANTOSO S.Sos., M.H.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Kepala Seksi Pengendalian Operasional Angkutan Jalan",
        "sisa_cuti": 17
    },
    {
        "no": 35,
        "nip": "197011091997031005",
        "nama": "IRFAN WIJAYA, A.Md.LLAJ",
        "golongan": "Penata/III/c",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 18
    },
    {
        "no": 36,
        "nip": "197303071996031001",
        "nama": "DANANG EKO PRASTOWO",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 16
    },
    {
        "no": 37,
        "nip": "198005272005011006",
        "nama": "YORRI KUSUMA NUGRAHA, SIP, MA",
        "golongan": "Pembina/IV/a",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 18
    },
    {
        "no": 38,
        "nip": "196903271998031001",
        "nama": "DIDIT SURANTO S.T., M.T.",
        "golongan": "Pembina Tk. I/IV/b",
        "jabatan": "Kepala Bidang Pengembangan Prasarana Transportasi",
        "sisa_cuti": 10
    },
    {
        "no": 39,
        "nip": "196910241990031007",
        "nama": "RADEN SIGIT WAHYU WIBOWO S.Sos., M.M.",
        "golongan": "Pembina/IV/a",
        "jabatan": "Kepala Seksi Pengembangan Prasarana Angkutan",
        "sisa_cuti": 18
    },
    {
        "no": 40,
        "nip": "198007212007121003",
        "nama": "ARIEF GUNAWAN, S.E., M.Sc.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 18
    },
    {
        "no": 41,
        "nip": "197109032005011011",
        "nama": "SIGIT BUDI RAHARDJO S.T.",
        "golongan": "Penata Tk. I/III/d",
        "jabatan": "Kepala Seksi Pengembangan Prasarana Lalu Lintas",
        "sisa_cuti": 16
    },
    {
        "no": 42,
        "nip": "197011302008011009",
        "nama": "NURYADI",
        "golongan": "Penata Muda/III/a",
        "jabatan": "Operator Layanan Operasional",
        "sisa_cuti": 18
    },
    {
        "no": 43,
        "nip": "199807162022022003",
        "nama": "DANA RESFIANA, S.Tr.Tra.",
        "golongan": "Penata Muda Tk. I/III/b",
        "jabatan": "Penelaah Teknis Kebijakan",
        "sisa_cuti": 12
    },
    {
        "no": 44,
        "nip": "199208172025211009",
        "nama": "BAGAS HARIYA MARDIKO , A.Md.",
        "golongan": "VII",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 11
    },
    {
        "no": 45,
        "nip": "199511232025212001",
        "nama": "RESA PUTRI NOVIYANTI, A.Md.",
        "golongan": "VII",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 6
    },
    {
        "no": 46,
        "nip": "199710072025211027",
        "nama": "AMRIZAL KURNIAWAN, A.Md.T",
        "golongan": "VII",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 10
    },
    {
        "no": 47,
        "nip": "199905012025211017",
        "nama": "M. FIRMAN CILAMAYA, A.Md",
        "golongan": "VII",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 7
    },
    {
        "no": 48,
        "nip": "199908132025212017",
        "nama": "ANISSA SALMA NABILA , A.Md.A.B.",
        "golongan": "VII",
        "jabatan": "Pengelola Layanan Operasional",
        "sisa_cuti": 10
    },
    {
        "no": 49,
        "nip": "197102162025211002",
        "nama": "SAMSUDIYONO",
        "golongan": "V",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 10
    },
    {
        "no": 50,
        "nip": "197309252025211004",
        "nama": "EKA YUDIYANTA",
        "golongan": "V",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 12
    },
    {
        "no": 51,
        "nip": "198908172025211017",
        "nama": "DWI AGUS PURNAMA",
        "golongan": "V",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 12
    },
    {
        "no": 52,
        "nip": "199109212025211007",
        "nama": "SURYA EFRATA",
        "golongan": "V",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 12
    },
    {
        "no": 53,
        "nip": "199706242025211006",
        "nama": "PRABA FAUZY AMIEN",
        "golongan": "V",
        "jabatan": "Pengadministrasi Perkantoran",
        "sisa_cuti": 12
    },
    {
        "no": 54,
        "nip": "199209232025211051",
        "nama": "HANDY WIBOWO, S.T",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 11
    },
    {
        "no": 55,
        "nip": "199312242025212010",
        "nama": "INDAH PUSPITASARI DEWI , S.E.",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 6
    },
    {
        "no": 56,
        "nip": "199505152025212003",
        "nama": "GHANIY WAHYU ANESYAWATI , S.T.",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 5
    },
    {
        "no": 57,
        "nip": "199511182025211007",
        "nama": "HUDZAIFAH IBNU ABDILLAH , S.ST.",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 11
    },
    {
        "no": 58,
        "nip": "199601232025212031",
        "nama": "ARIES DWI CYNTIA, S.Tr.Tra",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 9
    },
    {
        "no": 59,
        "nip": "199707042025211005",
        "nama": "IBNU ADIB ADIKA, S.ST.",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 8
    },
    {
        "no": 60,
        "nip": "199906302025212016",
        "nama": "DYAS AMALIA SRIE ANGGRIANA, S.Tr.Tra",
        "golongan": "IX",
        "jabatan": "Penata Layanan Operasional",
        "sisa_cuti": 12
    }
]
