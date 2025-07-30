import cv2
from datetime import datetime
import os
import time
from playsound import playsound
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN ---
OPACIDAD_MARCA = 0.3              # Transparencia de la marca de agua (0 a 1)
PORCENTAJE_TAMANO_FUENTE = 0.03  # Tamaño de fuente relativo al ancho de la imagen
FUENTE_PATH = "arial.ttf"         # Ruta o nombre de la fuente .ttf
# ---------------------

def obtener_nombre_unico(base_dir, base_nombre="foto", extension=".png"):
    contador = 0
    while True:
        nombre = f"{base_nombre}{contador if contador > 0 else ''}{extension}"
        ruta = os.path.join(base_dir, nombre)
        if not os.path.exists(ruta):
            return ruta
        contador += 1

def poner_fecha_proporcional(imagen_pil, texto_fecha, fuente_path=FUENTE_PATH, porcentaje_tamano=PORCENTAJE_TAMANO_FUENTE):
    draw = ImageDraw.Draw(imagen_pil)
    ancho_imagen = imagen_pil.width
    tamaño_fuente = max(12, int(ancho_imagen * porcentaje_tamano))
    try:
        font = ImageFont.truetype(fuente_path, tamaño_fuente)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), texto_fecha, font=font)
    texto_ancho = bbox[2] - bbox[0]
    texto_alto = bbox[3] - bbox[1]

    x = imagen_pil.width - texto_ancho - 10
    y = imagen_pil.height - texto_alto - 10
    sombra_color = "black"
    texto_color = "white"
    for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
        draw.text((x+dx, y+dy), texto_fecha, font=font, fill=sombra_color)
    draw.text((x, y), texto_fecha, font=font, fill=texto_color)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

if not os.path.exists("fotos"):
    os.makedirs("fotos")

marca_path = "marca.png"

cam = cv2.VideoCapture(0)
foto_tomada = False

print("🎥 Sistema activo. Esperando rostro frente a la cámara...")

while True:
    ret, frame = cam.read()
    if not ret:
        print("⚠️ Error al acceder a la cámara.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) > 0 and not foto_tomada:
        filename = obtener_nombre_unico("fotos", extension=".png")

        cv2.imwrite(filename, frame)

        try:
            base = Image.open(filename).convert("RGBA")
            marca = Image.open(marca_path).convert("RGBA")

            max_width = base.width // 4
            if marca.width > max_width:
                ratio = max_width / marca.width
                new_size = (int(marca.width * ratio), int(marca.height * ratio))
                marca = marca.resize(new_size, Image.Resampling.LANCZOS)

            alpha = marca.split()[3]
            alpha = alpha.point(lambda p: p * OPACIDAD_MARCA)
            marca.putalpha(alpha)

            posicion = (10, base.height - marca.height - 10)
            base.paste(marca, posicion, marca)

            fecha_texto = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            poner_fecha_proporcional(base, fecha_texto, fuente_path=FUENTE_PATH, porcentaje_tamano=PORCENTAJE_TAMANO_FUENTE)

            base.save(filename, "PNG")

            print(f"📸 ¡Persona detectada! Foto guardada como: {filename}")

            playsound("sound.wav")

        except Exception as e:
            print(f"❌ Error al aplicar marca de agua: {e}")

        foto_tomada = True
        time.sleep(2)

    cv2.imshow("Camara", frame)

    if len(faces) == 0:
        foto_tomada = False

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()


