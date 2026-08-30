import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Calorías AI 📸", page_icon="🥗", layout="centered")

st.title("🥗 Detector de Calorías por Foto")
st.write("Sube o haz una foto de tu plato para calcular sus calorías al instante.")

archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado")
    
    if st.button("🔥 Calcular Calorías y Nutrientes", type="primary"):
        with st.spinner("La Inteligencia Artificial está analizando los ingredientes..."):
            try:
                # Pasamos la clave directamente aquí sin depender de secretos externos
                client = genai.Client(api_key="AQ.Ab8RN6LgyvBiaZWIS1-FFqmmmftRTldc3vD0kVFmx9wiisK1Fg")
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        imagen, 
                        "Actúa como un nutricionista experto. Analiza esta foto de comida, identifica los alimentos, estima los gramos de forma realista y calcula las calorías totales, proteínas, grasas y carbohidratos en formato de lista clara."
                    ]
                )
                
                st.success("¡Análisis completado con éxito!")
                st.markdown("### 📊 Desglose Nutricional:")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Hubo un error al conectar con la IA: {e}")
