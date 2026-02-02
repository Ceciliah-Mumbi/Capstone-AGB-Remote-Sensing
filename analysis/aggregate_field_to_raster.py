# This script aggregates field-measured heights to match the spatial resolution of a LiDAR raster. It outputs a raster of mean heights per cell for comparison with the LiDAR-derived raster.
import pandas as pd
import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import Point
import matplotlib.pyplot as plt

# specifying data paths
CHM_path = "C:/Users/DELL/Capstone-AGB-Remote-Sensing/data/Canopy_Height_Model.tif"
F3_GT = "C:/Users/DELL/Capstone-AGB-Remote-Sensing/data/F3_GT.csv"
output_raster = "C:/Users/DELL/Capstone-AGB-Remote-Sensing/outputs"

# Loading the CHM raster file
with rasterio.open(CHM_path) as src:
 transform = src.transform
 crs = src.crs
 shape = src.shape
 raster_array = src.read(1)

print("Min value:", raster_array.min())
print("Max value:", raster_array.max())
print("Mean value:", raster_array.mean())

# read f3_GT csv into GeoDataFrame and reproject to raster CRS
GT_df = pd.read_csv(F3_GT)

# Convert tree_heigh to numeric, forcing errors to NaN
GT_df['tree_heigh'] = pd.to_numeric(GT_df['tree_heigh'], errors='coerce')

# Checking how many invalid values I have
print(f"Invalid tree height values: {GT_df['tree_heigh'].isna().sum()}")
print(f"Valid tree height values: {GT_df['tree_heigh'].notna().sum()}")


geometry = [Point(xy) for xy in zip(GT_df["Longitude"], GT_df["Latitude"])]
crs="EPSG:4326"
GT_geo = gpd.GeoDataFrame(GT_df, geometry=geometry)
GT_geo.crs="EPSG:4326"

# reproject to raster CRS
with rasterio.open(CHM_path) as src:
 CHM_crs = src.crs
 transform = src.transform
 CHM_height = src.height
 CHM_width = src.width

 GT_geo = GT_geo.to_crs(CHM_crs)

print(GT_geo.head())
print(GT_geo.crs)

# mapping GT points to raster cell
def GT_to_cell(geom, transform):
 col, row = ~transform * (geom.x, geom.y)
 return int(row), int(col)

GT_geo["row"], GT_geo["col"] = zip(*GT_geo.geometry.apply(lambda g: GT_to_cell(g, transform)))

#filter points that fall outside the F3
GT_geo = GT_geo [
 (GT_geo .row >= 0) & (GT_geo .col >= 0) &
 (GT_geo .row < CHM_height) &
 (GT_geo .col < CHM_width)
]
print(GT_df.columns.tolist())
#Grouping GT_geo points by raster cell
cell_stats = (
 GT_geo.groupby(["row", "col"])
 .agg(
  mean_height=("tree_heigh", "mean")
 )

)
print(cell_stats)
#Perform EDA visualization- check for outliers
plt.boxplot(cell_stats["mean_height"], vert=False)
plt.xlabel("Mean field height (m)")
plt.title("Outliers in mean field height")
plt.show()