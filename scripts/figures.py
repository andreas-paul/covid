import itertools
import streamlit as st
from datetime import datetime
from bokeh.plotting import figure
from bokeh.events import DoubleTap
from bokeh.palettes import Dark2_5 as palette
from bokeh.models import WheelZoomTool, CustomJS, DatetimeTickFormatter, Span, Label, HoverTool, NumeralTickFormatter


def bokeh_plot_vaccines(data, per_capita):

    if per_capita:
        title = 'Vaccine doses (per 100K people)'
    else:
        title = 'Vaccine doses'

    p = figure(title=title,
               x_axis_type='datetime',
               toolbar_location=None,
               plot_height=400
               )
    x = data.index

    colors = itertools.cycle(palette)

    for column in data.columns:
        df = list(data[column])
        p.line(x, df, legend_label=column, line_width=2, color=next(colors))

    for year in ['2020', '2021', '2022']:
        vline = Span(location=datetime.strptime(f'1/1/{year}', '%d/%m/%Y'),
                     dimension='height',
                     line_color='black',
                     line_width=0.25,
                     )
        text = Label(x=datetime.strptime(f'1/1/{year}', '%d/%m/%Y'), y=0,
                     text=f"{year}",
                     text_color='black',
                     angle=1.5708,
                     text_font_size='8pt',
                     text_alpha=0.7,
                     x_offset=15,
                     y_offset=-12
                     )

        p.renderers.extend([vline])
        p.add_layout(text)

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [("cases", "@y")]

    p.legend.location = "top_left"
    p.yaxis.formatter.use_scientific = False
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    p.xaxis.formatter = DatetimeTickFormatter(months=['%B'])
    p.xaxis.axis_label_text_align = 'right'  # <== THIS APPEARS TO DO NOTHING
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code='p.reset.emit()'))

    st.bokeh_chart(p, use_container_width=True)


def bokeh_plot(data, type, axis_type):

    y_label = type
    y_axis_type = axis_type

    p = figure(title='Active cases',
               x_axis_type='datetime',
               y_axis_label=y_label,
               y_axis_type=y_axis_type,
               toolbar_location=None,
               plot_height=400
               )
    x = data.index

    colors = itertools.cycle(palette)

    for column in data.columns:
        df = list(data[column])
        p.line(x, df, legend_label=column, line_width=2, color=next(colors))

    for year in ['2020', '2021', '2022']:
        vline = Span(location=datetime.strptime(f'1/1/{year}', '%d/%m/%Y'),
                     dimension='height',
                     line_color='black',
                     line_width=0.25,
                     )
        text = Label(x=datetime.strptime(f'1/1/{year}', '%d/%m/%Y'), y=0,
                     text=f"{year}",
                     text_color='black',
                     angle=1.5708,
                     text_font_size='8pt',
                     text_alpha=0.7,
                     x_offset=15,
                     y_offset=-12
                     )

        p.renderers.extend([vline])
        p.add_layout(text)

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [("cases", "@y")]

    p.legend.location = "top_left"
    # p.yaxis.formatter.use_scientific = False
    p.yaxis.formatter = NumeralTickFormatter(format="0,0M")
    p.xaxis.formatter = DatetimeTickFormatter(months=['%B'])
    p.xaxis.axis_label_text_align = 'right'  # <== THIS APPEARS TO DO NOTHING
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code='p.reset.emit()'))

    st.bokeh_chart(p, use_container_width=True)