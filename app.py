import time
import streamlit as st

# 1. Creamos una "memoria" para saber cuándo fue la última vez que se usó la IA
if "ultima_vez" not in st.session_state:
  st.session_state.ultima_vez = 0

# Tiempo de espera en segundos (por ejemplo, 5 segundos entre cada foto)
TIEMPO_ESPERA = 5

# Tu botón de análisis de siempre
if st.button("Identificar Plato con IA"):
  tiempo_actual = time.time()
  tiempo_transcurrido = tiempo_actual - st.session_state.ultima_vez

  # Si ha pasado menos tiempo del establecido, bloqueamos y avisamos
  if tiempo_transcurrido < TIEMPO_ESPERA:
    segundos_restantes = int(TIEMPO_ESPERA - tiempo_transcurrido)
    st.warning(
        f"⏳ ¡Espera un momentito! Por favor, aguarda {segundos_restantes}"
        " segundos antes de hacer otra consulta para no saturar a la IA."
    )
  else:
    # Actualizamos el cronómetro con el momento actual
    st.session_state.ultima_vez = time.time()

    # 2. Aquí metes tu código habitual que llama a Gemini
    with st.spinner("Analizando plato... 🤖"):
      # --- AQUÍ VA TU CÓDIGO DE LLAMADA A LA API ---
      # st.write("Resultado de la IA...")
      pass
