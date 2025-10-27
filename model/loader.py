import pandas as pd
from pathlib import Path

# Ruta base relativa al archivo actual
base_path = Path(__file__).resolve().parent / "data"

# Carpetas específicas
climate_path = base_path / "climate_data"
soil_path = base_path / "soil_data"
irrigation_path = base_path / "old_obsolete_data" / "RIEGOS ALMENDRO2024.csv"

# Cargar todos los Excel de clima
climate_files = sorted(climate_path.glob("*.xlsx"))
climate_dfs = [pd.read_excel(f) for f in climate_files]

# Cargar todos los Excel de suelo
soil_files = sorted(soil_path.glob("*.xlsx"))
soil_dfs = [pd.read_excel(f) for f in soil_files]

# Concatenar todos los años
climate_data = pd.concat(climate_dfs, ignore_index=True)
soil_data = pd.concat(soil_dfs, ignore_index=True)

print("Archivos de clima cargados:", len(climate_dfs))
print("Archivos de suelo cargados:", len(soil_dfs))
print("Clima:", climate_data.shape, "Suelo:", soil_data.shape)


df_riego = pd.read_csv(
    irrigation_path,
    sep=';',                      # Delimitador de punto y coma
    decimal=',',                  # Usa coma como separador decimal
    thousands=None,               # No hay separador de mile
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
df_riego.drop(columns=['Programa', 'Nombre', 'Abono 1 L', 'Abono 2 L', 'Abono 3 L', 'Abono 4 L', 'Tipo'], inplace=True)

# Eliminamos aquellas filas de riego que no pertenezcan a los sectores 1 y 3 ya que solo tenemos datos de suelo de esas zonas.
df_riego = df_riego[df_riego['Sectores de Riego'].isin([1, 3])]

# Lo convertimos a dateTime para poder usarlos en graficos 
#X_datos_suelo1['date'] = pd.to_datetime(X_datos_suelo1['date'])
#X_datos_suelo2['date'] = pd.to_datetime(X_datos_suelo2['date'])

