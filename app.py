import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import os
import time

# Configuración de Interfaz
st.set_page_config(page_title="Analizador RRHH - Sancho", layout="wide")

# Conexión Segura
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Configura la GEMINI_API_KEY en Streamlit Cloud.")

st.title("🎙️ Robot Auditor de Llamadas")

with st.sidebar:
    archivo = st.file_uploader("Subir MP3/WAV", type=["mp3", "wav"])
    if st.button("Limpiar Nube"):
        for f in genai.list_files(): genai.delete_file(f.name)
        st.success("Limpieza OK")

if archivo:
    st.audio(archivo)
    if st.button("🚀 INICIAR ANÁLISIS"):
        try:
            with st.status("Procesando con Gemini 1.5...", expanded=True) as status:
                # Guardar y Subir
                with open("temp.mp3", "wb") as f:
                    f.write(archivo.getbuffer())
                
                audio_file = genai.upload_file(path="temp.mp3")
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)
                
                # Análisis (Usando Flash para asegurar estabilidad, puedes cambiar a pro-latest)
                model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
                prompt = "Analiza esta llamada de ventas: Transcripción, Score (1-100) y 3 consejos de coaching."
                
                response = model.generate_content([prompt, audio_file])
                status.update(label="Análisis Completo", state="complete")

            st.subheader("📊 Informe de Auditoría")
            st.info(response.text)

            # Excel
            df = pd.DataFrame({"Fecha": [pd.Timestamp.now()], "Analisis": [response.text]})
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
                writer.close()
            st.download_button("📥 Descargar Excel", output.getvalue(), "Reporte.xlsx")
            
            genai.delete_file(audio_file.name)

        except Exception as e:
            st.error(f"Error: {e}")
