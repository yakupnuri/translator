import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Shopify Akıllı Çevirici", layout="wide")

st.title("🚀 Shopify Akıllı Çeviri Aracı")
st.markdown("Bu sürüm **kitap isimlerini ve linkleri korur**, sadece açıklamaları ve meta metinleri çevirir.")

def translate_html(html_text, translator):
    if not html_text or pd.isna(html_text) or str(html_text).strip() in ["", '""', "nan"]:
        return html_text
    
    soup = BeautifulSoup(str(html_text), "html.parser")
    for node in soup.find_all(string=True):
        original_text = node.string.strip()
        if original_text and not original_text.isdigit():
            try:
                translated = translator.translate(original_text)
                node.replace_with(translated)
            except:
                continue
    return str(soup)

uploaded_file = st.file_uploader("Shopify CSV dosyasını yükleyin", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### Dosya Yüklendi")
    st.dataframe(df.head(5))

    if st.button("🇬🇧 Sadece Gerekli Alanları İngilizceye Çevir"):
        if 'Default content' in df.columns:
            translator = GoogleTranslator(source='auto', target='en')
            progress_bar = st.progress(0)
            status_text = st.empty()
            total = len(df)
            
            translated_list = []
            
            for i, row in df.iterrows():
                field_type = str(row.get('Field', '')).lower()
                content = row['Default content']
                
                # KRİTİK KARAR: Kitap adı (title) veya link (handle) ise çevirme!
                if field_type in ['title', 'handle']:
                    translated_list.append(content) # Olduğu gibi bırak
                else:
                    # Diğer alanları (Açıklama, Slogan vb.) HTML koruyarak çevir
                    result = translate_html(content, translator)
                    translated_list.append(result)
                
                # İlerlemeyi göster
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"İşleniyor: {i+1} / {total}")

            df['Translated content'] = translated_list
            
            st.success("✅ İşlem bitti! Kitap isimleri korundu, açıklamalar çevrildi.")
            st.dataframe(df.head(10))

            csv_output = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Çevrilmiş Dosyayı İndir",
                data=csv_output,
                file_name="shopify_fixed_titles.csv",
                mime="text/csv",
            )
