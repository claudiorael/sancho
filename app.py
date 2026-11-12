import streamlit as st
import google.generativeai as genai
import io
import time
import os
import datetime
from docx import Document
from cryptography.fernet import Fernet
import base64
import hashlib

# 1. CONFIGURACIÓN DE PÁGINA Y SEGURIDAD
st.set_page_config(page_title="Sancho - Analizador de Personas", layout="wide", page_icon="🧠")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema Sancho")
        st.write("Bienvenido. Introduce tu credencial para acceder.")
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
    
    for linea in analisis_texto.split('\n'):
        if linea.startswith('##'):
            doc.add_heading(linea.replace('##', '').strip(), level=2)
        elif linea.startswith('#'):
            doc.add_heading(linea.replace('#', '').strip(), level=1)
        elif linea.startswith('**') and linea.endswith('**'):
            p = doc.add_paragraph()
            p.add_run(linea.replace('**', '')).bold = True
        elif linea.strip() != "":
            doc.add_paragraph(linea)
            
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

# 3. INTERFAZ PRINCIPAL
st.title("🧠 Sistema Sancho v2.0 (Cloud Secure)")
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
        tipo_analisis = st.radio("Enfoque de Análisis (Estricto):", ["Clínico (Terapia)", "Comercial (Venta)"])
        nombre_sujeto = st.text_input("Nombre del Paciente / Cliente:")
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
                        
                        # Leer instrucciones de entrenamiento
                        instrucciones_sistema = "Eres un asistente experto."
                        if os.path.exists("memoria_sancho.txt"):
                            with open("memoria_sancho.txt", "r", encoding="utf-8") as file:
                                instrucciones_sistema = file.read()
                        
                        # Temperatura 0.0 para conclusiones deterministas y lógicas
                        model = genai.GenerativeModel(
                            nombre_modelo, 
                            system_instruction=instrucciones_sistema,
                            generation_config={"temperature": 0.0} 
                        )
                        
                        if tipo_analisis == "Clínico (Terapia)":
                            prompt = """
                            Analiza esta sesión bajo un enfoque de PSICOLOGÍA CLÍNICA, integrando una mirada psicoanalítica y constructivista intersubjetiva. Usa un lenguaje analítico accesible, transversal y profundo, aplicando términos psicoanalíticos clásicos de forma clara.
                            1. **Síntesis del Relato (Contenido Manifiesto)**: Resumen del motivo de consulta y lo relatado conscientemente por el paciente.
                            2. **Análisis Psicoanalítico e Intersubjetivo (Contenido Latente)**: Identifica mecanismos de defensa, posición subjetiva frente al conflicto, angustia subyacente y aquello que se está actuando o repitiendo. 
                            3. **Dinámica Transferencial**: ¿Cómo se posiciona el paciente en el vínculo terapéutico? ¿Existen demandas encubiertas hacia el analista?
                            4. **Apreciación y Plan de Tratamiento**: Recomendaciones clínicas estructuradas para el manejo de la sesión y el encuadre futuro.
                            """
                        else:
                            prompt = """
                            Analiza esta llamada estrictamente bajo un enfoque de VENTAS Y CALIDAD.
                            1. **Resumen Comercial**: Interés del cliente y producto ofrecido.
                            2. **Score de Calidad (0-100)**: Evaluación del cumplimiento del script.
                            3. **Manejo de Objeciones**: ¿Cómo resolvió las negativas?
                            4. **Oportunidad de Mejora**: Feedback directo y estructurado.
                            """
                        
                        status.write("Redactando informe analítico...")
                        response = model.generate_content([prompt, audio_file])
                        
                        status.write("Estructurando Word y Encriptando...")
                        fecha_str = datetime.date.today().strftime("%Y-%m-%d")
                        word_bytes = crear_word(response.text, nombre_sujeto, tipo_analisis, fecha_str)
                        word_encriptado = encriptar_archivo(word_bytes, clave_encriptacion)
                            
                        status.update(label="Análisis Finalizado", state="complete")

                    st.subheader(f"📊 Reporte: {nombre_sujeto}")
                    st.markdown(response.text)
                    
                    st.success("✅ Informe generado. Descarga tu archivo encriptado para guardarlo de forma segura en tu computador.")
                    st.download_button(
                        label="🔒 Descargar Informe Encriptado (.enc)",
                        data=word_encriptado,
                        file_name=f"{fecha_str}_{nombre_sujeto}_Seguro.enc",
                        mime="application/octet-stream"
                    )

                    # Limpieza final
                    genai.delete_file(audio_file.name)
                    if os.path.exists(temp_file_name): os.remove(temp_file_name)

                except Exception as e:
                    st.error(f"Error en el proceso: {e}")
                    if os.path.exists(temp_file_name): os.remove(temp_file_name)
        elif archivo:
            st.warning("⚠️ Ingresa el Nombre y crea una Clave de Encriptación antes de iniciar.")

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
    st.info("Para que este entrenamiento sea **permanente** en la nube, crea un archivo llamado `memoria_sancho.txt` en tu repositorio de GitHub y escribe las instrucciones ahí.")
    
    estilo_actual = "Eres Sancho, un psicólogo clínico experto. Tu análisis clínico integra la profundidad del psicoanálisis con la co-construcción del constructivismo intersubjetivo. Utilizas un lenguaje analítico transversal y accesible, incorporando términos psicoanalíticos clásicos (como transferencia, mecanismos de defensa, represión, goce o contenido latente) de manera clara, explicándolos a través de los sucesos del relato del paciente. Prestas especial atención al discurso inconsciente y la posición subjetiva del paciente, evaluando siempre cómo el conflicto se despliega en el vínculo."
    
    if os.path.exists("memoria_sancho.txt"):
        with open("memoria_sancho.txt", "r", encoding="utf-8") as f:
            estilo_actual = f.read()
            
    nuevo_estilo = st.text_area("Define la personalidad y reglas:", value=estilo_actual, height=250)
    
    if st.button("Probar Aprendizaje (Temporal)"):
        with open("memoria_sancho.txt", "w", encoding="utf-8") as f:
            f.write(nuevo_estilo)
        st.success("Sancho usará este enfoque temporalmente.")
