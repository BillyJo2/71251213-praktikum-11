
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
import google.generativeai as genai

st.set_page_config(
    page_title="Pokémon Explorer",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Pokémon Explorer")
st.write("Jelajahi dan bandingkan Pokémon menggunakan data dari PokeAPI.")

# Konfigurasi Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)


@st.cache_data(ttl=3600)
def ambil_pokemon(nama):
    url = f"https://pokeapi.co/api/v2/pokemon/{nama.lower().strip()}"
    response = requests.get(url, timeout=15)

    if response.status_code != 200:
        return None

    return response.json()


def ambil_statistik(data):
    return {
        stat["stat"]["name"]: stat["base_stat"]
        for stat in data["stats"]
    }


def analisis_ai(data1, data2=None):
    if not API_KEY:
        return "API Key Gemini belum dipasang. Silakan atur GEMINI_API_KEY."

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    Kamu adalah ahli Pokémon.

    Analisis Pokémon berikut menggunakan bahasa Indonesia.

    Pokémon pertama:
    Nama: {data1['name']}
    Tipe: {[x['type']['name'] for x in data1['types']]}
    Statistik: {ambil_statistik(data1)}

    """

    if data2:
        prompt += f"""
        Pokémon kedua:
        Nama: {data2['name']}
        Tipe: {[x['type']['name'] for x in data2['types']]}
        Statistik: {ambil_statistik(data2)}

        Bandingkan kedua Pokémon dan jelaskan siapa yang unggul.
        """

    prompt += """
    Berikan:
    1. Penjelasan karakteristik Pokémon.
    2. Kelebihan dan kekurangan.
    3. Analisis statistik.
    4. Rekomendasi penggunaan.
    
    Gunakan bahasa Indonesia yang mudah dipahami.
    """

    response = model.generate_content(prompt)
    return response.text


# Input pencarian
st.sidebar.header("Pencarian Pokémon")

nama1 = st.sidebar.text_input("Nama Pokémon pertama", "pikachu")
nama2 = st.sidebar.text_input("Nama Pokémon kedua", "charizard")

if st.button("Cari Pokémon"):
    with st.spinner("Mengambil data Pokémon..."):
        pokemon1 = ambil_pokemon(nama1)
        pokemon2 = ambil_pokemon(nama2)

    if not pokemon1:
        st.error("Pokémon pertama tidak ditemukan.")
    elif not pokemon2:
        st.error("Pokémon kedua tidak ditemukan.")
    else:
        st.session_state["pokemon1"] = pokemon1
        st.session_state["pokemon2"] = pokemon2

if "pokemon1" in st.session_state:
    p1 = st.session_state["pokemon1"]
    p2 = st.session_state["pokemon2"]

    col1, col2 = st.columns(2)

    for col, pokemon in [(col1, p1), (col2, p2)]:
        with col:
            st.subheader(pokemon["name"].capitalize())

            st.image(
                pokemon["sprites"]["other"]["official-artwork"]["front_default"],
                width=200
            )

            st.write("**Tipe:**", ", ".join(
                x["type"]["name"] for x in pokemon["types"]
            ))
            st.write("**Tinggi:**", pokemon["height"] / 10, "meter")
            st.write("**Berat:**", pokemon["weight"] / 10, "kg")

            st.write("**Kemampuan:**", ", ".join(
                x["ability"]["name"] for x in pokemon["abilities"]
            ))

    st.divider()
    st.subheader("📊 Perbandingan Statistik")

    statistik1 = ambil_statistik(p1)
    statistik2 = ambil_statistik(p2)

    df = pd.DataFrame({
        p1["name"].capitalize(): statistik1,
        p2["name"].capitalize(): statistik2
    })

    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    df.plot(kind="bar", ax=ax)
    ax.set_title("Perbandingan Statistik Pokémon")
    ax.set_ylabel("Nilai Statistik")
    ax.set_xlabel("Jenis Statistik")
    plt.xticks(rotation=30)
    plt.tight_layout()

    st.pyplot(fig)

    st.download_button(
        "Unduh Data Pokémon (CSV)",
        df.to_csv().encode("utf-8"),
        "data_pokemon.csv",
        "text/csv"
    )

    st.divider()
    st.subheader("🤖 Analisis Pokémon dengan Gemini AI")

    if st.button("Analisis dengan AI"):
        try:
            with st.spinner("Gemini sedang menganalisis..."):
                hasil = analisis_ai(p1, p2)

            st.success("Analisis berhasil!")
            st.write(hasil)

        except Exception as e:
            st.error(f"Gagal melakukan analisis AI: {e}")