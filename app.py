import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import re
import time

# Sayfa Ayarları
st.set_page_config(page_title="Shopify Official Translator", layout="wide")

# --- FONKSİYONLAR ---
def smart_translate(text, translator):
    if not text or pd.isna(text) or str(text).strip() in ["", '""', "nan", "None"]:
        return text
    
    # 1. Liquid Tag Koruması
    placeholders = {}
    def preserve_liquid(match):
        placeholder = f" _TRX{len(placeholders)}X_ "
        placeholders[placeholder] = match.group(0)
        return placeholder
    text = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', preserve_liquid, str(text))
    
    # 2. HTML Parçala ve Çevir
    try:
        soup = BeautifulSoup(text, "html.parser")
        for node in soup.find_all(string=True):
            original_node = node.string.strip()
            # Sadece anlamlı metinleri çevir (sayı değilse ve 1 karakterden uzunsa)
            if original_node and not original_node.isdigit() and len(original_node) > 1:
                try:
                    translated = translator.translate(original_node)
                    node.replace_with(translated)
                except:
                    continue
        result = str(soup)
        # 3. Liquid Tag'leri Geri Yükle
        for placeholder, original in placeholders.items():
            result = result.replace(placeholder.strip(), original)
            result = result.replace(placeholder, original)
        return str(result)
    except:
        return str(text)

# --- ARAYÜZ ---
st.title("📦 Shopify Standart Çeviri Aracı")
st.info("Bu araç Shopify'ın resmi CSV çeviri formatına (Type, Identification, Field, Locale, Status...) tam uyumludur.")

# Yan Panel
st.sidebar.header("⚙️ Ayarlar")
languages = {"İngilizce": "en", "Fransızca": "fr", "Almanca": "de", "İspanyolca": "es", "İtalyanca": "it", "Hollandaca": "nl"}
target_lang_name = st.sidebar.selectbox("Hedef Dil (Locale):", list(languages.keys()))
target_lang_code = languages[target_lang_name]

st.sidebar.write("---")
only_empty = st.sidebar.checkbox("Sadece boş olanları çevir", value=True)

uploaded_file = st.file_uploader("Shopify'dan Export ettiğiniz CSV dosyasını yükleyin", type=["csv"])

if uploaded_file:
    # DOSYAYI OKU (Zorla String/Metin olarak oku, ID'ler bozulmasın!)
    df = pd.read_csv(uploaded_file, dtype=str)
    
    if 'Translated content' not in df.columns:
        df['Translated content'] = ""
    
    total_rows = len(df)
    
    # Checklist (Field sütununa göre)
    if 'Field' in df.columns:
        all_fields = df['Field'].unique().tolist()
        st.sidebar.write("---")
        st.sidebar.write("**Çevrilecek Alanlar:**")
        selected_fields = []
        for f in all_fields:
            # handle ve title genellikle orijinal kalmalı (Senin tercihin)
            is_on = f not in ['handle', 'title', 'Locale', 'Status', 'Identification', 'Market']
            if st.sidebar.checkbox(f, value=is_on):
                selected_fields.append(f)

    st.metric("Yüklenen Satır Sayısı", total_rows)

    if st.button(f"🚀 ÇEVİRİYE BAŞLA"):
        translator = GoogleTranslator(source='auto', target=target_lang_code)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # ÇEVİRİ DÖNGÜSÜ
        for i, row in df.iterrows():
            field = str(row['Field'])
            content = str(row['Default content'])
            translated_val = str(row.get('Translated content', ''))

            # Çevirme kriteri
            is_selected = field in selected_fields
            is_empty = translated_val.strip() in ["", "nan", "None", "NaN", "nan"]
            
            if is_selected:
                if not only_empty or (only_empty and is_empty):
                    res = smart_translate(content, translator)
                    df.at[i, 'Translated content'] = str(res)
                    # Çevrilen satırın durumunu 'published' yap (Shopify kuralı)
                    df.at[i, 'Status'] = 'published'
            
            # İlerlemeyi sadece 20 satırda bir güncelle
            if i % 20 == 0 or i == total_rows - 1:
                progress = (i + 1) / total_rows
                progress_bar.progress(progress)
                status_text.write(f"⏳ İşleniyor: {i+1} / {total_rows}")

        # Tüm Locale sütununu hedef dille güncelle (Shopify kuralı)
        df['Locale'] = target_lang_code
        
        st.balloons()
        st.success(f"✅ Çeviri bitti! Sütun yapısı ve ID'ler korundu. Status 'published' yapıldı.")
        
        # Dosyayı Kaydet Butonu
        st.write("---")
        # Shopify için UTF-8 formatında kaydet
        csv_data = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
        st.download_button(
            label="📥 SHOPIFY UYUMLU CSV DOSYASINI İNDİR",
            data=csv_data,
            file_name=f"shopify_translations_{target_lang_code}.csv",
            mime="text/csv"
        )
        st.dataframe(df.head(50))
