# app.py

import streamlit as st
import requests
import re
from PyPDF2 import PdfReader
from io import BytesIO
import docx

# Configurar la página
st.set_page_config(
    page_title="Buscador de Empleo",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("Buscador de Empleo 📄➡️💻")

# Instrucciones para el usuario
st.write("""
    **Bienvenido al Buscador de Empleo.**  
    Aquí puedes encontrar las mejores oportunidades laborales que coinciden con tu perfil.  
    **Métodos disponibles:**
    - **Cargar tu currículum** en formato PDF o DOCX.
    - **Ingresar manualmente tus habilidades** si prefieres no subir un currículum.
""")

# Opciones de entrada
opcion = st.radio(
    "Selecciona cómo deseas proporcionar tu información:",
    ("Cargar Currículum", "Ingresar Habilidades Manualmente")
)

# Función para extraer texto del currículum
def extraer_texto_curriculum(file):
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            texto = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + " "
            return texto
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            texto = ""
            for para in doc.paragraphs:
                texto += para.text + " "
            return texto
        else:
            st.error("Formato de archivo no soportado. Por favor, sube un PDF o DOCX.")
            return None
    except Exception as e:
        st.error(f"Error al procesar el currículum: {e}")
        return None

# Función para interactuar con la API de Together y extraer información clave
def procesar_con_together(texto_curriculum, api_key):
    try:
        url = "https://api.together.xyz/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = f"Por favor, extrae una lista concisa de habilidades, experiencia y puestos de trabajo relevantes de este currículum:\n\n{texto_curriculum}"
        data = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": "Eres un asistente que extrae información clave de currículums de manera concisa."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,  # Reducir la cantidad de tokens para respuestas más concisas
            "temperature": 0.5,  # Reducir la temperatura para respuestas más determinísticas
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1,
            "stop": ["<|eot_id|>"],
            "stream": False
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            respuesta = response.json()
            # Asumiendo que la respuesta tiene una estructura similar a OpenAI
            contenido = respuesta.get("choices", [])[0].get("message", {}).get("content", "")
            return contenido
        else:
            st.error(f"Error al procesar el currículum con Together: {response.text}")
            return None
    except Exception as e:
        st.error(f"Excepción al procesar el currículum con Together: {e}")
        return None

# Función para buscar empleos usando la API de Serper
def buscar_empleos(descripcion, api_key):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        query = descripcion.strip()
        # Verificar y limitar la longitud de la consulta
        max_query_length = 2048
        if len(query) > max_query_length:
            # Truncar la descripción para que la consulta no exceda el límite
            allowed_length = max_query_length
            descripcion_truncada = query[:allowed_length]
            st.warning("La descripción ha sido truncada para ajustarse al límite de la API.")
            query = descripcion_truncada
        
        payload = {
            "q": query
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error en la búsqueda de empleos: {response.text}")
            return None
    except Exception as e:
        st.error(f"Excepción al buscar empleos: {e}")
        return None

# Función para parsear los resultados de Serper y extraer información relevante
def parsear_resultados_serper(empleos_json):
    # La estructura de la respuesta depende de la API de Serper
    # Asumiendo que los resultados están en 'organic' y cada resultado tiene 'title', 'link', 'snippet'
    resultados = []
    try:
        if "organic" in empleos_json:
            for item in empleos_json["organic"]:
                titulo = item.get("title", "Sin Título")
                enlace = item.get("link", "#")
                snippet = item.get("snippet", "")
                resultados.append({
                    "titulo": titulo,
                    "enlace": enlace,
                    "descripcion": snippet
                })
    except Exception as e:
        st.error(f"Error al parsear los resultados de Serper: {e}")
    return resultados

# Función para procesar habilidades ingresadas manualmente
def procesar_habilidades_manual(habilidades_texto):
    # Limpiar y procesar las habilidades ingresadas
    habilidades = habilidades_texto.strip()
    # Puedes agregar más procesamiento si es necesario
    return habilidades

# Flujo principal basado en la opción seleccionada
if opcion == "Cargar Currículum":
    # Componente para cargar el currículum
    uploaded_file = st.file_uploader("Carga tu currículum (PDF o DOCX)", type=["pdf", "docx"])
    
    if uploaded_file:
        if st.button("Buscar Oportunidades de Empleo"):
            with st.spinner("Procesando tu currículum y buscando empleos..."):
                # Extraer texto del currículum
                texto_curriculum = extraer_texto_curriculum(uploaded_file)
                if texto_curriculum:
                    # Procesar el currículum con Together para extraer habilidades y experiencias
                    together_api_key = st.secrets["together_api_key"]
                    descripcion = procesar_con_together(texto_curriculum, together_api_key)
                    
                    if descripcion:
                        st.success("Currículum procesado exitosamente.")
                        
                        # Mostrar la descripción extraída (opcional)
                        st.subheader("Información Extraída del Currículum")
                        st.write(descripcion)
                        
                        # Buscar empleos adecuados con Serper
                        serper_api_key = st.secrets["serper_api_key"]
                        empleos = buscar_empleos(descripcion, serper_api_key)
                        
                        if empleos:
                            resultados = parsear_resultados_serper(empleos)
                            if resultados:
                                st.subheader("Opciones de Empleo Encontradas")
                                for idx, empleo in enumerate(resultados, 1):
                                    st.markdown(f"### {idx}. {empleo['titulo']}")
                                    st.markdown(f"**Descripción:** {empleo['descripcion']}")
                                    st.markdown(f"**Enlace:** [Aplicar Aquí]({empleo['enlace']})")
                                    st.markdown("---")
                            else:
                                st.warning("No se encontraron empleos adecuados.")
                        else:
                            st.warning("No se obtuvieron resultados de empleos.")
                    else:
                        st.error("No se pudo procesar el currículum con Together.")
                else:
                    st.error("No se pudo extraer texto del currículum.")

elif opcion == "Ingresar Habilidades Manualmente":
    # Campo para ingresar habilidades manualmente
    habilidades_texto = st.text_area("Ingresa tus habilidades (separadas por comas):", height=150)
    
    if habilidades_texto:
        if st.button("Buscar Oportunidades de Empleo"):
            with st.spinner("Procesando tus habilidades y buscando empleos..."):
                # Procesar habilidades ingresadas manualmente
                habilidades_procesadas = procesar_habilidades_manual(habilidades_texto)
                
                if habilidades_procesadas:
                    st.success("Habilidades procesadas exitosamente.")
                    
                    # Mostrar las habilidades ingresadas (opcional)
                    st.subheader("Habilidades Ingresadas")
                    st.write(habilidades_procesadas)
                    
                    # Buscar empleos adecuados con Serper
                    serper_api_key = st.secrets["serper_api_key"]
                    empleos = buscar_empleos(habilidades_procesadas, serper_api_key)
                    
                    if empleos:
                        resultados = parsear_resultados_serper(empleos)
                        if resultados:
                            st.subheader("Opciones de Empleo Encontradas")
                            for idx, empleo in enumerate(resultados, 1):
                                st.markdown(f"### {idx}. {empleo['titulo']}")
                                st.markdown(f"**Descripción:** {empleo['descripcion']}")
                                st.markdown(f"**Enlace:** [Aplicar Aquí]({empleo['enlace']})")
                                st.markdown("---")
                        else:
                            st.warning("No se encontraron empleos adecuados.")
                    else:
                        st.warning("No se obtuvieron resultados de empleos.")
                else:
                    st.error("No se pudo procesar las habilidades ingresadas.")
