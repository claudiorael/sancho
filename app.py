import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import time

# 1. Configuración de Interfaz
st.set_page_config(page_title="Analizador de Llamadas Pro", page_icon="📈", layout="wide")

# Inicializar Gemini con tu suscripción
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Por favor, agrega la GEMINI_API_KEY en los Secrets de Streamlit.")

st.title("🤖 Robot Analista (Power by Gemini)")
st.caption("Sistema avanzado de auditoría de ventas y calidad de llamadas.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Carga de Grabación")
    archivo = st.file_uploader("Subir MP3 o WAV", type=["mp3", "wav"])
    st.divider()
    st.info("Al usar Gemini Pro, el análisis incluye: detección de emociones, cumplimiento de guion y sugerencias de coaching.")

# --- PROCESO ---
if archivo:
    st.audio(archivo)
    
    if st.button("🚀 INICIAR AUDITORÍA"):
        try:
            with st.status("Analizando llamada con IA de alta resolución...", expanded=True) as status:
                t_start = time.time()
                
                # Subir audio a Gemini (soporta archivos largos)
                status.write("Subiendo audio al motor de procesamiento...")
                # Guardamos temporalmente para que Gemini lo lea
                with open("temp_audio.mp3", "wb") as f:
                    f.write(archivo.getbuffer())
                
                audio_file = genai.upload_file(path="temp_audio.mp3")
                
                # Esperar a que el archivo se procese en la nube
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)

                status.write("Generando transcripción y métricas...")
                model = genai.GenerativeModel(model_name="gemini-1.5-pro")
                
                # El Prompt maestro para tu análisis
                prompt = """
                Actúa como un experto en Auditoría de Call Center. Analiza este audio y entrega:
                1. Transcripción resumida de la llamada.
                2. Score de Venta (1-100) basado en el entusiasmo y claridad.
                3. Análisis de Emociones: ¿Cómo se siente el cliente y el vendedor?
                4. Checklist de cumplimiento: ¿Saludó? ¿Detectó necesidades? ¿Cerró la venta?
                5. 3 consejos específicos para el plan de capacitación (RRHH).
                """
                
                response = model.generate_content([prompt, audio_file])
                resultado_ia = response.text
                duracion = round(time.time() - t_start, 2)
                
                status.update(label="¡Análisis Finalizado!", state="complete")

            # --- DASHBOARD ---
            st.subheader("📊 Resultados de la Auditoría")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Tiempo de Auditoría", f"{duracion}s")
            c2.metric("Motor", "Gemini 1.5 Pro")
            c3.metric("Estado", "Finalizado")

            st.markdown("### 🧠 Informe Detallado de la IA")
            st.info(resultado_ia)

            # --- EXPORTACIÓN A EXCEL ---
            st.divider()
            df = pd.DataFrame({
                "Fecha": [pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")],
                "Archivo": [archivo.name],
                "Resultado_Analisis": [resultado_ia]
            })
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte_Calidad')
                writer.close()
            
            st.download_button(
                label="📥 Descargar Reporte para RRHH (Excel)",
                data=output.getvalue(),
                file_name=f"Reporte_Llamada_{archivo.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Error en el proceso: {e}")

else:
    st.write("### Bienvenido, Claudio.")
    st.warning("👈 Por favor, carga una llamada en el panel lateral para comenzar.")
