import streamlit as st
from PIL import Image

# Configuración de la página con tu icono personalizado (icon.png)
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

# Selector para subir foto o usar la cámara (corregido con camera_input)
metodo_foto = st.radio("¿Cómo prefieres añadir la imagen?", ("Subir archivo", "Hacer foto con la cámara"))

archivo_subido = None
if metodo_foto == "Subir archivo":
    archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])
else:
    archivo_subido = st.camera_input("Haz una foto al plato")

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado", use_container_width=True)
    
    if st.button("🔥 Analizar Plato", type="primary"):
        with st.spinner("Calculando nutrientes según el gramaje..."):
            
            # Valores base para 100 gramos de un croissant de ejemplo
            base_calorias = 387
            base_proteinas = 6.5
            base_grasas = 20.6
            base_carbos = 43.8
            
            # Recálculo dinámico basado en el slider de gramos
            factor = gramos_porcion / 100.0
            calorias = int(base_calorias * factor)
            proteinas = round(base_proteinas * factor, 1)
            grasas = round(base_grasas * factor, 1)
            carbos = round(base_carbos * factor, 1)
            
            st.success("¡Análisis completado con éxito!")
            
            # Visualización en métricas
            st.markdown(f"### 📊 Desglose Nutricional ({gramos_porcion}g):")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="🔥 Calorías Totales", value=f"{calorias} kcal")
                st.metric(label="🥩 Proteínas", value=f"{proteinas} g")
            with col2:
                st.metric(label="🥑 Grasas", value=f"{grasas} g")
                st.metric(label="🍞 Carbohidratos", value=f"{carbos} g")
            
            # Consejo inteligente según el objetivo
            if "Definición" in objetivo:
                st.warning("⚠️ **Consejo de Definición:** Este alimento es denso en calorías y grasas. Intenta moderar su consumo si estás en déficit calórico estricto.")
            elif "Volumen" in objetivo:
                st.info("💪 **Consejo de Volumen:** ¡Excelente opción para sumar calorías limpias o densas de forma rápida a tu dieta!")
            else:
                st.info("⚖️ **Consejo de Mantenimiento:** Disfrútalo con moderación dentro de tus calorías diarias totales.")

            # Guardar en el historial de la sesión
            resultado_resumen = f"{gramos_porcion}g - {calorias} kcal"
            if resultado_resumen not in st.session_state.historial:
                st.session_state.historial.append(resultado_resumen)

# Mostrar el historial en la barra lateral
if st.session_state.historial:
    for item in st.session_state.historial:
        st.sidebar.text(f"• {item}")
else:
    st.sidebar.text("Aún no hay registros")
