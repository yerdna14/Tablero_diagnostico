#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para descargar y procesar datos de KoboToolbox.
Genera un archivo CSV limpio para el dashboard.
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

TOKEN = os.getenv('KOBO_TOKEN')
UID = os.getenv('KOBO_UID')
BASE_URL = os.getenv('KOBO_BASE_URL', "https://kf.kobotoolbox.org")
OUTPUT_CSV = os.getenv('OUTPUT_CSV', "arauca.csv")

# ... resto del script (descargar_datos, limpiar_datos, etc.)

# ==========================================
# FUNCIONES
# ==========================================

def descargar_datos(token, uid, base_url):
    """Descarga todos los registros de un formulario con paginación."""
    if not token or not uid:
        raise ValueError("Faltan TOKEN o UID. Configúralos como variables de entorno.")

    headers = {"Authorization": f"Token {token}"}
    todos = []
    url = f"{base_url}/api/v2/assets/{uid}/data.json"

    while url:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al descargar datos: {e}")
            sys.exit(1)

        data = response.json()
        todos.extend(data["results"])
        url = data.get("next")  # None cuando termina

    df = pd.json_normalize(todos)
    print(f"✅ Descargados {len(df)} registros.")
    return df

def limpiar_datos(df):
    """Aplica las transformaciones de limpieza del notebook."""
    columnas_interes = [
        'nombre', 'organizacion_r', 'representante', 'fecha_N',
        'T_Identificacion', 'N_identificion', 'departamento', 'municipio',
        'escolaridad', 'discapacidad', 'campesinado', 'cuidado_mas',
        'cuidado_n', 'g_poblacional', 'E_paz', 'sexo', 'genero',
        'O_sexual', 'T_productor', 'extencion', 'organizacion_nom',
        'nit', 'pais_o', 'E_civil', 'tierras', 'personas_n'
    ]
    # Solo columnas existentes
    columnas_existentes = [col for col in columnas_interes if col in df.columns]
    df_clean = df[columnas_existentes].copy()

    # Normalizar nombres
    if 'nombre' in df_clean.columns:
        df_clean['nombre'] = df_clean['nombre'].str.capitalize()

    # Convertir columnas numéricas
    columnas_numericas = ['personas_n', 'N_identificion', 'representante', 'tierras', 'nit']
    for col in columnas_numericas:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Eliminar duplicados (primero por ID, luego por nombre)
    if 'N_identificion' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['N_identificion'])
    if 'nombre' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['nombre'])

    # Calcular edad
    if 'fecha_N' in df_clean.columns:
        df_clean['fecha_N'] = pd.to_datetime(df_clean['fecha_N'], errors='coerce')
        hoy = pd.Timestamp.now()
        df_clean['edad'] = (hoy - df_clean['fecha_N']).dt.days // 365

    print(f"✅ Limpieza completada. {len(df_clean)} registros después de limpieza.")
    return df_clean

def guardar_csv(df, filename):
    """Guarda el DataFrame en CSV."""
    df.to_csv(filename, index=False)
    print(f"✅ Datos guardados en '{filename}'")

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando proceso de descarga y procesamiento...")
    df_raw = descargar_datos(TOKEN, UID, BASE_URL)
    df_clean = limpiar_datos(df_raw)
    guardar_csv(df_clean, OUTPUT_CSV)
    print("🎉 ¡Proceso completado con éxito!")