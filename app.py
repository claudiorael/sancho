import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import time
import os

# Interfaz limpia
st.set_page_config(page_title="Analizador Sancho Pro", layout="wide")

# Conexión
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Configura GEMINI_API_KEY en Secrets.")

def buscar_modelo_activo():
    """Detecta qué modelo tienes habilitado en tu región/cuenta"""
    modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Priorizamos 1.5 Flash por velocidad, luego Pro
    for m in modelos_disponibles:
        if "1.5-flash" in m: return m
    for m in modelos_disponibles:
        if "1.5-pro" in m: return m
    return modelos_disponibles[0] if modelos_disponibles else None

st.title("🎙️ Robot Auditor de Llamadas")

with st.sidebar:
    st.header("Configuración")
    archivo = st.file_uploader("Subir MP3/WAV", type=["mp3", "wav"])
    if st.button("Limpiar archivos temporales"):
        for f in genai.list_files(): genai.delete_file(f.name)
        st.success("Nube limpia")

if archivo:
    st.audio(archivo)
    if st.button("🚀 INICIAR AUDITORÍA"):
        try:
            with st.status("Detectando motor y procesando...", expanded=True) as status:
                # 1. Autodetección de modelo (Evita el 404)
                nombre_modelo = buscar_modelo_activo()
                if not nombre_modelo:
                    st.error("No se encontraron modelos habilitados en esta API Key.")
                    st.stop()
                
                status.write(f"Motor detectado: {nombre_modelo}")
                
                # 2. Procesamiento de Audio
                with open("temp.mp3", "wb") as f:
                    f.write(archivo.getbuffer())
                
                audio_file = genai.upload_file(path="temp.mp3")
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)
                
                # 3. Análisis
                model = genai.GenerativeModel(nombre_modelo)
                prompt = """
                Analiza esta llamada de forma profesional:
                - Transcripción resumida.
                - Score de cumplimiento (1-100).
                - Tono emocional.
                - 3 consejos para el ejecutivo.
                """
                
                response = model.generate_content([prompt, audio_file])
                status.update(label="¡Análisis Exitoso!", state="complete")

            st.subheader("📊 Informe Detallado")
            st.info(response.text)

            # Exportación Excel
            df = pd.DataFrame({"Fecha": [pd.Timestamp.now()], "Analisis": [response.text]})
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
                writer.close()
            st.download_button("📥 Descargar Excel", output.getvalue(), "Reporte_Sancho.xlsx")
            
            genai.delete_file(audio_file.name)

        except Exception as e:
            st.error(f"Error técnico: {e}")
