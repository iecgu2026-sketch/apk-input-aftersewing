import streamlit as st
import datetime
import gspread
import json
import pandas as pd
from google.oauth2.service_account import Credentials

# Konfigurasi Halaman (Harus dipanggil pertama kali)
st.set_page_config(page_title="Data Produksi", page_icon="🏭", layout="centered")

# --- KUSTOMISASI DESAIN CSS ---
custom_css = """
<style>
/* Menghilangkan Header & Footer bawaan Streamlit */
header {
    visibility: hidden;
}
footer {
    visibility: hidden;
}
/* Memangkas jarak kosong (space) di bagian atas halaman agar lebih naik ke atas */
.stMainBlockContainer {
    padding-top: 2rem !important;
}

/* Mengubah background aplikasi menjadi abu-abu terang */
.stApp {
    background-color: #E8ECEF;
}

/* Memaksa teks label, judul, dan paragraf menjadi warna hitam */
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
    color: #000000 !important;
}

/* Memberikan garis bawah pada Header */
h1, h2, h3 {
    border-bottom: 2px solid #2C3E50;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

/* Mempercantik kotak input */
.stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
    background-color: #FFFFFF;
    color: #000000 !important;
    border-radius: 5px;
}

/* Mengatur warna tombol */
div.stButton > button {
    background-color: #4A5568 !important;
    color: #FFFFFF !important;
    border-radius: 5px;
    border: none;
    font-weight: bold;
    width: 100%;
}

div.stButton > button:hover {
    background-color: #2D3748 !important;
    color: #FFFFFF !important;
}
/* Mengubah warna toolbar melayang pada tabel (st.dataframe) menjadi abu-abu */
[data-testid="stElementToolbar"] {
    background-color: #CBD5E1 !important;
    border-radius: 8px;
    padding: 2px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Konfigurasi Akses Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '17ucBxMw5i6VxGrvNMjPGU9DAiwtkeLmHA4ndefD0oR4'

def get_sheet():
    try:
        if "kredensial_google" in st.secrets:
            kredensial_rahasia = json.loads(st.secrets["kredensial_google"])
            credentials = Credentials.from_service_account_info(kredensial_rahasia, scopes=SCOPES)
        else:
            credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return None

# --- INISIALISASI SESSION STATE UNTUK RESET FORM ---
if 'form_key' not in st.session_state:
    st.session_state['form_key'] = 0

# --- BAGIAN HEADER: LOGO, JUDUL, & TOMBOL REFRESH ---
col_logo, col_judul, col_refresh = st.columns([1, 4, 1.2], vertical_alignment="center")

with col_logo:
    try:
        st.image("logo pt.png", width=90) 
    except:
        st.write("Logo")

with col_judul:
    st.title("Form Input")

with col_refresh:
    if st.button("🔄 Refresh"):
        st.session_state['form_key'] += 1
        st.rerun()
# ---------------------------------------------------

f_key = st.session_state['form_key']

# 1. Tanggal (Otomatis hari ini)
tanggal_hari_ini = datetime.date.today()
tanggal_str = tanggal_hari_ini.strftime("%d-%m-%Y")
st.text_input("Tanggal", value=tanggal_str, disabled=True, key=f"tgl_{f_key}")

# 2. Jam Update
waktu_mulai = datetime.datetime.strptime("07:00", "%H:%M")
waktu_selesai = datetime.datetime.strptime("18:00", "%H:%M")
pilihan_jam = []

while waktu_mulai <= waktu_selesai:
    pilihan_jam.append(waktu_mulai.strftime("%H:%M"))
    waktu_mulai += datetime.timedelta(minutes=30)

jam_update = st.selectbox("Jam Update", pilihan_jam, key=f"jam_{f_key}")

# 3 - 8. Input Manual Text & Dropdown
st.subheader("Informasi Produksi")
group = st.text_input("Group", key=f"group_{f_key}")
line = st.text_input("Line", key=f"line_{f_key}")

# "OUT SEWING" ditaruh paling depan agar menjadi pilihan utama
pilihan_proses = ["OUT SEWING", "SNAP", "IRON", "TANDA KANCING", "PASANG KANCING", "EMBLEM", "LUBANG KANCING", "BARTACK", "FOLDING", "BUANG BENANG + KANCING"]
proses = st.selectbox("Proses", pilihan_proses, key=f"proses_{f_key}")

style = st.text_input("Style", key=f"style_{f_key}")
color = st.text_input("Color", key=f"color_{f_key}")

# 9. Input Size & Qty (Grid Layout)
st.subheader("Input Qty per Size")
daftar_size = ["XS", "M", "XL", "4XL", "S", "L", "2XL", "OVERSIZE"]
qty_inputs = {}

cols = st.columns(4)
for i, size in enumerate(daftar_size):
    with cols[i % 4]:
        qty_inputs[size] = st.number_input(f"Size {size}", min_value=0, step=1, key=f"qty_{size}_{f_key}")

st.markdown("<br>", unsafe_allow_html=True)

# Tombol Submit
if st.button("Submit Data"):
    total_qty = sum(qty_inputs.values())
    
    if group and line and style and color and total_qty > 0:
        sheet = get_sheet()
        if sheet:
            try:
                rows_data = []
                for size, qty in qty_inputs.items():
                    if qty > 0:
                        row_data = [
                            tanggal_str,    # TANGGAL
                            jam_update,     # JAM UPDATE
                            group,          # GROUP
                            line,           # LINE
                            proses,         # PROSES  
                            style,          # STYLE
                            color,          # COLOR
                            size,           # SIZE
                            qty             # QTY
                        ]
                        rows_data.append(row_data)
                
                sheet.append_rows(rows_data)
                st.success(f"Data berhasil tersimpan! ({len(rows_data)} baris data ditambahkan ke Google Sheets)")
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menyimpan: {e}")
    else:
        st.warning("Mohon lengkapi semua field text dan pastikan minimal ada satu Size dengan Qty lebih dari 0.")

# ==========================================================
# --- BAGIAN RESUME / REKAP PRODUKSI HARI INI ---
# ==========================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader(f"📊 Resume Produksi Hari Ini ({tanggal_str})")

sheet = get_sheet()
if sheet:
    try:
        all_data = sheet.get_all_records()
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.columns = [str(col).strip().upper() for col in df.columns]
            
            if 'TANGGAL' in df.columns and 'QTY' in df.columns:
                df_hari_ini = df[df['TANGGAL'] == tanggal_str].copy()
                
                if not df_hari_ini.empty:
                    df_hari_ini['QTY'] = pd.to_numeric(df_hari_ini['QTY'], errors='coerce').fillna(0)
                    
                    # 1. Sum Qty per Proses, Line, dan Jam Update untuk Tabel
                    rekap = df_hari_ini.groupby(['PROSES', 'LINE', 'JAM UPDATE'], as_index=False)['QTY'].sum()
                    rekap.rename(columns={'QTY': 'QTY JAM INI'}, inplace=True)
                    
                    rekap['QTY KUMULATIF'] = rekap.groupby(['PROSES', 'LINE'])['QTY JAM INI'].cumsum()
                    
                    # Mengatur agar "OUT SEWING" selalu di prioritas pertama (urutan 0)
                    def urutan_proses(p):
                        if str(p).strip().upper() == "OUT SEWING":
                            return 0
                        return 1

                    rekap['PRIORITAS'] = rekap['PROSES'].apply(urutan_proses)
                    rekap = rekap.sort_values(by=['PRIORITAS', 'PROSES', 'LINE', 'JAM UPDATE']).drop(columns=['PRIORITAS'])
                    
                    # Tampilkan Tabel Resume
                    st.dataframe(rekap, use_container_width=True, hide_index=True)
                    
                    # 2. Kotak Total per Proses (OUT SEWING ditaruh paling depan)
                    st.markdown("### 📌 Total Qty per Proses")
                    total_per_proses = df_hari_ini.groupby('PROSES')['QTY'].sum().reset_index()
                    total_per_proses['PRIORITAS'] = total_per_proses['PROSES'].apply(urutan_proses)
                    total_per_proses = total_per_proses.sort_values(by=['PRIORITAS', 'PROSES']).drop(columns=['PRIORITAS'])
                    
                    # Menampilkan metrik dalam kolom (2 kolom per baris)
                    proses_list = total_per_proses.values.tolist()
                    for i in range(0, len(proses_list), 2):
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric(label=f"Total {proses_list[i][0]}", value=int(proses_list[i][1]))
                        if i + 1 < len(proses_list):
                            with col_m2:
                                st.metric(label=f"Total {proses_list[i+1][0]}", value=int(proses_list[i+1][1]))
                                
                else:
                    st.info("Belum ada data produksi yang diinput untuk hari ini.")
            else:
                st.warning("Pastikan header di Google Sheets baris pertama sudah sesuai.")
        else:
            st.info("Google Sheets masih kosong.")
    except Exception as e:
        st.error(f"Gagal memuat resume data: {e}")
