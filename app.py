import time
import streamlit as st

# Título de tu aplicación
st.title("Calorías AI - Mejora 1.0")

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
  st.image(
      archivo_imagen, caption="Plato subido", use_container_width=True
  )

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

      # Aquí va tu lógica para llamar a Gemini y analizar el plato
      with st.spinner("Analizando plato... 🤖"):
        # --- AQUÍ PONES TU CÓDIGO DE LLAMADA A GEMINI ---
        # Ejemplo: respuesta = modelo.generate_content(...)
        # st.write(respuesta.text)
        pass
