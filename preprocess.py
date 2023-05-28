from pathlib import Path
import pandas as pd

p = Path('inputs')

with pd.ExcelWriter(p/'cell_data.xlsx') as w:
    for f in p.iterdir():
        if 'C.csv' in f.name:
            c_rate = float(f.stem[0:-1])
            df = pd.read_csv(f, names=['DoD', 'Voltage']).set_index('DoD')
            df = df.sort_index()
            df.to_excel(w, sheet_name=f"c_rate {c_rate}")