import pandas as pd
import geopandas as gpd

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# Assign Height to each loaction
def assign_height(data):
    data['height'] = 0
    for point in data.geometry.unique():
        # rint(point)
        same_point = data[data['geometry'] == point]
        sizeOfsamepointdata = len(same_point)
        # int(sizeOfwrk)

        for pointIndex, siteNumber in zip(same_point.index, range(1, sizeOfsamepointdata + 1)):
            # print(workIndex)
            data.iloc[pointIndex, -1] = siteNumber * 1 - 1

#visualize home loactions
def display_3D_tract(tract, road, data, zvalue, elev, azim, save_path = None):
    # Initialize 3D plot
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Remove grid and background panes
    ax.grid(False)
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('white')
    ax.yaxis.pane.set_edgecolor('white')
    ax.zaxis.pane.set_edgecolor('white')

    # Remove axes lines
    ax.xaxis.line.set_lw(0.)  # Updated to current attribute
    ax.yaxis.line.set_lw(0.)  # Updated to current attribute
    ax.zaxis.line.set_lw(0.)  # Updated to current attribute
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_zlim(0, zvalue)

    # Plot tract shapes
    for shape in tract.geometry:
        if shape.geom_type == 'Polygon':
            x, y = shape.exterior.xy
            ax.plot(x, y, zs=0, zdir='z', color='black')
        elif shape.geom_type == 'MultiPolygon':
            for poly in shape.geoms:
                x, y = poly.exterior.xy
                ax.plot(x, y, zs=0, zdir='z', color='black')

    # Plot road shapes
    for shape in road.geometry:
        if shape.geom_type == 'LineString':
            x, y = shape.xy
            ax.plot(x, y, zs=0, zdir='z', color='lightgray')
        elif shape.geom_type == 'MultiLineString':
            for line in shape.geoms:
                x, y = line.xy
                ax.plot(x, y, zs=0, zdir='z', color='lightgray')

    # Color mapping based on the count of points in the same location
    color_map = {
        range(1, 3): '#1a9641',
        range(3, 20): '#a6d96a',
        range(20, 40): '#d9ef8b',
        range(40, 80): '#fee08b',
        range(80, 100): '#fc8d59',
        range(100, 200): '#d7191c'  # Adjust the upper limit as needed
    }

    # Plot data points with color based on their quantity
    for _, group in data.groupby('geometry'):
        color = next(color for range_, color in color_map.items() if len(group) in range_)
        ax.scatter(group['long'], group['lat'], group['height'], s=2,
                   color=color)  # Ensure 'height' matches column name exactly

    # Set the view initialization (rotation) here
    ax.view_init(elev=elev, azim=azim)

    plt.show()

    if save_path:
        fig.savefig(save_path, dpi=300)  # Adjust dpi as needed