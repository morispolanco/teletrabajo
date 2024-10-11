# app.py

import streamlit as st
import requests
import os

# Configurar la página
st.set_page_config(
    page_title="Buscador de Teletrabajo",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("Buscador de Teletrabajo 📄➡️💻")

# Instrucciones para el usuario
st.write("""
    Carga tu currículum y encontraremos las mejores oportunidades de teletrabajo para ti.
    Una vez que encuentremos un empleo adecuado, enviaremos tu currículum al empleador correspondiente.
""")

# Función para procesar el currículum
def procesar_curriculum(file):
    try:
        # Aquí podrías agregar lógica para procesar el currículum,
        # como extraer texto o analizar habilidades. Por simplicidad,
        # asumiremos que simplemente enviamos el archivo a la API de Together.
        return file.read()
    except Exception as e:
        st.error(f"Error al procesar el currículum: {e}")
        return None

# Función para buscar empleos usando la API de Serper
def buscar_empleos(descripcion, api_key):
    try:
        url = "https://serper-api-endpoint.com/search"  # Reemplaza con el endpoint real de Serper
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": f"teletrabajo {descripcion}",
            "location": "remote"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error en la búsqueda de empleos: {response.text}")
            return None
    except Exception as e:
        st.error(f"Excepción al buscar empleos: {e}")
        return None

# Función para enviar el currículum al empleador usando la API de Together
def enviar_curriculum(empleador, curriculum_data, api_key):
    try:
        url = f"https://together-api-endpoint.com/send"  # Reemplaza con el endpoint real de Together
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "employer_id": empleador["id"],
            "resume": curriculum_data,
            "user_email": "usuario@ejemplo.com"  # Puedes solicitar el email al usuario
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error al enviar el currículum: {response.text}")
            return False
    except Exception as e:
        st.error(f"Excepción al enviar el currículum: {e}")
        return False

# Componente para cargar el currículum
uploaded_file = st.file_uploader("Carga tu currículum (PDF o DOCX)", type=["pdf", "docx"])

# Campo para el email del usuario
user_email = st.text_input("Introduce tu correo electrónico para notificaciones", type="email")

if uploaded_file and user_email:
    if st.button("Buscar y Enviar"):
        with st.spinner("Procesando tu currículum y buscando empleos..."):
            # Procesar el currículum
            curriculum = procesar_curriculum(uploaded_file)
            if curriculum:
                # Aquí podrías extraer una descripción o habilidades clave del currículum
                descripcion = "habilidades clave extraídas"  # Implementa la lógica necesaria

                # Buscar empleos adecuados
                serper_api_key = st.secrets["serper_api_key"]
                empleos = buscar_empleos(descripcion, serper_api_key)

                if empleos:
                    # Por simplicidad, tomaremos el primer empleo encontrado
                    empleo_seleccionado = empleos["results"][0]
                    
                    # Enviar el currículum al empleador
                    together_api_key = st.secrets["together_api_key"]
                    exito = enviar_curriculum(empleo_seleccionado, curriculum, together_api_key)

                    if exito:
                        st.success(f"¡Tu currículum ha sido enviado a {empleo_seleccionado['employer_name']}!")
                    else:
                        st.error("Hubo un problema al enviar tu currículum.")
                else:
                    st.warning("No se encontraron empleos adecuados.")
