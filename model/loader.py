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

df_datos_suelo2 = pd.read_csv(
    'data/Mini2_OUT.csv',
    sep=';',                    # Delimitador de columnas
    decimal=',',                # Separador decimal
    encoding='latin1',          # Codificación para caracteres especiales (Õ, Û, Ì, etc.)
    parse_dates=['date'],       # Convertir columna de fecha a datetime
    dayfirst=True  
)


df_riego = pd.read_csv(
    'data/RIEGOS ALMENDRO2024.csv',
    sep=';',                      # Delimitador de punto y coma
    decimal=',',                  # Usa coma como separador decimal
    thousands=None,               # No hay separador de miles
    parse_dates=['Inicio', 'Fin'], # Convierte estas columnas a datetime
    dayfirst=True,                # Formato de fecha día/mes/año
    dtype={
        'Activación': 'int',
        'Duración': 'str',       # Lo convertiremos después a timedelta
        'Agua m³': 'float',
        'Tipo': 'str',
        'Sectores de Riego': 'int'
    }
)



# Convertir la columna 'Duración' a timedelta
df_riego['Duración'] = pd.to_timedelta(df_riego['Duración'])

"""
    Eliminamos columna nombre y programa, ya que indican lo mismo que la columna sector, pero en un formato mas complicado de procesar o se repite
    Eliminamos Abono XL, porque no vamos a tener en cuenta esta variabble en nuestro estudiol
"""
df_riego.drop(columns=['Programa', 'Nombre', 'Abono 1 L', 'Abono 2 L', 'Abono 3 L', 'Abono 4 L'], inplace=True)

# Eliminamos hora de la fecha, ya que por la granularidad que vamos usar a la hora de analizar los datos, es irrelevante
df_riego['Inicio'] = df_riego['Inicio'].dt.normalize()  
df_riego['Fin'] = df_riego['Fin'].dt.normalize()  

"""
    El objetivo es juntar todos los datos de entrenamiento (X), los cuales estan en los DF: df_datos_suelo1, df_datos_suelo2, df_clima.

    df_datos_suelo1 y df_datos_suelo2 son mediciones de sensores sobre diferentes arboles que se encuentran en la misma finca, las mediciones 
    son similares, sin embargo, diferentes ligeramente. Crearemos dos conjuntos de datos de entrenamiento, uno con df_datos_suelo1 y df_clima y
    otro con df_datos_suelo2 y df_clima. 
"""
X_datos_suelo1 = pd.merge(df_datos_suelo1, df_clima)
X_datos_suelo2 = pd.merge(df_datos_suelo2, df_clima)

# Lo convertimos a dateTime para poder usarlos en graficos 
X_datos_suelo1['date'] = pd.to_datetime(X_datos_suelo1['date'])
X_datos_suelo2['date'] = pd.to_datetime(X_datos_suelo2['date'])

