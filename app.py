from datetime import datetime
import os
import sqlite3
import time
from google import genai
from PIL import Image, ImageOps
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA Y PWA ---
st.set_page_config(
    page_title="Calorías AI - Pro 2.0 📸", page_icon="icon.png", layout="wide"
)

st.markdown(
    """
    <link rel="manifest" href="https://raw.githubusercontent.com/columbus1100/app-calorias/main/manifest.json">
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

    active_key = keys[0]
    os.environ["GEMINI_API_KEY"] = active_key
    return genai.Client(api_key=active_key)


# --- PROCESADOR ROBUSTO DE IMÁGENES DE MÓVIL ---
def preparar_imagen_movil(archivo):
    try:
        img = Image.open(archivo)
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1280, 1280))
        return img
    except Exception as e:
        st.error(
            "❌ Error al procesar la foto del móvil. Asegúrate de que no sea formato"
            f" HEIC o cámbiala a JPG/PNG. Detalles: {e}"
        )
        return None


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


# --- VARIABLES DE SESIÓN GLOBALES ---
if "ultima_vez" not in st.session_state:
    st.session_state.ultima_vez = 0
if "usuario_identificado" not in st.session_state:
    st.session_state.usuario_identificado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""
if "es_pro" not in st.session_state:
    st.session_state.es_pro = False  # Por defecto el usuario es Gratis

TIEMPO_ESPERA = 2

# =========================================================================
# PANTALLA DE INICIO (LOGIN)
# =========================================================================
if not st.session_state.usuario_identificado:
    st.title("🥗 Bienvenido a Calorías AI Pro")
    st.markdown("### Por favor, identifícate para continuar")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            nombre_input = st.text_input(
                "👤 ¿Cuál es tu nombre o perfil?", placeholder="Ej: Lorena"
            )
            submitted = st.form_submit_button(
                "Entrar a la aplicación", use_container_width=True
            )

            if submitted:
                if nombre_input.strip() == "":
                    st.error("⚠️ Debes introducir un nombre para poder entrar.")
                else:
                    st.session_state.usuario_actual = nombre_input.strip()
                    st.session_state.usuario_identificado = True
                    st.rerun()

else:
    # =========================================================================
    # APLICACIÓN PRINCIPAL (Solo se ve si el usuario está identificado)
    # =========================================================================
    usuario_actual = st.session_state.usuario_actual

    # --- BARRA LATERAL PROFESIONAL ---
    st.sidebar.title("🥗 Calorías AI Pro")
    st.sidebar.markdown(f"👤 **Perfil:** {usuario_actual}")

    if st.session_state.es_pro:
        st.sidebar.success("⭐ USUARIO PRO ACTIVO")
    else:
        st.sidebar.info("🆓 Cuenta Gratuita")

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_identificado = False
        st.session_state.usuario_actual = ""
        st.rerun()

    st.sidebar.markdown("---")

    objetivo = st.sidebar.selectbox(
        "🎯 Objetivo Nutricional:",
        [
            "Mantener peso",
            "Definición / Perder grasa",
            "Volumen / Ganar músculo",
        ],
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
        " Inteligencia Artificial."
    )

    # --- SISTEMA DE PESTAÑAS PROFESIONALES (4 PESTAÑAS) ---
    pestana_analisis, pestana_diario, pestana_plan, pestana_config = st.tabs([
        "📸 Analizar Plato",
        "📖 Diario Nutricional",
        "⭐ Plan Semanal (PRO)",
        "⚙️ Ajustes y Perfil",
    ])

    # =========================================================================
    # PESTAÑA 1: ANALIZAR PLATO
    # =========================================================================
    with pestana_analisis:
        st.markdown("### Introduce tu comida mediante texto o fotografía")

        metodo_foto = st.radio(
            "Método de entrada:",
            (
                "Escribir descripción de texto",
                "Subir archivo",
                "Hacer foto con la cámara",
            ),
            horizontal=True,
        )

        if "form_key_counter" not in st.session_state:
            st.session_state.form_key_counter = 0
        if "analisis_realizado" not in st.session_state:
            st.session_state.analisis_realizado = False
        if "alimento_detectado" not in st.session_state:
            st.session_state.alimento_detectado = ""
        if "peso_estimado" not in st.session_state:
            st.session_state.peso_estimado = 200
        if "guardado_exitoso" not in st.session_state:
            st.session_state.guardado_exitoso = False
        if "resultado_texto" not in st.session_state:
            st.session_state.resultado_texto = ""
        if "ultima_foto_nombre" not in st.session_state:
            st.session_state.ultima_foto_nombre = None

        archivo_subido = None
        texto_usuario_input = ""
        current_key = f"input_media_{st.session_state.form_key_counter}"

        if metodo_foto == "Escribir descripción de texto":
            texto_usuario_input = st.text_area(
                "¿Qué has comido? (Describe plato y cantidad aproximada):",
                placeholder=(
                    "Ej: Un bol de arroz con pechuga de pollo a la plancha, unos"
                    " 250g en total."
                ),
                key=f"text_desc_{st.session_state.form_key_counter}",
            )
        elif metodo_foto == "Subir archivo":
            archivo_subido = st.file_uploader(
                "Selecciona una imagen...",
                type=["jpg", "jpeg", "png", "webp"],
                key=current_key,
            )
        else:
            archivo_subido = st.camera_input("Toma una foto", key=current_key)

        identificador_actual = (
            texto_usuario_input
            if metodo_foto == "Escribir descripción de texto"
            else getattr(archivo_subido, "name", "camara_foto")
        )
        if archivo_subido is not None or texto_usuario_input.strip() != "":
            if identificador_actual != st.session_state.ultima_foto_nombre:
                st.session_state.ultima_foto_nombre = identificador_actual
                st.session_state.analisis_realizado = False
                st.session_state.guardado_exitoso = False
                st.session_state.alimento_detectado = ""
                st.session_state.resultado_texto = ""
                st.rerun()

        col_img, col_datos = st.columns([1, 1], gap="large")

        with col_img:
            if (
                metodo_foto != "Escribir descripción de texto"
                and archivo_subido is not None
            ):
                imagen = preparar_imagen_movil(archivo_subido)
                if imagen:
                    st.image(
                        imagen,
                        caption="Imagen del plato analizado",
                        use_container_width=True,
                    )
            else:
                st.info(
                    "📝 Modo de entrada por texto activado. Rellena la"
                    " descripción y pulsa el botón."
                )

        with col_datos:
            hay_contenido = (
                metodo_foto == "Escribir descripción de texto"
                and texto_usuario_input.strip() != ""
            ) or (
                metodo_foto != "Escribir descripción de texto"
                and archivo_subido is not None
            )

            if hay_contenido and not st.session_state.analisis_realizado:
                st.info("💡 La IA está lista para procesar tu información.")
                if st.button(
                    "🔥 Identificar Plato y Estimar Peso",
                    type="primary",
                    use_container_width=True,
                ):
                    tiempo_actual = time.time()
                    if (
                        tiempo_actual - st.session_state.ultima_vez
                    ) < TIEMPO_ESPERA:
                        st.warning(
                            "⏳ ¡Espera un segundo antes de otra consulta!"
                        )
                    else:
                        st.session_state.ultima_vez = time.time()
                        with st.spinner("Analizando componentes..."):

                            prompt_reconocimiento = (
                                "Analiza este alimento o plato descrito. Responde"
                                " estrictamente con una estructura de dos"
                                " líneas:\nLínea 1: El nombre claro y directo"
                                " del plato.\nLínea 2: Una estimación numérica"
                                " del peso total en gramos (solo el número"
                                " entero, ej: 350)."
                            )

                            try:
                                client = obtener_cliente_ia()
                                if (
                                    metodo_foto
                                    == "Escribir descripción de texto"
                                ):
                                    contents_ia = [
                                        prompt_reconocimiento,
                                        f"Descripción del usuario:"
                                        f" {texto_usuario_input}",
                                    ]
                                else:
                                    imagen_prep = preparar_imagen_movil(
                                        archivo_subido
                                    )
                                    contents_ia = [
                                        prompt_reconocimiento,
                                        imagen_prep,
                                    ]

                                respuesta = client.models.generate_content(
                                    model="gemini-3.6-flash",
                                    contents=contents_ia,
                                )
                                resultado_ia = respuesta.text.strip()

                                lineas = resultado_ia.split("\n")
                                st.session_state.alimento_detectado = (
                                    lineas[0].replace("Línea 1:", "").strip()
                                )
                                try:
                                    import re

                                    match = re.search(
                                        r"\d+",
                                        lineas[1]
                                        if len(lineas) > 1
                                        else resultado_ia,
                                    )
                                    if match:
                                        st.session_state.peso_estimado = int(
                                            match.group()
                                        )
                                except Exception:
                                    st.session_state.peso_estimado = 200

                                st.session_state.analisis_realizado = True
                                st.session_state.current_texto_input = (
                                    texto_usuario_input
                                )
                                st.rerun()
                            except Exception as api_err:
                                st.error(
                                    "❌ Error de la IA:"
                                    f" {str(api_err)[:250]}..."
                                )

            if st.session_state.analisis_realizado:
                st.success(
                    f"🤖 **Identificado:** {st.session_state.alimento_detectado}"
                )

                es_correccion = st.radio(
                    "¿Deseas modificar el nombre?",
                    (
                        "Mantener nombre detectado",
                        "Corregir nombre manualmente",
                    ),
                    key=f"radio_corr_{st.session_state.form_key_counter}",
                )

                alimento_final = st.session_state.alimento_detectado
                if es_correccion == "Corregir nombre manualmente":
                    alimento_final = st.text_input(
                        "Escribe el nombre correcto:",
                        value=st.session_state.alimento_detectado,
                        key=f"text_corr_{st.session_state.form_key_counter}",
                    )

                gramos_porcion = st.slider(
                    "⚖️ Ajustar gramaje (g):",
                    50,
                    800,
                    int(st.session_state.peso_estimado),
                    step=10,
                    key=f"slider_gramos_{st.session_state.form_key_counter}",
                )

                if not st.session_state.guardado_exitoso:
                    if st.button(
                        "📊 Calcular y Guardar en el Diario",
                        type="primary",
                        use_container_width=True,
                    ):
                        with st.spinner("Calculando nutrientes detallados..."):
                            prompt_calculo = (
                                f"Analiza el alimento '{alimento_final}' con un"
                                f" peso de {gramos_porcion} gramos. Devuelve la"
                                " respuesta en formato estricto separado con"
                                " este orden exacto (solo los números para los"
                                " valores):\nCALORIAS: [número"
                                " kcal]\nPROTEINAS: [número gramos]\nGRASAS:"
                                " [número gramos]\nCARBS: [número gramos]\nY"
                                " añade después un breve comentario nutricional"
                                " útil."
                            )

                            try:
                                client = obtener_cliente_ia()
                                if (
                                    metodo_foto
                                    == "Escribir descripción de texto"
                                ):
                                    contents_calc = [
                                        prompt_calculo,
                                        f"Descripción previa:"
                                        f" {st.session_state.get('current_texto_input', '')}",
                                    ]
                                else:
                                    contents_calc = [
                                        prompt_calculo,
                                        preparar_imagen_movil(archivo_subido),
                                    ]

                                res_final = client.models.generate_content(
                                    model="gemini-3.6-flash",
                                    contents=contents_calc,
                                )
                                st.session_state.resultado_texto = (
                                    res_final.text
                                )

                                import re

                                try:
                                    cal_match = re.search(
                                        r"CALORIAS[:\s]*(\d+)",
                                        st.session_state.resultado_texto,
                                        re.IGNORECASE,
                                    )
                                    prot_match = re.search(
                                        r"PROTEINAS[:\s]*([\d\.]+)",
                                        st.session_state.resultado_texto,
                                        re.IGNORECASE,
                                    )
                                    gras_match = re.search(
                                        r"GRASAS[:\s]*([\d\.]+)",
                                        st.session_state.resultado_texto,
                                        re.IGNORECASE,
                                    )
                                    carb_match = re.search(
                                        r"CARBS[:\s]*([\d\.]+)",
                                        st.session_state.resultado_texto,
                                        re.IGNORECASE,
                                    )

                                    val_cal = (
                                        int(cal_match.group(1))
                                        if cal_match
                                        else 300
                                    )
                                    val_prot = (
                                        float(prot_match.group(1))
                                        if prot_match
                                        else 15.0
                                    )
                                    val_gras = (
                                        float(gras_match.group(1))
                                        if gras_match
                                        else 10.0
                                    )
                                    val_carb = (
                                        float(carb_match.group(1))
                                        if carb_match
                                        else 30.0
                                    )

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
                                    st.session_state.guardado_exitoso = True
                                    st.rerun()

                                except Exception as parse_err:
                                    st.warning(
                                        f"Aviso al procesar valores: {parse_err}"
                                    )

                            except Exception as err_c:
                                st.error(
                                    "❌ Error al calcular macros:"
                                    f" {str(err_c)[:250]}..."
                                )

                if st.session_state.guardado_exitoso:
                    st.markdown("---")
                    st.markdown(
                        f"### 📋 Resultados nutricionales para {gramos_porcion}g"
                    )
                    st.write(st.session_state.resultado_texto)
                    st.success("✨ ¡Guardado con éxito en tu diario nutricional!")

                    if st.button(
                        "🔄 Analizar otro plato (Nuevo)",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.analisis_realizado = False
                        st.session_state.guardado_exitoso = False
                        st.session_state.alimento_detectado = ""
                        st.session_state.resultado_texto = ""
                        st.session_state.ultima_foto_nombre = None
                        st.session_state.form_key_counter += 1
                        st.rerun()

    # =========================================================================
    # PESTAÑA 2: DIARIO NUTRICIONAL
    # =========================================================================
    with pestana_diario:
        st.markdown(
            f"### 📖 Registro de comidas de hoy para **{usuario_actual}**"
        )

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
                        f"**{idx+1}. {item[0]}**  \n⚖️ **Peso:** {item[1]}g  |"
                        f"  🔥 **Calorías:** {item[2]} kcal  |  🥩 **Prot:**"
                        f" {item[3]}g  |  🥑 **Grasas:** {item[4]}g  |  🍞"
                        f" **Carbs:** {item[5]}g"
                    )
                    st.divider()
        else:
            st.info(
                "📭 Aún no hay alimentos registrados para hoy. ¡Sube una foto o"
                " escribe tu comida!"
            )

    # =========================================================================
    # PESTAÑA 3: PLAN SEMANAL DE PAGO (SOLO USUARIOS PRO)
    # =========================================================================
    with pestana_plan:
        st.markdown("### 📅 Plan Semanal de Dieta Personalizada")

        # Comprobación de si el usuario ha pagado (Es PRO)
        if not st.session_state.es_pro:
            # PANTALLA BLOQUEADA PARA USUARIOS QUE NO HAN PAGADO
            st.warning("🔒 Esta función es exclusiva para miembros PRO")
            st.write(
                "Consigue un plan nutricional a tu medida, cálculos de déficit y"
                " menú completo de Lunes a Domingo por solo **4,99€/mes**."
            )

            col_pago1, col_pago2 = st.columns([2, 1])
            with col_pago1:
                st.link_button(
                    "💳 Suscribirme por 4,99€/mes (Suscripción)",
                    "https://buy.stripe.com/tu_enlace_de_pago",
                    type="primary",
                    use_container_width=True,
                )

            st.markdown("---")
            st.info("💡 Modo Pruebas para el Creador (Para probar la app):")
            if st.checkbox("🧪 Activar Modo PRO de prueba"):
                st.session_state.es_pro = True
                st.rerun()

        else:
            # PANTALLA DESBLOQUEADA PARA USUARIOS PRO
            st.success(
                "🎉 ¡Eres usuario PRO! Tienes acceso ilimitado al Plan"
                " Semanal."
            )
            st.write(
                "Introduce tus datos antropométricos para que la IA calcule tu"
                " déficit calórico y te elabore un menú semanal completo."
            )

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                edad_usr = st.number_input(
                    "Edad (años):", min_value=15, max_value=100, value=30
                )
                peso_usr = st.number_input(
                    "Peso actual (kg):",
                    min_value=35.0,
                    max_value=250.0,
                    value=75.0,
                    step=0.5,
                )
            with col_p2:
                altura_usr = st.number_input(
                    "Altura (cm):", min_value=120, max_value=220, value=170
                )
                genero_usr = st.selectbox("Sexo biológico:", ["Hombre", "Mujer"])
            with col_p3:
                actividad_usr = st.selectbox(
                    "Nivel de actividad física:",
                    [
                        "Sedentario (poco o nada ejercicio)",
                        "Ligero (ejercicio ligero 1-3 días/semana)",
                        "Moderado (ejercicio moderado 3-5 días/semana)",
                        "Activo (ejercicio fuerte 6-7 días/semana)",
                    ],
                )
                preferencias_usr = st.text_input(
                    "Preferencias o alergias (opcional):",
                    placeholder="Ej: Sin gluten, vegetariano, sin frutos secos...",
                )

            if "plan_semanal_generado" not in st.session_state:
                st.session_state.plan_semanal_generado = ""

            if st.button(
                "🚀 Generar Plan Semanal de Dieta Personalizada",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(
                    "Calculando TDEE, déficit calórico óptimo y diseñando menú"
                    " semanal..."
                ):
                    prompt_plan = (
                        "Actúa como un nutricionista experto y deportivo."
                        " Diseña un PLAN SEMANAL DE DIETA PARA BAJAR DE PESO"
                        " estricto y saludable para un usuario con las"
                        " siguientes características:\n- Edad:"
                        f" {edad_usr} años\n- Sexo: {genero_usr}\n- Altura:"
                        f" {altura_usr} cm\n- Peso actual: {peso_usr} kg\n-"
                        f" Nivel de actividad: {actividad_usr}\n- Restricciones/Preferencias:"
                        f" {preferencias_usr if preferencias_usr else 'Ninguna'}\n\nEl"
                        " plan debe incluir:\n1. Calorías diarias"
                        " recomendadas y distribución de macros (Proteínas,"
                        " Grasas, Carbohidratos) para asegurar pérdida de"
                        " grasa.\n2. Un menú detallado de Lunes a Domingo"
                        " (Desayuno, Almuerzo, Comida, Merienda y Cena) con"
                        " porciones orientativas en gramos.\n3. Consejos"
                        " prácticos de hidratación y cumplimiento.\nEstructura"
                        " el texto de manera limpia, profesional y lista para"
                        " imprimir."
                    )

                    try:
                        client = obtener_cliente_ia()
                        res_plan = client.models.generate_content(
                            model="gemini-3.6-flash", contents=[prompt_plan]
                        )
                        st.session_state.plan_semanal_generado = (
                            res_plan.text
                        )
                        st.success("¡Plan semanal generado con éxito!")
                    except Exception as e:
                        st.error(f"Error al generar el plan con la IA: {e}")

            if st.session_state.plan_semanal_generado:
                st.markdown("---")
                st.markdown("### 📄 Tu Plan Nutricional Personalizado")
                st.markdown(st.session_state.plan_semanal_generado)

                st.markdown("---")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 Descargar Plan Semanal (TXT)",
                        data=st.session_state.plan_semanal_generado,
                        file_name=(
                            "plan_semanal_perder_peso_"
                            f"{usuario_actual.lower()}.txt"
                        ),
                        mime="text/plain",
                        use_container_width=True,
                    )
                with col_dl2:
                    if st.button(
                        "🖨️ Imprimir Plan (Abrir vista de impresión)",
                        use_container_width=True,
                    ):
                        st.markdown(
                            """
                            <script>
                            window.print();
                            </script>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.info(
                            "💡 Si la ventana de impresión no se abre"
                            " automáticamente, usa las opciones de impresión de"
                            " tu navegador (Ctrl+P o Cmd+P)."
                        )

    # =========================================================================
    # PESTAÑA 4: AJUSTES Y PERFIL
    # =========================================================================
    with pestana_config:
        st.markdown("### ⚙️ Configuración del Perfil")
        st.write(
            "Si necesitas cambiar tu nombre o corregirlo, puedes cerrar sesión"
            " desde el menú lateral izquierdo."
        )

        st.markdown("---")
        st.markdown("### 💳 Estado de la suscripción")
        if st.session_state.es_pro:
            st.success("Suscripción activa: **Plan PRO Mensual**")
            if st.button("Cancelar suscripción de prueba"):
                st.session_state.es_pro = False
                st.rerun()
        else:
            st.info("Suscripción activa: **Plan Gratuito**")
            if st.button("Activar prueba PRO"):
                st.session_state.es_pro = True
                st.rerun()
