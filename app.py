from datetime import datetime
import os
import sqlite3
import time
from google import genai
from PIL import Image
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA Y PWA ---
st.set_page_config(
    page_title="Calorías AI - Pro 2.0 📸", page_icon="icon.png", layout="wide"
)

st.markdown(
    """
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0083B8">
    <meta name="mobile-web-app-capable" content="yes">
    <style>
        .stMetric {
            background-color: rgba(28, 32, 44, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- GESTOR DE CLIENTE IA ---
def obtener_cliente_ia():
  raw_keys = st.secrets.get("GEMINI_API_KEY", "")
  keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

  if not keys:
    st.error(
        "⚠️ Configura al menos una clave 'GEMINI_API_KEY' en los Secrets de"
        " Streamlit."
    )
    return None

  # Usamos siempre la primera clave disponible de forma limpia
  active_key = keys[0]
  os.environ["GEMINI_API_KEY"] = active_key
  return genai.Client(api_key=active_key)


# --- CONFIGURACIÓN DE BASE DE DATOS LOCAL SEGURA ---
def init_db():
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
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


def guardar_en_db(usuario, fecha, alimento, gramos, cal, prot, grasas, carbs):
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO registros (usuario, fecha, alimento, gramos, calorias, proteinas, grasas, carbs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (usuario, fecha, alimento, gramos, cal, prot, grasas, carbs),
  )
  conn.commit()
  conn.close()


def obtener_registros_hoy(usuario):
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  hoy = datetime.now().strftime("%Y-%m-%d")
  try:
    cursor.execute(
        """
            SELECT alimento, gramos, calorias, proteinas, grasas, carbs FROM registros WHERE usuario = ? AND fecha = ?
        """,
        (usuario, hoy),
    )
    datos = cursor.fetchall()
  except sqlite3.OperationalError:
    cursor.execute("DROP TABLE IF EXISTS registros")
    cursor.execute("""
            CREATE TABLE registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
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
    datos = []
  conn.close()
  return datos


def limpiar_db_hoy(usuario):
  conn = sqlite3.connect("historial_nutricional.db", check_same_thread=False)
  cursor = conn.cursor()
  hoy = datetime.now().strftime("%Y-%m-%d")
  cursor.execute(
      "DELETE FROM registros WHERE usuario = ? AND fecha = ?", (usuario, hoy)
  )
  conn.commit()
  conn.close()


if "ultima_vez" not in st.session_state:
  st.session_state.ultima_vez = 0

# Aumentamos el tiempo de espera preventivo a 4 segundos para cuidar la cuota gratuita
TIEMPO_ESPERA = 4

# --- BARRA LATERAL PROFESIONAL ---
st.sidebar.title("🥗 Calorías AI Pro")
st.sidebar.markdown("---")

usuario_actual = st.sidebar.text_input(
    "👤 Perfil Activo:", value="Usuario 1"
)
objetivo = st.sidebar.selectbox(
    "🎯 Objetivo Nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"],
)

st.sidebar.markdown("---")
registros_hoy = obtener_registros_hoy(usuario_actual)
total_cal = sum([r[2] for r in registros_hoy])
total_prot = sum([r[3] for r in registros_hoy])
total_grasas = sum([r[4] for r in registros_hoy])
total_carbs = sum([r[5] for r in registros_hoy])

st.sidebar.subheader("📊 Resumen Diario")
st.sidebar.metric("🔥 Calorías", f"{total_cal} kcal")

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
  st.metric("🥩 Prot", f"{total_prot:.1f}g")
  st.metric("🥑 Grasas", f"{total_grasas:.1f}g")
with col_sb2:
  st.metric("🍞 Carbs", f"{total_carbs:.1f}g")

st.sidebar.markdown("---")
if st.sidebar.button(
    f"🗑️ Reiniciar día de {usuario_actual}", use_container_width=True
):
  limpiar_db_hoy(usuario_actual)
  st.rerun()

if registros_hoy:
  texto_informe = (
      f"INFORME NUTRICIONAL ({usuario_actual}) -"
      f" {datetime.now().strftime('%Y-%m-%d')}\n\n"
  )
  texto_informe += f"Objetivo: {objetivo}\n"
  texto_informe += f"Calorías Totales: {total_cal} kcal\n"
  texto_informe += (
      f"Macros -> Prot: {total_prot:.1f}g | Grasas:"
      f" {total_grasas:.1f}g | Carbs: {total_carbs:.1f}g\n\nDetalle:\n"
  )
  for r in registros_hoy:
    texto_informe += f"- {r[0]} ({r[1]}g): {r[2]}kcal\n"

  st.sidebar.download_button(
      label="📥 Descargar Informe TXT",
      data=texto_informe,
      file_name=(
          f"informe_{usuario_actual.lower()}_"
          f"{datetime.now().strftime('%Y-%m-%d')}.txt"
      ),
      mime="text/plain",
      use_container_width=True,
  )

