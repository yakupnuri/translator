import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Shopify Gelişmiş Çevirici", layout="wide")

st.title("🚀 Shopify HTML Korumalı Çeviri Aracı")
st.markdown("Bu araç **Default content** sütunundaki HTML kodlarını koruyarak metinleri İngilizceye çevirir.")

# HTML metinlerini etiketsiz çeviren fonksiyon
def translate_html(html_text, translator):
    if not html_text or pd.isna(html_text) or str(html_text).strip() == "" or str(html_text).strip() == '""':
        return html_text
    
    soup = BeautifulSoup(str(html_text), "html.parser")
    
    # HTML içindeki tüm metin parçalarını bul
    for node in soup.find_all(string=True):
        original_text = node.string.strip()
        if original_text and not original_text.isdigit():
            try:
                # Sadece metni çevir, etiketi elleme
                translated = translator.translate(original_text)
                node.replace_with(translated)
            except:
                continue
    return str(soup)

uploaded_file = st.file_uploader("Shopify CSV dosyasını yükleyin", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### Dosya Hazır. Sütunlar:", list(df.columns))
    st.dataframe(df.head(5))

    if st.button("🇬🇧 HTML'leri Koruyarak İngilizceye Çevir"):
        if 'Default content' in df.columns:
            translator = GoogleTranslator(source='auto', target='en')
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total = len(df)
            
            # Çeviri işlemi
            translated_list = []
            for i, val in enumerate(df['Default content']):
                # HTML korumalı çeviri yap
                result = translate_html(val, translator)
                translated_list.append(result)
                
                # İlerlemeyi göster
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"Çevriliyor: {i+1} / {total}")
                
                # Google engeline takılmamak için çok kısa bekleme
                if i % 50 == 0:
                    time.sleep(0.5)

            df['Translated content'] = translated_list
            
            st.success("✅ İşlem başarıyla tamamlandı!")
            st.dataframe(df.head(10))

            # İndirme Butonu
            csv_output = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Çevrilmiş CSV Dosyasını İndir",
                data=csv_output,
                file_name="shopify_translated_fixed.csv",
                mime="text/csv",
            )
        else:
            st.error("Hata: Dosyada 'Default content' sütunu bulunamadı! Lütfen Shopify'dan doğru dosyayı aldığınızdan emin olun.")
