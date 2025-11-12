"""
Dashboard Estudiantil en Streamlit
Autor: Deivy (adaptado para Arch Linux)
------------------------------------
Este script:
- Lee un CSV con datos de estudiantes.
- Calcula Edad, Estatura en cm, IMC y Clasificación IMC.
- Muestra la tabla y gráficos interactivos.
- Permite descargar archivos Excel y Top 5.
Ejecutar con:
    streamlit run main.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Estudiantil")

# --- Funciones auxiliares ---

def parse_height_to_cm(value):
    if pd.isna(value): return np.nan
    s = str(value).strip().replace(',', '.')
    try:
        num = float(s)
    except:
        return np.nan
    return round(num * 100 if num <= 3 else num, 2)

def parse_weight(value):
    if pd.isna(value): return np.nan
    s = str(value).strip().replace(',', '.')
    try:
        return float(s)
    except:
        return np.nan

def calculate_age(birthdate):
    if pd.isna(birthdate): return np.nan
    try:
        bd = pd.to_datetime(birthdate, dayfirst=True, errors='coerce')
        today = pd.Timestamp.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except:
        return np.nan

def calculate_bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm: return np.nan
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 2)

def bmi_category(bmi):
    if pd.isna(bmi): return "Desconocido"
    if bmi < 18.5: return "Bajo peso"
    elif bmi < 25: return "Normal"
    elif bmi < 30: return "Sobrepeso"
    else: return "Obesidad"

# --- Lectura del CSV ---
st.title("Dashboard Estudiantil – Grupo 001")

uploaded = st.file_uploader("Selecciona archivo CSV", type=["csv"])
if uploaded is None:
    # Si no sube archivo, usar el CSV local
    try:
        uploaded = open("estudiantes.csv", "rb")
        st.info("Usando archivo local 'estudiantes.csv'")
    except FileNotFoundError:
        st.error("No se encontró 'estudiantes.csv'. Sube tu archivo CSV.")
        st.stop()

df = pd.read_csv(uploaded, dtype=str)

# Normalización de columnas esperadas
for col in ['Código','Nombre_Estudiante','Apellido_Estudiante','Fecha_Nacimiento',
            'Estatura','Peso','RH','Color_Cabello','Talla_Zapato','Barrio_Residencia']:
    if col not in df.columns:
        df[col] = np.nan

df['Integrante'] = df['Nombre_Estudiante'].fillna('') + ' ' + df['Apellido_Estudiante'].fillna('')

# --- Nuevas columnas ---
df['Estatura_cm'] = df['Estatura'].apply(parse_height_to_cm)
df['Peso_kg'] = df['Peso'].apply(parse_weight)
df['Edad'] = df['Fecha_Nacimiento'].apply(calculate_age)
df['IMC'] = df.apply(lambda r: calculate_bmi(r['Peso_kg'], r['Estatura_cm']), axis=1)
df['Clasificacion_IMC'] = df['IMC'].apply(bmi_category)

# --- Mostrar tabla ---
st.subheader("Archivo procesado")
st.dataframe(df, use_container_width=True)

# --- Filtros ---
with st.sidebar:
    st.header("Filtros")
    rh = st.multiselect("Tipo de Sangre", df['RH'].dropna().unique())
    color = st.multiselect("Color de Cabello", df['Color_Cabello'].dropna().unique())
    barrio = st.multiselect("Barrio", df['Barrio_Residencia'].dropna().unique())

filtered = df.copy()
if rh: filtered = filtered[filtered['RH'].isin(rh)]
if color: filtered = filtered[filtered['Color_Cabello'].isin(color)]
if barrio: filtered = filtered[filtered['Barrio_Residencia'].isin(barrio)]

# --- Sliders ---
age_min, age_max = int(filtered['Edad'].min(skipna=True)), int(filtered['Edad'].max(skipna=True))
height_min, height_max = int(filtered['Estatura_cm'].min(skipna=True)), int(filtered['Estatura_cm'].max(skipna=True))

age_range = st.sidebar.slider("Rango de Edad", 0, 120, (age_min, age_max))
height_range = st.sidebar.slider("Rango de Estatura (cm)", 0, 250, (height_min, height_max))

filtered = filtered[(filtered['Edad'] >= age_range[0]) & (filtered['Edad'] <= age_range[1])]
filtered = filtered[(filtered['Estatura_cm'] >= height_range[0]) & (filtered['Estatura_cm'] <= height_range[1])]

# --- KPIs ---
st.markdown("---")
cols = st.columns(5)
cols[0].metric("Total Estudiantes", len(filtered))
cols[1].metric("Edad Promedio", round(filtered['Edad'].mean(), 2))
cols[2].metric("Estatura Promedio (cm)", round(filtered['Estatura_cm'].mean(), 2))
cols[3].metric("Peso Promedio (kg)", round(filtered['Peso_kg'].mean(), 2))
cols[4].metric("IMC Promedio", round(filtered['IMC'].mean(), 2))

# --- Gráficos ---
st.markdown("---")
st.subheader("Distribución por Edad")
if not filtered['Edad'].isna().all():
    fig = px.bar(filtered, x="Edad", title="Distribución por Edad")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Relación Estatura vs Peso")
if not filtered[['Estatura_cm', 'Peso_kg']].dropna().empty:
    fig = px.scatter(filtered, x="Estatura_cm", y="Peso_kg", color="RH", hover_data=["Integrante"])
    st.plotly_chart(fig, use_container_width=True)

# --- Exportar archivos ---
st.markdown("---")
st.subheader("Exportar resultados")

top_est = filtered.sort_values(by="Estatura_cm", ascending=False).head(5)
top_peso = filtered.sort_values(by="Peso_kg", ascending=False).head(5)

def to_csv_bytes(df_):
    return df_.to_csv(index=False).encode('utf-8')

st.download_button("Descargar Top 5 Estatura", to_csv_bytes(top_est), "top5_estatura.csv")
st.download_button("Descargar Top 5 Peso", to_csv_bytes(top_peso), "top5_peso.csv")

# --- Resumen estadístico ---
st.markdown("---")
st.subheader("Resumen Estadístico")
st.write(filtered[['Estatura_cm', 'Peso_kg', 'IMC']].describe())

# --- Exportar Excel completo ---
@st.cache_data
def to_excel_bytes(df_):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_.to_excel(writer, index=False, sheet_name='Estudiantes')
    return output.getvalue()

st.download_button(
    "Descargar Excel completo",
    data=to_excel_bytes(filtered),
    file_name="estudiantes_modificado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

