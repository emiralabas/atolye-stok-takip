import pandas as pd
import streamlit as st
from supabase import create_client

# Streamlit Secrets üzerinden Supabase bağlantısı
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Sayfa Ayarları
st.set_page_config(page_title="Ar-Ge Atölye Stok Takibi", layout="wide")
st.title("📦 Ar-Ge Atölyesi Komponent Takip Sistemi (Supabase)")

# Sol Menü
menu = st.sidebar.selectbox(
    "İşlem Seçin",
    ["Yeni Komponent Ekle", "Stok Listesi ve Arama", "Stok Güncelle / Sil"],
)

# --- MODÜL 1: YENİ KOMPONENT EKLE ---
if menu == "Yeni Komponent Ekle":
    st.subheader("➕ Kutuyu Numaralandır ve Komponent Ekle")

    with st.form("ekle_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            box_no = st.text_input(
                "Box / Kutu Numarası *", placeholder="Örn: 1 veya ORG1-A3"
            )
            komponent_adi = st.text_input(
                "Komponent Adı *", placeholder="Örn: 1k ohm direnç"
            )
            kategori = st.selectbox(
                "Kategori",
                [
                    "Direnç",
                    "Kondansatör",
                    "Entegre / Mikrodenetleyici",
                    "Transistör / Diyot",
                    "Konnektör / Kablo",
                    "Sensör",
                    "Diğer",
                ],
            )

        with col2:
            miktar = st.number_input(
                "Adet / Miktar *", min_value=1, value=10, step=1
            )
            aciklama = st.text_area(
                "Açıklama / Notlar", placeholder="Örn: 0805 kılıf"
            )

        submit_button = st.form_submit_button("Veritabanına Kaydet")

        if submit_button:
            if not box_no or not komponent_adi:
                st.error(
                    "Lütfen Kutu Numarası ve Komponent Adı alanlarını"
                    " doldurun!"
                )
            else:
                data = {
                    "box_no": box_no,
                    "komponent_adi": komponent_adi,
                    "kategori": kategori,
                    "miktar": miktar,
                    "aciklama": aciklama,
                }
                supabase.table("stok").insert(data).execute()
                st.success(
                    f"✅ **{box_no}** numaralı kutuya **{miktar} adet"
                    f" {komponent_adi}** eklendi!"
                )

# --- MODÜL 2: STOK LİSTESİ VE ARAMA ---
elif menu == "Stok Listesi ve Arama":
    st.subheader("🔍 Stok Arama ve Kutu Sorgulama")

    arama_termi = st.text_input("Kutu No veya Komponent Adı ile Ara...", "")

    # Verileri Supabase'den Çek
    response = supabase.table("stok").select("*").execute()
    data = response.data

    if data:
        df = pd.DataFrame(data)
        # Sütunları düzenle
        df = df[
            ["id", "box_no", "komponent_adi", "kategori", "miktar", "aciklama"]
        ]
        df.columns = [
            "ID",
            "Kutu No",
            "Komponent",
            "Kategori",
            "Miktar",
            "Açıklama",
        ]

        if arama_termi:
            df = df[
                df["Kutu No"]
                .astype(str)
                .str.contains(arama_termi, case=False, na=False)
                | df["Komponent"].str.contains(
                    arama_termi, case=False, na=False
                )
            ]

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Veritabanında henüz kayıtlı ürün yok.")

# --- MODÜL 3: STOK GÜNCELLE VEYA SİL ---
elif menu == "Stok Güncelle / Sil":
    st.subheader("✏️ Veri Düzenleme")

    response = supabase.table("stok").select("*").execute()
    data = response.data

    if data:
        df = pd.DataFrame(data)
        secilen_id = st.selectbox(
            "Düzenlenecek Komponenti Seçin",
            df["id"].tolist(),
            format_func=lambda x: (
                f"ID: {x} | Box:"
                f" {df[df['id']==x]['box_no'].values[0]} -"
                f" {df[df['id']==x]['komponent_adi'].values[0]}"
            ),
        )

        kayit = df[df["id"] == secilen_id].iloc[0]
        yeni_miktari = st.number_input(
            "Yeni Stok Miktarı", value=int(kayit["miktar"])
        )

        col_guncelle, col_sil = st.columns(2)

        with col_guncelle:
            if st.button("Miktarı Güncelle"):
                supabase.table("stok").update({"miktar": yeni_miktari}).eq(
                    "id", secilen_id
                ).execute()
                st.success("Stok miktarı güncellendi!")
                st.rerun()

        with col_sil:
            if st.button("Kaydı Sil", type="primary"):
                supabase.table("stok").delete().eq(
                    "id", secilen_id
                ).execute()
                st.warning("Kayıt veritabanından silindi!")
                st.rerun()
    else:
        st.info("Veritabanında henüz kayıtlı ürün yok.")
