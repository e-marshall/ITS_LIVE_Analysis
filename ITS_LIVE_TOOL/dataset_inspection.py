# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_Data_inspection.ipynb.

# %% auto 0
__all__ = ['find_longterm_median_v', 'calc_min_tbaseline', 'trim_by_baseline']

# %% ../nbs/04_Data_inspection.ipynb 5
from . import datacube_tools, interactive, obj_setup

# %% ../nbs/04_Data_inspection.ipynb 6
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.interpolate import CubicSpline
import xarray as xr

# %% ../nbs/04_Data_inspection.ipynb 30
def find_longterm_median_v(ds):

    ds_long = ds.where(ds.img_separation >= 365, drop=True)

    med_v = ds_long.v.mean(dim=['x','y','time_numeric']).data
    return med_v, ds_long

# %% ../nbs/04_Data_inspection.ipynb 33
def calc_min_tbaseline(ds):

    med_v = find_longterm_median_v(ds)[0]
    gsd_l5, gsd_l7, gsd_s2, gsd_l8, gsd_s1, gsd_l9 = 30, 15, 10, 15, 10, 15
    name_ls = ['L5','L7', 'S2','L8','S1', 'L9']
    gsd_ls = [gsd_l5, gsd_l7, gsd_s2, gsd_l8, gsd_s1, gsd_l9]
    sensor_str_ls = ['5','7',['2A','2B'], '8',['1A','1B'],'9']
    min_tb_ls = []
    for element in range(len(gsd_ls)):
        min_tb = ((gsd_ls[element]*2)/med_v)*365
        min_tb_ls.append(min_tb)
        #print(min_tb, ' days')

    min_tb_dict= {'sensor':name_ls, 
                  'gsd': gsd_ls, 
                  'min_tb (days)': min_tb_ls,
                 'sensor_str':sensor_str_ls}
    df = pd.DataFrame(min_tb_dict)
    return df

# %% ../nbs/04_Data_inspection.ipynb 34
def trim_by_baseline(ds):

    min_tb_df = calc_min_tbaseline(ds)

    l5 = ds.where(ds.satellite_img1 == '5', drop=True)
    l7 = ds.where(ds.satellite_img1 == '7', drop=True)
    l8 = ds.where(ds.satellite_img1 == '8',drop=True)
    l9 = ds.where(ds.satellite_img1 == '9',drop=True)
    s1 = ds.where(ds.satellite_img1.isin(['1A','1B']),drop=True)
    s2 = ds.where(ds.satellite_img1.isin(['2A','2B']),drop=True)

    l5_sub = l5.where(l5.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'L5']['min_tb (days)']), drop=True)
    l7_sub = l7.where(l7.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'L7']['min_tb (days)']), drop=True)
    l8_sub = l8.where(l8.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'L8']['min_tb (days)']), drop=True)
    l9_sub = l9.where(l9.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'L9']['min_tb (days)']), drop=True)
    s1_sub = s1.where(s1.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'S1']['min_tb (days)']), drop=True)
    s2_sub = s2.where(s2.img_separation >= int(min_tb_df.loc[min_tb_df['sensor'] == 'S2']['min_tb (days)']), drop=True)
    ds_ls = [l5_sub, l7_sub, l8_sub, l9_sub, s1_sub, s2_sub]
    concat_ls = []
    for ds in range(len(ds_ls)):
            if len(ds_ls[ds].mid_date) > 0:
                concat_ls.append(ds_ls[ds])
    try:
        combine = xr.concat(concat_ls, dim='time_numeric')
        combine = combine.sortby(combine.mid_date)
        return combine
    except:
        print('something went wrong')
