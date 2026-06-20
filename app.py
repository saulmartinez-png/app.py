import streamlit as tf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage
import io
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
tf.set_page_config(page_title="Generador de Informes Técnicos", layout="centered")
tf.title("📝 M. DEL ANGEL S.A. de C.V. ")
tf.write("Llene los campos para generar el reporte técnico.")

# --- EVIDENCIA FOTOGRÁFICA ---
# --- 1. EVIDENCIA FOTOGRÁFICA (OPTIMIZADA PARA CELULARES) ---
tf.subheader("1. Evidencia Fotográfica")
fotos = tf.file_uploader("Cargar imágenes (puedes seleccionar varias)", type=["jpg", "png", "jpeg"],
                         accept_multiple_files=True)
notas_fotos = []

# Forzamos a Streamlit a esperar que el archivo se procese por completo antes de redibujar la interfaz
if fotos is not None and len(fotos) > 0:
    tf.info(f"📸 Se han cargado {len(fotos)} imágenes. Añade una descripción para cada una:")
    for i, foto in enumerate(fotos):
        # Usamos el tamaño del archivo en la clave para forzar la sincronización inmediata del navegador
        clave_unica = f"nota_{foto.name}_{foto.size}_{i}"
        nota = tf.text_input(
            f"Descripción para la Foto {i + 1} ({foto.name})",
            f"Evidencia fotográfica número {i + 1}",
            key=clave_unica
        )
        notas_fotos.append(nota)


# --- LIENZO INTERACTIVO PARA FIRMA DIGITAL ---
tf.subheader("2. Firma Digital del Mecánico")
tf.caption("Trace su firma con el dedo o el mouse en el recuadro blanco de abajo:")

try:
    from streamlit_drawable_canvas import st_canvas

    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=3,
        stroke_color="#1A365D",
        background_color="#FFFFFF",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas_firma",
    )
except ImportError:
    tf.error("Falta instalar la librería del lienzo. Por favor ejecuta: 'pip install streamlit-drawable-canvas'")

# --- FORMULARIO PRINCIPAL DE ENTRADA ---
with tf.form("datos_informe"):
    tf.subheader("3. Información del Vehículo y Reporte")
    titulo = tf.text_input("ECO")

    modelo = tf.text_input("Modelo del Vehículo", placeholder="Ej. Kenworth T680 / 2022")
    placas = tf.text_input("Placas", placeholder="Ej. XX-1234-X")
    kilometraje = tf.text_input("Kilometraje", placeholder="Ej. 150,000 km")

    codigo = tf.text_input("Código/Referencia del Informe", "INF-2026-001")
    especialista = tf.text_input("Nombre del Operador", "")
    fecha = tf.date_input("Fecha de la Inspección")

    tf.subheader("4. Detalles Técnicos")
    descripcion = tf.text_area("Descripción de la falla ")
    conclusiones = tf.text_area("Descripción de trabajo que se realizó para diagnóstico ")

    enviado = tf.form_submit_button("🚀 Procesar y Generar PDF")

titulos = "Informe de inspección técnica"


