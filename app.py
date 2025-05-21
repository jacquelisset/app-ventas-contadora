import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import os

sns.set(style="whitegrid")

def cargar_datos_excel(archivo):
    df = pd.read_excel(archivo, engine='openpyxl', parse_dates=['fecha'])
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
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='año', y='venta', palette='viridis')
    plt.title("Comparación de Ventas por Año")
    plt.ylabel("Ventas Totales")
    plt.tight_layout()
    ruta = "grafico_anual.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def graficar_mensual(df):
    df_mensual = df.groupby(['año', 'mes'])['venta'].sum().reset_index()
    df_mensual['mes'] = pd.Categorical(df_mensual['mes'],
        categories=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'], ordered=True)
    df_mensual = df_mensual.sort_values(['mes'])

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_mensual, x='mes', y='venta', hue='año', marker="o")
    plt.title("Evolución Mensual de Ventas")
    plt.ylabel("Ventas")
    plt.tight_layout()
    ruta = "grafico_mensual.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def graficar_pie(df):
    df_categoria = df.groupby('categoria')['venta'].sum().reset_index()
    plt.figure(figsize=(6, 6))
    plt.pie(df_categoria['venta'], labels=df_categoria['categoria'], autopct='%1.1f%%', startangle=140)
    plt.title("Distribución de Ventas por Categoría")
    ruta = "grafico_pie.png"
    plt.savefig(ruta)
    plt.close()
    return ruta

def exportar_pdf_con_graficos(resumen, rutas_graficos):
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
    for ruta in rutas_graficos:
        pdf.image(ruta, w=180)
        pdf.ln(5)

    nombre_pdf = "reporte_ventas.pdf"
    pdf.output(nombre_pdf)

    with open(nombre_pdf, "rb") as f:
        pdf_bytes = BytesIO(f.read())

    return pdf_bytes

# --- INTERFAZ STREAMLIT ---
st.title("📊 Reporte de Ventas para Contadores")

archivo = st.file_uploader("📁 Selecciona el archivo Excel de ventas", type=[".xlsx"])

if archivo is not None:
    try:
        df = cargar_datos_excel(archivo)

        cliente = st.selectbox("Filtrar por cliente (opcional):", ["Todos"] + sorted(df['cliente'].unique().tolist()))
        categoria = st.selectbox("Filtrar por categoría (opcional):", ["Todas"] + sorted(df['categoria'].unique().tolist()))

        if cliente != "Todos":
            df = df[df['cliente'] == cliente]
        if categoria != "Todas":
            df = df[df['categoria'] == categoria]

        resumen = generar_resumen_anual(df)
        ruta_barra = graficar_comparacion(resumen)
        ruta_linea = graficar_mensual(df)
        ruta_pie = graficar_pie(df)

        st.subheader("Resumen Anual")
        st.dataframe(resumen)
        st.image(ruta_barra, caption="Ventas por Año", use_container_width=True)
        st.image(ruta_linea, caption="Ventas Mensuales", use_container_width=True)
        st.image(ruta_pie, caption="Gráfico Circular", use_container_width=True)

        pdf_bytes = exportar_pdf_con_graficos(resumen, [ruta_barra, ruta_linea, ruta_pie])

        st.download_button(
            label="📥 Descargar PDF del Reporte",
            data=pdf_bytes,
            file_name="reporte_ventas.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel con columnas: fecha, venta, cliente, categoria")