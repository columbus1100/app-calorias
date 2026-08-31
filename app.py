import streamlit as st
import google.generativeai as genai

st.title("Prueba de Clave")

clave = "AQ.Ab8RN6KOhN13ff7i5G8eP3t8mzUnbgmjRxRypVv3uZCsRYLTlw"

try:
    genai.configure(api_key=clave)
    model = genai.GenerativeModel('gemini-1.5-flash')
    st.success("¡La librería se ha configurado correctamente!")
except Exception as e:
    st.error(f"Error: {e}")