# --- LÓGICA DE GENERACIÓN DE PDF ---
def crear_pdf(titulos, titulo, modelo, placas, kilometraje, codigo, especialista, fecha, descripcion, conclusiones,
              fotos, notas_fotos, firma_img_bytes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('TituloStyle', parent=styles['Heading1'], fontSize=24, leading=28,
                                   textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    estilo_sub = ParagraphStyle('SubStyle', parent=styles['Heading2'], fontSize=14, leading=18,
                                textColor=colors.HexColor("#2B6CB0"), spaceBefore=12, spaceAfter=6)
    estilo_texto = ParagraphStyle('TextoStyle', parent=styles['Normal'], fontSize=10, leading=14,
                                  textColor=colors.HexColor("#2D3748"))
    estilo_tabla_encabezado = ParagraphStyle('TableEnc', parent=styles['Normal'], fontSize=10, leading=12,
                                             fontName="Helvetica-Bold", textColor=colors.white)
    estilo_firma = ParagraphStyle('FirmaStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=1,
                                  textColor=colors.HexColor("#2D3748"))

    story.append(Paragraph(titulos.upper(), estilo_titulo))
    story.append(Spacer(1, 10))

    datos_tabla = [
        [Paragraph("Código:", estilo_tabla_encabezado), Paragraph(codigo, estilo_texto),
         Paragraph("Fecha:", estilo_tabla_encabezado), Paragraph(str(fecha), estilo_texto)],
        [Paragraph("Operador:", estilo_tabla_encabezado), Paragraph(especialista, estilo_texto),
         Paragraph("ECO:", estilo_tabla_encabezado), Paragraph(titulo, estilo_texto)],
        [Paragraph("Modelo:", estilo_tabla_encabezado), Paragraph(modelo, estilo_texto),
         Paragraph("Placas:", estilo_tabla_encabezado), Paragraph(placas, estilo_texto)],
        [Paragraph("Kilometraje:", estilo_tabla_encabezado), Paragraph(kilometraje, estilo_texto),
         Paragraph("", estilo_tabla_encabezado), Paragraph("", estilo_texto)]
    ]

    # SOLUCIÓN DEFINITIVA: Convertimos tuplas explícitas para no usar corchetes en los anchos
    meta_w1 = 90
    meta_w2 = 175
    meta_w3 = 65
    meta_w4 = 100
    anchos_encabezado = tuple((meta_w1, meta_w2, meta_w3, meta_w4))

    tabla_meta = Table(datos_tabla, colWidths=anchos_encabezado)
    tabla_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 3), colors.HexColor("#1A365D")),
        ('BACKGROUND', (2, 0), (2, 3), colors.HexColor("#1A365D")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla_meta)

    story.append(Spacer(1, 15))
    nombre_operador = especialista if especialista else "Operador"

    if firma_img_bytes:
        img_firma_pdf = Image(firma_img_bytes, width=130, height=50)
        celda_firma_operador = [
            img_firma_pdf,
            Spacer(1, 2),
            Paragraph("___________________________", estilo_firma),
            Paragraph(f"<b>Firma del Operador</b><br/>{nombre_operador}", estilo_firma)
        ]
    else:
        celda_firma_operador = [
            Spacer(1, 40),
            Paragraph("___________________________", estilo_firma),
            Paragraph(f"<b>Firma del Operador</b><br/>{nombre_operador}", estilo_firma)
        ]

    datos_firmas = [[celda_firma_operador]]

    # Ancho de firma blindado
    firma_w = 530
    anchos_firmas = tuple((firma_w,))

    tabla_firmas = Table(datos_firmas, colWidths=anchos_firmas)
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(tabla_firmas)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Descripción del Análisis", estilo_sub))
    story.append(Paragraph(descripcion.replace("\n", "<br/>"), estilo_texto))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Conclusiones y Recomendaciones", estilo_sub))
    story.append(Paragraph(conclusiones.replace("\n", "<br/>"), estilo_texto))
    story.append(Spacer(1, 15))

    if fotos:
        story.append(Paragraph("Evidencia Fotográfica", estilo_sub))
        story.append(Spacer(1, 5))

        tabla_fotos_datos = []
        fila_actual = []

        for i, foto_archivo in enumerate(fotos):
            foto_archivo.seek(0)
            img_pil = PILImage.open(foto_archivo)
            img_ancho, img_alto = img_pil.size
            proporcion = img_alto / img_ancho

            nuevo_ancho = 230
            nuevo_alto = int(nuevo_ancho * proporcion)

            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format=img_pil.format if img_pil.format else 'JPEG')
            img_byte_arr.seek(0)

            img_reportlab = Image(img_byte_arr, width=nuevo_ancho, height=nuevo_alto)

            celda = [
                img_reportlab,
                Spacer(1, 4),
                Paragraph(f"<b>Foto {i + 1}:</b> {notas_fotos[i]}", estilo_texto)
            ]
            fila_actual.append(celda)

            if len(fila_actual) == 2:
                tabla_fotos_datos.append(fila_actual)
                fila_actual = []

        if fila_actual:
            fila_actual.append("")
            tabla_fotos_datos.append(fila_actual)

        # Anchos de fotos blindados
        foto_w = 265
        anchos_fotos_blindados = tuple((foto_w, foto_w))

        tabla_fotos = Table(tabla_fotos_datos, colWidths=anchos_fotos_blindados)
        tabla_fotos.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(tabla_fotos)

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- ACCIÓN DEL FORMULARIO ---
if enviado:
    if not especialista or not descripcion:
        tf.error("❌ Por favor, rellene al menos el nombre del Operador y la descripción de la falla.")
    else:
        firma_bytes = None
        if canvas_result.image_data is not None:
            if np.sum(canvas_result.image_data[:, :, 3]) > 0:
                img_firma_pil = PILImage.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                firma_bytes = io.BytesIO()
                img_firma_pil.save(firma_bytes, format='PNG')
                firma_bytes.seek(0)

        with tf.spinner("Generando archivo PDF..."):
            pdf_data = crear_pdf(titulos, titulo, modelo, placas, kilometraje, codigo, especialista, fecha, descripcion,
                                 conclusiones, fotos, notas_fotos, firma_bytes)

            tf.success("✔️ ¡Informe procesado con éxito!")
            tf.download_button(
                label="📥 Descargar Informe Técnico (PDF)",
                data=pdf_data,
                file_name=f"{codigo}_Informe_Tecnico.pdf",
                mime="application/pdf",
                use_container_width=True
            )