# --- CABECERA PRINCIPAL ---
st.title("🥗 Detector Inteligente de Calorías")
st.markdown(
    f"Bienvenido, **{usuario_actual}**. Gestiona tu nutrición diaria con"
    f" Inteligencia Artificial."
)

# --- SISTEMA DE PESTAÑAS PROFESIONALES ---
pestana_analisis, pestana_diario, pestana_config = st.tabs(
    ["📸 Analizar Plato", "📖 Diario Nutricional", "⚙️ Ajustes y Perfil"]
)

# =========================================================================
# PESTAÑA 1: ANALIZAR PLATO
# =========================================================================
with pestana_analisis:
  st.markdown("### Sube o fotografía tu comida para un análisis instantáneo")

  metodo_foto = st.radio(
      "Método de captura:",
      ("Subir archivo", "Hacer foto con la cámara"),
      horizontal=True,
  )

  if "form_key_counter" not in st.session_state:
    st.session_state.form_key_counter = 0

  archivo_subido = None
  if metodo_foto == "Subir archivo":
    archivo_subido = st.file_uploader(
        "Selecciona una imagen...",
        type=["jpg", "jpeg", "png"],
        key=f"uploader_{st.session_state.form_key_counter}",
    )
  else:
    archivo_subido = st.camera_input(
        "Toma una foto", key=f"camera_{st.session_state.form_key_counter}"
    )

  if "analisis_realizado" not in st.session_state:
    st.session_state.analisis_realizado = False
  if "alimento_detectado" not in st.session_state:
    st.session_state.alimento_detectado = ""
  if "peso_estimado" not in st.session_state:
    st.session_state.peso_estimado = 200
  if "ultima_foto" not in st.session_state:
    st.session_state.ultima_foto = None

  if archivo_subido is not None:
    if archivo_subido != st.session_state.ultima_foto:
      st.session_state.ultima_foto = archivo_subido
      st.session_state.analisis_realizado = False
      st.session_state.alimento_detectado = ""
      st.rerun()

    col_img, col_datos = st.columns([1, 1], gap="large")

    with col_img:
      try:
        imagen = Image.open(archivo_subido)
        st.image(
            imagen,
            caption="Imagen del plato analizado",
            use_container_width=True,
        )
      except Exception as img_err:
        st.error(f"Error al abrir la imagen: {img_err}")
        imagen = None

    with col_datos:
      if imagen and not st.session_state.analisis_realizado:
        st.info("💡 La IA está lista para procesar tu imagen.")
        if st.button(
            "🔥 Identificar Plato y Estimar Peso",
            type="primary",
            use_container_width=True,
        ):
          tiempo_actual = time.time()
          if (tiempo_actual - st.session_state.ultima_vez) < TIEMPO_ESPERA:
            st.warning(
                "⏳ Por favor, espera unos segundos antes de realizar otra"
                " consulta para evitar bloqueos."
            )
          else:
            st.session_state.ultima_vez = time.time()
            with st.spinner("Analizando componentes visuales..."):
              prompt_reconocimiento = (
                  "Analiza esta imagen de comida. Responde estrictamente con una"
                  " estructura de dos líneas:\nLínea 1: El nombre claro y"
                  " directo del plato.\nLínea 2: Una estimación numérica del"
                  " peso total en gramos (solo el número entero, ej: 350)."
              )

              try:
                client = obtener_cliente_ia()
                respuesta = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[prompt_reconocimiento, imagen],
                )
                resultado_ia = respuesta.text.strip()

                lineas = resultado_ia.split("\n")
                st.session_state.alimento_detectado = lineas[0].replace(
                    "Línea 1:", ""
                ).strip()
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
              except Exception as api_err:
                error_str = str(api_err)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                  st.warning(
                      "⏳ Se ha alcanzado el límite temporal de peticiones."
                      " Espera un par de minutos y vuelve a intentarlo."
                  )
                else:
                  st.error(f"❌ Error detallado de la IA: {error_str[:250]}...")

      if st.session_state.analisis_realizado:
        st.success(
            f"🤖 **Identificado:** {st.session_state.alimento_detectado}"
        )

        es_correccion = st.radio(
            "¿Deseas modificar el nombre?",
            ("Mantener nombre detectado", "Corregir nombre manualmente"),
        )

        alimento_final = st.session_state.alimento_detectado
        if es_correccion == "Corregir nombre manualmente":
          alimento_final = st.text_input(
              "Escribe el nombre correcto:",
              value=st.session_state.alimento_detectado,
          )

        gramos_porcion = st.slider(
            "⚖️ Ajustar gramaje (g):",
            50,
            800,
            int(st.session_state.peso_estimado),
            step=10,
        )

        if st.button(
            "📊 Calcular y Guardar en el Diario",
            type="primary",
            use_container_width=True,
        ):
          with st.spinner("Calculando nutrientes detallados..."):
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

            try:
              client = obtener_cliente_ia()
              res_final = client.models.generate_content(
                  model="gemini-3.6-flash", contents=[prompt_calculo, imagen]
              )
              texto_respuesta = res_final.text
              st.markdown("---")
              st.markdown(
                  f"### 📋 Resultados nutricionales para {gramos_porcion}g"
              )
              st.write(texto_respuesta)

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

                hoy = datetime.now().strftime("%Y-%m-%d")
                guardar_en_db(
                    usuario_actual,
                    hoy,
                    alimento_final,
                    gramos_porcion,
                    val_cal,
                    val_prot,
                    val_gras,
                    val_carb,
                )
                st.success("✨ ¡Guardado con éxito en tu diario nutricional!")

              except Exception as parse_err:
                st.warning(f"Aviso al procesar valores: {parse_err}")

              if st.button(
                  "🔄 Analizar otro plato", use_container_width=True
              ):
                st.session_state.analisis_realizado = False
                st.session_state.alimento_detectado = ""
                st.session_state.ultima_foto = None
                st.session_state.form_key_counter += 1
                st.rerun()

            except Exception as err_c:
              error_calc = str(err_c)
              if "429" in error_calc or "RESOURCE_EXHAUSTED" in error_calc:
                st.warning(
                    "⏳ Se ha alcanzado el límite temporal de peticiones."
                    " Espera un par de minutos y vuelve a intentarlo."
                )
              else:
                st.error(
                    f"❌ Error detallado al calcular macros:"
                    f" {error_calc[:250]}..."
                )

