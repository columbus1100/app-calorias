import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Calorías AI 📸", page_icon="🥗", layout="centered")

st.title("🥗 Detector de Calorías por Foto")
st.write("Sube o haz una foto de tu plato para calcular sus calorías al instante.")

# Leemos la clave de los secretos de Streamlit
api_key = st.secrets.get("GEMINI_API_KEY", "")

archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado")
    
    if st.button("🔥 Calcular Calorías y Nutrientes", type="primary"):
        if not api_key:
            st.error("Falta configurar la GEMINI_API_KEY en los Secrets de Streamlit.")
        else:
            with st.spinner("La Inteligencia Artificial está analizando los ingredientes..."):
                try:
                    # Convertimos la imagen a base64 para enviarla por HTTP
                    buffered = BytesIO()
                    imagen.save(buffered, format="JPEG")
                    img_bytes = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    # URL oficial de la API de Gemini usando el modelo gemini-2.5-flash
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": "Actúa como un nutricionista experto. Analiza esta foto de comida, identifica los alimentos, estima los gramos de forma realista y calcula las calorías totales, proteínas, grasas y carbohidratos en formato de lista clara."},
                                    {
                                        "inline_data": {
                                            "mime_type": "image/jpeg",
                                            "data": img_bytes
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    
                    # Petición POST directa
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        texto_respuesta = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        st.success("¡Análisis completado con éxito!")
                        st.markdown("### 📊 Desglose Nutricional:")
                        st.markdown(texto_respuesta)
                    else:
                        st.error(f"Error de la API ({response.status_code}): {response.text}")
                        
                except Exception as e:
                    st.error(f"Hubo un error al procesar la solicitud: {e}")
