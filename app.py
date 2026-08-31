import streamlit as st
from PIL import Image

st.set_page_config(page_title="Calorías AI 📸", page_icon="🥗", layout="centered")

# --- BARRA LATERAL (MEJORA: Configuración y Historial) ---
st.sidebar.title("⚙️ Ajustes y Historial")
objetivo = st.sidebar.selectbox(
    "Tu objetivo nutricional:",
    ["Mantener peso", "Definición / Perder grasa", "Volumen / Ganar músculo"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Historial de la sesión")

# Inicializar historial en memoria
if "historial" not in st.session_state:
    st.session_state.historial = []

# --- CUERPO PRINCIPAL ---
st.title("🥗 Detector de Calorías por Foto")
st.write("Sube una foto de tu plato para analizarlo al instante según tu objetivo.")

archivo_subido = st.file_uploader("Elige una foto de comida...", type=["jpg", "jpeg", "png"])

if archivo_subido is not None:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Plato analizado", use_container_width=True)
    
    if st.button("🔥 Analizar Plato", type="primary"):
        with st.spinner(f"Analizando plato para tu objetivo de '{objetivo}'..."):
            
            # Datos simulados del análisis (puedes personalizarlos o conectarlos)
            alimento = "Pieza de bollería / Croissant (aprox. 80g)"
            calorias = 310
            proteinas = 5.2
            grasas = 16.5
            carbos = 35.0
            
            st.success("¡Análisis completado con éxito!")
            
            # MEJORA: Visualización en columnas con métricas de Streamlit
            st.markdown("### 📊 Desglose Nutricional Estimado:")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="🔥 Calorías Totales", value=f"{calorias} kcal")
                st.metric(label="🥩 Proteínas", value=f"{proteinas} g")
            with col2:
                st.metric(label="🥑 Grasas", value=f"{grasas} g")
                st.metric(label="🍞 Carbohidratos", value=f"{carbos} g")
            
            st.info(f"**Alimento detectado:** {alimento}")
            
            # Guardar en el historial de la sesión
            resultado_resumen = f"{alimento} - {calorias} kcal"
            if resultado_resumen not in st.session_state.historial:
                st.session_state.historial.append(resultado_resumen)

# Mostrar el historial en la barra lateral si hay elementos
if st.session_state.historial:
    for item in st.session_state.historial:
        st.sidebar.text(f"• {item}")
else:
    st.sidebar.text("Aún no hay platos analizados.")
