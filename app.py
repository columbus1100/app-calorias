from google import genai
from PIL import Image
import streamlit as st

st.title("Prueba limpia de Gemini")

# Cliente de la API
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

archivo_subido = st.file_uploader(
    "Sube una foto de prueba", type=["jpg", "jpeg", "png"]
)

if archivo_subido is not None:
  imagen = Image.open(archivo_subido)
  st.image(imagen, caption="Imagen cargada", use_container_width=True)

  if st.button("Hacer prueba directa"):
    with st.spinner("Conectando con Gemini..."):
      try:
        # Usamos el modelo correcto que pide Google
        respuesta = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=["¿Qué ves en esta imagen?", imagen],
        )
        st.success("¡Conexión exitosa!")
        st.write(respuesta.text)

      except Exception as e:
        st.error(f"El error exacto que da Google es: {e}")
