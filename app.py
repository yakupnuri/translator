import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import re
import time

# Sayfa Ayarları
st.set_page_config(page_title="Shopify Çeviri Fabrikası", layout="wide")

# --- FONKSİYONLAR ---
def smart_translate(text, translator):
    if not text or pd.isna(text) or str(text).strip() in ["", '""', "nan", "None"]:
        return text
    
    # Liquid Tag'leri Korumaya Al
    placeholders = {}
    def preserve_liquid(match):
        placeholder = f" _TRX{len(placeholders)}X_ "
        placeholders[placeholder] = match.group(0)
        return placeholder

    text = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', preserve_liquid, str(text))
    
    # HTML Parçala ve Metinleri Çevir
    try:
        soup = BeautifulSoup(text, "html.parser")
        for node in soup.find_all(string=True):
            original_node = node.string.strip()
            if original_node and not original_node.isdigit() and len(original_node) > 1:
                try:
                    translated = translator.translate(original_node)
                    node.replace_with(translated)
                except:
                    continue
        result = str(soup)
        # Liquid Tag'leri Geri Yükle
        for placeholder, original in placeholders.items():
            result = result.replace(placeholder.strip(), original)
            result = result.replace(placeholder, original)
        return result
    except:
        return text

# --- ARAYÜZ ---
st.title("🚀 Shopify Ultimate Çeviri Paneli")

st.sidebar.header("⚙️ Ayarlar")
languages = {"İngilizce": "en", "Fransızca": "fr", "Almanca": "de", "Hollandaca": "nl", "Türkçe": "tr", "İspanyolca": "es"}
target_lang_name = st.sidebar.selectbox("Hedef Dili Seçin:", list(languages.keys()))
target_lang_code = languages[target_lang_name]

st.sidebar.write("---")
only_empty = st.sidebar.checkbox("Sadece boş olanları çevir", value=True, help="Eğer işlem yarıda kalırsa, dosyayı tekrar yükleyip bu seçeneği işaretleyin. Böylece çevrilmiş olanları atlar.")

uploaded_file = st.file_uploader("Shopify CSV dosyasını yükleyin", type=["csv"])

if uploaded_file:
    # Bellek sorunu olmaması için dosyayı bir kez okuyalım
    if 'main_df' not in st.session_state:
        st.session_state.main_df = pd.read_csv(uploaded_file)
    
    df = st.session_state.main_df
    total_rows = len(df)
    
    # Checklist
    if 'Field' in df.columns:
        all_fields = df['Field'].unique().tolist()
        st.sidebar.write("---")
        st.sidebar.write("**Çevrilecek Alanlar:**")
        selected_fields = []
        for f in all_fields:
            is_on = f not in ['handle', 'title', 'Locale', 'Status', 'Identification', 'Market']
            if st.sidebar.checkbox(f, value=is_on):
                selected_fields.append(f)

    # İstatistik
    c1, c2 = st.columns(2)
    c1.metric("Toplam Satır", total_rows)
    c2.metric("Hedef Dil", target_lang_name)

    if st.button(f"🔥 ÇEVİRİYİ BAŞLAT"):
        translator = GoogleTranslator(source='auto', target=target_lang_code)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if 'Translated content' not in df.columns:
            df['Translated content'] = ""

        # ÇEVİRİ DÖNGÜSÜ
        for i, row in df.iterrows():
            field = str(row['Field'])
            content = row['Default content']
            translated_val = str(row.get('Translated content', ''))

            # Çevirme kriteri
            is_selected = field in selected_fields
            is_empty = translated_val.strip() in ["", "nan", "None"]
            
            if is_selected:
                if not only_empty or (only_empty and is_empty):
                    res = smart_translate(content, translator)
                    df.at[i, 'Translated content'] = res
            
            # İlerlemeyi her 10 satırda bir güncelle (Sistemi yormamak için)
            if i % 10 == 0 or i == total_rows - 1:
                progress = (i + 1) / total_rows
                progress_bar.progress(progress)
                status_text.write(f"⏳ İşleniyor: {i+1} / {total_rows} - Son İşlem: {field}")

        # Final Düzenleme
        df['Locale'] = target_lang_code
        
        st.balloons()
        st.success("✅ İŞLEM TAMAMLANDI!")
        
        # Dosyayı Kaydet Butonu
        st.write("### 📥 Dosyayı İndir")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 ÇEVRİLMİŞ CSV DOSYASINI KAYDET",
            data=csv_data,
            file_name=f"shopify_{target_lang_code}_output.csv",
            mime="text/csv",
        )
        st.dataframe(df.head(100))
