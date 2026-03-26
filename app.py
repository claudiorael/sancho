import streamlit as st
from openai import OpenAI
import pandas as pd
import io
import time
import os

# Configuración de Interfaz Premium
st.set_page_config(page_title="Analizador de Llamadas Pro", page_icon="🎙️", layout="wide")

# Inicializar cliente OpenAI (usando los Secrets de Streamlit)
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("⚠️ Falta la API Key en los Secrets de Streamlit.")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stButton>button { background-color: #052c54; color: white; border-radius: 8px; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🎙️ Robot Auditor de Llamadas (Cloud Edition)")
st.caption("Análisis avanzado de ventas, sentimientos y cumplimiento normativo.")

with st.sidebar:
    st.header("📂 Carga de Grabación")
    archivo_audio = st.file_uploader("Subir MP3/WAV", type=["mp3", "wav"])
    st.divider()
    st.info("Esta versión utiliza procesamiento en la nube para garantizar estabilidad y velocidad.")

if archivo_audio:
    st.audio(archivo_audio)
    
    if st.button("🚀 INICIAR AUDITORÍA COMPLETA"):
        with st.status("Procesando con Inteligencia Artificial...", expanded=True) as status:
            t_start = time.time()
            
            # 1. Transcripción con Whisper API
            status.write("Transcribiendo audio de alta precisión...")
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=archivo_audio
            )
            texto_final = transcript.text
            
            # 2. Análisis de Sentimiento y Ventas con GPT-4o
            status.write("Analizando tonos, emociones y script de venta...")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un experto en calidad de Call Center. Analiza la transcripción y devuelve: 1. Score de 1-100. 2. Emoción predominante. 3. 3 puntos clave detectados."},
                    {"role": "user", "content": texto_final}
                ]
            )
            analisis_ia = response.choices[0].message.content
            
            duracion = round(time.time() - t_start, 2)
            status.update(label="Análisis Finalizado", state="complete")

        # --- DASHBOARD ---
        st.subheader("📊 Resultados de la Auditoría")
        c1, c2, c3 = st.columns(3)
        c1.metric("Efectividad", "Calculada", help="Basado en el análisis semántico")
        c2.metric("Tiempo de Proceso", f"{duracion}s")
        c3.metric("Motor IA", "GPT-4o + Whisper")

        col_t, col_a = st.columns([1, 1])
        with col_t:
            st.markdown("### 📝 Transcripción")
            st.info(texto_final)
        
        with col_a:
            st.markdown("### 🧠 Insights de la IA")
            st.success(analisis_ia)

        # --- EXPORTACIÓN ---
        st.divider()
        df = pd.DataFrame({
            "Fecha": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
            "Archivo": [archivo_audio.name],
            "Analisis_Completo": [analisis_ia],
            "Transcripcion": [texto_final]
        })
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte_RRHH')
            writer.close()
        
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo (Excel)",
            data=output.getvalue(),
            file_name=f"Auditoria_{archivo_audio.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.write("### 👋 Hola Claudio")
    st.info("Sube una llamada para comenzar el análisis automático sin errores de instalación.")
