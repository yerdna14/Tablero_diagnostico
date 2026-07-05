#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import requests
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('kobo.env')

TOKEN = os.getenv('KOBO_TOKEN', '')
UID = os.getenv('KOBO_UID', '')
BASE_URL = os.getenv('KOBO_BASE_URL', "https://kf.kobotoolbox.org")
OUTPUT_CSV = os.getenv('OUTPUT_CSV', "arauca.csv")

def descargar_datos(token, uid, base_url):
    if not token or not uid:
        raise ValueError("Faltan TOKEN o UID.")
    headers = {"Authorization": f"Token {token}"}
    todos = []
    url = f"{base_url}/api/v2/assets/{uid}/data.json"
    while url:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error al descargar: {e}")
            sys.exit(1)
        data = response.json()
        todos.extend(data["results"])
        url = data.get("next")
    df = pd.json_normalize(todos)
    print(f"✅ Descargados {len(df)} registros.")
    return df

def procesar_ubicacion(df, col_geopoint='_geolocation'):
    """Extrae lat, lon desde lista o string. Versión robusta."""
    if col_geopoint not in df.columns:
        for alt in ['Localizacion', 'geolocation']:
            if alt in df.columns:
                col_geopoint = alt
                break
        else:
            print("⚠️ No se encontró columna de ubicación.")
            return df

    def extraer(valor):
        if valor is None:
            return np.nan, np.nan
        if isinstance(valor, list):
            if len(valor) >= 2:
                try:
                    return float(valor[0]), float(valor[1])
                except:
                    return np.nan, np.nan
            return np.nan, np.nan
        if isinstance(valor, str):
            partes = valor.strip().split()
            if len(partes) >= 2:
                try:
                    return float(partes[0]), float(partes[1])
                except:
                    return np.nan, np.nan
        return np.nan, np.nan

    try:
        df['lat'] = df[col_geopoint].apply(lambda x: extraer(x)[0])
        df['lon'] = df[col_geopoint].apply(lambda x: extraer(x)[1])
    except Exception as e:
        print(f"⚠️ Error al procesar ubicación: {e}")
        df['lat'] = np.nan
        df['lon'] = np.nan
    return df

def limpiar_datos(df):
    columnas_interes = [
        'nombre', 'organizacion_r', 'representante', 'fecha_N',
        'T_Identificacion', 'N_identificion', 'departamento', 'municipio',
        'escolaridad', 'discapacidad', 'campesinado', 'cuidado_mas',
        'cuidado_n', 'g_poblacional', 'E_paz', 'sexo', 'genero',
        'O_sexual', 'organizacion_nom', 'nit', 'pais_o', 'E_civil',
        'tierras', 'personas_n', '_geolocation', 'lat', 'lon'  # Añadimos lat y lon
    ]
    existing = [col for col in columnas_interes if col in df.columns]
    df_clean = df[existing].copy()

    # Normalizar nombres
    if 'nombre' in df_clean.columns:
        df_clean['nombre'] = df_clean['nombre'].str.capitalize()

    # Convertir numéricas
    numeric_cols = ['personas_n', 'N_identificion', 'representante', 'tierras', 'nit']
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Eliminar duplicados
    if 'N_identificion' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['N_identificion'])
    if 'nombre' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['nombre'])

    # Edad
    if 'fecha_N' in df_clean.columns:
        df_clean['fecha_N'] = pd.to_datetime(df_clean['fecha_N'], errors='coerce')
        hoy = pd.Timestamp.now()
        df_clean['edad'] = (hoy - df_clean['fecha_N']).dt.days // 365

    # Extraer lat/lon (si no existen)
    if 'lat' not in df_clean.columns or 'lon' not in df_clean.columns:
        df_clean = procesar_ubicacion(df_clean)

    print(f"✅ Limpieza completada. {len(df_clean)} registros.")
    return df_clean

def guardar_csv(df, filename):
    df.to_csv(filename, index=False)
    print(f"✅ Datos guardados en '{filename}'")

if __name__ == "__main__":
    print("🚀 Iniciando...")
    df_raw = descargar_datos(TOKEN, UID, BASE_URL)
    df_clean = limpiar_datos(df_raw)
    guardar_csv(df_clean, OUTPUT_CSV)
    print("🎉 ¡Proceso completado!")