import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
import pytz

# 1. CONFIGURACIÓN DE HORA LOCAL (GMT-5)
def obtener_hora_local():
    zona_horaria = pytz.timezone('America/Bogota')
    return datetime.now(zona_horaria)

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor STO/USDT Tactical Pro", layout="wide")

# 3. SEGURIDAD: ACCESO POR PIN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acceso Restringido")
    pin = st.text_input("Introduce el PIN de Seguridad:", type="password")
    if st.button("Ingresar"):
        if pin == "1234":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("PIN incorrecto.")
    st.stop()

# 4. INTERFAZ
st.title("📊 Analizador Táctico STO/USDT")
archivo = st.file_uploader("Sube captura de Binance", type=["jpg", "png", "jpeg"])

if archivo is not None:
    img = Image.open(archivo)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    bordes = cv2.Canny(gris, 50, 150, apertureSize=3)
    
    # Detección de líneas (Soportes/Resistencias)
    lineas = cv2.HoughLinesP(bordes, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    height, width, _ = img_cv.shape
    punto_medio = height / 2
    
    niveles_resistencia = 0
    if lineas is not None:
        for l in lineas:
            x1, y1, x2, y2 = l[0]
            if abs(y1 - y2) < 5:
                # Rojo para Resistencia (arriba), Verde para Soporte (abajo)
                es_resistencia = y1 < punto_medio
                color = (0, 0, 255) if es_resistencia else (0, 255, 0)
                if es_resistencia: niveles_resistencia += 1
                cv2.line(img_cv, (x1, y1), (x2, y2), color, 2)

    # 5. CEREBRO DE TENDENCIA Y ESTADO
    y_coords = np.argwhere(bordes > 0)[:, 0]
    tendencia_msg = "INDETERMINADA"
    estado_msg = "ESTABLE"
    
    if len(y_coords) > 100:
        # Dividimos el gráfico en inicio (izquierda) y fin (derecha) para ver la pendiente
        mitad_w = bordes.shape[1] // 2
        parte_izq = np.argwhere(bordes[:, :mitad_w] > 0)[:, 0]
        parte_der = np.argwhere(bordes[:, mitad_w:] > 0)[:, 0]
        
        izq_avg = np.mean(parte_izq) if len(parte_izq) > 0 else punto_medio
        der_avg = np.mean(parte_der) if len(parte_der) > 0 else punto_medio
        
        # En imagen, menor Y es más arriba
        es_alcista = der_avg < izq_avg
        tendencia_msg = "ALCISTA 🚀" if es_alcista else "BAJISTA 📉"
        
        # Agotamiento: si es alcista pero hay muchas líneas rojas (niveles_resistencia)
        if es_alcista and niveles_resistencia > 5:
            estado_msg = "AGOTÁNDOSE / LATERALIZADO ⚠️"
        else:
            estado_msg = "CON IMPULSO ⚡"

    # 6. SALIDA DE DATOS (MÁXIMA CLARIDAD)
    vencimiento = (obtener_hora_local() + timedelta(minutes=15)).strftime('%H:%M')
    
    st.markdown(f"### ⏱️ VENCE: {vencimiento} (Hora Local)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("TENDENCIA", tendencia_msg)
    with c2:
        st.metric("ESTADO", estado_msg)

    st.markdown("---")
    st.image(img_cv, channels="BGR", use_container_width=True)

    # 7. ANÁLISIS ESCRITO AUTOMÁTICO
    st.info(f"**Análisis Técnico:** El activo presenta una tendencia **{tendencia_msg}**. "
            f"Se observa un estado **{estado_msg}**. "
            "Las líneas rojas marcan techos de venta y las verdes suelos de compra. "
            "Si ves muchas líneas rojas cerca del precio actual, el movimiento alcista está perdiendo fuerza.")

st.sidebar.write(f"Sincronizado: {obtener_hora_local().strftime('%H:%M:%S')}")
