import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import time
import os

# 1. Configuración de Interfaz
st.set_page_config(page_title="Analizador de Llamadas Pro", page_icon="📈", layout="wide")

# Inicializar Gemini con tu Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Error: Configura la GEMINI_API_KEY en los Secrets de Streamlit.")

st.title("🤖 Robot Analista (Multimodal)")
st.caption("Auditoría inteligente de llamadas utilizando Google Gemini 1.5.")

with st.sidebar:
    st.header("📂 Carga de Grabación")
    archivo = st.file_uploader("Subir MP3 o WAV", type=["mp3", "wav"])
    st.info("Nota: Esta versión procesa el audio directamente para detectar tonos y emociones.")

if archivo:
    st.audio(archivo)
    
    if st.button("🚀 INICIAR AUDITORÍA"):
        try:
            with st.status("Procesando con IA de Google...", expanded=True) as status:
                # Guardar temporalmente
                temp_path = "temp_audio.mp3"
                with open(temp_path, "wb") as f:
                    f.write(archivo.getbuffer())
                
                status.write("Subiendo archivo a la nube de Google...")
                audio_file = genai.upload_file(path=temp_path)
                
                # Esperar procesamiento del archivo
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)
                
                status.write("Analizando semántica y tonos...")
                
                # LÓGICA DE SELECCIÓN DE MODELO (Fallback)
                modelos_a_probar = ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.5-flash"]
                
                response = None
                prompt = """
                Analiza esta llamada de Call Center de forma profesional:
                1. Transcripción detallada.
                2. Score de Calidad (1-100).
                3. Detección de Emociones (Vendedor vs Cliente).
                4. Identificación de puntos de cumplimiento del script.
                5. 3 recomendaciones accionables para mejora de ventas.
                """

                for nombre_modelo in modelos_a_probar:
                    try:
                        model = genai.GenerativeModel(model_name=f"models/{nombre_modelo}")
                        response = model.generate_content([prompt, audio_file])
                        if response:
                            break
                    except Exception:
                        continue
                
                if not response:
                    raise Exception("No se pudo conectar con ninguno de los modelos de Gemini. Revisa los permisos de tu API Key.")

                resultado_ia = response.text
                status.update(label="¡Análisis Exitoso!", state="complete")

            # --- VISUALIZACIÓN ---
            st.subheader("📊 Informe de Auditoría")
            st.markdown(resultado_ia)

            # --- EXPORTACIÓN ---
            st.divider()
            df = pd.DataFrame({
                "Fecha": [pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")],
                "Archivo": [archivo.name],
                "Analisis": [resultado_ia]
            })
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
                writer.close()
            
            st.download_button(
                label="📥 Descargar Reporte Excel",
                data=output.getvalue(),
                file_name=f"Auditoria_{archivo_audio.name if 'archivo_audio' in locals() else 'Llamada'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Limpieza obligatoria
            genai.delete_file(audio_file.name)
            if os.path.exists(temp_path):
                os.remove(temp_path)

        except Exception as e:
            st.error(f"Error detectado: {e}")

else:
    st.write("### 👋 Hola Claudio")
    st.info("Carga un audio en el panel lateral para que el robot comience el trabajo.")
