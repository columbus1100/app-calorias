import streamlit as st
from PIL import Image
from google import genai
import time

# Configuración de la página
st.set_page_config(
    page_title="Calorías AI 📸", 
    page_icon="icon.png", 
    layout="centered"
)

# --- INYECTAR SOPORTE PARA MÓVIL (PWA) ---
st.markdown(
    """
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0083B8">
    """,
    unsafe_allow_html=True
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_key = st.secrets.get("GEMINI_API_KEY")

# --- BARRA LATERAL (AJUSTES E HISTORIAL) ---
st.sidebar.title("⚙️ Configuración")
objetivo = st.sidebar.selectbox(
    "Tu objetivo nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"]
)

gramos_porcion = st.sidebar.slider("Gramaje estimado de la porción (g):", 50, 500, 100, step=10)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Historial de la sesión")

if "historial" not in st.session_state:
    st.session_state.historial = []

if st.sidebar.button("🗑️ Limpiar historial"):
    st.session_state.historial = []
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🥗 Detector de Calorías por IA")
st.write(f"Analizando bajo el objetivo de: **{objetivo}**")

metodo_foto = st.radio("¿Cómo prefieres añadir la imagen?", ("Subir archivo", "Hacer foto con la cámara"))

archivo_subido = None
if metodo_foto == "Subir archivo":
    archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])
else:
    archivo_subido = st.camera_input("Haz una foto al plato")

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado", use_container_width=True)
    
    if st.button("🔥 Analizar Plato con IA", type="primary"):
        if not api_key:
            st.error("⚠️ Falta configurar la `GEMINI_API_KEY` en los secretos de Streamlit Cloud.")
        else:
            with st.spinner("La IA está examinando los ingredientes y calculando..."):
                exito = False
                intentos = 3
                respuesta_texto = ""
                
                # Bucle de reintentos por si los servidores de Google se saturan (Error 503)
                for intento in range(intentos):
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        prompt = (
                            f"Analiza esta imagen de comida. El usuario indica que la porción pesa aproximadamente {gramos_porcion} gramos. "
                            f"Identifica el plato y calcula de forma realista para esos gramos: "
                            f"1. Calorías totales (kcal). "
                            f"2. Gramos de proteínas. "
                            f"3. Gramos de grasas. "
                            f"4. Gramos de carbohidratos. "
                            f"Responde de forma clara y directa indicando el nombre del plato detectado y los valores nutricionales estimados."
                        )
                        
                        # Usamos gemini-2.5-flash que es sumamente estable
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[imagen, prompt]
                        )
                        
                        respuesta_texto = response.text
                        exito = True
                        break # Si sale bien, salimos del bucle
                    except Exception as e:
                        if intento < intentos - 1:
                            time.sleep(2) # Espera 2 segundos antes de reintentar
                        else:
                            error_actual = str(e)
                
                if exito:
                    st.success("¡Análisis de IA completado!")
                    st.markdown("### 📊 Resultado del Plato:")
                    st.write(respuesta_texto)
                    
                    resultado_resumen = f"{gramos_porcion}g - Analizado por IA"
                    if resultado_resumen not in st.session_state.historial:
                        st.session_state.historial.append(resultado_resumen)
                else:
                    st.error(f"Los servidores están ocupados en este momento. Por favor, espera unos segundos y vuelve a pulsar el botón. (Error: {error_actual})")

# Mostrar historial
if st.session_state.historial:
    for item in st.session_state.historial:
        st.sidebar.text(f"• {item}")
else:
    st.sidebar.text("Aún no hay registros")
