import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from dotenv import load_dotenv
import os
from datetime import datetime

# Cargar variables de entorno desde archivo .env
load_dotenv()

API_USER = os.getenv("API_USER")
API_PASS = os.getenv("API_PASS")
API_URL = os.getenv("API_URL")  

# ---------------------------
# Función para consultar la API
# ---------------------------
def consultar_api(campaign_id):
    try:
        url = f"{API_URL}{campaign_id}"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, auth=(API_USER, API_PASS), headers=headers)

        if response.status_code == 200:
            data = response.json().get("data", {})
            df_sends = pd.DataFrame(data.get("sends", []))
            df_receiveds = pd.DataFrame(data.get("receiveds", []))

            df_sends = df_sends.rename(columns={
                'phone': 'celular',
                'text': 'mensaje',
                'send_at': 'fecha_envio',
                'status': 'estado',
                'carrier': 'operadora',
                'credit': 'credito'
            })

            df_receiveds = df_receiveds.rename(columns={
                'phone': 'celular',
                'content': 'respuesta',
                'received_at': 'fecha_respuesta'
            })

            # Filtrar respuestas no deseadas
            #if 'respuesta' in df_receiveds.columns:
            #    df_receiveds = df_receiveds[~df_receiveds['respuesta'].str.contains('Feliz cumpleanhos', na=False, case=False)]

            return df_sends, df_receiveds
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Error al consultar la API: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

# ---------------------------
# Función para generar archivo Excel
# ---------------------------
def generar_descarga_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output

# ---------------------------
# Configuración de la app
# ---------------------------
st.set_page_config(page_title="Reporte SMS", layout="wide")

if "login_success" not in st.session_state:
    st.session_state.login_success = False

# ---------------------------
# Interfaz de inicio de sesión
# ---------------------------
if not st.session_state.login_success:
    st.title("🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        # Cambiar estos valores para producción
        if username == "admin" and password == "1234":
            st.session_state.login_success = True
            st.success("¡Ingreso exitoso!")
        else:
            st.error("Credenciales incorrectas. Intente nuevamente.")

# ---------------------------
# Interfaz principal
# ---------------------------
else:
    st.title("📊 Consulta de Campaña SMS")

    id_campaña = st.text_input("Ingrese el ID de campaña:")

    if st.button("Consultar API"):
        if id_campaña.strip() == "":
            st.warning("⚠️ Por favor ingrese un ID de campaña válido.")
        else:
            df_sends, df_receiveds = consultar_api(id_campaña)

            if df_sends.empty and df_receiveds.empty:
                st.info("No se encontraron datos para la campaña ingresada.")
            else:
                if not df_sends.empty:
                    st.subheader("📤 SMS Enviados")
                    st.dataframe(df_sends, use_container_width=True)
                    nombre_envio = f"sms_enviados_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
                    st.download_button("📥 Descargar Enviados", data=generar_descarga_excel(df_sends), file_name=nombre_envio)

                if not df_receiveds.empty:
                    st.subheader("📥 SMS Recibidos")
                    st.dataframe(df_receiveds, use_container_width=True)
                    nombre_recibidos = f"sms_recibidos_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
                    st.download_button("📥 Descargar Recibidos", data=generar_descarga_excel(df_receiveds), file_name=nombre_recibidos)
