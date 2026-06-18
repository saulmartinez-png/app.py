import streamlit as tf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage
import io
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.runtime.uploaded_file_manager import UploadedFile


def my_background_task(ctx):
    # Attach context to the new thread
    add_script_run_ctx(threading.current_thread(), ctx)
    # Your Streamlit code here

# On your main Streamlit thread
ctx = get_script_run_ctx()
thread = threading.Thread(target=my_background_task, args=(ctx,))
thread.start()

# --- CONFIGURACIÓN DE LA PÁGINA ---
tf.set_page_config(page_title="Generador de Informes Técnicos", layout="centered")
tf.title("📝 Informe Tecnico ")
tf.write("Llene los campos!!!")

# --- FORMULARIO DE ENTRADA ---
with tf.form("datos_informe"):
    tf.subheader("1.Informacion del Vehiculo")
    titulo = tf.text_input("ECO", "Escribe el economico de la unidad")
    codigo = tf.text_input("Código/Referencia del Informe", "INF-2026-001")
    especialista = tf.text_input("Nombre del Mecanico", "")
    fecha = tf.date_input("Fecha de la Inspección")

    tf.subheader("2. Detalles Técnicos")
    descripcion = tf.text_area("Descripción de la falla ", "")
    conclusiones = tf.text_area("Descripcion de trabajo que se realizo para diagnostico ", "")

    tf.subheader("3. Evidencia Fotográfica")
    fotos: list[UploadedFile] | UploadedFile | None = tf.file_uploader("Cargar imágenes (puedes seleccionar varias)", type=["jpg", "png", "jpeg"],
                             accept_multiple_files=True)
    notas_fotos = []

    if fotos:
        tf.info(f"Se han cargado {len(fotos)} imágenes. Añade una descripción para cada una:")
        for i, foto in enumerate(fotos):
            nota = tf.text_input(f"Descripción para la Foto {i + 1}", f"Evidencia fotográfica número {i + 1}",
                                 key=f"nota_{i}")
            notas_fotos.append(nota)

    enviado = tf.form_submit_button("Generar PDF")


# --- LÓGICA DE GENERACIÓN DE PDF ---
def crear_pdf(titulo, codigo, especialista, fecha, descripcion, conclusiones, fotos, notas_fotos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('TituloStyle', parent=styles['Heading1'], fontSize=24, leading=28,
                                   textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    estilo_sub = ParagraphStyle('SubStyle', parent=styles['Heading2'], fontSize=14, leading=18,
                                textColor=colors.HexColor("#2B6CB0"), spaceBefore=12, spaceAfter=6)
    estilo_texto = ParagraphStyle('TextoStyle', parent=styles['Normal'], fontSize=10, leading=14,
                                  textColor=colors.HexColor("#2D3748"))
    estilo_tabla_encabezado = ParagraphStyle('TableEnc', parent=styles['Normal'], fontSize=10, leading=12,
                                             fontName="Helvetica-Bold", textColor=colors.white)

    # Título Principal
    story.append(Paragraph(titulo.upper(), estilo_titulo))
    story.append(Spacer(1, 10))

    # Tabla de Metadatos
    datos_tabla = [
        [Paragraph("Código:", estilo_tabla_encabezado), Paragraph(codigo, estilo_texto),
         Paragraph("Fecha:", estilo_tabla_encabezado), Paragraph(str(fecha), estilo_texto)],
        [Paragraph("Especialista:", estilo_tabla_encabezado), Paragraph(especialista, estilo_texto),
         Paragraph("", estilo_texto), Paragraph("", estilo_texto)]
    ]

    tabla_meta = Table(datos_tabla, colWidths=[90, 175, 65, 200])
    tabla_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 1), colors.HexColor("#1A365D")),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor("#1A365D")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla_meta)
    story.append(Spacer(1, 15))

    # Cuerpo del Informe
    story.append(Paragraph("Descripción del Análisis", estilo_sub))
    story.append(Paragraph(descripcion.replace("\n", "<br/>"), estilo_texto))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Conclusiones y Recomendaciones", estilo_sub))
    story.append(Paragraph(conclusiones.replace("\n", "<br/>"), estilo_texto))
    story.append(Spacer(1, 15))

    # Sección de Fotos (Diseño en cuadrícula de 2 columnas)
    if fotos:
        story.append(Paragraph("Evidencia Fotográfica", estilo_sub))
        story.append(Spacer(1, 5))

        tabla_fotos_datos = []
        fila_actual = []

        for i, foto_archivo in enumerate(fotos):
            # Procesar imagen con Pillow para redimensionarla proporcionalmente
            img_pil = PILImage.open(foto_archivo)
            img_ancho, img_alto = img_pil.size
            proporcion = img_alto / img_ancho

            nuevo_ancho = 240
            nuevo_alto = int(nuevo_ancho * proporcion)

            # Convertir de nuevo a bytes para ReportLab
            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format=img_pil.format)
            img_byte_arr.seek(0)

            img_reportlab = Image(img_byte_arr, width=nuevo_ancho, height=nuevo_alto)

            # Crear celda con la imagen y su descripción abajo
            celda = [
                img_reportlab,
                Spacer(1, 4),
                Paragraph(f"<b>Foto {i + 1}:</b> {notas_fotos[i]}", estilo_texto)
            ]

            fila_actual.append(celda)

            # Cada 2 fotos se cierra la fila de la cuadrícula
            if len(fila_actual) == 2:
                tabla_fotos_datos.append(fila_actual)
                fila_actual = []

        if fila_actual:  # Si quedó una foto huérfana al final
            fila_actual.append("")  # Celda vacía para completar la fila
            tabla_fotos_datos.append(fila_actual)

        tabla_fotos = Table(tabla_fotos_datos, colWidths=[265, 265])
        tabla_fotos.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(tabla_fotos)

    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# --- ACCIÓN DEL FORMULARIO ---
if enviado:
    if not especialista or not descripcion:
        tf.error("Por favor, rellene al menos el nombre del especialista y la descripción.")
    else:
        with tf.spinner("Generando archivo PDF..."):
            pdf_data = crear_pdf(titulo, codigo, especialista, fecha, descripcion, conclusiones, fotos, notas_fotos)

            tf.success("¡Informe generado con éxito!")
            tf.download_button(
                label="📥 Descargar Informe Técnico (PDF)",
                data=pdf_data,
                file_name=f"{codigo}_Informe_Tecnico.pdf",
                mime="application/pdf"
            )
