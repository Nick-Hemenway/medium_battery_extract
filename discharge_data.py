from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
import matplotlib.pyplot as plt
from typing import Optional, Union

class DischargeData():
    
    def __init__(self, file: Union[Path, str], nominal_capacity_Ah: float, scale_x: Optional[bool]=False,
                 dod_lower: float=0, dod_upper: float=1):
        """initialize the discharge data

        Parameters
        ----------
        file : Union[Path, str]
            File path to excel spreadsheet containing discharge data. Excel file should
            contain multiple sheets with name format of the form "c_rate 0.5". Each sheet should 
            contain two columns -- The first column can either be the discharge capacity in Ah
            or the depth of discharge (DoD). If it is in Ah, scale_x, must be set to True
            
        nominal_capacity_Ah: float
            Nominal cell capacity in Ah, used to scale C-rates to current values and 
            discharge capacity in Ah to DoD
            
        scale_x : Optional[bool], optional
            Whether to scale x-data (first column) in Excel spreadsheets. Set to True if Excel file contains
            discharge data in Ah, set to False if Excel file already contains DoD data. By default False
            
        dod_lower: float
            lower limit for cropping depth of discharge data for model extraction
            
        dod_upper: float
            upper limit for cropping depth of discharge data for model extraction
        """
        
        #specify data types for attributes set in "load_data" method
        self._data: pd.DataFrame
        self.nominal_capacity_Ah: float
        
        #load data from excel file
        self.load_data(file=file, nominal_capacity_Ah=nominal_capacity_Ah, scale_x=scale_x) #load data into _data attribute

        #store dod limits for cropped fit data
        self.dod_lower = dod_lower
        self.dod_upper = dod_upper
        
    def load_data(self, file: Union[Path, str], nominal_capacity_Ah: float, scale_x: Optional[bool]=False) -> None:
        """load excel file containing multiple sheets into single pandas DataFrame of long format

        Parameters
        ----------
        file : Path or str
            Path to Excel file containing discharge data

        Returns
        -------
        pd.DataFrame
            DataFrame containing all of the discharge curves in long format
        """
        
        #ensure that it is a Path object
        file = Path(file)
        self.nominal_capacity_Ah = nominal_capacity_Ah
        
        #first load the workbook and extract the sheetnames
        wb = load_workbook(filename=file)
        sheets = wb.sheetnames
        wb.close()
        
        #create empty list to dataframes for each excel sheet to
        dfs = []
        
        #loop over each sheet in the excel file
        for sheet in sheets:
            #extract c-rate from sheet name (this assumes sheets are named with convention "c_rate 1.2" or similar)
            c_rate = float(sheet.split()[-1])
            #load data into pandas dataframe (we are overwriting the column names specified in the spreadsheet)
            #the spreadsheet must have a first row of capacity in Ah or DoD and the second column of voltage
            df = pd.read_excel(file, sheet_name=sheet, names=['DoD', 'V'])
            if scale_x:
                df['DoD'] /= self.nominal_capacity_Ah #normalize data to DoD if provided in Ah
            
            #add additional computed columns to the dataframe
            df['C-rate'] = c_rate
            df['SoC'] = 1 - df['DoD']
            df['I [A]'] = df['C-rate']*self.nominal_capacity_Ah
            
            dfs.append(df)
            
        #combine all of the dataframes into a single dataframe
        self._data = pd.concat(dfs, ignore_index=True)
    
    @property
    def data(self) -> pd.DataFrame:
        return self._data

    @property
    def data_cropped(self) -> pd.DataFrame:
        """extract subset of all data in limited range of DoD

        Parameters
        ----------
        dod_lower : float
            lower bound of DoD to chop data for fitting
        dod_upper : float
            upper bound of DoD to chop data for fitting
        """
        return self.data[(self.data['DoD']>self.dod_lower) & (self.data['DoD']<self.dod_upper)].copy()
    
    
    def plot(self, cropped=False, **kwargs) -> tuple:
        """convenience function to plot the raw constant current discharge curves

        Parameters
        ----------
        kwargs : dict
            key word arguments to supply to the subplots command in matplotlib

        Returns
        -------
        tuple
            tuple containing the figure and axes objects created
        """
        
        if cropped:
            data = self.data_cropped
        else:
            data = self.data
        
        fig, ax = plt.subplots(**kwargs)
        for (c_rate, df) in data.groupby('C-rate'):
            ax.plot(df['DoD'], df['V'], label=f'{c_rate} C')
        
        ax.set_xlabel('DoD [-]')
        ax.set_ylabel('Terminal Voltage [V]')
        ax.legend()
        
        fig.tight_layout()
    
        return fig, ax
    
d = DischargeData('inputs/cell_data.xlsx', nominal_capacity_Ah=2.2)
d.plot(cropped=True)