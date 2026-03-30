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
st.set_page_config(page_title="Monitor STO/USDT Pro", layout="centered")

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
            st.error("PIN incorrecto. Acceso denegado.")
    st.stop()

# 4. INTERFAZ DEL ANALIZADOR
st.title("📊 Analizador Táctico STO/USDT Pro")
st.write("Sube tu captura de pantalla de Binance para procesar niveles y tendencia.")

archivo = st.file_uploader("Seleccionar imagen...", type=["jpg", "png", "jpeg"])

if archivo is not None:
    # Procesar imagen con OpenCV
    img = Image.open(archivo)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Detección de bordes (Canny)
    bordes = cv2.Canny(gris, 50, 150, apertureSize=3)
    
    # Transformada de Hough para detectar soportes/resistencias
    lineas = cv2.HoughLinesP(bordes, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    # Determinamos el punto medio para separar soportes y resistencias
    height, width, _ = img_cv.shape
    punto_medio = height / 2
    
    if lineas is not None:
        for l in lineas:
            x1, y1, x2, y2 = l[0]
            # Dibujamos solo líneas horizontales (posibles soportes/resistencias)
            if abs(y1 - y2) < 5:
                # Lógica de color: Resistencias (Arriba, y1 < punto_medio) son Rojas, Soportes (Abajo) son Verdes
                color = (0, 0, 255) if y1 < punto_medio else (0, 255, 0) # BGR
                cv2.line(img_cv, (x1, y1), (x2, y2), color, 2)

    # DETECCIÓN DE TENDENCIA (Lógica basada en altura de los últimos puntos)
    # Analizamos los últimos 50 puntos de bordes para ver si suben o bajan
    y_coordenadas = np.argwhere(bordes > 0)[:, 0] # Obtenemos coordenadas Y de los bordes
    if len(y_coordenadas) > 100:
        primeros_puntos = np.mean(y_coordenadas[:50]) # Promedio de los primeros puntos (izquierda del gráfico)
        ultimos_puntos = np.mean(y_coordenadas[-50:]) # Promedio de los últimos puntos (derecha)
        
        # En imagen, Y menor es más arriba. Si los últimos puntos están "más arriba", es alcista.
        tendencia = "🚀 ALCISTA" if ultimos_puntos < primeros_puntos else "📉 BAJISTA"
    else:
        tendencia = "❓ INDETERMINADA"

    # 5. CÁLCULO DE TIEMPO (VENCE)
    hora_actual = obtener_hora_local()
    vencimiento = (hora_actual + timedelta(minutes=15)).strftime('%H:%M')

    # 6. MOSTRAR RESULTADOS
    col1, col2 = st.columns(2)
    with col1:
        st.image(img_cv, channels="BGR", caption="Análisis Visual de Niveles")
    
    with col2:
        st.success("✅ ANÁLISIS COMPLETADO")
        st.metric(label="⏱️ PRÓXIMO VENCE (GMT-5)", value=vencimiento)
        st.metric(label="📊 TENDENCIA DETECTADA", value=tendencia)
        st.info("Recomendación: Validar con volumen y fuerza de ruptura.")

st.sidebar.write(f"Conectado: {obtener_hora_local().strftime('%d/%m/%Y %H:%M:%S')}")
