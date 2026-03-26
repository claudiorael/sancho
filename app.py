import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import time
import os

# 1. CONFIGURACIÓN DE PÁGINA Y SEGURIDAD
st.set_page_config(page_title="Sancho - Analizador de Personas", layout="wide", page_icon="🧠")

def check_password():
    """Retorna True si el usuario introdujo la contraseña correcta."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema Sancho")
        st.write("Bienvenido, Claudio. Introduce tu credencial para acceder al analizador.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            pwd = st.text_input("Contraseña:", type="password")
            if st.button("Ingresar"):
                if pwd == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🚫 Contraseña incorrecta")
        return False
    return True

# Si no pasa la contraseña, el código se detiene aquí
if not check_password():
    st.stop()

# 2. INICIALIZACIÓN DE IA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la API Key de Gemini en los Secrets.")
    st.stop()

def buscar_modelo_activo():
    """Detecta dinámicamente el modelo para evitar el error 404."""
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in modelos:
            if "1.5-flash" in m: return m
        for m in modelos:
            if "1.5-pro" in m: return m
        return modelos[0] if modelos else None
    except:
        return None

# 3. INTERFAZ PRINCIPAL
st.title("🧠 Sancho: Psicología + Datos")
st.markdown("---")

with st.sidebar:
    st.header("📂 Carga de Evidencia")
    archivo = st.file_uploader("Subir grabación de llamada (MP3/WAV)", type=["mp3", "wav"])
    
    st.divider()
    if st.button("🗑️ Limpiar Nube"):
        for f in genai.list_files():
            genai.delete_file(f.name)
        st.success("Archivos eliminados de la nube.")

if archivo:
    st.audio(archivo)
    
    if st.button("🚀 INICIAR AUDITORÍA CLÍNICO-COMERCIAL"):
        try:
            with st.status("Procesando información...", expanded=True) as status:
                # Detectar Motor
                nombre_modelo = buscar_modelo_activo()
                if not nombre_modelo:
                    st.error("No se detectaron modelos activos.")
                    st.stop()
                
                status.write(f"Motor activo: {nombre_modelo}")
                
                # Guardar archivo local para subirlo
                with open("temp_audit.mp3", "wb") as f:
                    f.write(archivo.getbuffer())
                
                status.write("Subiendo audio a Google AI Studio...")
                audio_file = genai.upload_file(path="temp_audit.mp3")
                
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)
                
                # Análisis con enfoque mixto (Psicología + Eficiencia)
                status.write("Generando análisis semántico y métricas...")
                model = genai.GenerativeModel(nombre_modelo)
                
                prompt = """
                Analiza esta llamada con una mirada de Psicólogo de RRHH y Experto en Ventas:
                1. **Transcripción**: Breve resumen de lo hablado.
                2. **Score de Desempeño (0-100)**: Evalúa objetividad y datos.
                3. **Análisis Psicológico**: ¿Cómo fue la transferencia? ¿Hubo empatía real o mecánica? 
                4. **Criterio de Calidad**: ¿Cumplió con los hitos obligatorios del script?
                5. **Plan de Acción**: 3 recomendaciones concretas para coaching.
                """
                
                response = model.generate_content([prompt, audio_file])
                
                status.update(label="Análisis Finalizado", state="complete")

            # Muestra de Resultados
            st.subheader("📊 Reporte de Auditoría")
            st.markdown(response.text)

            # Generar Excel para descarga
            df = pd.DataFrame({
                "Fecha": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                "Colaborador": ["Evaluación Automática"],
                "Análisis": [response.text]
            })
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
                writer.close()
            
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=output.getvalue(),
                file_name=f"Auditoria_{archivo.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Limpieza final
            genai.delete_file(audio_file.name)
            if os.path.exists("temp_audit.mp3"):
                os.remove("temp_audit.mp3")

        except Exception as e:
            st.error(f"Error en el proceso: {e}")
else:
    st.info("Sube una llamada para empezar el cruce de datos y psicología.")
