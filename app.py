import time
from google import genai
from PIL import Image
import streamlit as st

# --- MEJORA 1.0: CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Calorías AI - Mejora 1.0 📸",
    page_icon="icon.png",
    layout="centered",
)

# --- INYECTAR SOPORTE PARA MÓVIL (PWA Y MANIFEST) ---
st.markdown(
    """
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0083B8">
    <meta name="mobile-web-app-capable" content="yes">
    """,
    unsafe_allow_html=True,
)

# Configurar el cliente de la IA de Google usando los secrets
try:
  client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
  st.error(
      "⚠️ Configura correctamente la clave 'GEMINI_API_KEY' en los Secrets de"
      " Streamlit."
  )

# --- CONTROL DE TIEMPO (COOLDOWN) PARA EVITAR LÍMITES ---
if "ultima_vez" not in st.session_state:
  st.session_state.ultima_vez = 0

TIEMPO_ESPERA = 5  # Segundos de espera obligatorios entre peticiones

# --- BARRA LATERAL (CONFIGURACIÓN E HISTORIAL ACUMULATIVO) ---
st.sidebar.title("⚙️ Configuración")
objetivo = st.sidebar.selectbox(
    "Tu objetivo nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"],
)

# Control de tamaño de porción en la barra lateral
gramos_porcion = st.sidebar.slider(
    "Gramaje estimado de la porción (g):", 50, 500, 100, step=10
)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Resumen Diario del Día")

# Inicializar variables acumulativas en session_state
if "historial" not in st.session_state:
  st.session_state.historial = []
if "total_calorias" not in st.session_state:
  st.session_state.total_calorias = 0
if "total_proteinas" not in st.session_state:
  st.session_state.total_proteinas = 0
if "total_grasas" not in st.session_state:
  st.session_state.total_grasas = 0
if "total_carbs" not in st.session_state:
  st.session_state.total_carbs = 0

# Mostrar métricas acumuladas en la barra lateral
st.sidebar.metric("🔥 Calorías Totales", f"{st.session_state.total_calorias} kcal")
st.sidebar.metric("🥩 Proteínas", f"{st.session_state.total_proteinas} g")
st.sidebar.metric("🥑 Grasas", f"{st.session_state.total_grasas} g")
st.sidebar.metric("🍞 Carbohidratos", f"{st.session_state.total_carbs} g")

# Botón para limpiar todo el día
if st.sidebar.button("🗑️ Reiniciar día completo"):
  st.session_state.historial = []
  st.session_state.total_calorias = 0
  st.session_state.total_proteinas = 0
  st.session_state.total_grasas = 0
  st.session_state.total_carbs = 0
  st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🥗 Detector de Calorías - Mejora 1.0")
st.write(f"Analizando bajo el objetivo de: **{objetivo}**")

# Selector para subir foto o usar la cámara
metodo_foto = st.radio(
    "¿Cómo prefieres añadir la imagen?",
    ("Subir archivo", "Hacer foto con la cámara"),
)

archivo_subido = None
if metodo_foto == "Subir archivo":
  archivo_subido = st.file_uploader(
      "Elige una foto de comida...", type=["jpg", "jpeg", "png"]
  )
else:
  archivo_subido = st.camera_input("Haz una foto al plato")

# Control de estados para el flujo de validación
if "analisis_realizado" not in st.session_state:
  st.session_state.analisis_realizado = False
if "alimento_detectado" not in st.session_state:
  st.session_state.alimento_detectado = ""

