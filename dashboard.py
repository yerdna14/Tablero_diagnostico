import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página (siempre primero)
st.set_page_config(
    page_title="Dashboard Arauca",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CARGA DE DATOS (desde CSV)
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('arauca.csv', index_col=0)
        # Asegurar que las columnas numéricas sean float (si es necesario)
        # df[['personas_n','N_identificion','representante','tierras','nit']] = \
        #     df[['personas_n','N_identificion','representante','tierras','nit']].astype(float)
        return df
    except FileNotFoundError:
        st.error("No se encontró el archivo 'arauca.csv'. Asegúrate de que esté en el mismo directorio.")
        st.stop()

df = load_data()

# ==========================================
# TÍTULO Y DESCRIPCIÓN
# ==========================================
st.title("📊 Dashboard de Caracterización - Arauca")
st.markdown("Visualización interactiva de las variables principales del formulario.")
st.markdown("---")

# ==========================================
# FILTROS EN LA BARRA LATERAL
# ==========================================
st.sidebar.header("🔍 Filtros")

# Filtro por departamento (si existe)
if 'departamento' in df.columns:
    deptos = sorted(df['departamento'].dropna().unique())
    selected_depto = st.sidebar.selectbox("Departamento", options=["Todos"] + deptos)
else:
    selected_depto = "Todos"

# Filtro por municipio (si existe)
if 'municipio' in df.columns:
    if selected_depto != "Todos":
        municipios = sorted(df[df['departamento'] == selected_depto]['municipio'].dropna().unique())
    else:
        municipios = sorted(df['municipio'].dropna().unique())
    selected_mun = st.sidebar.selectbox("Municipio", options=["Todos"] + municipios)
else:
    selected_mun = "Todos"

# Aplicar filtros
df_filtrado = df.copy()
if selected_depto != "Todos":
    df_filtrado = df_filtrado[df_filtrado['departamento'] == selected_depto]
if selected_mun != "Todos":
    df_filtrado = df_filtrado[df_filtrado['municipio'] == selected_mun]

# ==========================================
# MÉTRICAS GENERALES
# ==========================================
total = len(df_filtrado)
st.markdown(f"### 📌 Total de registros: **{total}**")

# Si hay columna de personas, mostrar promedio
if 'personas_n' in df_filtrado.columns:
    promedio_personas = df_filtrado['personas_n'].mean()
    st.metric("👥 Promedio de personas por hogar", f"{promedio_personas:.1f}")

st.markdown("---")

# ==========================================
# VARIABLES A VISUALIZAR
# ==========================================
variables = ['sexo', 'genero', 'discapacidad', 'E_paz', 'cuidado_n', 'cuidado_mas']
nombres_mostrar = {
    'sexo': 'Sexo',
    'genero': 'Género',
    'discapacidad': 'Discapacidad',
    'E_paz': 'Escolaridad (E_paz)',
    'cuidado_n': 'Cuidado de niños',
    'cuidado_mas': 'Cuidado de adultos mayores'
}

colores = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel

# ==========================================
# CREAR GRÁFICOS EN COLUMNAS (2 por fila)
# ==========================================
cols = st.columns(2)
col_idx = 0

for var in variables:
    if var not in df_filtrado.columns:
        continue

    datos = df_filtrado[var].dropna()
    if len(datos) == 0:
        continue

    conteo = datos.value_counts().reset_index()
    conteo.columns = ['Categoría', 'Frecuencia']
    total_var = conteo['Frecuencia'].sum()
    conteo['Porcentaje'] = (conteo['Frecuencia'] / total_var * 100).round(1)

    # Gráfico de barras
    fig_bar = px.bar(
        conteo,
        x='Categoría',
        y='Frecuencia',
        text='Porcentaje',
        title=nombres_mostrar.get(var, var),
        color='Categoría',
        color_discrete_sequence=colores,
        labels={'Frecuencia': 'Frecuencia', 'Categoría': ''}
    )
    fig_bar.update_traces(
        texttemplate='%{text}%',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Frecuencia: %{y}<br>Porcentaje: %{text}%<extra></extra>'
    )
    fig_bar.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Frecuencia",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12)
    )

    # Gráfico de pastel
    fig_pie = px.pie(
        conteo,
        values='Frecuencia',
        names='Categoría',
        title=nombres_mostrar.get(var, var),
        color='Categoría',
        color_discrete_sequence=colores,
        hole=0.3
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Frecuencia: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )
    fig_pie.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12),
        showlegend=False
    )

    # Mostrar en la columna correspondiente
    with cols[col_idx % 2]:
        tab1, tab2 = st.tabs(["📊 Barras", "🥧 Pastel"])
        with tab1:
            st.plotly_chart(fig_bar, width='stretch')
        with tab2:
            st.plotly_chart(fig_pie, width='stretch')

        with st.expander("📋 Ver tabla de frecuencias"):
            st.dataframe(
                conteo,
                use_container_width=True,   # Este todavía es válido, pero puedes cambiarlo a width='stretch' si quieres
                hide_index=True,
                column_config={
                    "Categoría": "Categoría",
                    "Frecuencia": "Frecuencia",
                    "Porcentaje": st.column_config.NumberColumn("Porcentaje", format="%.1f%%")
                }
            )
        st.markdown("---")

    col_idx += 1

# ==========================================
# MAPA (si existen coordenadas)
# ==========================================
if 'lat' in df_filtrado.columns and 'lon' in df_filtrado.columns:
    map_data = df_filtrado[['lat', 'lon']].dropna()
    if not map_data.empty:
        st.markdown("### 🗺️ Ubicación de los registros")
        st.map(map_data, width='stretch')
    else:
        st.info("No hay datos de ubicación disponibles.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Dashboard generado con Streamlit y Plotly • Datos procesados desde KoboToolbox")