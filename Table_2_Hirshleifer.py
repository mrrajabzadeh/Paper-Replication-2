"""
Created on Wed Apr 12 16:56:53 2023
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

#*******************************MONTHLY-LEVEL VARIABLES***************************

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


#***********************************************************************************
#********************************** REThigh & RETlow *******************************
#***********************************************************************************

#REThigh and Retlow based on definition 
JMmean = crspm[crspm['month'].isin([1, 3])].groupby(['permno', 'year']).mean()
SOmean = crspm[crspm['month'].isin([9, 10])].groupby(['permno', 'year']).mean()
JMmean= JMmean.rename(columns={'mthret':'Rethigh'})
SOmean= SOmean.rename(columns={'mthret':'Retlow'})

#merge REThigh and Retlow
high_low = pd.merge(JMmean, SOmean, how='outer', on=['permno','year'])

#************************ Cogruent-mood recurrence, lag (1) ************************
#lag1
high_low = high_low.sort_values(by=['permno','year'])
high_low['lagged_Rethigh'] = high_low.groupby('permno')['Rethigh'].shift(1)
high_low['lagged_Retlow'] = high_low.groupby('permno')['Retlow'].shift(1)
high_low=high_low.reset_index()
high_low = high_low.sort_values(by=['permno', 'year'])

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg1 = high_low[['permno','year','Rethigh', 'lagged_Rethigh']]
suffix1 = "1"
reg1['year'] = reg1['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg2 = high_low[['permno','year','Retlow', 'lagged_Retlow']]
suffix2 = "2"
reg2['year'] = reg2['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg1= reg1.rename(columns={'Rethigh':'y','lagged_Rethigh':'x'})
reg2= reg2.rename(columns={'Retlow':'y','lagged_Retlow':'x'})
reg= reg1.append(reg2)
reg = reg.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg['year'] = reg['year'].astype(int)
reg=reg.set_index(['permno', 'year'],drop=False)
y = reg['y']
x = sm.add_constant(reg['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)

#************************ Noncogruent-mood reversal, lag (1) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg3 = high_low[['permno','year','Rethigh', 'lagged_Retlow']]
reg3['year'] = reg3['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg4 = high_low[['permno','year','Retlow', 'lagged_Rethigh']]
reg4['year'] = reg4['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg3= reg3.rename(columns={'Rethigh':'y','lagged_Retlow':'x'})
reg4= reg4.rename(columns={'Retlow':'y','lagged_Rethigh':'x'})
reg_revers= reg3.append(reg4)
reg_revers = reg_revers.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg_revers['year'] = reg_revers['year'].astype(int)
reg_revers=reg_revers.set_index(['permno', 'year'])
y = reg_revers['y']
x = sm.add_constant(reg_revers['x'])
fm = FamaMacBeth(y, x)
res_noc = fm.fit(cov_type='kernel')
print(res_noc)

#************************ Cogruent-mood recurrence, lag (2-5) ****************************
#define the lag values
lags25 = [2, 3, 4, 5]

#averaged across the designated lags(2-5) before used in the regression
shifted_values = [high_low.groupby('permno')['Rethigh'].shift(lag) for lag in lags25]
lagged_Rethigh25 = np.nanmean(np.vstack(shifted_values), axis=0)

#add 'lagged_Rethigh25' column to 'high_low' DataFrame
high_low['lagged_Rethigh25'] = lagged_Rethigh25

#averaged across the designated lags(2-5) before used in the regression
shifted_values = [high_low.groupby('permno')['Retlow'].shift(lag) for lag in lags25]
lagged_Retlow25 = np.nanmean(np.vstack(shifted_values), axis=0)

#add 'lagged_Retlow25' column to 'high_low' DataFrame
high_low['lagged_Retlow25'] = lagged_Retlow25

#reset indexes in high_low df
high_low=high_low.reset_index()
high_low = high_low.sort_values(by=['permno', 'year'])

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg5 = high_low[['permno','year','Rethigh', 'lagged_Rethigh25']]
reg5['year'] = reg5['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg6 = high_low[['permno','year','Retlow', 'lagged_Retlow25']]
reg6['year'] = reg6['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg5= reg5.rename(columns={'Rethigh':'y','lagged_Rethigh25':'x'})
reg6= reg6.rename(columns={'Retlow':'y','lagged_Retlow25':'x'})
reg25= reg5.append(reg6)
reg25 = reg25.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg25['year'] = reg25['year'].astype(int)
reg25=reg25.set_index(['permno', 'year'])
y = reg25['y']
x = sm.add_constant(reg25['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)

#************************ Noncogruent-mood reversal, lag (2-5) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg7 = high_low[['permno','year','Rethigh', 'lagged_Retlow25']]
reg7['year'] = reg7['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg8 = high_low[['permno','year','Retlow', 'lagged_Rethigh25']]
reg8['year'] = reg8['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg7= reg7.rename(columns={'Rethigh':'y','lagged_Retlow25':'x'})
reg8= reg8.rename(columns={'Retlow':'y','lagged_Rethigh25':'x'})
reg_revers25= reg7.append(reg8)
reg_revers25 = reg_revers25.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg_revers25['year'] = reg_revers25['year'].astype(int)
reg_revers25=reg_revers25.set_index(['permno', 'year'])
y = reg_revers25['y']
x = sm.add_constant(reg_revers25['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)


#************************ Cogruent-mood recurrence, lag (6-10) ****************************

#averaged across the designated lags(6-10) before used in the regression
lags610 = [6, 7, 8, 9, 10]
shifted_values = [high_low.groupby('permno')['Retlow'].shift(lag) for lag in lags610]
lagged_Retlow610 = np.nanmean(np.vstack(shifted_values), axis=0)
high_low['lagged_Retlow610'] = lagged_Retlow610
shifted_values = [high_low.groupby('permno')['Rethigh'].shift(lag) for lag in lags610]
lagged_Rethigh610 = np.nanmean(np.vstack(shifted_values), axis=0)
high_low['lagged_Rethigh610'] = lagged_Rethigh610

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg9 = high_low[['permno','year','Rethigh', 'lagged_Rethigh610']]
reg9['year'] = reg9['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg10 = high_low[['permno','year','Retlow', 'lagged_Retlow610']]
reg10['year'] = reg10['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg9= reg9.rename(columns={'Rethigh':'y','lagged_Rethigh610':'x'})
reg10= reg10.rename(columns={'Retlow':'y','lagged_Retlow610':'x'})
reg610= reg9.append(reg10)
reg610 = reg610.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg610['year'] = reg610['year'].astype(int)
reg610=reg610.set_index(['permno', 'year'])
y = reg610['y']
x = sm.add_constant(reg610['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)


#************************ Noncogruent-mood reversal, lag (6-10) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
reg11 = high_low[['permno','year','Rethigh', 'lagged_Retlow610']]
reg11['year'] = reg11['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
reg12 = high_low[['permno','year','Retlow', 'lagged_Rethigh610']]
reg12['year'] = reg12['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
reg11= reg11.rename(columns={'Rethigh':'y','lagged_Retlow610':'x'})
reg12= reg12.rename(columns={'Retlow':'y','lagged_Rethigh610':'x'})
reg_revers610= reg11.append(reg12)
reg_revers610 = reg_revers610.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg_revers610['year'] = reg_revers610['year'].astype(int)
reg_revers610=reg_revers610.set_index(['permno', 'year'])
y = reg_revers610['y']
x = sm.add_constant(reg_revers610['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)



#***************************************************************************************
#********************************** RETRhigh & RETRlow *********************************
#***************************************************************************************

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


#RETRhigh and RetRlow based on definition 
Rhigh = top_crspm_filtered.groupby(['permno','year']).mean()
Rlow = bottom_crspm_filtered.groupby(['permno','year']).mean()
Rhigh= Rhigh.rename(columns={'mthret':'Rethigh'})
Rlow= Rlow.rename(columns={'mthret':'Retlow'})

#merge RETRhigh and RetRlow
high_lowR = pd.merge(Rhigh, Rlow, how='outer', on=['permno','year'])

#************************ Cogruent-mood recurrence, lag (1) ****************************

#lag1
high_lowR = high_lowR.sort_values(by=['permno','year'])
high_lowR['lagged_Rethigh'] = high_lowR.groupby('permno')['Rethigh'].shift(1)
high_lowR['lagged_Retlow'] = high_lowR.groupby('permno')['Retlow'].shift(1)
high_lowR=high_lowR.reset_index()
high_lowR = high_lowR.sort_values(by=['permno', 'year'])

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR1 = high_lowR[['permno','year', 'lagged_Rethigh']]
regR1 = pd.merge(regR1, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
suffix1 = "1"
regR1['year'] = regR1['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR2 = high_lowR[['permno','year', 'lagged_Retlow']]
regR2 = pd.merge(regR2, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
suffix2 = "2"
regR2['year'] = regR2['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR1= regR1.rename(columns={'Rethigh':'y','lagged_Rethigh':'x'})
regR2= regR2.rename(columns={'Retlow':'y','lagged_Retlow':'x'})
regR= regR1.append(regR2)
regR = regR.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
regR['year'] = regR['year'].astype(int)
regR=regR.set_index(['permno', 'year'])
y = regR['y']
x = sm.add_constant(regR['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)

#************************ Noncogruent-mood reversal, lag (1) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR3 = high_lowR[['permno','year', 'lagged_Retlow']]
regR3 = pd.merge(regR3, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
suffix1 = "1"
regR3['year'] = regR3['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR4 = high_lowR[['permno','year', 'lagged_Rethigh']]
regR4 = pd.merge(regR4, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
suffix2 = "2"
regR4['year'] = regR4['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR3= regR3.rename(columns={'Rethigh':'y','lagged_Retlow':'x'})
regR4= regR4.rename(columns={'Retlow':'y','lagged_Rethigh':'x'})
reg_reversR= regR3.append(regR4)
reg_reversR = reg_reversR.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
reg_reversR['year'] = reg_reversR['year'].astype(int)
reg_reversR=reg_reversR.set_index(['permno', 'year'])
y = reg_reversR['y']
x = sm.add_constant(reg_reversR['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)

#************************ Cogruent-mood recurrence, lag (2-5) ****************************

#averaged across the designated lags(2-5) before used in the regression
shifted_values = [high_lowR.groupby('permno')['Rethigh'].shift(lag) for lag in lags25]
lagged_Rethigh25R = np.nanmean(np.vstack(shifted_values), axis=0)
high_lowR['lagged_Rethigh25'] = lagged_Rethigh25R

shifted_values = [high_lowR.groupby('permno')['Retlow'].shift(lag) for lag in lags25]
lagged_Retlow25R = np.nanmean(np.vstack(shifted_values), axis=0)
high_lowR['lagged_Retlow25'] = lagged_Retlow25R


high_lowR=high_lowR.reset_index()
high_lowR = high_lowR.sort_values(by=['permno', 'year'])

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR5 = high_lowR[['permno','year', 'lagged_Rethigh25']]
regR5 = pd.merge(regR5, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
regR5['year'] = regR5['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR6 = high_lowR[['permno','year', 'lagged_Retlow25']]
regR6 = pd.merge(regR6, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
regR6['year'] = regR6['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR5= regR5.rename(columns={'Rethigh':'y','lagged_Rethigh25':'x'})
regR6= regR6.rename(columns={'Retlow':'y','lagged_Retlow25':'x'})
regR25= regR5.append(regR6)
regR25 = regR25.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
regR25['year'] = regR25['year'].astype(int)
regR25=regR25.set_index(['permno', 'year'])
y = regR25['y']
x = sm.add_constant(regR25['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)


#************************ Noncogruent-mood reversal, lag (2-5) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR7 = high_lowR[['permno','year', 'lagged_Retlow25']]
regR7 = pd.merge(regR7, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
regR7['year'] = regR7['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR8 = high_lowR[['permno','year', 'lagged_Rethigh25']]
regR8 = pd.merge(regR8, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
regR8['year'] = regR8['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR7= regR7.rename(columns={'Rethigh':'y','lagged_Retlow25':'x'})
regR8= regR8.rename(columns={'Retlow':'y','lagged_Rethigh25':'x'})
regR_reverse25= regR7.append(regR8)
regR_reverse25 = regR_reverse25.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
regR_reverse25['year'] = regR_reverse25['year'].astype(int)
regR_reverse25=regR_reverse25.set_index(['permno', 'year'])
y = regR_reverse25['y']
x = sm.add_constant(regR_reverse25['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)

#************************ Cogruent-mood recurrence, lag (6-10) ****************************

#averaged across the designated lags(6-10) before used in the regression
shifted_values = [high_lowR.groupby('permno')['Rethigh'].shift(lag) for lag in lags610]
lagged_Rethigh610R = np.nanmean(np.vstack(shifted_values), axis=0)
high_lowR['lagged_Rethigh610'] = lagged_Rethigh610R

shifted_values = [high_lowR.groupby('permno')['Retlow'].shift(lag) for lag in lags610]
lagged_Retlow610R = np.nanmean(np.vstack(shifted_values), axis=0)
high_lowR['lagged_Retlow610'] = lagged_Retlow610R

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR9 = high_lowR[['permno','year', 'lagged_Rethigh610']]
regR9 = pd.merge(regR9, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
regR9['year'] = regR9['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR10 = high_lowR[['permno','year', 'lagged_Retlow610']]
regR10 = pd.merge(regR10, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
regR10['year'] = regR10['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR9= regR9.rename(columns={'Rethigh':'y','lagged_Rethigh610':'x'})
regR10= regR10.rename(columns={'Retlow':'y','lagged_Retlow610':'x'})
regR610= regR9.append(regR10)
regR610 = regR610.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
regR610['year'] = regR610['year'].astype(int)
regR610=regR610.set_index(['permno', 'year'])
y = regR610['y']
x = sm.add_constant(regR610['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)


#************************ Noncogruent-mood reversal, lag (6-10) ****************************

#add suffix "1" at the end of "year" variable as a reperesentetive of REThigh
regR11 = high_lowR[['permno','year', 'lagged_Retlow610']]
regR11 = pd.merge(regR11, high_low[['Rethigh','permno','year']], how='left', on=['permno','year'])
regR11['year'] = regR11['year'].astype(str).apply(lambda x: x + suffix1)

#add suffix "2" at the end of "year" variable as a reperesentetive of RETlow
regR12 = high_lowR[['permno','year','lagged_Rethigh610']]
regR12 = pd.merge(regR12, high_low[['Retlow','permno','year']], how='left', on=['permno','year'])
regR12['year'] = regR12['year'].astype(str).apply(lambda x: x + suffix2)

#append two cunstructed dataframe
regR11= regR11.rename(columns={'Rethigh':'y','lagged_Retlow610':'x'})
regR12= regR12.rename(columns={'Retlow':'y','lagged_Rethigh610':'x'})
regR_reverse610= regR11.append(regR12)
regR_reverse610 = regR_reverse610.sort_values(by=['permno', 'year'])

#FamaMacBeth regression; adding constant to independent variable
regR_reverse610['year'] = regR_reverse610['year'].astype(int)
regR_reverse610=regR_reverse610.set_index(['permno', 'year'])
y = regR_reverse610['y']
x = sm.add_constant(regR_reverse610['x'])
fm = FamaMacBeth(y, x)
res = fm.fit(cov_type='kernel')
print(res)









































