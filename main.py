import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
from pathlib import Path

st.set_page_config(layout="wide", page_title="Dashboard Estudiantil")

# ----------------- Helpers -----------------
def parse_height_to_cm(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip().replace(',', '.')
    try:
        num = float(s)
    except:
        return np.nan
    return round(num * 100, 2) if num <= 3 else round(num, 2)

def parse_weight(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip().replace(',', '.')
    try:
        return float(s)
    except:
        return np.nan

def calculate_age(birthdate):
    if pd.isna(birthdate):
        return np.nan
    try:
        bd = pd.to_datetime(birthdate, dayfirst=True, errors='coerce')
        if pd.isna(bd):
            return np.nan
        today = pd.Timestamp.today()
        years = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        return int(years)
    except:
        return np.nan

def calculate_bmi(weight_kg, height_cm):
    try:
        if pd.isna(weight_kg) or pd.isna(height_cm) or height_cm == 0:
            return np.nan
        h_m = height_cm / 100
        return round(weight_kg / (h_m * h_m), 2)
    except:
        return np.nan

def bmi_category(bmi):
    if pd.isna(bmi):
        return "Desconocido"
    if bmi < 18.5:
        return "Bajo peso"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Sobrepeso"
    else:
        return "Obesidad"

# ----------------- Leer CSV local -----------------
CSV_NAME = "estudiantes.csv"
p = Path(CSV_NAME)
if not p.exists():
    st.error(f"No se encontró el archivo '{CSV_NAME}' en esta carpeta.")
    st.stop()

df = pd.read_csv(p, dtype=str)
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # eliminar columnas vacías

# ----------------- Normalizar columnas -----------------
expected_cols = [
    'Código','Nombre_Estudiante','Apellido_Estudiante','Fecha_Nacimiento',
    'Estatura','Peso','RH','Color_Cabello','Talla_Zapato','Barrio_Residencia'
]
for c in expected_cols:
    if c not in df.columns:
        df[c] = np.nan

df['Integrante'] = df['Nombre_Estudiante'].fillna('') + ' ' + df['Apellido_Estudiante'].fillna('')

# ----------------- Limpieza y nuevas columnas -----------------
# Convertimos a formato título para evitar duplicados por mayúsculas/minúsculas
text_cols = ['RH', 'Color_Cabello', 'Barrio_Residencia']
for col in text_cols:
    df[col] = df[col].astype(str).str.strip().str.title()

df['Estatura_cm'] = df['Estatura'].apply(parse_height_to_cm)
df['Peso'] = df['Peso'].apply(parse_weight)
df['Edad'] = df['Fecha_Nacimiento'].apply(calculate_age)
df['IMC'] = df.apply(lambda r: calculate_bmi(r['Peso'], r['Estatura_cm']), axis=1)
df['Clasificacion_IMC'] = df['IMC'].apply(bmi_category)

for c in ['Estatura_cm','Peso','IMC','Edad']:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# ----------------- Mostrar archivo original -----------------
st.subheader("Archivo de Excel procesado (vista)")
st.dataframe(df, use_container_width=True)

# ----------------- Título -----------------
st.title("Dashboard Estudiantil – Grupo 001")

# ----------------- Filtros -----------------
st.sidebar.header("Filtros")
rh_options = sorted(df['RH'].dropna().unique().tolist())
hair_options = sorted(df['Color_Cabello'].dropna().unique().tolist())
barrio_options = sorted(df['Barrio_Residencia'].dropna().unique().tolist())

rh_sel = st.sidebar.multiselect("Tipo de Sangre (RH)", rh_options, default=rh_options)
hair_sel = st.sidebar.multiselect("Color de Cabello", hair_options, default=hair_options)
barrio_sel = st.sidebar.multiselect("Barrio de Residencia", barrio_options, default=barrio_options)

st.sidebar.markdown("---")
edad_min = int(df['Edad'].min(skipna=True)) if not df['Edad'].dropna().empty else 0
edad_max = int(df['Edad'].max(skipna=True)) if not df['Edad'].dropna().empty else 100
est_min = int(df['Estatura_cm'].min(skipna=True)) if not df['Estatura_cm'].dropna().empty else 0
est_max = int(df['Estatura_cm'].max(skipna=True)) if not df['Estatura_cm'].dropna().empty else 250

edad_range = st.sidebar.slider("Rango de Edad", 0, 120, (edad_min, edad_max))
estatura_range = st.sidebar.slider("Rango de Estatura (cm)", 0, 250, (est_min, est_max))

# ----------------- Aplicar filtros -----------------
filtered = df.copy()
if rh_sel:
    filtered = filtered[filtered['RH'].isin(rh_sel)]
if hair_sel:
    filtered = filtered[filtered['Color_Cabello'].isin(hair_sel)]
if barrio_sel:
    filtered = filtered[filtered['Barrio_Residencia'].isin(barrio_sel)]
filtered = filtered[(filtered['Edad'] >= edad_range[0]) & (filtered['Edad'] <= edad_range[1])]
filtered = filtered[(filtered['Estatura_cm'] >= estatura_range[0]) & (filtered['Estatura_cm'] <= estatura_range[1])]

# ----------------- KPIs y tabla -----------------
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)
total_est = len(filtered)
edad_prom = round(filtered['Edad'].mean(skipna=True), 2) if total_est>0 else np.nan
est_prom = round(filtered['Estatura_cm'].mean(skipna=True), 2) if total_est>0 else np.nan
peso_prom = round(filtered['Peso'].mean(skipna=True), 2) if total_est>0 else np.nan
imc_prom = round(filtered['IMC'].mean(skipna=True), 2) if total_est>0 else np.nan

col1.metric("Total Estudiantes", total_est)
col2.metric("Edad Promedio", edad_prom if not np.isnan(edad_prom) else "N/A")
col3.metric("Estatura Promedio (cm)", est_prom if not np.isnan(est_prom) else "N/A")
col4.metric("Peso Promedio (kg)", peso_prom if not np.isnan(peso_prom) else "N/A")
col5.metric("IMC Promedio", imc_prom if not np.isnan(imc_prom) else "N/A")

st.markdown("**Resumen (tabla) — Estudiantes filtrados**")
cols_to_show = [
    'Código','Integrante','Edad','Estatura_cm','Peso','IMC','Clasificacion_IMC','RH',
    'Color_Cabello','Talla_Zapato','Barrio_Residencia'
]
st.dataframe(filtered[cols_to_show], use_container_width=True)

# ----------------- 1era fila de gráficos -----------------
st.markdown("---")
st.subheader("1ª Fila de gráficos")
c1, c2 = st.columns([2,1])

with c1:
    st.write("Distribución por Edad (Barras)")
    if filtered['Edad'].dropna().empty:
        st.write("Sin datos.")
    else:
        edad_counts = filtered['Edad'].value_counts().sort_index()
        fig_age = px.bar(
            x=edad_counts.index,
            y=edad_counts.values,
            title="Distribución por Edad",
            labels={'x': 'Edad', 'y': 'Cantidad de Estudiantes'},
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_age, use_container_width=True)

with c2:
    st.write("Distribución por Tipo de Sangre (Torta)")
    rh_counts = filtered['RH'].fillna('Desconocido').value_counts()
    if rh_counts.empty:
        st.write("Sin datos.")
    else:
        fig_rh = px.pie(values=rh_counts.values, names=rh_counts.index, title="Tipo de Sangre (RH)")
        st.plotly_chart(fig_rh, use_container_width=True)

# ----------------- 2da fila de gráficos -----------------
st.markdown("---")
st.subheader("2ª Fila de gráficos")
c3, c4 = st.columns([2,1])

with c3:
    st.write("Relación Estatura vs Peso (Scatter)")
    scatter_df = filtered.dropna(subset=['Estatura_cm','Peso'])
    if scatter_df.empty:
        st.write("Sin datos suficientes.")
    else:
        fig_scatter = px.scatter(
            scatter_df, x='Estatura_cm', y='Peso', hover_data=['Integrante','Edad','RH'],
            title="Estatura vs Peso", color='RH'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with c4:
    st.write("Distribución por Color de Cabello (Barras)")
    hair_counts = filtered['Color_Cabello'].fillna('Desconocido').value_counts()
    if hair_counts.empty:
        st.write("Sin datos.")
    else:
        fig_hair = px.bar(
            x=hair_counts.index, y=hair_counts.values, title="Color de Cabello",
            labels={'x':'Color de Cabello','y':'Cantidad'}
        )
        st.plotly_chart(fig_hair, use_container_width=True)

# ----------------- 3era fila de gráficos -----------------
st.markdown("---")
st.subheader("3ª Fila de gráficos")
c5, c6 = st.columns([2,1])

with c5:
    st.write("Distribución de Tallas de Zapato (Línea)")
    shoe_counts = filtered['Talla_Zapato'].dropna().astype(str).value_counts().sort_index()
    if shoe_counts.empty:
        st.write("Sin datos.")
    else:
        fig_shoe = px.line(
            x=shoe_counts.index, y=shoe_counts.values, title="Tallas de Zapato",
            labels={'x':'Talla Zapato','y':'Cantidad'}
        )
        st.plotly_chart(fig_shoe, use_container_width=True)

with c6:
    st.write("Top 10 Barrios de Residencia (Barras)")
    barrio_top = filtered['Barrio_Residencia'].fillna('Desconocido').value_counts().head(10)
    if barrio_top.empty:
        st.write("Sin datos.")
    else:
        fig_barrio = px.bar(
            x=barrio_top.index, y=barrio_top.values, title="Top 10 Barrios",
            labels={'x':'Barrio','y':'Cantidad'}
        )
        st.plotly_chart(fig_barrio, use_container_width=True)

# ----------------- Top 5 Archivos -----------------
st.markdown("---")
st.subheader("Top 5 - Mayor Estatura y Mayor Peso")
top5_est = filtered.sort_values(by='Estatura_cm', ascending=False).head(5)
top5_peso = filtered.sort_values(by='Peso', ascending=False).head(5)

c7, c8 = st.columns(2)
with c7:
    st.write("Top 5 Mayor Estatura")
    st.dataframe(top5_est[['Código','Integrante','Estatura_cm','Edad','Barrio_Residencia']])
with c8:
    st.write("Top 5 Mayor Peso")
    st.dataframe(top5_peso[['Código','Integrante','Peso','IMC','Barrio_Residencia']])

def to_csv_bytes(df_):
    return df_.to_csv(index=False).encode('utf-8')

c9, c10 = st.columns(2)
with c9:
    st.download_button("Descargar Top 5 Estatura (CSV)", to_csv_bytes(top5_est), "top5_estatura.csv")
with c10:
    st.download_button("Descargar Top 5 Peso (CSV)", to_csv_bytes(top5_peso), "top5_peso.csv")

# ----------------- Resumen Estadístico -----------------
st.markdown("---")
st.subheader("Resumen Estadístico")
sc1, sc2, sc3 = st.columns(3)
with sc1:
    st.write("Estatura (cm)")
    st.write(filtered['Estatura_cm'].describe())
with sc2:
    st.write("Peso (kg)")
    st.write(filtered['Peso'].describe())
with sc3:
    st.write("IMC")
    st.write(filtered['IMC'].describe())

# ----------------- Botón Excel completo -----------------
@st.cache_data
def to_excel_bytes(df_):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df_.to_excel(writer, index=False, sheet_name='Estudiantes')
    return out.getvalue()

st.markdown("---")
st.download_button(
    "Descargar Excel modificado (.xlsx)",
    data=to_excel_bytes(filtered),
    file_name="ListadoDeEstudiantes_modificado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

