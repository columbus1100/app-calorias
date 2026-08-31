import time
from google import genai
import streamlit as st

# Título de tu aplicación
st.title("Calorías AI - Mejora 1.0")

# Configuración del cliente de Gemini (asegúrate de tener tu API Key en los secrets de Streamlit o ponla aquí)
# client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 1. Memoria para controlar el tiempo entre peticiones
if "ultima_vez" not in st.session_state:
  st.session_state.ultima_vez = 0

# Tiempo de espera en segundos (por ejemplo, 5 segundos)
TIEMPO_ESPERA = 5

# 2. Tu componente para subir la imagen
archivo_imagen = st.file_uploader(
    "Sube la foto de tu plato", type=["jpg", "jpeg", "png"]
)

if archivo_imagen is not None:
  # Mostramos la imagen en pantalla
  st.image(archivo_imagen, caption="Plato subido", use_container_width=True)

  # 3. El botón de análisis
  if st.button("Identificar Plato con IA"):
    tiempo_actual = time.time()
    tiempo_transcurrido = tiempo_actual - st.session_state.ultima_vez

    # Si han pasado menos de los segundos configurados, bloqueamos
    if tiempo_transcurrido < TIEMPO_ESPERA:
      segundos_restantes = int(TIEMPO_ESPERA - tiempo_transcurrido)
      st.warning(
          f"⏳ ¡Un momento! Espera {segundos_restantes} segundos antes de"
          " hacer otra consulta."
      )
    else:
      # Actualizamos el cronómetro
      st.session_state.ultima_vez = time.time()

      # Procesamiento con la IA
      with st.spinner("Analizando plato... 🤖"):
        try:
          # --- PEGA AQUÍ TU CÓDIGO DE LLAMADA A GEMINI ---
          # Ejemplo con la nueva SDK:
          # response = client.models.generate_content(
          #     model='gemini-2.5-flash',
          #     contents=[archivo_imagen, "Analiza este plato y dime las calorías."]
          # )
          # st.write(response.text)

          # (De momento ponemos esto para que veas que funciona el botón)
          st.success("¡Plato analizado con éxito! (Aquí irán tus calorías)")

        except Exception as e:
          st.error(f"Ha ocurrido un error al conectar con la IA: {e}")
