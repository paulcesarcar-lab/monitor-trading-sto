import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime, timedelta

# Configuración de hora local (Colombia/Panamá GMT-5)
def obtener_hora_local():
    # El servidor suele estar en UTC (GMT+0), restamos 5 horas
    return datetime.now() - timedelta(hours=5)

# Ejemplo de cómo usarlo en tu etiqueta de "VENCE":
hora_actual = obtener_hora_local()
hora_vencimiento = hora_actual + timedelta(minutes=15) # O el tiempo que definas

# 1. CONFIGURACIÓN DE SEGURIDAD (CAMBIA TU PIN AQUÍ)
PIN_CORRECTO = "1234" 

st.set_page_config(page_title="Monitor Seguro STO", layout="centered")

# --- BLOQUE DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acceso Restringido")
    pin_ingresado = st.text_input("Introduce tu PIN de Ingeniero:", type="password")
    if st.button("Desbloquear Analizador"):
        if pin_ingresado == PIN_CORRECTO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("PIN incorrecto. Acceso denegado.")
    st.stop() # Detiene la ejecución si no está autenticado
# -------------------------------

# 2. INTERFAZ PRINCIPAL (Solo visible si el PIN es correcto)
st.title("📊 Sistema de Control de Riesgo")
st.sidebar.success("✅ Conexión Segura Activa")

archivo = st.file_uploader("Subir captura de Binance (15m / 1h / 1d)", type=['png', 'jpg', 'jpeg'])

if archivo is not None:
    image = Image.open(archivo)
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detección de bordes y líneas (Lógica de Trading)
    edges = cv2.Canny(gray, 50, 150)
    min_line_width = int(width * 0.3) 
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=min_line_width, maxLineGap=10)
    
    soportes, resistencias = [], []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 3:
                if y1 > (height / 2):
                    soportes.append(y1)
                    cv2.line(img, (0, y1), (width, y1), (255, 0, 0), 4)
                else:
                    resistencias.append(y1)
                    cv2.line(img, (0, y1), (width, y1), (0, 0, 255), 4)

    # Lógica de Tiempo
    ahora = datetime.now()
    vencimiento = ahora + timedelta(minutes=60)
    hora_vence = vencimiento.strftime("%H:%M")

    # Estampado en imagen
    cv2.rectangle(img, (width-380, 10), (width-10, 90), (0, 0, 0), -1)
    cv2.putText(img, f"VENCE: {hora_vence}", (width-360, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)

    # Panel de Resultados
    st.divider()
    if len(resistencias) > len(soportes):
        st.error(f"🔴 TENDENCIA: BAJISTA (Vence {hora_vence})")
    else:
        st.success(f"🟢 TENDENCIA: ALCISTA (Vence {hora_vence})")

    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
    
    if st.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
        
