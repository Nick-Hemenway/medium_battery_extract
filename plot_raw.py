import pandas as pd
import matplotlib.pyplot as plt
import openpyxl

plt.style.use('bmh')

f = 'inputs/cell_data.xlsx'

wb = openpyxl.load_workbook(f)
sheets = wb.sheetnames

fig, ax = plt.subplots()
ax.set_xlabel('DoD [-]')
ax.set_ylabel('Voltage [V]')

for sheet in sheets:
    df = pd.read_excel(f, sheet_name=sheet, index_col=0)
    ax.plot(df, label=f"{sheet.split()[-1]} C")
    
ax.legend(facecolor='white')
fig.tight_layout()

fig.savefig('outputs/fake_spec_sheet_data_plot.png')


