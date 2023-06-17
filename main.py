from pathlib import Path
import models as mdl
from discharge_data import DischargeData, DischargeVar
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

#set default plotting settings to personal preference
plt.style.use('seaborn-v0_8-darkgrid')
font_settings = {'family':'Times New Roman', 'size':12}
line_settings = {'lw':2}
plt.rc('font', **font_settings)
plt.rc('lines', **line_settings)

output_folder = Path('outputs')

#################   read in discharge data   #################

data_interface = DischargeData(Path('inputs/cell_data.xlsx'), nominal_capacity_Ah=2.2, x_axis=DischargeVar.DOD,
                  dod_lower=0.01, dod_upper=1)

#plot raw discharge curves
fig, ax = data_interface.plot()
fig.savefig(output_folder/"fit_data.png")

data_interface.dod_upper = 0.05
data_interface.dod_upper=0.9
fig, ax = data_interface.plot(cropped=True)
fig.savefig(output_folder/"fit_data_extreme_crop.png")

#################   polynomial model   #################

p = mdl.PolynomialFit(data=data_interface) #create polynomial model with discharge data
p.fit_model(Ne=7, Nr=3)

fig, ax = mdl.plot_params(p)
fig.savefig(output_folder/'model_params.png')

fig, ax = mdl.plot_model_fit(p)
fig.savefig(output_folder/'model_fit.png')

#################   output circuit params from polynomial model   #################

#compute circuit parameters over range of DoD(SoC) and output to csv file
dod = np.linspace(0,1,100)
soc = 1 - dod
Rs = p.Rs(dod)
OCV = p.OCV(dod)

df = pd.DataFrame({'soc':soc, 'OCV':OCV, 'Rs':Rs}).set_index('soc').sort_index()
df
