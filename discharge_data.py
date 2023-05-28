from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
import matplotlib.pyplot as plt
from typing import Optional, Union

class DischargeData():
    
    def __init__(self, file: Union[Path, str], scale_factor: Optional[float]=None,
                 dod_lower: float=0, dod_upper: float=1):
        """initialize the discharge data

        Parameters
        ----------
        file : Union[Path, str]
            File path to excel spreadsheet containing discharge data. Excel file should
            contain multiple sheets with name format like "c_rate 0.5". Each sheet should 
            contain two columns -- one for discharge capacity or depth of discharge (dod) 
            data and one for the terminal voltage of the cell
            
        scale_factor : Optional[float], optional
            Scale factor by which to scale the x-data to normalize it to DoD data. e.g.
            this would be the nominal capacity of the cell in Ah or mAh. If None, the
            data is assumed to already be DoD data and is not scaled. Data is scaled as:
            scaled_x_data = x_data/scale_factor. By default None 
            
        dod_lower: float
            lower limit for cropping depth of discharge data for model extraction
            
        dod_upper: float
            upper limit for cropping depth of discharge data for model extraction
        """
        
                
        self._data: pd.DataFrame #specify type of _data attribute
        self.load_data(file=file, scale_factor=scale_factor) #load data into _data attribute

        self.dod_lower = dod_lower
        self.dod_upper = dod_upper
        
    def load_data(self, file: Union[Path, str], scale_factor: Optional[float]=None) -> None:
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
            #the spreadsheet must have a first row of capacity in mAh and the second column of voltage
            df = pd.read_excel(file, sheet_name=sheet, names=['DoD', 'V'])
            if scale_factor is not None:
                df['DoD'] /= scale_factor #normalize data to DoD if scale factor is provided
            
            #add additional computed columns to the dataframe
            df['C-rate'] = c_rate
            df['SoC'] = 1 - df['DoD']
            
            dfs.append(df)
            
        #combine all of the dataframes into a single dataframe and return
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
        
    def plot(self, **kwargs) -> tuple:
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
        
        return self._plot(self.data, **kwargs)
    
    def plot_cropped(self, **kwargs) -> tuple:
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
    
        return self._plot(self.data_cropped)
    
    def _plot(self, data, **kwargs) -> tuple:
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
        
        fig, ax = plt.subplots(**kwargs)
        for (c_rate, df) in data.groupby('C-rate'):
            ax.plot(df['DoD'], df['V'], label=f'{c_rate} C')
        
        ax.set_xlabel('DoD [-]')
        ax.set_ylabel('Terminal Voltage [V]')
        ax.legend()
        
        fig.tight_layout()
    
        return fig, ax
    
