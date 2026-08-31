import streamlit as st
from google import genai
from PIL import Image
import traceback

st.title("🔍 Cazador de Errores")

api_key = "AQ.Ab8RN6Lztnm_ZKF5stmztJNUn3VQnAGHbRO7W-ISURujXDGhRQ"

archivo_subido = st.file_uploader("Sube una foto", type=["jpg", "jpeg", "png"])

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen)
    
    if st.button("Probar conexión a la fuerza"):
        try:
            client = genai.Client(api_key=api_key)
            st.write("Cliente creado, intentando conectar con Gemini...")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[imagen, "Hola, dime qué ves brevemente."]
            )
            st.success("¡FUNCIONÓ!")
            st.write(response.text)
            
        except Exception as e:
            st.error("¡Aquí está el error completo!")
            # Esto imprimirá el error técnico exacto en rojo grande
            st.exception(e)