if archivo_subido is not None:
  imagen = Image.open(archivo_subido)
  st.image(imagen, caption="Plato analizado", use_container_width=True)

  # PASO 1: Análisis inicial de la IA para reconocer el plato
  if not st.session_state.analisis_realizado:
    if st.button("🔥 Identificar Plato con IA", type="primary"):
      # Comprobamos el tiempo transcurrido desde la última petición
      tiempo_actual = time.time()
      tiempo_transcurrido = tiempo_actual - st.session_state.ultima_vez

      if tiempo_transcurrido < TIEMPO_ESPERA:
        segundos_restantes = int(TIEMPO_ESPERA - tiempo_transcurrido)
        st.warning(
            f"⏳ ¡Espera {segundos_restantes} segundos antes de hacer otra"
            " consulta para no saturar a la IA!"
        )
      else:
        st.session_state.ultima_vez = time.time()
        with st.spinner("La IA está examinando la imagen..."):
          prompt_reconocimiento = (
              "Identifica brevemente qué plato o alimento aparece en esta"
              " imagen. Responde solo con el nombre del plato de forma clara"
              " y directa, sin dar valores nutricionales todavía."
          )

          exito = False
          resultado_ia = ""
          ultimo_error = ""

          for intento in range(3):
            try:
              respuesta = client.models.generate_content(
                  model="gemini-2.5-flash",
                  contents=[prompt_reconocimiento, imagen],
              )
              resultado_ia = respuesta.text.strip()
              exito = True
              break
            except Exception as e:
              ultimo_error = str(e)
              if "429" in ultimo_error:
                time.sleep(5)
              else:
                time.sleep(2)

          if exito:
            st.session_state.alimento_detectado = resultado_ia
            st.session_state.analisis_realizado = True
            st.rerun()
          else:
            if "429" in ultimo_error:
              st.error(
                  "⚠️ Límite de peticiones gratuitas alcanzado. Espera un"
                  " minuto antes de volver a pulsar."
              )
            else:
              st.error(f"Error de conexión con la IA: {ultimo_error}")

  # PASO 2: Confirmación y corrección manual si la IA falla
  if st.session_state.analisis_realizado:
    st.info(
        f"🤖 La IA cree que esto es:"
        f" **{st.session_state.alimento_detectado}**"
    )

    es_correcto = st.radio(
        "¿Es correcto este alimento?",
        ("Sí, es correcto", "No, quiero corregirlo/escribirlo yo"),
        key="radio_correccion",
    )

    alimento_final = st.session_state.alimento_detectado
    if es_correcto == "No, quiero corregirlo/escribirlo yo":
      alimento_final = st.text_input(
          "Escribe el nombre real del plato o ingredientes:",
          value=st.session_state.alimento_detectado,
      )

    if st.button("📊 Calcular Calorías y Macros", type="primary"):
      with st.spinner("Calculando nutrientes detallados..."):
        prompt_calculo = (
            f"Analiza este alimento: '{alimento_final}' con un peso exacto de"
            f" {gramos_porcion} gramos. Proporciona estrictamente los"
            f" siguientes datos numéricos aproximados para esos"
            f" {gramos_porcion}g: - Calorías totales (kcal) - Proteínas (g) -"
            f" Grasas (g) - Carbohidratos (g) Y añade un pequeño desglose o"
            " comentario útil."
        )

        exito_calculo = False
        res_final = None
        error_msg = ""

        for intento in range(3):
          try:
            res_final = client.models.generate_content(
                model="gemini-2.5-flash", contents=[prompt_calculo, imagen]
            )
            exito_calculo = True
            break
          except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
              time.sleep(5)
            else:
              time.sleep(2)

        if exito_calculo:
          st.success("¡Cálculo nutricional completado con éxito!")
          st.markdown(
              f"### 📊 Resultado para {gramos_porcion}g de"
              f" **{alimento_final}**:"
          )
          st.write(res_final.text)

          # Consejo según objetivo
          if "Definición" in objetivo:
            st.warning(
                "⚠️ **Consejo de Definición:** Controla el total diario para"
                " mantener tu déficit."
            )
          elif "Volumen" in objetivo:
            st.info(
                "💪 **Consejo de Volumen:** ¡Excelente aporte para construir"
                " masa muscular!"
            )
          else:
            st.info(
                "⚖️ **Consejo de Mantenimiento:** Estupendo plato para tu"
                " equilibrio diario."
            )

          # Añadir al historial visual y de sesión
          resultado_resumen = f"{alimento_final} ({gramos_porcion}g)"
          if resultado_resumen not in st.session_state.historial:
            st.session_state.historial.append(resultado_resumen)

          # Botón para resetear y hacer otra foto
          if st.button("🔄 Analizar otro plato"):
            st.session_state.analisis_realizado = False
            st.session_state.alimento_detectado = ""
            st.rerun()
        else:
          st.error(f"Error al conectar con la IA: {error_msg}")

# Mostrar el listado rápido de comidas en la barra lateral
if st.session_state.historial:
  st.sidebar.markdown("---")
  st.sidebar.text("Platos registrados hoy:")
  for item in st.session_state.historial:
    st.sidebar.text(f"• {item}")
else:
  st.sidebar.text("Sin platos registrados aún")
