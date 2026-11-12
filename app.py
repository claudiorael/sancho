import streamlit as st
import google.generativeai as genai
import io
import time
import os
import datetime
import re
from docx import Document
from cryptography.fernet import Fernet
import base64
import hashlib

# 1. CONFIGURACIÓN DE PÁGINA Y ESTADO
st.set_page_config(page_title="Sancho - Analizador de Personas", layout="wide", page_icon="🧠")

# Inicializar variables de sesión para que el informe no desaparezca
if "informe_actual" not in st.session_state:
    st.session_state.informe_actual = None
if "word_encriptado" not in st.session_state:
    st.session_state.word_encriptado = None
if "nombre_informe" not in st.session_state:
    st.session_state.nombre_informe = None
if "fecha_informe" not in st.session_state:
    st.session_state.fecha_informe = None

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema Sancho")
        st.write("Bienvenido, Claudio. Introduce tu credencial para acceder.")
        col1, col2 = st.columns([1, 2])
        with col1:
            pwd = st.text_input("Contraseña de Aplicación:", type="password")
            if st.button("Ingresar"):
                if pwd == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🚫 Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# 2. INICIALIZACIÓN DE IA Y ENCRIPTACIÓN
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la API Key de Gemini en los Secrets.")
    st.stop()

def buscar_modelo_activo():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in modelos:
            if "1.5-pro" in m: return m 
        for m in modelos:
            if "1.5-flash" in m: return m
        return modelos[0] if modelos else None
    except Exception as e:
        st.error(f"Error interno al conectar con Gemini: {e}")
        return None

