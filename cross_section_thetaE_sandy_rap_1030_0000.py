#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 10:32:09 2017

@author: ken.pryor
"""
from __future__ import print_function, division
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib.cm as cm
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.io.shapereader as shpreader

plt.rcParams["figure.figsize"] = [8,8]

def read_RAP(ncf):
    nc_fid = Dataset(ncf, 'r')
    T = nc_fid.variables["Temperature_isobaric"][:]  # shape lat, lon as shown above
    RH = nc_fid.variables["Relative_humidity_isobaric"][:]
    Z = nc_fid.variables["Geopotential_height_isobaric"][:]
    VV = nc_fid.variables["Vertical_velocity_pressure_isobaric"][:]
    u = nc_fid.variables["u-component_of_wind_isobaric"][:]
    v = nc_fid.variables["v-component_of_wind_isobaric"][:]
    lat = nc_fid.variables['lat'][:]  # extract/copy the data
    lon = nc_fid.variables['lon'][:]
    names = nc_fid.variables.keys()
    nc_fid.close()
    return T, RH, Z, VV, u, v, lat, lon, names

def read_RAP_vort(ncf):
    nc_fid = Dataset(ncf, 'r')
    AV = nc_fid.variables["Absolute_vorticity_isobaric"][:]  # shape lat, lon as shown above
    lat = nc_fid.variables['lat'][:]  # extract/copy the data
    lon = nc_fid.variables['lon'][:]
    names = nc_fid.variables.keys()
    nc_fid.close()
    return AV, lat, lon, names

RAP_file = 'rap_130_20121030_0000_000.nc'
names = read_RAP(RAP_file)
T, RH, Z, VV, u, v, lat, lon, names = read_RAP(RAP_file)
#print(names)
print('lat shape, lon shape', lat.shape, lon.shape,lat,lon)
print('U shape, V shape', u.shape, v.shape,u,v)

RAP_file_vort = 'rap_130_20121030_0000_AV.nc'
names = read_RAP_vort(RAP_file_vort)
AV, latv, lonv, names = read_RAP_vort(RAP_file_vort)

#Plot theta-e map at a single pressure level

T1000 = T[0,36,:,:]
RH1000 = RH[0,36,:,:]
Z1000 = Z[0,36,:,:]
U1000 = u[0,36,:,:]
V1000 = v[0,36,:,:]
Z1000km = Z1000/1000
TC1000 = T1000 - 273.15
print('TC shape', TC1000.shape, TC1000)
print('RH shape', RH1000.shape, RH1000)
print('U1000 shape, V1000 shape', U1000.shape, V1000.shape, U1000, V1000)
print('lat shape, lon shape', lat.shape, lon.shape,lat,lon)

prlev = 1000
ThetaE_1000 = (273.15 + TC1000)*((1000/prlev)**0.286)+(3 * (RH1000 * (3.884266 * 10**
         ((7.5 * TC1000)/(237.7 + TC1000)))/100))
print('ThetaE 1000mb shape', ThetaE_1000.shape, ThetaE_1000)

T850 = T[0,30,:,:]
RH850 = RH[0,30,:,:]
Z850 = Z[0,30,:,:]
U850 = u[0,30,:,:]
U850[::2, 1::2] = np.nan
U850[1::2, ::2] = np.nan
U850[::3, 1::3] = np.nan
U850[1::3, ::3] = np.nan
V850 = v[0,30,:,:]
V850[::2, 1::2] = np.nan
V850[1::2, ::2] = np.nan
V850[::3, 1::3] = np.nan
V850[1::3, ::3] = np.nan
Z850km = Z850/1000
print('Z850km shape', Z850km.shape, Z850km)
TC850 = T850 - 273.15
print('TC shape', TC850.shape, TC850)
print('RH shape', RH850.shape, RH850)
print('U850 shape, V850 shape', U850.shape, V850.shape, U850, V850)
print('lat shape, lon shape', lat.shape, lon.shape,lat,lon)

prlev = 850
ThetaE_850 = (273.15 + TC850)*((1000/prlev)**0.286)+(3 * (RH850 * (3.884266 * 10**
         ((7.5 * TC850)/(237.7 + TC850)))/100))
print('ThetaE 850mb shape', ThetaE_850.shape, ThetaE_850)

fig = plt.figure(figsize=(10, 10))
img_extent = (-78, -68, 32, 42)
ax = plt.axes(projection=ccrs.PlateCarree(globe=None))
ax.set_extent([-78, -68, 32, 42], ccrs.PlateCarree(globe=None))

shapename = 'admin_1_states_provinces_lakes_shp'
states_shp = shpreader.natural_earth(resolution='110m',
                                         category='cultural', name=shapename)
plt.title('RAP Analysis\n'
          '850 mb Theta-e 10/30/2012 00:00 UTC')
levels = np.arange(280,350,2)
mi = ax.contourf(lon, lat, ThetaE_850, levels, extent=img_extent, transform=ccrs.PlateCarree(globe=None), cmap='gist_rainbow_r')
ax.barbs(lon,lat,U850,V850)
ax.coastlines(resolution='50m', color='cyan', linewidth=1)
for state in shpreader.Reader(states_shp).geometries():
    # pick a default color for the land with a black outline,
    facecolor = ''
    edgecolor = 'white'
    ax.add_geometries([state], ccrs.PlateCarree(),
                          facecolor=facecolor, edgecolor=edgecolor)
    
ax.set_xticks([-78,-77,-76,-75,-74,-73,-72,-71,-70,-69,-68])
ax.set_yticks([32,33,34,35,36,37,38,39,40,41,42])   

ax.plot(-76.8785, 39.0554, 'wo', markersize=7, transform=ccrs.Geodetic())
ax.text(-76.82, 39.04, 'BLT', color='white', weight='bold', transform=ccrs.Geodetic())
ax.plot(-76.14, 38.59, 'wo', markersize=7, transform=ccrs.Geodetic())
ax.text(-76.09, 38.58, 'HPL', color='white', weight='bold', transform=ccrs.Geodetic())
ax.plot(-74.5, 39.5, 'w*', markersize=7, transform=ccrs.Geodetic())
ax.text(-74.45, 39.49, '00', color='white', weight='bold', transform=ccrs.Geodetic())  
ax.plot(-75.7974, 39.2592, 'wX', markersize=9, transform=ccrs.Geodetic()) 

lon_formatter = LongitudeFormatter()
lat_formatter = LatitudeFormatter()

ax.xaxis.set_major_formatter(lon_formatter)
ax.yaxis.set_major_formatter(lat_formatter)
cbar=plt.colorbar(mi,fraction=0.035,pad=0.03)
plt.savefig("thetae_850_1030_0000.png",dpi=250,bbox_inches='tight')
plt.show()

AV = AV[0,0,:,:]
U500 = u[0,16,:,:]
U500[::2, 1::2] = np.nan
U500[1::2, ::2] = np.nan
U500[::3, 1::3] = np.nan
U500[1::3, ::3] = np.nan
V500 = v[0,16,:,:]
V500[::2, 1::2] = np.nan
V500[1::2, ::2] = np.nan
V500[::3, 1::3] = np.nan
V500[1::3, ::3] = np.nan

print('U500 shape, V500 shape', U500.shape, V500.shape, U500, V500)
print('lat shape, lon shape', lat.shape, lon.shape,lat,lon)

fig = plt.figure(figsize=(10, 10))
img_extent = (-78, -68, 32, 42)
ax = plt.axes(projection=ccrs.PlateCarree(globe=None))
ax.set_extent([-78, -68, 32, 42], ccrs.PlateCarree(globe=None))

shapename = 'admin_1_states_provinces_lakes_shp'
states_shp = shpreader.natural_earth(resolution='110m',
                                         category='cultural', name=shapename)
plt.title('RAP Analysis\n'
          '500 mb Vorticity 10/30/2012 00:00 UTC')
levels = np.arange(-0.0001,0.0009,0.00005)
mi = ax.contourf(lon, lat, AV, levels, extent=img_extent, transform=ccrs.PlateCarree(globe=None), cmap='gist_rainbow_r')
ax.barbs(lon,lat,U500,V500)
ax.coastlines(resolution='50m', color='cyan', linewidth=1)
for state in shpreader.Reader(states_shp).geometries():
    # pick a default color for the land with a black outline,
    facecolor = ''
    edgecolor = 'white'
    ax.add_geometries([state], ccrs.PlateCarree(),
                          facecolor=facecolor, edgecolor=edgecolor)
    
ax.set_xticks([-78,-77,-76,-75,-74,-73,-72,-71,-70,-69,-68])
ax.set_yticks([32,33,34,35,36,37,38,39,40,41,42])   

ax.plot(-76.8785, 39.0554, 'wo', markersize=7, transform=ccrs.Geodetic())
ax.text(-76.82, 39.04, 'BLT', color='white', weight='bold', transform=ccrs.Geodetic())
ax.plot(-76.14, 38.59, 'wo', markersize=7, transform=ccrs.Geodetic())
ax.text(-76.09, 38.58, 'HPL', color='white', weight='bold', transform=ccrs.Geodetic())
ax.plot(-74.5, 39.5, 'w*', markersize=7, transform=ccrs.Geodetic())
ax.text(-74.45, 39.49, '00', color='white', weight='bold', transform=ccrs.Geodetic())  
ax.plot(-74.6538, 39.2587, 'wX', markersize=9, transform=ccrs.Geodetic()) 

lon_formatter = LongitudeFormatter()
lat_formatter = LatitudeFormatter()

ax.xaxis.set_major_formatter(lon_formatter)
ax.yaxis.set_major_formatter(lat_formatter)
cbar=plt.colorbar(mi,fraction=0.035,pad=0.03)
plt.savefig("vort_500_1030_0000.png",dpi=250,bbox_inches='tight')
plt.show()

"""
#Plot vertical theta-e cross section
"""
T, RH, Z, VV, u, v, lat, lon, names = read_RAP(RAP_file)
press = np.array([100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,525,550,575,600,625,650,675,700,725,750,775,800,825,850,875,900,925,950,975,1000])
print(len(press))
T = T[0,:,80,40:80]
RH = RH[0,:,80,40:80]
VV = VV[0,:,80,40:80]
VV_min = np.amin(VV)
VV_max = np.amax(VV)
print("VV min, VV max = %f Pa/s %f Pa/s" % (VV_min, VV_max))

TC = T - 273.15
lev = np.arange(0,37,1)
lon = lon[80,40:80]
lons, prlevs = np.meshgrid(lon, press)

ThetaE = (273.15 + TC)*((1000/prlevs)**0.286)+(3 * (RH * (3.884266 * 10**
         ((7.5 * TC)/(237.7 + TC)))/100))

levels_TE = np.arange(290,370,2.5)
levels_RH = np.array([86,88,90,92,94,96,98])
levels_VV = np.arange(-3.0,0.5,0.25)

fig = plt.figure(figsize=(12,12))
cf = plt.contourf(lons, prlevs, ThetaE, cmap=cm.jet, levels = levels_TE)
CS = plt.contour(lons, prlevs, VV, colors='w', levels = levels_VV)
plt.clabel(CS, inline=True, inline_spacing = 1, fontsize=10, fmt='%1.0f')
plt.xlim(-79.25,-73.75)
plt.ylim(1000,200)
plt.colorbar(cf)
plt.plot(-79.0121,990,'w^',markersize=9)
plt.text(-79.0121, 980, 'PNR', color='white', weight='bold')
plt.plot(-76.8785,990,'w^',markersize=9)
plt.text(-76.8785, 980, 'BLT', color='white', weight='bold')
plt.plot(-76.14,990,'w^',markersize=9)
plt.text(-76.14, 980, 'HPL', color='white', weight='bold')
plt.xlabel("Longitude (deg west)")
plt.ylabel("Height (mb)")
plt.title("Theta-E (K) and Vertical Velocity (Pa/s) 0000 UTC 30 October 2012")
plt.savefig("thtae_crosssctn_1030_0000.png",dpi=250,bbox_inches='tight')
plt.grid(True)
plt.show()

"""
#Plot vertical zonal wind cross section
"""
T, RH, Z, VV, u, v, lat, lon, names = read_RAP(RAP_file)
press = np.array([100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,525,550,575,600,625,650,675,700,725,750,775,800,825,850,875,900,925,950,975,1000])
print(len(press))
U = u[0,:,80,40:80]
U_min = np.amin(U)
U_max = np.amax(U)
VV = VV[0,:,80,40:80]
VV_min = np.amin(VV)
VV_max = np.amax(VV)
print("U min, U max = %f m/s %f m/s" % (U_min, U_max))
print("VV min, VV max = %f Pa/s %f Pa/s" % (VV_min, VV_max))

lev = np.arange(0,37,1)
lon = lon[80,40:80]
lons, prlevs = np.meshgrid(lon, press)
levels_VV = np.arange(-3.0,0.5,0.25)
levels_U = np.arange(-40.0,40,0.5)

fig = plt.figure(figsize=(12,12))

cf = plt.contourf(lons, prlevs, U, cmap=cm.jet, levels = levels_U)
CS = plt.contour(lons, prlevs, VV, colors='w', levels = levels_VV)
plt.clabel(CS, inline=True, inline_spacing = 1, fontsize=10, fmt='%1.0f')
plt.xlim(-79.25,-73.75)
plt.ylim(1000,200)
plt.colorbar(cf)
plt.plot(-79.0121,990,'w^',markersize=9)
plt.text(-79.0121, 980, 'PNR', color='white', weight='bold')
plt.plot(-76.8785,990,'w^',markersize=9)
plt.text(-76.8785, 980, 'BLT', color='white', weight='bold')
plt.plot(-76.14,990,'w^',markersize=9)
plt.text(-76.14, 980, 'HPL', color='white', weight='bold')
plt.xlabel("Longitude (deg west)")
plt.ylabel("Height (mb)")
plt.title("Zonal Wind (U, m/s) and Vertical Velocity (Pa/s) 0000 UTC 30 October 2012")
plt.savefig("Uwind_crosssctn_1030_0000.png",dpi=250,bbox_inches='tight')
plt.grid(True)
plt.show()

