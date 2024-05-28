"""
Created on Tue Apr 18 09:52:47 2023
@author: MohamadReza
"""
import pandas as pd
import numpy as np
import csv
import math
import wrds
import datetime as dt
from linearmodels.panel import FamaMacBeth
import statsmodels.api as sm

#Establishe a connection to the WRDS (Wharton Research Data Services) database using the wrds.Connection() method and assigns it to the variable db.
db=wrds.Connection()

#**************************************************************************************************************
#****************************WORKING WITH LIBRARIES AND TABLES IN WRDS*****************************************
#Lists all the available libraries in the connected database and sorts them alphabetically.
sorted(db.list_libraries())
# Lists all the available tables in the "crsp" library of the connected database.
db.list_tables(library="crsp")
#Provides a description of the "dsf" table in the "crsp" library of the connected database, including the column names, data types, and other properties.
db.describe_table(library="crsp", table="dsf")
crspd.head
#Displays the documentation for the get_table() method of the wrds.Connection object.
help(db.get_table)
#Retrieves the first 10 observations of the "gvkey" column from the "funda" table in the "comp" library of the connected database, and stores the result in the data variable.
data = db.get_table(library='comp', table='funda', columns=['gvkey'], obs=10)
data = db.get_table(library='crsp', table='dsf', columns=['ret', 'date'])

#**************************************************************************************************************
#***********************************MONTHLY-LEVEL VARIABLES****************************************************

#Extract data using SQL query
crspm = db.raw_sql("""
                      select a.permno, a.permco, a.mthcaldt, 
                      a.issuertype, a.securitytype, a.securitysubtype, a.sharetype, a.usincflg, 
                      a.primaryexch, a.conditionaltype, a.tradingstatusflg,
                      a.mthret, a.mthretx, a.shrout, a.mthprc
                      from crsp.msf_v2 as a
                      where a.mthcaldt between '01/01/1963' and '12/31/2016'
                      """, date_cols=['mthcaldt']) 

#Select common stock universe
crspm = crspm.loc[(crspm.sharetype=='NS') & \
                    (crspm.securitytype=='EQTY') & \
                    (crspm.securitysubtype=='COM') & \
                    (crspm.usincflg=='Y') & \
                    (crspm.issuertype.isin(['ACOR', 'CORP']))]

#Select stocks traded on NYSE, AMEX and NASDAQ
crspm = crspm.loc[(crspm.primaryexch.isin(['N', 'A', 'Q'])) & \
                   (crspm.conditionaltype =='RW') & \
                   (crspm.tradingstatusflg =='A')]
    
#Delete extra variables    
del crspm['issuertype']
del crspm['securitytype']
del crspm['securitysubtype']
del crspm['sharetype']
del crspm['usincflg']
del crspm['primaryexch']
del crspm['conditionaltype']
del crspm['tradingstatusflg']
del crspm['permco']

## Form Fama French Factors #
ff = db.get_table(library='ff', table='factors_monthly')

# Add new columns for year, month, and date information extracted from 'mthcaldt'
crspm['year']=crspm['mthcaldt'].dt.year
crspm['month']=crspm['mthcaldt'].dt.month
crspm['date']=crspm['mthcaldt'].dt.date

# Sort the DataFrame by 'permno' and 'mthcaldt', and drop any duplicate rows
crspm=crspm.sort_values(by=['permno','mthcaldt']).drop_duplicates()

# Rename the 'date' column to 'dateff' in the 'crspm' DataFrame based on the FF data
crspm= crspm.rename(columns={'date':'dateff'})

# Merge the 'crspm' and 'ff' DataFrames based on the 'dateff' column, adding 'rf' and 'mktrf' data to 'crspm'
crspm = pd.merge(crspm,ff[['dateff','rf','mktrf']], how='left', on='dateff')

#crspm['exret']=crspm['mthret']-crspm['rf']
#Compute mean, standard deviation, median, and percentiles of the data for January and March months
Rethigh_mean = crspm[crspm['month'].isin([1, 3])]['mthret'].mean()
Rethigh_sd = crspm[crspm['month'].isin([1, 3])]['mthret'].std()
Rethigh_median = crspm[crspm['month'].isin([1, 3])]['mthret'].median()
Rethigh_percentile = crspm[crspm['month'].isin([1, 3])]['mthret'].quantile([0.10,0.25,0.75,0.90])

