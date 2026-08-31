import streamlit as st
from PIL import Image
from google import genai
import time

# Configuración de la página con tu icono personalizado (icon.png)
st.set_page_config(
    page_title="Calorías AI 📸", 
    page_icon="icon.png", 
    layout="centered"
)

# --- INYECTAR SOPORTE PARA MÓVIL (PWA Y MANIFEST) ---
st.markdown(
    """
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0083B8">
    <meta name="mobile-web-app-capable" content="yes">
    """,
    unsafe_allow_html=True
)

# Configurar el cliente de la IA de Google usando los secrets
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("⚠️ Configura correctamente la clave 'GEMINI_API_KEY' en los Secrets de Streamlit.")

# --- BARRA LATERAL (AJUSTES E HISTORIAL) ---
st.sidebar.title("⚙️ Configuración")
objetivo = st.sidebar.selectbox(
    "Tu objetivo nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"]
)

# Control de tamaño de porción en la barra lateral
gramos_porcion = st.sidebar.slider("Gramaje estimado de la porción (g):", 50, 500, 100, step=10)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Historial de la sesión")

# Inicializar historial en memoria
if "historial" not in st.session_state:
    st.session_state.historial = []

# Botón para limpiar historial
if st.sidebar.button("🗑️ Limpiar historial"):
    st.session_state.historial = []
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🥗 Detector de Calorías por Foto")
st.write(f"Analizando bajo el objetivo de: **{objetivo}**")

# Selector para subir foto o usar la cámara
metodo_foto = st.radio("¿Cómo prefieres añadir la imagen?", ("Subir archivo", "Hacer foto con la cámara"))

archivo_subido = None
if metodo_foto == "Subir archivo":
    archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])
else:
    archivo_subido = st.camera_input("Haz una foto al plato")

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado", use_container_width=True)
    
    if st.button("🔥 Analizar con IA", type="primary"):
        with st.spinner("La IA está analizando el plato (si hay mucha demanda, reintentará automáticamente)..."):
            prompt = (
                f"Analiza esta imagen de comida. El usuario indica que la porción pesa exactamente {gramos_porcion} gramos. "
                f"Identifica el alimento y calcula de manera aproximada para esos {gramos_porcion} gramos: "
                f"1. Calorías totales (kcal). "
                f"2. Gramos de proteínas. "
                f"3. Gramos de grasas. "
                f"4. Gramos de carbohidratos. "
                f"Devuelve los resultados de forma clara y directa."
            )
            
            # Sistema de reintentos automáticos para evitar el error 503 por saturación
            exito = False
            respuesta_ia = None
            intentos = 3
            
            for intento in range(intentos):
                try:
                    respuesta_ia = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt, imagen]
                    )
                    exito = True
                    break
                except Exception as e:
                    if "503" in str(e) and intento < intentos - 1:
                        time.sleep(2) # Espera 2 segundos y vuelve a probar
                        continue
                    else:
                        error_msg = str(e)

            if exito:
                st.success("¡Análisis completado con éxito!")
                
                # Mostrar el resultado devuelto por la IA
                st.markdown(f"### 📊 Resultado para {gramos_porcion}g:")
                st.write(respuesta_ia.text)
                
                # Consejo inteligente según el objetivo
                if "Definición" in objetivo:
                    st.warning("⚠️ **Consejo de Definición:** Vigila las calorías totales y prioriza alimentos saciantes dentro de tu déficit.")
                elif "Volumen" in objetivo:
                    st.info("💪 **Consejo de Volumen:** ¡Aprovecha para sumar nutrientes de calidad que te ayuden a llegar a marcas!")
                else:
                    st.info("⚖️ **Consejo de Mantenimiento:** Mantén el equilibrio adaptando las porciones a tu gasto diario.")

                # Guardar en el historial de la sesión
                resultado_resumen = f"{gramos_porcion}g - Analizado por IA"
                if resultado_resumen not in st.session_state.historial:
                    st.session_state.historial.append(resultado_resumen)
            else:
                st.error(f"Error al conectar con la IA tras varios intentos: {error_msg}")

# Mostrar el historial en la barra lateral
if st.session_state.historial:
    for item in st.session_state.historial:
        st.sidebar.text(f"• {item}")
else:
    st.sidebar.text("Aún no hay registros")
