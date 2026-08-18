import streamlit as st
import datetime
import gspread
import json
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

/* Mengatur warna tombol Submit */
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
    # Tombol Refresh untuk memuat ulang halaman secara manual
    if st.button("🔄 Refresh"):
        st.rerun()
# ---------------------------------------------------

# 1. Tanggal (Otomatis hari ini)
tanggal_hari_ini = datetime.date.today()
st.text_input("Tanggal", value=tanggal_hari_ini.strftime("%d-%m-%Y"), disabled=True)

# 2. Jam Update (07:00 - 18:00, interval 30 menit)
waktu_mulai = datetime.datetime.strptime("07:00", "%H:%M")
waktu_selesai = datetime.datetime.strptime("18:00", "%H:%M")
pilihan_jam = []

while waktu_mulai <= waktu_selesai:
    pilihan_jam.append(waktu_mulai.strftime("%H:%M"))
    waktu_mulai += datetime.timedelta(minutes=30)

jam_update = st.selectbox("Jam Update", pilihan_jam)

# 3 - 8. Input Manual Text & Dropdown
st.subheader("Informasi Produksi")
group = st.text_input("Group")
line = st.text_input("Line")

pilihan_proses = ["END LINE", "SNAP", "IRON"]
proses = st.selectbox("Proses", pilihan_proses)

style = st.text_input("Style")
color = st.text_input("Color")

# 9. Input Size & Qty (Grid Layout)
st.subheader("Input Qty per Size")
daftar_size = ["XS", "S", "M", "L", "XL", "2XL", "4XL", "OVERSIZE"]
qty_inputs = {}

cols = st.columns(4)
for i, size in enumerate(daftar_size):
    with cols[i % 4]:
        qty_inputs[size] = st.number_input(f"Size {size}", min_value=0, step=1, key=f"qty_{size}")

st.markdown("<br>", unsafe_allow_html=True)

# Tombol Submit (Manual, data tidak langsung hilang setelah submit)
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
                            tanggal_hari_ini.strftime("%d-%m-%Y"),
                            jam_update,
                            group,
                            line,
                            proses,  
                            style,
                            color,
                            size,
                            qty
                        ]
                        rows_data.append(row_data)
                
                sheet.append_rows(rows_data)
                st.success(f"Data berhasil tersimpan! ({len(rows_data)} baris data ditambahkan ke Google Sheets)")
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menyimpan: {e}")
    else:
        st.warning("Mohon lengkapi semua field text dan pastikan minimal ada satu Size dengan Qty lebih dari 0.")
