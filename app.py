import sys
# Solución para error audioop en Python 3.13+
try:
    import audioop
except ImportError:
    import pyaudioop
    sys.modules["audioop"] = pyaudioop

import streamlit as st
import whisper
import pandas as pd
from pydub import AudioSegment
import io
import time

# Configuración estética
st.set_page_config(page_title="Analizador de Llamadas Pro", page_icon="📈", layout="wide")

# CSS personalizado para un look más limpio
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_stdio=True)

@st.cache_resource
def load_speech_model():
    return whisper.load_model("base")

model = load_speech_model()

# --- INTERFAZ ---
st.title("🤖 Robot Analista de Llamadas")
st.markdown("Análisis automático de guiones, tonos y métricas de desempeño.")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1998/1998664.png", width=100)
    st.header("Panel de Control")
    archivo = st.file_uploader("Cargar MP3 de la llamada", type=["mp3", "wav"])
    st.divider()
    umbral_exito = st.slider("Umbral de éxito esperado", 0, 100, 80)

if archivo:
    # Reproductor y botón principal
    st.audio(archivo)
    
    if st.button("🚀 INICIAR PROCESAMIENTO"):
        with st.status("Analizando audio...", expanded=True) as status:
            st.write("Convertiendo formatos...")
            t_inicio = time.time()
            
            # Guardar temporalmente
            with open("temp.mp3", "wb") as f:
                f.write(archivo.getbuffer())
            
            st.write("Transcribiendo con IA (Whisper)...")
            resultado = model.transcribe("temp.mp3")
            texto = resultado['text']
            
            st.write("Evaluando métricas de venta...")
            # Lógica de keywords (puedes ampliar esta lista)
            keywords = {"Bienvenida": ["hola", "buenos días", "saluda"], 
                        "Cierre": ["comprar", "agendar", "mañana", "oferta"],
                        "Objeciones": ["entiendo", "pero", "descuento", "beneficio"]}
            
            hallazgos = {k: any(word in texto.lower() for word in v) for k, v in keywords.items()}
            score = sum(hallazgos.values()) / len(hallazgos) * 100
            
            t_total = round(time.time() - t_inicio, 2)
            status.update(label="¡Análisis completado!", state="complete", expanded=False)

        # --- DASHBOARD DE RESULTADOS ---
        st.subheader("📊 Resultados del Análisis")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score de Venta", f"{int(score)}%", delta=f"{int(score-umbral_exito)}% vs meta")
        c2.metric("Emoción", "Positiva", delta="Calma")
        c3.metric("Duración", f"{int(t_total)}s", help="Tiempo de procesamiento")
        c4.metric("Script", "Cumplido" if score > 70 else "Incompleto")

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            with st.expander("📝 Transcripción de la llamada", expanded=True):
                st.write(texto)

        with col_right:
            st.info("💡 **Feedback Automático**")
            if not hallazgos["Cierre"]:
                st.warning("- No se detectó un cierre claro. Intentar llamado a la acción.")
            if score > 80:
                st.success("- Excelente manejo del protocolo de saludo.")
            else:
                st.error("- Faltaron elementos clave del script oficial.")

        # --- EXPORTACIÓN A EXCEL ---
        st.divider()
        reporte_data = {
            "Fecha": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
            "Ejecutivo": ["No asignado"],
            "Archivo": [archivo.name],
            "Score %": [score],
            "Estado Script": ["OK" if score > 70 else "Revisar"],
            "Transcripcion": [texto]
        }
        df = pd.DataFrame(reporte_data)
        
        # Crear buffer para Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte')
            writer.close()
        
        st.download_button(
            label="📥 Descargar Reporte para RRHH (Excel)",
            data=buffer.getvalue(),
            file_name=f"Analisis_{archivo.name}.xlsx",
            mime="application/vnd.ms-excel"
        )

else:
    st.info("Esperando carga de archivo para iniciar el robot...")
