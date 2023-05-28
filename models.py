import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
from scipy.interpolate import interp1d
from discharge_data import DischargeData
import abc

class ModelBase(abc.ABC):
    """abstract base class defining the methods that each model must have"""
    
    @abc.abstractmethod
    def OCV(self, dod):
        pass
    
    @abc.abstractmethod
    def Rs(self, dod):
        pass
    
    @abc.abstractmethod
    def modeled_terminal_voltage(self, dod, c_rate):
        pass

class NonParametric(ModelBase):
    
    def __init__(self, data:DischargeData):
        
        self.data = data #stores DischargeData object
        
        #extract vector of all discharge c_rates
        self.c_rates = self.data.data['C-rate'].unique()
        #extract vector of currents corresponding to c_rate
        self.x = self.c_rates*(self.data.nominal_capacity_mAh/1000)
        
    def _get_y(self, dod):
        """interpolates voltage for each discharge curve at specified DoD and stacks
        them into a vector"""
        
        y = [self._get_v_terminal(dod, c_rate) for c_rate in self.c_rates]
        return np.array(y)
        
    def _get_v_terminal(self, dod, c_rate):
        """interpolates raw voltage data at specific c_rate and specified DoD"""
        
        df = self.data.data_cropped[self.data.data_cropped['C-rate']==c_rate]
        f = interp1d(df['DoD'], df['V'], fill_value='extrapolate')
        
        return f(dod)
    
    def _get_params(self, dod):
        """get ocv and rs for single value of dod by fitting line to data"""    
        y = self._get_y(dod)
        p = np.polyfit(self.x, y, deg=1)
        rs, ocv = p
        return -rs, ocv
    
    def OCV(self, dod):
        """compute OCV at given dod"""
        return self._get_params(dod)[1]
    
    def Rs(self, dod):
        """compute rs at given dod"""
        return self._get_params(dod)[0]
    
    def modeled_terminal_voltage(self, dod, c_rate):
        """computes modeled voltage at given dod and discharge rate"""
        return self.OCV(dod) - c_rate*(self.data.nominal_capacity_mAh/1000)*self.Rs(dod)
        
class PolynomialFit(ModelBase):
    
    def __init__(self, data:DischargeData):
        
        self.data = data  #store discharge data as attribute
        
        #create multi-variate linear regression model
        self.reg_model = linear_model.LinearRegression(fit_intercept=True)
    
    def get_X(self, Ne=9, Nr=9):
        """constructs feature matrix X for performing linear regression"""
        
        X = pd.DataFrame()

        for i in range(1, Ne+1):
            X[f'D^{i}'] = (self.data.data_cropped['DoD'])**i
            
        for i in range(Nr+1):
            X[f'-ID^{i}'] = -self.data.data_cropped['I [A]']*(self.data.data_cropped['DoD'])**i
            
        return X
    
    def fit_model(self, Ne=9, Nr=9):
        """fits polynomial model of given degree and extracts the fit coefficients
        into an attribute w_vec"""        
        self.Ne = Ne
        self.Nr = Nr
        self.reg_model.fit(self.get_X(Ne, Nr), y=self.data.data_cropped['V'])
        w_vec = [self.reg_model.intercept_]
        w_vec.extend(self.reg_model.coef_)
        self.w_vec = np.array(w_vec)
        
    def alpha_coeff(self):
        """extracts coefficients from w_vec that correspond to E_0"""
        return self.w_vec[0:self.Ne+1]        
    
    def beta_coeff(self):
        """extracts coefficients from w_vec that correspond to R_s"""
        return self.w_vec[self.Ne+1::]        
        
    def OCV(self, dod):
        #we must reverse the order of the array because numpy expects the
        #polynomial to start at the highest degree
        return np.polyval(self.alpha_coeff()[-1::-1], dod)
    
    def Rs(self, dod):
        #we must reverse the order of the array because numpy expects the
        #polynomial to start at the highest degree
        return np.polyval(self.beta_coeff()[-1::-1], dod)
    
    def modeled_terminal_voltage(self, dod, c_rate):
        """computes modeled voltage at given dod and discharge rate"""
        return self.OCV(dod) - c_rate*(self.data.nominal_capacity_mAh/1000)*self.Rs(dod)
    
    
def plot_model_fit(model, **kwargs):
    
    """convenience function that takes in model and plots it's fit over experimental data"""
    
    fig, ax = model.data.plot_raw_data(**kwargs)
    ax.set_prop_cycle(None)
    
    dod = np.linspace(0, 1, 50)
    for c_rate in model.data.df['C-rate'].unique():
        v_modeled = model.modeled_terminal_voltage(dod, c_rate=c_rate)
        ax.plot(dod, v_modeled, ls='', marker='x', label='Modeled')
    
    fig.tight_layout()
    
    return fig, ax
        
def plot_params(model, **kwargs):
    
    """convenience function that takes in model and plots the circuit parameters"""
    
    fig, ax = plt.subplots(**kwargs)
    ax1 = ax.twinx()
    dod = np.linspace(0,1,100)
    ocv = model.OCV(dod)
    Rs = model.Rs(dod)
    ax1.grid(False)
    ax.plot(dod, ocv)
    ax1.plot(dod, Rs, color='C1')
    ax1.set_ylabel('Internal Resistance [$\Omega$]', color='C1')
    ax.set_ylabel('OCV [V]', color='C0')
    ax.set_xlabel('DoD')
    ax1.tick_params(labelcolor='C1')
    ax.tick_params(axis='y', labelcolor='C0')
    fig.tight_layout()
    
    return fig, ax