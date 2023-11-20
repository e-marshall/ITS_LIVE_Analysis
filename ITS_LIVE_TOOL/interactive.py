# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_interactive.ipynb.

# %% auto 0
__all__ = ['Widget', 'create_multiple_glacier_objs', 'create_multiple_glacier_point_objs',
           'create_multiple_glacier_centerline_objs']

# %% ../nbs/02_interactive.ipynb 3
import numpy as np
import pyproj
import matplotlib.path as path
import s3fs
import zarr
import matplotlib.pyplot as plt
import scipy
from datetime import timedelta
from tqdm import tqdm
import xarray as xr
import re
import pandas as pd
import geopandas as gpd
import matplotlib.path as mplp
import ipyleaflet as ipyl
from ipyleaflet import WMSLayer
import ipywidgets as ipyw
import json
import pandas as pd
from ipyleaflet import Map, WMSLayer, basemaps, GeoData
from ipywidgets import HTML
from owslib.wms import WebMapService
import ipywidgets as widgets
from ipywidgets import Label, VBox
from owslib.wfs import WebFeatureService
from requests import Request
import urllib.request, json 


# %% ../nbs/02_interactive.ipynb 5
class Widget():
    '''this is an interactive map widget to streamline access itslive data. 
    left and right click for rgi info about a selected location and corresponding url 
    to ITS_LIVE image pair time series granule
    '''
    def __init__(self):

        self.wms_url = "https://glims.org/geoserver/ows?SERVICE=WMS&"
        self.map, self.label = self.make_map()
        
        self.coordinates_label = widgets.Label(value="Clicked Coordinates: ")
        self.coordinates_output = widgets.Output()
        self.map.on_interaction(self.click_handler)
        self.geojson_layer = self._make_geojson_layer()
        self.wms_layer = self._make_wms_layer()
        self.wms = self._make_wms_obj()
        self.map.geojson_layer = self.map.add(self.geojson_layer)
        self.map.wms_layer = self.map.add(self.wms_layer)
        self.geojson_layer.on_click(self._json_handler)
        self.geojson_layer.on_hover(self._hover_handler)
        self.added_glaciers =  []
        self.urls = []
        self.added_coords = []
        self.added_urls = []

    def make_map(self):
        
        map = ipyl.Map(basemap=basemaps.Esri.WorldImagery, center=(0, 0), zoom=2)
        label = ipyw.Label(layout=ipyw.Layout(width="100%"))
        map.scroll_wheel_zoom = True
        return map, label
        
    def _make_wms_layer(self):

        wms_layer = WMSLayer(
            url = self.wms_url,
            layers = 'GLIMS:RGI',
            transparent=True,
            format = 'image/png'
        )
        return wms_layer
        
    def _make_wms_obj(self):
        wms = WebMapService(self.wms_url)
        return wms

    def _make_geojson_layer(self):
        # geojson layer with hover handler
        with urllib.request.urlopen('https://its-live-data.s3.amazonaws.com/datacubes/catalog_v02.json') as url:

            geojson_data = json.load(url)
        
        for feature in geojson_data["features"]:
            feature["properties"]["style"] = {
                "color": "grey",
                "weight": 1,
                "fillColor": "grey",
                "fillOpacity": 0.5,
            }
        
        geojson_layer = ipyl.GeoJSON(data=geojson_data, hover_style={"fillColor": "red"})
        return geojson_layer

    def _hover_handler(self, event=None, feature=None, id=None, properties=None):
        self.label.value = properties["zarr_url"]

    def _json_handler(self, event=None, feature=None, id=None, properties=None):
        zarr_url = properties.get("zarr_url", "N/A")
        self.urls.append(zarr_url)
        print(f"Clicked URL: {zarr_url}")
        print("All Clicked URLs:", self.urls)

        #self.added_urls.append(urls)

    def click_handler(self, properties=None, **kwargs):
        
        if kwargs.get('type') == 'contextmenu':
            latlon = kwargs.get('coordinates')
            lat, lon = latlon[0], latlon[1]
            print(f"Clicked at (Lat: {lat}, Lon: {lon})")
            self.added_coords.append([lat, lon])
            
            # Arrange the coordinates
            
            response = self.wms.getfeatureinfo(
                layers=['GLIMS:RGI'],
                srs='EPSG:4326',
                bbox=(lon-0.001,lat-0.001,lon+0.001,lat+0.001),
                size=(1,1),
                format='image/jpeg',
                query_layers=['GLIMS:RGI'],
                info_format="application/json",
                xy=(0,0))
            df = gpd.read_file(response)
            #self.added_glacier.append(df)
            print(f"You have selected the glacier {df['NAME'].values[0]}, ID: {df['RGIID'].values[0]} ")
            #gdf_list.append(df)
            self.added_glaciers.append(df)

            geo_data = GeoData(geo_dataframe = df,
                               style={'color':'black', 'fillColor':'#3366cc','opacity':0.05, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0.6},
                               hover_style={'fillColor':'blue','fillOpacity':0.2},
                               name = 'Glacier')
            self.map.add_layer(geo_data) #add glacier highlight to map



            #return gdf_list
            
    def update_coordinates_label(self):
        self.coordinates_label.value = "Clicked Coordinates: " + str(self.coordinates)

    def clear_coordinates(self, b):
        self.coordinates = []
        self.update_coordinates_label()
        
    def get_coordinates(self):
        return self.coordinates
    def display(self):
        return VBox([self.map, self.coordinates_label, self.coordinates_output])

# %% ../nbs/02_interactive.ipynb 18
def create_multiple_glacier_objs(w_obj):
    '''wrapper function to create multiple objects from multiple clicks
    '''
    glacier_ls = []

    for i in range(len(w_obj.added_glaciers)):
    
        glacier = create_glacier_from_click(w_obj, i)
        glacier_ls.append(glacier)

    return glacier_ls
    #glacier0, glacier1 = glacier_ls[0], glacier_ls[1]

# %% ../nbs/02_interactive.ipynb 24
def create_multiple_glacier_point_objs(w_obj):
    '''wrapper function to create multiple glacier point objects from multiple clicks
    '''
    
    glacier_pt_ls = []

    label_ls = ['point 0','point 1']
    
    for i in range(len(w_obj.added_glaciers)):
    
        glacier_pt = create_glacier_point_from_click(w_obj,i, label_ls[i])
        glacier_pt_ls.append(glacier_pt)

    return glacier_pt_ls
   # glacier_pt0, glacier_pt1 = glacier_pt_ls[0], glacier_pt_ls[1]

# %% ../nbs/02_interactive.ipynb 25
def create_multiple_glacier_centerline_objs(w_obj):
    '''wrapper  function to create multiple glacier centerline objects from multiple clicks 
    '''

    glacier_centerline_ls = []

    for i in range(len(w_obj.added_glaciers)):

        glacier_centerline = create_glacier_centerline_from_click(w_obj, i)
        glacier_centerline_ls.append(glacier_centerline)

    return glacier_centerline_ls
