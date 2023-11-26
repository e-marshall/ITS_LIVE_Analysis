# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_interactive.ipynb.

# %% auto 0
__all__ = ['Widget']

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
from ipyleaflet import Map, WMSLayer, basemaps, GeoData, AwesomeIcon, Marker, Polygon
from ipywidgets import HTML, widgets
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
        self.geo_data = []
        self.colors = ['red', 'green', 'blue', 'purple', 'gray', 'orange', 'beige']
        self.colors_iterator = 0
        self.point_iterator = 0
        self.markers = []
        self.button = None
        self.glacier_select = None
        self.datacube_select = None
        self.selector = None
        self.layout = None
        self.geojson_data = None

    def make_map(self):
        map = ipyl.Map(basemap=basemaps.Esri.WorldImagery, center=(0, 0), zoom=2)
        label = ipyw.Label(layout=ipyw.Layout(width="100%"))
        map.scroll_wheel_zoom = True
        return map, label

    def remove_point(self, *args, **kwargs):
        if self.markers:  # Check if there are markers
            self.map.remove_layer(self.markers[-1])  # Remove the marker from the map
            self.markers = self.markers[:-1]
            self.added_coords = self.added_coords[:-1]
    
    def selector_function_glacier(self, *args, **kwargs):
        self.selector = 'glacier_select'

    def selector_function_datacube(self, *args, **kwargs):
        self.selector = 'datacube_select'
        
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

            self.geojson_data = json.load(url)
        
        for feature in self.geojson_data["features"]:
            feature["properties"]["style"] = {
                "color": "grey",
                "weight": 1,
                "fillColor": "grey",
                "fillOpacity": 0.5,
            }
        
        geojson_layer = ipyl.GeoJSON(data=self.geojson_data, hover_style={"fillColor": "red"})
        return geojson_layer

    def _hover_handler(self, event=None, feature=None, id=None, properties=None):
        self.label.value = properties["zarr_url"]

    def _json_handler(self, event=None, feature=None, id=None, properties=None):
        if self.selector == 'datacube_select':
            zarr_url = properties.get("zarr_url", "N/A")
            self.urls.append(zarr_url)
            self.urls = list(np.unique(self.urls))
            print(f"Clicked URL: {zarr_url}")
            print("All Clicked URLs:", self.urls)
            # Create a Polygon layer from the clicked feature's geometry
            polygon = Polygon(
                locations=[list(reversed(coord)) for coord in feature['geometry']['coordinates'][0]],  # Reverse lat and lon
                color="yellow",
                fill_color="yellow",
                fill_opacity=0.2,
                weight=1,
            )

            # Add the Polygon layer to the map
            self.map.add_layer(polygon)


    def click_handler(self, properties=None, **kwargs):
        if self.selector == 'glacier_select':
            if kwargs.get('type') == 'click':
                icon = AwesomeIcon(name='fa-cog', marker_color = self.colors[self.point_iterator])
                self.point_iterator += 1
                self.colors_iterator += 1
                if self.colors_iterator > len(self.colors)-1:
                    self.colors_iterator = 0
                latlon = kwargs.get('coordinates')
                marker = Marker(location=latlon, icon=icon, draggable = False)
                self.map.add_layer(marker)
                self.markers.append(marker)
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
                print(f"You have selected the glacier {df['NAME'].values[0]}, ID: {df['RGIID'].values[0]} ")
                self.added_glaciers.append(df)
                try:
                        print(f"You have selected the glacier {df['NAME'].values[0]}, ID: {df['id'].values[0]} ")
                except:
                        print(f"This glacier is not recognized by the RGI (maybe an ice-shelf ?) -> Choose another one")

                geo_data = GeoData(geo_dataframe = df,
                                       style={'color':'black', 'fillColor':'#3366cc','opacity':0.05, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0.6},
                                       hover_style={'fillColor':'blue','fillOpacity':0.2},
                                       name = 'Glacier')
                if geo_data not in self.geo_data:
                    self.geo_data.append(geo_data)
                    self.map.add_layer(geo_data) 
                #print(len(self.added_glacier))
                #return gdf_list
            
    def update_coordinates_label(self):
        self.coordinates_label.value = "Clicked Coordinates: " + str(self.coordinates)

    def clear_coordinates(self, b):
        self.coordinates = []
        self.update_coordinates_label()
        
    def get_coordinates(self):
        return self.coordinates
        
    def display(self):
        # Create a button for removing points
        self.button = ipyw.Button(description="Remove latest point", icon='trash')
        self.button.on_click(self.remove_point)
        self.glacier_select =  widgets.Button(
                                description='Select glacier',
                                button_style='primary',
                                icon='flag',
                                style={'description_width': 'initial'})
        self.glacier_select.on_click(self.selector_function_glacier)
        self.datacube_select =  widgets.Button(
                                description='Select datacube',
                                button_style='primary',
                                icon='cube',
                                style={'description_width': 'initial'})
        self.datacube_select.on_click(self.selector_function_datacube)
        
        self.layout = widgets.Layout(align_items='stretch',
                        display='flex',
                        flex_flow='row wrap',
                        border='none',
                        grid_template_columns="repeat(auto-fit, minmax(720px, 1fr))",
                        # grid_template_columns='48% 48%',
                        width='99%',
                        height='100%')
                

        
        #return VBox([self.map, self.coordinates_label, self.coordinates_output, self.button, self.glacier_select, self.datacube_select])

        return widgets.GridBox([VBox([self.map, widgets.HBox([self.coordinates_label, self.coordinates_output, self.button, self.glacier_select, self.datacube_select], layout=widgets.Layout(align_items="flex-start", flex_flow='row wrap'))],

                                    layout=widgets.Layout(min_width="100%",
                                                            display="flex",
                                                            # height="100%",
                                                            # max_height="100%",
                                                            max_width="100%"))],
                        layout=self.layout)