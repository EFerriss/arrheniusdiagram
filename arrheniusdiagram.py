# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 16:42:23 2017

@author: Elizabeth Ferriss

To run and test alone on local computer:
On command line: bokeh serve arreniusdiagram.py
Navigate to: http://localhost:5006/arrheniusdiagram
"""

from bokeh.plotting import figure, ColumnDataSource
from bokeh.layouts import layout, widgetbox
from bokeh.models import HoverTool, Range1d, BoxZoomTool, SaveTool, ResetTool
from bokeh.models import PanTool
from bokeh.io import curdoc
import pandas as pd
import numpy as np
import os
import pynams
from bokeh.models.widgets import (CheckboxGroup,
        RadioButtonGroup, RangeSlider, CheckboxButtonGroup, Button)


# The data
file = os.path.join(pynams.__path__[0], 'diffusion', 'literaturevalues.csv')
olivine = pd.read_csv(file)
olivine = olivine.dropna(how='all') # ignore empty rows
olivine.fillna(0, inplace=True) # replace missing values with zero
olivine.loc[olivine['orientation'] == 'u', 'orientation'] = 'not oriented'
olivine.loc[olivine['name'] == 0, 'name'] = ''
olivine.loc[olivine['fO2Buffer'] == 0, 'fO2Buffer'] = ''
olivine["color"] = np.where(olivine["Author"] == 'Ferriss', "green", "grey")
olivine.loc[olivine["Author"] == 'Newcombe', "color"] = "blue"
olivine.loc[olivine["Author"] == 'Portnyagin et al.', "color"] = "red"
olivine.loc[olivine["Author"] == 'Gaetani et al.', "color"] = "yellow"
olivine.loc[olivine["Author"] == 'Hauri', "color"] = "black"
olivine.loc[olivine["Author"] == 'Chen et al.', "color"] = "brown"
olivine.loc[olivine["name"] == 'kiki', "color"] = "purple"
olivine.loc[olivine["name"] == 'SC1-7', "color"] = "orange"
olivine["alpha"] = np.where(olivine["Author"] == 'Ferriss', 0.75, 0.75)
olivine["paper"] = olivine["Author"] + ' ' + olivine["Year"].map(str)

source = ColumnDataSource(data=dict(
        x = [],
        y = [],
        color = [],
        year = [],
        author = [],
        fonum = [],
        celsius = [],
        orient = [],
        exper = [],
        mech = [],
        alpha = [],
        hours = [],
        buffer = [],
        name = [],
        logD = [],
    ))

# Hover
hover = HoverTool(tooltips=[
        ("||", "@orient"),
        ("Fe", "Fo# @fonum{0.0} @buffer"),
        ("Heat", "@hours hrs at @celsius C "),
        ("log10D", "@logD{0.0} in m2/s"),
        ("Type", "@exper, @mech"),
        ("Source", "@author @year @name"),
])

# The figure
left, right, bottom, top = 6, 10, -16, -8
p = figure(plot_width=500, plot_height=500, 
           tools=[BoxZoomTool(), hover, SaveTool(), ResetTool()],
           title="H diffusion in olivine", 
           x_range=Range1d(left, right), y_range=Range1d(bottom, top))
p.circle('x', 'y', size=10, source=source, color='color', alpha='alpha')
p.xaxis.axis_label = "1e4 / Temperature (K)"
p.yaxis.axis_label = "log10 Diffusivity (m2/s)"
#p.toolbar.active_drag = BoxZoomTool()

# pp and pv areas
wD = 1.8    
leftD = -10.4
rightD = -12.8
pvd = wD
p.patch([6, 6, 10, 10], [leftD, leftD+wD, rightD+wD, rightD], 
        alpha=0.075, line_width=0, color='lightcoral')
p.patch([6, 6, 10, 10], [leftD-pvd, leftD+wD-pvd, rightD+wD-pvd, rightD-pvd], 
        alpha=0.2, line_width=0, color='powderblue')
#glyph = Text(x="x", y="y", text="text", angle=0.3, text_color="#96deb3")
#plot.add_glyph(source, glyph)

# The widgets
widget_orient = CheckboxButtonGroup(
        labels=['|| a', '|| b', '|| c', 'not oriented'], active=[0, 1, 2, 3])
widget_mech = CheckboxButtonGroup(
        labels=['bulk H "pp"', 'bulk H "pv"', '[Si]', '[Ti]', \
                '[tri]', '[Mg]'], active=[0, 1])
widget_fo = RangeSlider(title='Fo#', start=80, end=100, range=(80, 100))
widget_exper = CheckboxButtonGroup(
		labels=['hydration', 'dehydration'], active=[0, 1])

papersdf = olivine.groupby(['paper'])
papers = [paper for paper, group in papersdf]
widget_papers=CheckboxGroup(labels=papers, active=list(range(len(papers))))
select_all = Button(label='select all papers', width=100)
deselect_all = Button(label='deselect all papers', width=100)

widget_max = Button(label='Show max/min estimates')


# What to plot
def select_data():
    selected = olivine
    orient_val = widget_orient.active
    mech_val = widget_mech.active
    fomax_val = widget_fo.range[1]
    fomin_val = widget_fo.range[0]
    exper_val = widget_exper.active
    papers_val = widget_papers.active
    
    selected = selected[selected.Fo.values <= fomax_val]
    selected = selected[selected.Fo.values >= fomin_val]
    
    orient_labels = ['a', 'b', 'c', 'not oriented']
    orient_list = [orient_labels[idx] for idx in orient_val]
    selected = selected[selected['orientation'].isin(orient_list)]

    mech_labels = ['pp', 'pv', '[Si]', '[Ti]', '[tri]', '[Mg]']
    mech_list = [mech_labels[idx] for idx in mech_val]
    selected = selected[selected['mechanism'].isin(mech_list)]
    
    exper_labels = ['hydration', 'dehydration']
    exper_list = [exper_labels[idx] for idx in exper_val]
    selected = selected[selected['Experiment'].isin(exper_list)]
        
    for idx, paper in enumerate(papers):
        if idx not in papers_val:
            selected = selected[selected.paper != paper]

    return selected

	
# Selecting data to plot
def update():
    df = select_data()
    
    source.data=dict(
        x = 1e4 / (df['celsius'].values + 273.15),
        y = df['log10D'].values,
        color = df['color'],
        alpha = df['alpha'],
        year = df['Year'].values,
        author = df['Author'].values,
        fonum = df['Fo'].values,
        celsius = df['celsius'].values,
        orient = df['orientation'].values,
        exper = df['Experiment'].values,
        mech = df['mechanism'].values,
        hours = df['hours'].values,
        buffer = df['fO2Buffer'].values,
        logD = df['log10D'].values,
        name = df['name'].values
    )

# Initial state
update()

# set up callbacks
controls = [widget_orient, widget_mech, widget_fo, widget_exper, \
            deselect_all, select_all, widget_papers]
for control in [widget_orient, widget_mech, widget_exper, widget_papers]:
    control.on_change('active', lambda attr, old, new: update())
widget_fo.on_change('range', lambda attr, old, new: update())
widget_max.on_click(update())


def select_all_pressed():
    widget_papers.active = list(range(len(papers)))
select_all.on_click(select_all_pressed)


def deselect_all_pressed():
    widget_papers.active = []
deselect_all.on_click(deselect_all_pressed)

# layout
sizing_mode = 'fixed' 
inputs = widgetbox(*controls, sizing_mode=sizing_mode)
layout = layout([
            [inputs, p]
            ], sizing_mode=sizing_mode)

curdoc().add_root(layout)
curdoc().title = "Arrhenius Diagram"
