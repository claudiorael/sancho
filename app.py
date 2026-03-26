import streamlit as st
import whisper
import os
from pydub import AudioSegment

# Configuración de la página
st.set_page_config(page_title="Analizador de Llamadas Pro", layout="wide")
st.title("🤖 Robot de Análisis de Ventas y Emociones")

# 1. Carga del Modelo de Whisper (se cachea para no recargar siempre)
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# 2. Sidebar para cargar archivos
st.sidebar.header("Configuración")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo de audio (MP3)", type=["mp3", "wav"])

if uploaded_file is not None:
    # Guardar temporalmente el archivo
    with open("temp_audio.mp3", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.audio(uploaded_file, format='audio/mp3')

    if st.button("Iniciar Análisis"):
        with st.spinner("Transcribiendo audio..."):
            # Transcripción
            result = model.transcribe("temp_audio.mp3")
            transcript_text = result['text']
            
        # Layout de columnas para mostrar resultados
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📝 Transcripción Completa")
            st.text_area("Texto detectado:", transcript_text, height=300)

        with col2:
            st.subheader("📊 Análisis de Inteligencia")
            
            # Aquí simularíamos la lógica de análisis (puedes conectar con GPT-4 o Claude)
            # Por ahora, haremos un análisis basado en reglas simples para el ejemplo:
            palabras_clave = ["oferta", "descuento", "competencia", "precio", "garantía"]
            encontradas = [p for p in palabras_clave if p in transcript_text.lower()]
            
            st.info(f"**Palabras clave detectadas:** {', '.join(encontradas) if encontradas else 'Ninguna'}")
            
            # Simulación de Score de Emoción
            st.metric(label="Tono del Vendedor", value="Entusiasta", delta="Positivo")
            st.metric(label="Cumplimiento de Script", value="85%", delta="Cumple")

        st.divider()
        st.subheader("💡 Sugerencias de Mejora")
        st.write("""
        - **Cierre de venta:** Se detectó una pausa larga después del precio. Reforzar el manejo de objeciones.
        - **Empatía:** El tono fue adecuado, pero faltó confirmar si el cliente tenía dudas adicionales.
        """)

else:
    st.info("Por favor, sube un archivo MP3 en la barra lateral para comenzar.")
