
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import os
import io

st.set_page_config(
    page_title="Analisis Penjualan",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Aplikasi Analisis Penjualan")
st.write("Analisis data penjualan dengan bantuan Gemini AI.")

# Konfigurasi Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)


# Fungsi membaca data
def baca_data(file):
    df = pd.read_csv(file)

    kolom = ["Tanggal", "Produk", "Kategori", "Jumlah", "Harga"]

    for k in kolom:
        if k not in df.columns:
            raise ValueError(f"Kolom {k} tidak ditemukan.")

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Jumlah"] = pd.to_numeric(df["Jumlah"], errors="coerce")
    df["Harga"] = pd.to_numeric(df["Harga"], errors="coerce")

    df = df.dropna(subset=kolom)

    if df.empty:
        raise ValueError("Data CSV tidak memiliki baris valid.")

    if (df["Jumlah"] < 0).any() or (df["Harga"] < 0).any():
        raise ValueError("Jumlah dan harga tidak boleh negatif.")

    df["Total"] = df["Jumlah"] * df["Harga"]

    return df


# Fungsi analisis AI
def analisis_ai(df):
    if not API_KEY:
        return "API Key Gemini belum dipasang. Silakan atur GEMINI_API_KEY."

    ringkasan = df.to_string(index=False)

    prompt = f"""
    Kamu adalah analis penjualan profesional.

    Analisis data penjualan berikut:

    {ringkasan[:12000]}

    Berikan hasil dalam bahasa Indonesia yang mudah dipahami:

    1. Ringkasan kondisi penjualan.
    2. Produk paling laris.
    3. Produk dengan pendapatan tertinggi.
    4. Pola penjualan.
    5. Rekomendasi meningkatkan penjualan.

    Gunakan angka dari data yang diberikan.
    Jangan mengarang data.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text


# Input file
st.sidebar.header("Unggah Data")

file = st.sidebar.file_uploader(
    "Pilih file CSV penjualan",
    type=["csv"]
)

if file is None:
    st.info("Silakan unggah file CSV untuk memulai analisis.")

else:
    try:
        df = baca_data(file)

        st.success("Data berhasil dibaca!")

        st.subheader("📋 Data Penjualan")
        st.dataframe(df, use_container_width=True)

        # Struktur data dictionary
        ringkasan = {
            "total_pendapatan": df["Total"].sum(),
            "total_produk": df["Jumlah"].sum(),
            "jumlah_transaksi": len(df),
            "rata_rata": df["Total"].mean()
        }

        st.divider()
        st.subheader("📌 Ringkasan Penjualan")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Pendapatan",
            f"Rp {ringkasan['total_pendapatan']:,.0f}"
        )

        c2.metric(
            "Total Barang Terjual",
            f"{ringkasan['total_produk']:,.0f}"
        )

        c3.metric(
            "Jumlah Transaksi",
            len(df)
        )

        c4.metric(
            "Rata-rata Transaksi",
            f"Rp {ringkasan['rata_rata']:,.0f}"
        )

        # Mengelompokkan penjualan berdasarkan tanggal
        harian = df.groupby("Tanggal")["Total"].sum()

        # Mengelompokkan berdasarkan produk
        produk = df.groupby("Produk")["Jumlah"].sum().sort_values(
            ascending=False
        )

        st.divider()
        st.subheader("📈 Grafik Penjualan Harian")

        fig, ax = plt.subplots(figsize=(10, 4))
        harian.plot(kind="line", marker="o", ax=ax)
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Pendapatan (Rp)")
        ax.set_title("Tren Pendapatan Harian")
        ax.grid(True)
        plt.tight_layout()

        st.pyplot(fig)

        st.subheader("🏆 Grafik Produk Terlaris")

        fig2, ax2 = plt.subplots(figsize=(10, 4))
        produk.plot(kind="bar", color="orange", ax=ax2)
        ax2.set_xlabel("Produk")
        ax2.set_ylabel("Jumlah Terjual")
        ax2.set_title("Jumlah Penjualan per Produk")
        plt.xticks(rotation=30)
        plt.tight_layout()

        st.pyplot(fig2)

        st.divider()
        st.subheader("🤖 Analisis Penjualan dengan Gemini AI")

        if st.button("Analisis Data dengan AI"):
            try:
                with st.spinner("Gemini sedang menganalisis data..."):
                    hasil = analisis_ai(df)

                st.success("Analisis berhasil!")
                st.write(hasil)

            except Exception as e:
                st.error(f"Gagal melakukan analisis AI: {e}")

        # Ekspor Excel
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(
                writer,
                index=False,
                sheet_name="Data Penjualan"
            )

        st.download_button(
            "📥 Unduh Laporan Excel",
            data=output.getvalue(),
            file_name="laporan_penjualan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            "📥 Unduh Data CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="laporan_penjualan.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