def obtener_llave(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encriptar_archivo(data_bytes, password):
    f = Fernet(obtener_llave(password))
    return f.encrypt(data_bytes)

def desencriptar_archivo(data_bytes, password):
    try:
        f = Fernet(obtener_llave(password))
        return f.decrypt(data_bytes)
    except Exception:
        return None

def crear_word(analisis_texto, nombre, tipo, fecha):
    doc = Document()
    doc.add_heading(f"Reporte de Auditoría: {tipo}", 0)
    doc.add_paragraph(f"Sujeto/Paciente: {nombre}")
    doc.add_paragraph(f"Fecha de Análisis: {fecha}")
    doc.add_paragraph(f"Generado por: Sistema Sancho IA\n")
    
    # Procesamiento inteligente de Markdown para limpiar los asteriscos
    for linea in analisis_texto.split('\n'):
        linea = linea.strip()
        if not linea:
            continue
            
        if linea.startswith('### '):
            doc.add_heading(linea.replace('### ', ''), level=3)
        elif linea.startswith('## '):
            doc.add_heading(linea.replace('## ', ''), level=2)
        elif linea.startswith('# '):
            doc.add_heading(linea.replace('# ', ''), level=1)
        else:
            # Detectar si es una viñeta
            is_bullet = False
            if linea.startswith('* ') or linea.startswith('- '):
                linea = linea[2:]
                is_bullet = True
            
            p = doc.add_paragraph(style='List Bullet' if is_bullet else 'Normal')
            
            # Expresión regular para encontrar textos entre **negritas**
            partes = re.split(r'(\*\*.*?\*\*)', linea)
            for parte in partes:
                if parte.startswith('**') and parte.endswith('**'):
                    texto_limpio = parte[2:-2].replace('*', '') # Remueve asteriscos internos
                    p.add_run(texto_limpio).bold = True
                else:
                    texto_limpio = parte.replace('*', '') # Limpia cualquier asterisco suelto
                    if texto_limpio.strip():
                        p.add_run(texto_limpio)
            
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

# 3. INTERFAZ PRINCIPAL
st.title("🧠 Sistema Sancho v2.1")
st.markdown("---")

tab_analisis, tab_desencriptador, tab_entrenamiento = st.tabs([
    "🎙️ Analizador", 
    "🔓 Desencriptar Informe", 
    "⚙️ Entrenamiento de IA"
])

# --- PESTAÑA 1: ANALIZADOR ---
with tab_analisis:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configuración")
        tipo_analisis = st.radio(
            "Enfoque de Análisis:", 
            ["Mixto (Original RRHH y Ventas)", "Clínico Estricto (Terapia)", "Comercial Estricto (Ventas)"]
        )
        nombre_sujeto = st.text_input("Nombre del Paciente / Colaborador:")
        clave_encriptacion = st.text_input("Crea una clave para encriptar este informe:", type="password")
        
        st.divider()
        archivo = st.file_uploader("Subir grabación (MP3/WAV/MP4/M4A/OGG)", type=["mp3", "wav", "mp4", "m4a", "ogg"])
        
        if st.button("🗑️ Limpiar Nube"):
            try:
                for f in genai.list_files():
                    genai.delete_file(f.name)
                st.success("Nube limpia.")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if archivo and nombre_sujeto and clave_encriptacion:
            st.audio(archivo)
            
            if st.button("🚀 INICIAR PROCESAMIENTO", use_container_width=True):
                ext = archivo.name.split('.')[-1].lower()
                temp_file_name = f"temp_audit.{ext}"

                try:
                    with st.status("Procesando información...", expanded=True) as status:
                        nombre_modelo = buscar_modelo_activo()
                        
                        with open(temp_file_name, "wb") as f:
                            f.write(archivo.getbuffer())
                        
                        if ext == "mp4": tipo_mime = "audio/mp4"
                        elif ext in ["m4a", "aac"]: tipo_mime = "audio/aac"
                        elif ext == "ogg": tipo_mime = "audio/ogg"
                        elif ext == "mp3": tipo_mime = "audio/mp3"
                        elif ext == "wav": tipo_mime = "audio/wav"
                        else: tipo_mime = None

                        status.write("Subiendo a Google AI Studio...")
                        audio_file = genai.upload_file(path=temp_file_name, mime_type=tipo_mime)
                        
                        while audio_file.state.name == "PROCESSING":
                            time.sleep(2)
                            audio_file = genai.get_file(audio_file.name)
                        
                        if audio_file.state.name == "FAILED":
                            st.error("Error en el archivo. El formato interno es incompatible o está dañado.")
                            st.stop()
                        
                        instrucciones_sistema = "Eres un asistente experto."
                        if os.path.exists("memoria_sancho.txt"):
                            with open("memoria_sancho.txt", "r", encoding="utf-8") as file:
                                instrucciones_sistema = file.read()
                        
                        model = genai.GenerativeModel(
                            nombre_modelo, 
                            system_instruction=instrucciones_sistema,
                            generation_config={"temperature": 0.0} 
                        )
                        
                        if tipo_analisis == "Mixto (Original RRHH y Ventas)":
                            prompt = """
                            Analiza esta llamada con una mirada de Psicólogo de RRHH y Experto en Ventas:
                            0. **Estados de Ánimo**: Incluye 2 emojis precisos que resuman la actitud/emoción del Evaluador/Vendedor y del Cliente/Paciente.
                            1. **Transcripción**: Breve resumen de lo hablado.
                            2. **Score de Desempeño (0-100)**: Evalúa objetividad y datos.
                            3. **Análisis Psicológico**: ¿Cómo fue la transferencia? ¿Hubo empatía real o mecánica? 
                            4. **Criterio de Calidad**: ¿Cumplió con los hitos obligatorios del script?
                            5. **Plan de Acción**: 3 recomendaciones concretas para coaching.
                            """
                        elif tipo_analisis == "Clínico Estricto (Terapia)":
                            prompt = """
                            Analiza esta sesión bajo un enfoque de PSICOLOGÍA CLÍNICA (Constructivismo Intersubjetivo y Psicoanálisis):
                            0. **Estados de Ánimo**: Incluye emojis que representen el estado emocional del Paciente y la disposición analítica del Terapeuta.
                            1. **Transcripción**: Breve síntesis del relato manifiesto y motivo de consulta.
                            2. **Score de Alianza (0-100)**: Evalúa la calidad del vínculo terapéutico.
                            3. **Análisis Psicológico**: ¿Cómo fue la dinámica transferencial? Identifica mecanismos de defensa y contenido latente con lenguaje accesible.
                            4. **Criterio Clínico**: ¿Se mantuvo el encuadre, la escucha activa y la contención?
                            5. **Plan de Acción**: 3 recomendaciones concretas para la próxima sesión.
                            """
                        else:
                            prompt = """
                            Analiza esta llamada estrictamente bajo un enfoque de VENTAS Y CALIDAD:
                            0. **Estados de Ánimo**: Incluye emojis que reflejen la disposición del Cliente y la energía/postura del Vendedor.
                            1. **Transcripción**: Breve resumen del interés del cliente y producto abordado.
                            2. **Score de Desempeño (0-100)**: Evalúa objetividad, uso de datos y cumplimiento de metas.
                            3. **Análisis Comercial**: ¿Cómo fue la capacidad de persuasión y manejo de objeciones?
                            4. **Criterio de Calidad**: ¿Cumplió con los hitos obligatorios del script?
                            5. **Plan de Acción**: 3 recomendaciones concretas para coaching y mejora de cierre.
                            """
                        
                        status.write("Redactando informe analítico...")
                        response = model.generate_content([prompt, audio_file])
                        
                        status.write("Estructurando Word y Encriptando...")
                        fecha_str = datetime.date.today().strftime("%Y-%m-%d")
                        word_bytes = crear_word(response.text, nombre_sujeto, tipo_analisis, fecha_str)
                        word_encriptado = encriptar_archivo(word_bytes, clave_encriptacion)
                        
                        # GUARDAR EN VARIABLES DE SESIÓN PARA QUE NO DESAPAREZCA
                        st.session_state.informe_actual = response.text
                        st.session_state.word_encriptado = word_encriptado
                        st.session_state.nombre_informe = nombre_sujeto
                        st.session_state.fecha_informe = fecha_str
                            
                        status.update(label="Análisis Finalizado", state="complete")

                    genai.delete_file(audio_file.name)
                    if os.path.exists(temp_file_name): os.remove(temp_file_name)

                except Exception as e:
                    st.error(f"Error en el proceso: {e}")
                    if os.path.exists(temp_file_name): os.remove(temp_file_name)
        elif archivo:
            st.warning("⚠️ Ingresa el Nombre y crea una Clave de Encriptación antes de iniciar.")
            
        # MOSTRAR EL INFORME MIENTRAS ESTÉ EN MEMORIA DE SESIÓN
        if st.session_state.informe_actual:
            st.markdown("---")
            st.subheader(f"📊 Reporte: {st.session_state.nombre_informe}")
            st.markdown(st.session_state.informe_actual)
            
            col_d1, col_d2 = st.columns([1, 1])
            with col_d1:
                st.download_button(
                    label="🔒 Descargar Informe Encriptado (.enc)",
                    data=st.session_state.word_encriptado,
                    file_name=f"{st.session_state.fecha_informe}_{st.session_state.nombre_informe}_Seguro.enc",
                    mime="application/octet-stream",
                    use_container_width=True
                )
            with col_d2:
                # Botón para borrar el informe de la pantalla voluntariamente
                if st.button("❌ Cerrar Informe", use_container_width=True):
                    st.session_state.informe_actual = None
                    st.session_state.word_encriptado = None
                    st.session_state.nombre_informe = None
                    st.session_state.fecha_informe = None
                    st.rerun()

# --- PESTAÑA 2: DESENCRIPTADOR ---
with tab_desencriptador:
    st.header("🔓 Lector de Informes Seguros")
    st.write("Sube un archivo `.enc` generado por Sancho e ingresa la contraseña con la que fue creado para convertirlo nuevamente a Word.")
    
    archivo_enc = st.file_uploader("Sube el informe encriptado (.enc)", type=["enc"])
    clave_desencriptar = st.text_input("Ingresa la clave original:", type="password", key="pwd_dec")
    
    if archivo_enc and clave_desencriptar:
        if st.button("Desencriptar Archivo"):
            data_encriptada = archivo_enc.getvalue()
            word_recuperado = desencriptar_archivo(data_encriptada, clave_desencriptar)
            
            if word_recuperado:
                st.success("✅ Clave correcta. Archivo desencriptado.")
                st.download_button(
                    label="📄 Descargar Documento Word (.docx)",
                    data=word_recuperado,
                    file_name=f"Informe_Recuperado_{archivo_enc.name.replace('.enc', '')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error("🚫 Clave incorrecta o archivo dañado.")

# --- PESTAÑA 3: ENTRENAMIENTO ---
with tab_entrenamiento:
    st.header("Entrenamiento del Rol de Sancho")
    
    estilo_actual = "Eres Sancho. Tu objetivo es analizar a las personas de forma clara, directa y estructurada. Si el contexto es clínico, integra conceptos psicoanalíticos (transferencia, mecanismos de defensa, contenido latente) y del constructivismo intersubjetivo explicando de forma sencilla cómo se observan en el comportamiento del paciente. Si el contexto es de ventas, enfócate estrictamente en la persuasión, manejo de objeciones y cumplimiento de protocolos."
    
    if os.path.exists("memoria_sancho.txt"):
        with open("memoria_sancho.txt", "r", encoding="utf-8") as f:
            estilo_actual = f.read()
            
    nuevo_estilo = st.text_area("Define la personalidad y reglas:", value=estilo_actual, height=200)
    
    if st.button("Probar Aprendizaje (Temporal)"):
        with open("memoria_sancho.txt", "w", encoding="utf-8") as f:
            f.write(nuevo_estilo)
        st.success("Sancho usará este enfoque temporalmente.")
