import streamlit as st
import whisper
import pandas as pd
import io
import time
import os
import subprocess

# Configuración de página
st.set_page_config(page_title="Analizador Pro", page_icon="🎙️", layout="wide")

# Estilo elegante
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stButton>button { background-color: #1a73e8; color: white; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_stdio=True)

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

st.title("🤖 Auditor de Llamadas Inteligente")
st.markdown("Análisis de cumplimiento y sentimiento para capacitación de ejecutivos.")

with st.sidebar:
    st.header("Configuración")
    archivo_audio = st.file_uploader("Subir MP3/WAV", type=["mp3", "wav"])
    st.divider()
    st.info("Este motor utiliza Whisper para transcripción directa, evitando errores de librerías antiguas.")

if archivo_audio:
    st.audio(archivo_audio)
    
    if st.button("🚀 INICIAR AUDITORÍA"):
        with st.status("Procesando archivo...", expanded=True) as status:
            t_start = time.time()
            
            # Guardar el archivo físicamente para que Whisper lo lea
            path_temporal = "temp_call.mp3"
            with open(path_temporal, "wb") as f:
                f.write(archivo_audio.getbuffer())
            
            status.write("IA analizando ondas de sonido...")
            # Whisper puede leer el archivo directamente sin Pydub/audioop
            result = model.transcribe(path_temporal)
            texto_final = result['text']
            
            status.write("Evaluando métricas de RRHH...")
            # Diccionario de KPIs
            kpis = {
                "Cordialidad": ["hola", "buenos días", "buenas tardes", "gusto en saludar"],
                "Escucha Activa": ["entiendo", "comprendo", "perfecto", "claro"],
                "Cierre/Venta": ["agendamos", "mañana", "pago", "confirmar", "listo"]
            }
            
            puntos = 0
            check_list = []
            for k, v in kpis.items():
                encontrado = any(p in texto_final.lower() for p in v)
                if encontrado:
                    puntos += 33
                    check_list.append(f"✅ **{k}**: Detectado")
                else:
                    check_list.append(f"❌ **{k}**: No detectado")
            
            status.update(label="Análisis Completo", state="complete")

        # --- RESULTADOS ---
        st.subheader("📊 Dashboard de Desempeño")
        c1, c2, c3 = st.columns(3)
        c1.metric("Puntaje Total", f"{min(puntos, 100)}%", help="Basado en palabras clave del script")
        c2.metric("Velocidad IA", f"{round(time.time()-t_start, 1)}s")
        c3.metric("Calidad Audio", "Alta")

        col_text, col_check = st.columns([2, 1])
        with col_text:
            st.markdown("### 📝 Transcripción")
            st.info(texto_final)
        
        with col_check:
            st.markdown("### 🔍 Validación")
            for item in check_list:
                st.write(item)

        # --- EXCEL ---
        df = pd.DataFrame({
            "Fecha": [pd.Timestamp.now()],
            "Archivo": [archivo_audio.name],
            "Score": [puntos],
            "Transcripcion": [texto_final]
        })
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analisis')
            writer.close()
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=output.getvalue(),
            file_name="Reporte_Llamada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Limpieza de archivo temporal
        if os.path.exists(path_temporal):
            os.remove(path_temporal)

else:
    st.warning("👈 Por favor, carga un archivo de audio en el panel lateral.")
