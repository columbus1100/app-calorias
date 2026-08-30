import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

st.set_page_config(page_title="Calorías AI 📸", page_icon="🥗", layout="centered")

st.title("🥗 Detector de Calorías por Foto")
st.write("Sube o haz una foto de tu plato para calcular sus calorías al instante.")

# Forzamos la clave para que la librería la detecte correctamente
api_key = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = api_key
genai.configure(api_key=api_key)

archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado")
    
    if st.button("🔥 Calcular Calorías y Nutrientes", type="primary"):
        with st.spinner("La Inteligencia Artificial está analizando los ingredientes..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                response = model.generate_content([
                    imagen, 
                    "Actúa como un nutricionista experto. Analiza esta foto de comida, identifica los alimentos, estima los gramos de forma realista y calcula las calorías totales, proteínas, grasas y carbohidratos en formato de lista clara."
                ])
                
                st.success("¡Análisis completado con éxito!")
                st.markdown("### 📊 Desglose Nutricional:")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Hubo un error al conectar con la IA: {e}")
