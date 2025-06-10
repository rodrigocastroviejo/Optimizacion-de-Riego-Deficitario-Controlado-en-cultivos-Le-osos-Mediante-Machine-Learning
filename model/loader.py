#Importamos los datos desde los archivos .csv a DataFrames.

import pandas as pd 


df_clima = pd.read_csv(
    'data/clima_OUT.csv',
    sep=';',                    # Delimitador de columnas
    decimal=',',                # Separador decimal
    encoding='latin1',          # Codificación para caracteres especiales (Õ, Û, Ì, etc.)
    parse_dates=['date'],       # Convertir columna de fecha a datetime
    dayfirst=True  
)



df_datos_suelo1 = pd.read_csv(
    'data/Mini1_OUT.csv',
    sep=';',                    # Delimitador de columnas
    decimal=',',                # Separador decimal
    encoding='latin1',          # Codificación para caracteres especiales (Õ, Û, Ì, etc.)
    parse_dates=['date'],       # Convertir columna de fecha a datetime
    dayfirst=True  
)

# Convertir la columna 'hour' a tipo datetime combinándola con 'date'
#df_datos_suelo1['datetime'] = pd.to_datetime(df_datos_suelo1['date']) + pd.to_timedelta(df_datos_suelo1['hour'], unit='h')

df_datos_suelo2 = pd.read_csv(
    'data/Mini2_OUT.csv',
    sep=';',                    # Delimitador de columnas
    decimal=',',                # Separador decimal
    encoding='latin1',          # Codificación para caracteres especiales (Õ, Û, Ì, etc.)
    parse_dates=['date'],       # Convertir columna de fecha a datetime
    dayfirst=True  
)

# Convertir la columna 'hour' a tipo datetime combinándola con 'date'
#df_datos_suelo2['datetime'] = pd.to_datetime(df_datos_suelo2['date']) + pd.to_timedelta(df_datos_suelo2['hour'], unit='h')

df_riego = pd.read_csv(
    'data/RIEGOS ALMENDRO2024.csv',
    sep=';',                      # Delimitador de punto y coma
    decimal=',',                  # Usa coma como separador decimal
    thousands=None,               # No hay separador de miles
    parse_dates=['Inicio', 'Fin'], # Convierte estas columnas a datetime
    dayfirst=True,                # Formato de fecha día/mes/año
    dtype={
        'Programa': 'int',
        'Nombre': 'str',
        'Activación': 'int',
        'Duración': 'str',       # Lo convertiremos después a timedelta
        'Agua m³': 'float',
        'Abono 1 L': 'float',
        'Abono 2 L': 'float',
        'Abono 3 L': 'float',
        'Abono 4 L': 'float',
        'Tipo': 'str',
        'Sectores de Riego': 'int'
    }
)

# Convertir la columna 'Duración' a timedelta
df_riego['Duración'] = pd.to_timedelta(df_riego['Duración'])
# Eliminar columna nombre, ya que indica lo mismo que la columna programa, pero en un formato mas complicado de procesar
df_riego.drop('Nombre', axis=1, inplace=True)


"""
    El objetivo es juntar todos los datos de entrenamiento (X), los cuales estan en los DF: df_datos_suelo1, df_datos_suelo2, df_clima.

    df_datos_suelo1 y df_datos_suelo2 son mediciones de sensores sobre diferentes arboles que se encuentran en la misma finca, las mediciones 
    son similares, sin embargo, diferentes ligeramente. Crearemos dos conjuntos de datos de entrenamiento, uno con df_datos_suelo1 y df_clima y
    otro con df_datos_suelo2 y df_clima. 
"""
X_datos_suelo1 = pd.merge(df_datos_suelo1, df_clima)
X_datos_suelo2 = pd.merge(df_datos_suelo2, df_clima)