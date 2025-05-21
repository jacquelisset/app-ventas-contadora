import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io

sns.set(style="whitegrid")

def cargar_datos_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, engine='openpyxl', parse_dates=['fecha'])
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.strftime('%b')
    return df

def generar_resumen_anual(df):
    resumen = df.groupby('año')['venta'].sum().reset_index()
    resumen['venta'] = resumen['venta'].round(2)
    resumen = resumen.sort_values('año')
    resumen['crecimiento'] = resumen['venta'].pct_change().fillna(0) * 100
    return resumen

def graficar_comparacion(resumen):
    plt.figure(figsize=(8,5))
    sns.barplot(data=resumen, x='año', y='venta', palette='viridis')
    plt.title("Comparación de Ventas por Año")
    plt.ylabel("Ventas Totales")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def graficar_mensual(df):
    df_mensual = df.groupby(['año', 'mes'])['venta'].sum().reset_index()
    meses_ordenados = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    df_mensual['mes'] = pd.Categorical(df_mensual['mes'], categories=meses_ordenados, ordered=True)
    df_mensual = df_mensual.sort_values(['año','mes'])

    plt.figure(figsize=(8,5))
    sns.lineplot(data=df_mensual, x='mes', y='venta', hue='año', marker="o")
    plt.title("Evolución Mensual de Ventas")
    plt.ylabel("Ventas")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def graficar_pie(df):
    df_categoria = df.groupby('categoria')['venta'].sum().reset_index()
    plt.figure(figsize=(6,6))
    plt.pie(df_categoria['venta'], labels=df_categoria['categoria'], autopct='%1.1f%%', startangle=140)
    plt.title("Ventas por Categoría")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def exportar_pdf_en_memoria(resumen, imagenes_buffers):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte de Ventas Anual", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for _, fila in resumen.iterrows():
        texto = f"Año: {int(fila['año'])} | Ventas: ${fila['venta']:.2f} | Crecimiento: {fila['crecimiento']:.2f}%"
        pdf.cell(0, 10, texto, ln=True)
    pdf.ln(10)

    # Guardar imágenes en archivos temporales en memoria para usar en pdf.image()
    # FPDF no soporta imágenes desde bytes directamente, entonces guardamos en disco virtual
    for i, img_buf in enumerate(imagenes_buffers):
        img_buf.seek(0)
        ruta_temporal = f"temp_grafico_{i}.png"
        with open(ruta_temporal, "wb") as f:
            f.write(img_buf.read())
        pdf.image(ruta_temporal, w=180)
        pdf.ln(5)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# --- Streamlit app ---

st.title("📈 App de Ventas para Contadora")

uploaded_file = st.file_uploader("Selecciona archivo Excel con ventas", type=['xlsx'])

if uploaded_file:
    try:
        df = cargar_datos_excel(uploaded_file)

        # Filtros
        clientes = df['cliente'].unique()
        categorias = df['categoria'].unique()

        cliente_seleccionado = st.multiselect("Filtrar por cliente", options=clientes, default=clientes)
        categoria_seleccionada = st.multiselect("Filtrar por categoría", options=categorias, default=categorias)

        df_filtrado = df[(df['cliente'].isin(cliente_seleccionado)) & (df['categoria'].isin(categoria_seleccionada))]

        resumen = generar_resumen_anual(df_filtrado)

        # Gráficos
        img_barra = graficar_comparacion(resumen)
        img_linea = graficar_mensual(df_filtrado)
        img_pie = graficar_pie(df_filtrado)

        st.subheader("Gráfico de barras - Ventas por año")
        st.image(img_barra, use_container_width=True)

        st.subheader("Gráfico de línea - Evolución mensual")
        st.image(img_linea, use_container_width=True)

        st.subheader("Gráfico circular - Ventas por categoría")
        st.image(img_pie, use_container_width=True)

        # Exportar PDF
        pdf_bytes = exportar_pdf_en_memoria(resumen, [img_barra, img_linea, img_pie])

        st.download_button(
            label="Descargar reporte PDF",
            data=pdf_bytes,
            file_name="reporte_ventas.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")

else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
