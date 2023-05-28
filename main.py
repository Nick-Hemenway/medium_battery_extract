from pathlib import Path
import models as mdl
from discharge_data import DischargeData
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

try:
    plt.style.use("emarine")
except:
    pass

#################   read in discharge data   #################

d = DischargeData(Path('inputs/cell_data.xlsx'), nominal_capacity_Ah=2.2,
                  dod_lower=0.01, dod_upper=1)

#plot raw discharge curves
figsize=(6,5)
fig, ax = d.plot(figsize=figsize)
# fig.savefig("processed_data/raw_data.png")
# fig.savefig("processed_data/raw_data.svg")
# fig.savefig("processed_data/raw_data.pdf")

#################   non parametric model   #################

n = mdl.NonParametric(d) #create non-parametric model with discharge data
fig, ax = mdl.plot_params(n, figsize=figsize)
# fig.savefig("processed_data/model_params_non_parametric.png")
# fig.savefig("processed_data/model_params_non_parametric.svg")
# fig.savefig("processed_data/model_params_non_parametric.pdf")

fig, ax = mdl.plot_model_fit(n, figsize=figsize)
# fig.savefig('processed_data/model_fit_non_parametric.png')
# fig.savefig('processed_data/model_fit_non_parametric.svg')
# fig.savefig('processed_data/model_fit_non_parametric.pdf')

#################   polynomial model   #################

p = mdl.PolynomialFit(data=d) #create polynomial model with discharge data
p.fit_model(Ne=7, Nr=3)

fig, ax = mdl.plot_params(p, figsize=figsize)
# fig.savefig('processed_data/model_params.png')
# fig.savefig('processed_data/model_params.svg')
# fig.savefig('processed_data/model_params.pdf')

fig, ax = mdl.plot_model_fit(p, figsize=figsize)
# fig.savefig('processed_data/model_fit.png')
# fig.savefig('processed_data/model_fit.svg')
# fig.savefig('processed_data/model_fit.pdf')

#################   output circuit params from polynomial model   #################

#compute circuit parameters over range of DoD(SoC) and output to csv file
dod = np.linspace(0,1,100)
soc = 1 - dod
Rs = p.Rs(dod)
OCV = p.OCV(dod)

df = pd.DataFrame({'soc':soc, 'OCV':OCV, 'Rs':Rs}).set_index('soc').sort_index()
# df.to_csv("processed_data/LG-M50_cell_params.csv")
