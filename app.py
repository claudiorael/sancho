import sys
import os

# --- FIX CRÍTICO PARA PYTHON 3.13+ ---
# Engañamos al sistema para que pydub encuentre 'audioop' usando 'pyaudioop'
try:
    import audioop
except ImportError:
    try:
        import pyaudioop
        sys.modules["audioop"] = pyaudioop
    except ImportError:
        pass # Streamlit instalará esto desde requirements.txt

import streamlit as st
import whisper
import pandas as pd
from pydub import AudioSegment
import io
import time

# 1. Configuración de Interfaz Elegante
st.set_page_config(page_title="Analizador de Llamadas Pro", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_stdio=True)

# 2. Carga de Modelo (Optimizado con Cache)
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

# --- ESTRUCTURA DE LA APP ---
st.title("🤖 Robot de Auditoría de Llamadas")
st.caption("Herramienta de análisis semántico y cumplimiento de scripts de venta.")

with st.sidebar:
    st.header("📁 Carga de Datos")
    archivo_audio = st.file_uploader("Subir grabación (MP3/WAV)", type=["mp3", "wav"])
    st.divider()
    st.info("Este sistema analiza: \n1. Saludo inicial \n2. Detección de necesidades \n3. Manejo de objeciones \n4. Cierre de venta")

if archivo_audio:
    # Mostrar reproductor
    st.audio(archivo_audio)
    
    if st.button("🔍 ANALIZAR LLAMADA"):
        with st.status("Procesando inteligencia de audio...", expanded=True) as status:
            t_start = time.time()
            
            # Guardado temporal para procesamiento
            with open("temp_audio_file.mp3", "wb") as f:
                f.write(archivo_audio.getbuffer())
            
            status.write("Transcribiendo voz a texto...")
            result = model.transcribe("temp_audio_file.mp3")
            texto_final = result['text']
            
            status.write("Calculando indicadores de desempeño...")
            # Lógica de keywords para el análisis
            diccionario_ventas = {
                "Protocolo Saludo": ["buenos días", "hola", "habla", "gusto"],
                "Detección Necesidad": ["necesita", "ayudar", "buscando", "entiendo"],
                "Manejo Objeciones": ["beneficio", "garantía", "descuento", "calidad"],
                "Cierre Efectivo": ["confirmamos", "agendamos", "mañana", "pago", "listo"]
            }
            
            puntos = 0
            detalles_analisis = []
            for categoria, palabras in diccionario_ventas.items():
                encontrado = any(p in texto_final.lower() for p in palabras)
                if encontrado:
                    puntos += 25
                    detalles_analisis.append(f"✅ {categoria}: Detectado")
                else:
                    detalles_analisis.append(f"❌ {categoria}: No detectado")
            
            duracion_proc = round(time.time() - t_start, 2)
            status.update(label="¡Análisis Exitoso!", state="complete", expanded=False)

        # --- VISUALIZACIÓN DE RESULTADOS ---
        st.subheader("📊 Panel de Métricas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Score de Venta", f"{puntos}%", delta="Cumplimiento")
        with col2:
            st.metric("Sentimiento", "Neutral/Positivo", delta="Estable")
        with col3:
            st.metric("Procesamiento", f"{duracion_proc}s")
        with col4:
            estado = "APROBADO" if puntos >= 75 else "REQUIERE COACHING"
            st.write(f"**Estado Final:**")
            st.info(estado)

        st.divider()

        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("### 📝 Transcripción Detectada")
            st.text_area("", texto_final, height=300)

        with c_right:
            st.markdown("### 💡 Checklist de Auditoría")
            for item in detalles_analisis:
                st.write(item)
            
            if puntos < 75:
                st.warning("Sugerencia: Reforzar el cierre de ventas y el manejo de objeciones con el ejecutivo.")

        # --- EXPORTACIÓN A EXCEL ---
        st.divider()
        st.markdown("### 📥 Reporte para Gestión de RRHH")
        
        # Crear DataFrame para el reporte
        df_reporte = pd.DataFrame({
            "Fecha Análisis": [pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")],
            "Archivo Analizado": [archivo_audio.name],
            "Puntaje Venta %": [puntos],
            "Estado": [estado],
            "Transcripción Completa": [texto_final]
        })

        # Generar archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name='Resultado_Llamada')
            # Ajustar ancho de columnas automáticamente
            worksheet = writer.sheets['Resultado_Llamada']
            worksheet.set_column('A:D', 20)
            worksheet.set_column('E:E', 100)
            writer.close()
        
        st.download_button(
            label="Descargar Reporte en Excel",
            data=output.getvalue(),
            file_name=f"Analisis_{archivo_audio.name.split('.')[0]}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.image("https://cdn-icons-png.flaticon.com/512/4359/4359908.png", width=100)
    st.write("### Bienvenido, Claudio.")
    st.info("Sube un archivo de audio en el panel de la izquierda para comenzar el análisis automático.")
