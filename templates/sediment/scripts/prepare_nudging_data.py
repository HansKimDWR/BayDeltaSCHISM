#!/usr/bin/env python
# -*- coding: utf-8 -*-import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
from dms_datastore.read_ts import *
from dms_datastore.dstore_config import *
from schimpy.unit_conversions import *
from vtools.data.vtime import days
import glob
import os

station_df=station_dbase()
stations = ['anh','benbr','hsl','bts','snc','cyg','hun','bdl','fmb','msl','cll','gzl','ryc','hon',
            'c24','pct','flt','mrz','pct','mal','pts','carqb','benbr',
            'co5','ssi','emm','sdi','jer','sjj',
            'dsj','frp','fal','hll','frk','mdm',
            'dbi','oh4','pri','ppt','rindg','sjc','sjg',
            'dvi','sjr','pdup','tpp','uni',
            'trp','clc','vcu','rri2','mdmzq','sdc','ges','swe','gss',
            'nmr','sss','sut','snod','gln','rye','ryf','rvb','dws','lib','ucs','has',
            'srh','awb','afo','hst','ist','ssw','von','few','fre','wlk','god','sal']


add_upper = ["anh","cll","mrz","emm","mal","pts"]
t0 = pd.Timestamp(2015,11,18)
nudgelen =days(30)

station_df = station_df.loc[stations]

repo = "//nasbdo/modeling_data/continuous_station_repo_beta/formatted_1yr/"
no_such_file = []
tndx = pd.date_range(t0,t0+nudgelen,freq='H')
all_vars = ["temperature","salinity"]
used_stations = set()
nudging_dfs = {}
accepted_loc= [] 
for label_var in all_vars:
    var = {"temperature":"temp","salinity":"ec"}[label_var] # working variable for data
    print(f"Working on variable: {label_var},{var}")
    vals = []
    accepted = {}

    for ndx,row in station_df.iterrows():
        x = row.x
        y = row.y
        fndx = ndx+"@upper" if ndx in add_upper else ndx
        
        pat = f"*_{fndx}_*_{var}*_20??.csv"
        pat = os.path.join(repo,pat)
        matches = glob.glob(pat)
        if len(matches) == 0:
            no_such_file.append((ndx,var))
            continue
        try:
            ts = read_ts(pat)
            ts = ts.interpolate(limit=4)
            if ts.shape[1] >1:
                ts=ts.mean(axis=1)
                ts.name="value"
            else:
                ts = ts.squeeze()
            if var == "temp":
                if (ts > 35).any(axis=None):            
                    print("Transforming F to C")
                    ts = fahrenheit_to_celsius(ts)
            elif var == "ec":
                ts = ec_psu_25c(ts)
            else:
                raise ValueError(f"Haven't worked out transforms needed except for {var}, only salt/temp")
            
           
            val = ts.at[t0]
            if not np.isnan(val): 
                vals.append((ndx,x,y,val))
                
            # This is the fraction of missing data
            ts = ts.reindex(tndx)
            gap_frac = ts.isnull().sum()/len(ts)
            print(f"Fraction of mssing data for {ndx} {var} is {gap_frac}")                
            if gap_frac < 0.25:
                print(f"Accepted {ndx} {var}")
                ts.columns=[ndx]
                ts = ts.fillna(-9999.)
                accepted[ndx]=ts
                if ndx not in used_stations:
                    accepted_loc.append((ndx,x,y))
                    used_stations.add(ndx)
            
                       
        except Exception as err:
            print("Exception")
            print(str(err))
            print(ndx,var)
            print(ts.iloc[0:5])
            print(err)
    var_df = pd.DataFrame(data = vals,columns=("station","x","y",f"{label_var}"))
    var_df.set_index("station")
    var_df.to_csv(f"hotstart_data_{label_var}.csv",sep=",",float_format="%.2f")
  
    nudging_df = pd.concat(accepted,axis=1)
    nudging_df.index.name='datetime'
    nudging_dfs[label_var] = nudging_df
    print(nudging_df)

obs_xy = pd.DataFrame(data=accepted_loc,columns=["site","x","y"])
print("reindexing and printing")

for label_var in all_vars:
    nudging_dfs[label_var].to_csv(f"nudging_data_{label_var}.csv",sep=",",float_format="%.2f")
#    nudging_dfs[label_var].reindex(columns=obs_xy.site).to_csv(f"nudging_data_{label_var}_b.csv",sep=",",float_format="%.2f")


obs_xy = obs_xy.set_index("site",drop=True)
obs_xy.to_csv(f"obs_xy.csv",sep=",",float_format="%.2f")

print("No such file")
for item in no_such_file:
    print(item)
    
