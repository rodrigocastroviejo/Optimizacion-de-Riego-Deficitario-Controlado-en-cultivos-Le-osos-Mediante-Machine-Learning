import pandas as pd
from pathlib import Path

# Ruta base relativa al archivo actual
base_path = Path(__file__).resolve().parent / "data"

# Carpetas específicas
climate_path = base_path / "climate_data"
soil_path = base_path / "soil_data"
irrigation_path = base_path / "old_obsolete_data" / "RIEGOS ALMENDRO2024.csv"

soil_mini1_path = soil_path / "mini1"
soil_mini2_path = soil_path / "mini2"

# Cargar todos los Excel de clima
climate_files = sorted(climate_path.glob("*.xlsx"))
climate_dfs = [pd.read_excel(f, parse_dates=["Fecha"]) for f in climate_files]

# Cargar todos los Excel de suelo
soil_files = {
    "mini_1": list(sorted(soil_mini1_path.glob("*.xlsx"))), 
    "mini_2" : list(sorted(soil_mini2_path.glob("*.xlsx")))
}

soil_mini1_dfs = [pd.read_excel(f, parse_dates=["Fecha"]) for f in soil_files['mini_1']]
soil_mini2_dfs = [pd.read_excel(f, parse_dates=["Fecha"]) for f in soil_files['mini_2']]

# Concatenar todos los años
climate_data = pd.concat(climate_dfs, ignore_index=True)
soil_mini1_data = pd.concat(soil_mini1_dfs, ignore_index=True)
soil_mini2_data = pd.concat(soil_mini2_dfs, ignore_index=True)



