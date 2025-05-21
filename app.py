
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

sns.set(style="whitegrid")

# --- Funciones ---

def cargar_datos_excel(archivo_excel):
    df = pd.read_excel(archivo_excel, engine='openpyxl', parse_dates=['fecha'])
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
    plt.figure(figsize=(8, 5))
    sns.barplot(data=resumen, x='año', y='venta', palette='viridis')
    plt.title("Comparación de Ventas por Año")
    plt.ylabel("Ventas Totales")
    plt.tight_layout()
    ruta = "grafico_barra.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def graficar_mensual(df):
    df_mensual = df.groupby(['año', 'mes'])['venta'].sum().reset_index()
    df_mensual['mes'] = pd.Categorical(df_mensual['mes'],
        categories=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'], ordered=True)
    df_mensual = df_mensual.sort_values(['mes'])

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=df_mensual, x='mes', y='venta', hue='año', marker="o")
    plt.title("Evolución Mensual de Ventas")
    plt.ylabel("Ventas")
    plt.tight_layout()
    ruta = "grafico_linea.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def graficar_pie(df):
    resumen_pie = df.groupby('categoria')['venta'].sum()
    plt.figure(figsize=(6, 6))
    plt.pie(resumen_pie, labels=resumen_pie.index, autopct='%1.1f%%', startangle=140)
    plt.title("Distribución de Ventas por Categoría")
    ruta = "grafico_pie.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def exportar_pdf_con_graficos(resumen, imagenes):
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
    for imagen in imagenes:
        pdf.image(imagen, w=180)
        pdf.ln(5)

    # Guardar el PDF en memoria
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- Interfaz Streamlit ---

st.set_page_config(page_title="Reporte de Ventas", layout="centered")
st.title("📊 Aplicación de Reportes para Contadores")

archivo = st.file_uploader("📂 Selecciona el archivo Excel de ventas", type=["xlsx"])

if archivo:
    try:
        df = cargar_datos_excel(archivo)

        # Filtros
        clientes = st.multiselect("Filtrar por cliente", df['cliente'].unique())
        categorias = st.multiselect("Filtrar por categoría", df['categoria'].unique())

        if clientes:
            df = df[df['cliente'].isin(clientes)]
        if categorias:
            df = df[df['categoria'].isin(categorias)]

        st.success("Datos cargados correctamente.")
        st.dataframe(df.head())

        resumen = generar_resumen_anual(df)
        ruta_barra = graficar_comparacion(resumen)
        ruta_linea = graficar_mensual(df)
        ruta_pie = graficar_pie(df)

        st.image(ruta_barra, caption="Gráfico de Barras", use_column_width=True)
        st.image(ruta_linea, caption="Gráfico de Línea", use_column_width=True)
        st.image(ruta_pie, caption="Gráfico Circular", use_column_width=True)

        pdf_buffer = exportar_pdf_con_graficos(resumen, [ruta_barra, ruta_linea, ruta_pie])

        st.download_button(
            label="📥 Descargar PDF del reporte",
            data=pdf_buffer,
            file_name="reporte_ventas.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