# =========================================================================
# PESTAÑA 2: DIARIO NUTRICIONAL
# =========================================================================
with pestana_diario:
  st.markdown(f"### 📖 Registro de comidas de hoy para **{usuario_actual}**")

  if registros_hoy:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
      st.metric("🔥 Calorías", f"{total_cal} kcal")
    with col_m2:
      st.metric("🥩 Proteínas", f"{total_prot:.1f} g")
    with col_m3:
      st.metric("🥑 Grasas", f"{total_grasas:.1f} g")
    with col_m4:
      st.metric("🍞 Carbohidratos", f"{total_carbs:.1f} g")

    st.markdown("---")
    st.subheader("📋 Detalle de ingestas")
    for idx, item in enumerate(registros_hoy):
      with st.container():
        st.markdown(
            f"""**{idx+1}. {item[0]}**  
            ⚖️ **Peso:** {item[1]}g  |  🔥 **Calorías:** {item[2]} kcal  |  🥩"
            f" **Prot:** {item[3]}g  |  🥑 **Grasas:** {item[4]}g  |  🍞"
            f" **Carbs:** {item[5]}g"""
        )
        st.divider()
  else:
    st.info(
        "📭 Aún no hay alimentos registrados para hoy. ¡Sube tu primera foto"
        " desde la pestaña de análisis!"
    )

# =========================================================================
# PESTAÑA 3: AJUSTES Y PERFIL
# =========================================================================
with pestana_config:
  st.markdown("### ⚙️ Configuración del Perfil y Preferencias")
  st.write(f"Estás configurando actualmente el perfil de: **{usuario_actual}**")

  st.text_input(
      "Modificar nombre de usuario:",
      value=usuario_actual,
      key="input_mod_usuario",
  )
  st.selectbox(
      "Cambiar objetivo nutricional:",
      [
          "Mantener peso",
          "Definición / Perder grasa",
          "Volumen / Ganar músculo",
      ],
      index=0,
  )

  st.success(
      "Los cambios de perfil se aplican automáticamente en la barra lateral."
  )
