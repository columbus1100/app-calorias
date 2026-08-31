from datetime import datetime
import sqlite3
import time
from google import genai
from PIL import Image
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA Y PWA ---
st.set_page_config(
    page_title="Calorías AI - Pro 2.0 📸", page_icon="icon.png", layout="centered"
)

st.markdown(
    """
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0083B8">
    <meta name="mobile-web-app-capable" content="yes">
    """,
    unsafe_allow_html=True,
)

# --- CONFIGURACIÓN DE BASE DE DATOS LOCAL (PERSISTENCIA) ---
def init_db():
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            alimento TEXT,
            gramos INTEGER,
            calorias INTEGER,
            proteinas REAL,
            grasas REAL,
            carbs REAL
        )
    """)
  conn.commit()
  conn.close()

init_db()

def guardar_en_db(fecha, alimento, gramos, cal, prot, grasas, carbs):
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO registros (fecha, alimento, gramos, calorias, proteinas, grasas, carbs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
      (fecha, alimento, gramos, cal, prot, grasas, carbs),
  )
  conn.commit()
  conn.close()

def obtener_registros_hoy():
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  hoy = datetime.now().strftime("%Y-%m-%d")
  cursor.execute(
      """
        SELECT alimento, gramos, calorias, proteinas, grasas, carbs FROM registros WHERE fecha = ?
    """,
      (hoy,),
  )
  datos = cursor.fetchall()
  conn.close()
  return datos

def limpiar_db_hoy():
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  hoy = datetime.now().strftime("%Y-%m-%d")
  cursor.execute("DELETE FROM registros WHERE fecha = ?", (hoy,))
  conn.commit()
  conn.close()

# --- CONFIGURACIÓN DE LA IA ---
try:
  client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
  st.error(
      "⚠️ Configura correctamente la clave 'GEMINI_API_KEY' en los Secrets de"
      " Streamlit."
  )

if "ultima_vez" not in st.session_state:
  st.session_state.ultima_vez = 0

TIEMPO_ESPERA = 3

# --- BARRA LATERAL AVANZADA ---
st.sidebar.title("⚙️ Configuración Pro")
objetivo = st.sidebar.selectbox(
    "Tu objetivo nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Resumen Diario (Persistente)")

# Cargar registros desde la base de datos de hoy
registros_hoy = obtener_registros_hoy()
total_cal = sum([r[2] for r in registros_hoy])
total_prot = sum([r[3] for r in registros_hoy])
total_grasas = sum([r[4] for r in registros_hoy])
total_carbs = sum([r[5] for r in registros_hoy])

# Mostrar métricas actualizadas
st.sidebar.metric("🔥 Calorías Totales", f"{total_cal} kcal")
st.sidebar.metric("🥩 Proteínas", f"{total_prot:.1f} g")
st.sidebar.metric("🥑 Grasas", f"{total_grasas:.1f} g")
st.sidebar.metric("🍞 Carbohidratos", f"{total_carbs:.1f} g")

# Botón para reiniciar el día en la BD
if st.sidebar.button("🗑️ Reiniciar día completo"):
  limpiar_db_hoy()
  st.rerun()

# Exportar informe diario
if registros_hoy:
  st.sidebar.markdown("---")
  texto_informe = f"INFORME NUTRICIONAL - {datetime.now().strftime('%Y-%m-%d')}\n\n"
  texto_informe += f"Objetivo: {objetivo}\n"
  texto_informe += f"Calorías Totales: {total_cal} kcal\n"
  texto_informe += (
      f"Macros -> Prot: {total_prot:.1f}g | Grasas:"
      f" {total_grasas:.1f}g | Carbs: {total_carbs:.1f}g\n\nDetalle:\n"
  )
  for r in registros_hoy:
    texto_informe += f"- {r[0]} ({r[1]}g): {r[2]}kcal\n"

  st.sidebar.download_button(
      label="📥 Descargar Informe Diario",
      data=texto_informe,
      file_name=f"informe_nutricional_{datetime.now().strftime('%Y-%m-%d')}.txt",
      mime="text/plain",
  )

# --- CUERPO PRINCIPAL ---
st.title("🥗 Detector de Calorías Pro - 2.0")
st.write(f"Analizando bajo el objetivo de: **{objetivo}**")

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

if "analisis_realizado" not in st.session_state:
  st.session_state.analisis_realizado = False
if "alimento_detectado" not in st.session_state:
  st.session_state.alimento_detectado = ""
if "peso_estimado" not in st.session_state:
  st.session_state.peso_estimado = 200

if archivo_subido is not None:
  imagen = Image.open(archivo_subido)
  st.image(imagen, caption="Plato analizado", use_container_width=True)

  # PASO 1: Identificación y estimación automática de peso por IA
  if not st.session_state.analisis_realizado:
    if st.button("🔥 Identificar Plato y Estimar Peso con IA", type="primary"):
      tiempo_actual = time.time()
      if (tiempo_actual - st.session_state.ultima_vez) < TIEMPO_ESPERA:
        st.warning("⏳ ¡Espera unos segundos antes de otra consulta!")
      else:
        st.session_state.ultima_vez = time.time()
        with st.spinner("La IA analiza el plato y calcula el gramaje..."):
          prompt_reconocimiento = (
              "Analiza esta imagen de comida. Responde estrictamente con una"
              " estructura de dos líneas:\nLínea 1: El nombre claro y directo"
              " del plato.\nLínea 2: Una estimación numérica del peso total en"
              " gramos (solo el número entero, ej: 350)."
          )

          exito = False
          resultado_ia = ""
          for intento in range(3):
            try:
              respuesta = client.models.generate_content(
                  model="gemini-3.6-flash",
                  contents=[prompt_reconocimiento, imagen],
              )
              resultado_ia = respuesta.text.strip()
              exito = True
              break
            except Exception:
              time.sleep(2)

          if exito:
            lineas = resultado_ia.split("\n")
            st.session_state.alimento_detectado = lineas[0].replace(
                "Línea 1:", ""
            ).strip()
            # Intentar extraer el número de gramos de la segunda línea
            try:
              import re

              match = re.search(
                  r"\d+", lineas[1] if len(lineas) > 1 else resultado_ia
              )
              if match:
                st.session_state.peso_estimado = int(match.group())
            except Exception:
              st.session_state.peso_estimado = 200

            st.session_state.analisis_realizado = True
            st.rerun()
          else:
            st.error("Error al conectar con la IA.")

  # PASO 2: Confirmación, edición y cálculo automatizado
  if st.session_state.analisis_realizado:
    st.info(
        f"🤖 La IA cree que es: **{st.session_state.alimento_detectado}**"
        f" (Peso estimado: {st.session_state.peso_estimado}g)"
    )

    es_correcto = st.radio(
        "¿Es correcto?",
        ("Sí, es correcto", "No, quiero corregirlo/escribirlo yo"),
        key="radio_correccion",
    )

    alimento_final = st.session_state.alimento_detectado
    if es_correcto == "No, quiero corregirlo/escribirlo yo":
      alimento_final = st.text_input(
          "Escribe el nombre real:", value=st.session_state.alimento_detectado
      )

    # Permitir afinar el peso estimado por la IA mediante un slider ajustable
    gramos_porcion = st.slider(
        "Ajusta el gramaje de la porción (g):",
        50,
        800,
        int(st.session_state.peso_estimado),
        step=10,
    )

    if st.button("📊 Calcular y Guardar en el Diario", type="primary"):
      with st.spinner("Calculando nutrientes exactos..."):
        # Pedimos formato estructurado estricto para extraer los números informáticamente
        prompt_calculo = (
            f"Analiza el alimento '{alimento_final}' con un peso de"
            f" {gramos_porcion} gramos. Devuelve la respuesta en formato"
            " estricto separada por comas con este orden exacto (solo los"
            " números para los valores):"
            "\nCALORIAS: [número kcal]"
            "\nPROTEINAS: [número gramos]"
            "\nGRASAS: [número gramos]"
            "\nCARBS: [número gramos]"
            "\nY añade después un breve comentario nutricional útil."
        )

        exito_calculo = False
        res_final = None
        for intento in range(3):
          try:
            res_final = client.models.generate_content(
                model="gemini-3.6-flash", contents=[prompt_calculo, imagen]
            )
            exito_calculo = True
            break
          except Exception:
            time.sleep(2)

        if exito_calculo:
          texto_respuesta = res_final.text
          st.success("¡Cálculo nutricional completado y guardado!")
          st.markdown(
              f"### 📊 Resultado para {gramos_porcion}g de"
              f" **{alimento_final}**:"
          )
          st.write(texto_respuesta)

          # Extracción inteligente de valores mediante expresiones regulares para la base de datos
          import re
          try:
            cal_match = re.search(
                r"CALORIAS[:\s]*(\d+)", texto_respuesta, re.IGNORECASE
            )
            prot_match = re.search(
                r"PROTEINAS[:\s]*([\d\.]+)", texto_respuesta, re.IGNORECASE
            )
            gras_match = re.search(
                r"GRASAS[:\s]*([\d\.]+)", texto_respuesta, re.IGNORECASE
            )
            carb_match = re.search(
                r"CARBS[:\s]*([\d\.]+)", texto_respuesta, re.IGNORECASE
            )

            val_cal = int(cal_match.group(1)) if cal_match else 300
            val_prot = float(prot_match.group(1)) if prot_match else 15.0
            val_gras = float(gras_match.group(1)) if gras_match else 10.0
            val_carb = float(carb_match.group(1)) if carb_match else 30.0

            # Guardar de forma persistente en SQLite
            hoy = datetime.now().strftime("%Y-%m-%d")
            guardar_en_db(
                hoy,
                alimento_final,
                gramos_porcion,
                val_cal,
                val_prot,
                val_gras,
                val_carb,
            )

          except Exception as parse_err:
            st.warning(
                "Aviso: Se calculó correctamente pero hubo un pequeño detalle"
                f" al sumar automáticamente los macros ({parse_err})."
            )

          if st.button("🔄 Analizar otro plato"):
            st.session_state.analisis_realizado = False
            st.session_state.alimento_detectado = ""
            st.rerun()
        else:
          st.error("Error al conectar con la IA para calcular los macros.")

# Mostrar listado persistente en la barra lateral
if registros_hoy:
  st.sidebar.markdown("---")
  st.sidebar.text("Platos registrados hoy:")
  for item in registros_hoy:
    st.sidebar.text(f"• {item[0]} ({item[1]}g) - {item[2]}kcal")
else:
  st.sidebar.text("Sin platos registrados aún hoy")