#Compute mean, standard deviation, median, and percentiles of the data for September and October months
Retlow_mean = crspm[crspm['month'].isin([9, 10])]['mthret'].mean()
Retlow_sd = crspm[crspm['month'].isin([9, 10])]['mthret'].std()
Retlow_median = crspm[crspm['month'].isin([9, 10])]['mthret'].median()
Retlow_percentile = crspm[crspm['month'].isin([9, 10])]['mthret'].quantile([0.10,0.25,0.75,0.90])

#Compute mean, standard deviation, median, and percentiles of the data for January, March, September, and October (JMSO) months
Rethighlow_mean = crspm[crspm['month'].isin([1, 3,9,10])]['mthret'].mean()
Rethighlow_sd = crspm[crspm['month'].isin([1, 3,9,10])]['mthret'].std()
Rethighlow_median = crspm[crspm['month'].isin([1, 3,9,10])]['mthret'].median()
Rethighlow_percentile = crspm[crspm['month'].isin([1, 3,9,10])]['mthret'].quantile([0.10,0.25,0.75,0.90])

#Compute the average monthly return for each month and year
RetMean = crspm.groupby(['year', 'month'])['mthret'].mean()

#For each year, find the top two months with the highest average monthly returns
top_two_months_by_year = RetMean.groupby('year').apply(lambda x: x.nlargest(2))

#For each year, find the bottom two months with the lowest average monthly returns
bottom_two_months_by_year = RetMean.groupby('year').apply(lambda x: x.nsmallest(2))

#Reset the indices of the dataframe to create a new column for the year and drop the original year index
top_two_months_by_year = top_two_months_by_year.reset_index(level=[0, 2])
top_two_months_by_year = top_two_months_by_year.reset_index(level=0, drop=True)
bottom_two_months_by_year = bottom_two_months_by_year.reset_index(level=[0, 2])
bottom_two_months_by_year = bottom_two_months_by_year.reset_index(level=0, drop=True)

# Reset the index of the dataframe and select only the 'year' and 'month' columns
top_two_months_by_year = top_two_months_by_year.reset_index()[['year', 'month']]
bottom_two_months_by_year = bottom_two_months_by_year.reset_index()[['year', 'month']]

# Convert the dataframe to a list of tuples
top_selected_months = [(y, m) for y, m in top_two_months_by_year.to_records(index=False)]
bottom_selected_months = [(y, m) for y, m in bottom_two_months_by_year.to_records(index=False)]

# Create a boolean mask to select only rows where the 'year' and 'month' are in the list of top selected months
top_mask = crspm[['year', 'month']].apply(tuple, axis=1).isin(top_selected_months)
bottom_mask = crspm[['year', 'month']].apply(tuple, axis=1).isin(bottom_selected_months)

# Filter the original dataframe to select only the rows corresponding to the top selected months
top_crspm_filtered = crspm[top_mask]
bottom_crspm_filtered = crspm[bottom_mask]

# Compute the mean, sd, median and percentiles of the filtered dataframe (for the top selected months)
RetRhigh_mean = top_crspm_filtered['mthret'].mean()
RetRhigh_sd = top_crspm_filtered['mthret'].std()
RetRhigh_median = top_crspm_filtered['mthret'].median()
RetRhigh_percentile=top_crspm_filtered['mthret'].quantile([0.10,0.25,0.75,0.90])

# Compute the mean, sd, median and percentiles of the filtered dataframe (for the bottom selected months)
RetRlow_mean = bottom_crspm_filtered['mthret'].mean()
RetRlow_sd = bottom_crspm_filtered['mthret'].std()
RetRlow_median = bottom_crspm_filtered['mthret'].median()
RetRlow_percentile=bottom_crspm_filtered['mthret'].quantile([0.10,0.25,0.75,0.90])

# Combine masks to filter the original dataframe based on top and bottom months
top_bottom_mask = top_mask | bottom_mask
crspm_filtered = crspm[top_bottom_mask]

# Compute the mean, sd, median and percentiles of the filtered dataframe (for the top and bottom selected months)
RetRhighRlow_mean = crspm_filtered['mthret'].mean()
RetRhighRlow_sd = crspm_filtered['mthret'].std()
RetRhighRlow_median = crspm_filtered['mthret'].median()
RetRhighRlow_percentile=crspm_filtered['mthret'].quantile([0.10,0.25,0.75,0.90])








