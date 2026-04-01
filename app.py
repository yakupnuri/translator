import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Shopify Çevirici", layout="wide")

st.title("🚀 Shopify CSV İngilizce Çeviri Aracı")
st.markdown("Shopify'dan aldığın CSV dosyasını buraya yükle, otomatik olarak İngilizceye çevirsin.")

uploaded_file = st.file_uploader("CSV Dosyasını Seç", type=["csv"])

if uploaded_file is not None:
    # Dosyayı oku
    df = pd.read_csv(uploaded_file)
    st.write("### Yüklenen Dosya Önizlemesi")
    st.dataframe(df.head(10))

    if st.button("🇬🇧 İngilizceye Çevirmeye Başla"):
        if 'Value' in df.columns:
            translator = GoogleTranslator(source='auto', target='en')
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            translations = []
            total = len(df)

            for i, val in enumerate(df['Value']):
                text = str(val).strip()
                if text and text != 'nan':
                    try:
                        # Çeviri yap
                        translations.append(translator.translate(text))
                    except:
                        translations.append(val)
                else:
                    translations.append(val)
                
                # İlerleme çubuğunu güncelle
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"İşleniyor: {i+1} / {total}")

            df['Translation'] = translations
            
            st.success("✅ Çeviri başarıyla tamamlandı!")
            st.dataframe(df.head(10))

            # İndirme Butonu
            csv_output = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Çevrilmiş Dosyayı İndir",
                data=csv_output,
                file_name="shopify_ingilizce.csv",
                mime="text/csv",
            )
        else:
            st.error("Hata: CSV dosyasında 'Value' sütunu bulunamadı!")
