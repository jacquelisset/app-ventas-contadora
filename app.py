
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from io import BytesIO
import tempfile
import os

sns.set(style="whitegrid")

def cargar_datos_excel(file, cliente=None, categoria=None):
    df = pd.read_excel(file, engine='openpyxl', parse_dates=['fecha'])
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.strftime('%b')
    if cliente:
        df = df[df['cliente'] == cliente]
    if categoria:
        df = df[df['categoria'] == categoria]
    return df

def generar_resumen_anual(df):
    resumen = df.groupby('año')['venta'].sum().reset_index()
    resumen['venta'] = resumen['venta'].round(2)
    resumen = resumen.sort_values('año')
    resumen['crecimiento'] = resumen['venta'].pct_change().fillna(0) * 100
    return resumen

def graficar_comparacion(resumen, ruta_guardar):
    plt.figure(figsize=(10, 5))
    sns.barplot(data=resumen, x='año', y='venta', palette='viridis')
    plt.title("Comparación de Ventas por Año")
    plt.ylabel("Ventas Totales")
    plt.tight_layout()
    plt.savefig(ruta_guardar)
    plt.close()

def graficar_mensual(df, ruta_guardar):
    df_mensual = df.groupby(['año', 'mes'])['venta'].sum().reset_index()
    df_mensual['mes'] = pd.Categorical(df_mensual['mes'],
        categories=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'], ordered=True)
    df_mensual = df_mensual.sort_values(['mes'])
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df_mensual, x='mes', y='venta', hue='año', marker='o')
    plt.title("Evolución Mensual de Ventas")
    plt.ylabel("Ventas")
    plt.tight_layout()
    plt.savefig(ruta_guardar)
    plt.close()

def graficar_circular_categoria(df, ruta_guardar):
    resumen_cat = df.groupby('categoria')['venta'].sum()
    plt.figure(figsize=(7,7))
    resumen_cat.plot.pie(autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title("Distribución de Ventas por Categoría")
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(ruta_guardar)
    plt.close()

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

    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes

# --- Streamlit App ---
st.title("📈 App de Ventas para Contadoras")

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    df_base = pd.read_excel(archivo, engine='openpyxl', parse_dates=['fecha'])
    clientes = df_base['cliente'].dropna().unique().tolist()
    categorias = df_base['categoria'].dropna().unique().tolist()

    cliente_sel = st.selectbox("Filtrar por cliente (opcional)", [""] + clientes)
    categoria_sel = st.selectbox("Filtrar por categoría (opcional)", [""] + categorias)

    df = cargar_datos_excel(archivo, cliente_sel if cliente_sel else None, categoria_sel if categoria_sel else None)

    if not df.empty:
        resumen = generar_resumen_anual(df)

        # Crear archivos temporales para los gráficos
        with tempfile.TemporaryDirectory() as tmpdirname:
            ruta_barra = os.path.join(tmpdirname, "grafico_anual.png")
            ruta_linea = os.path.join(tmpdirname, "grafico_mensual.png")
            ruta_pie = os.path.join(tmpdirname, "grafico_categoria.png")

            graficar_comparacion(resumen, ruta_barra)
            graficar_mensual(df, ruta_linea)
            graficar_circular_categoria(df, ruta_pie)

            st.subheader("Gráficos de Ventas")
            st.image(ruta_barra, caption="Comparación Anual")
            st.image(ruta_linea, caption="Evolución Mensual")
            st.image(ruta_pie, caption="Distribución por Categoría")

            pdf_bytes = exportar_pdf_con_graficos(resumen, [ruta_barra, ruta_linea, ruta_pie])

            st.download_button("Descargar reporte en PDF con gráficos", data=pdf_bytes, file_name="reporte_ventas.pdf")

    else:
        st.warning("No se encontraron datos con esos filtros.")
