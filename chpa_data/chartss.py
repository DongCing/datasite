from pyecharts.charts import Line, Bar
from pyecharts import options as opts


def echarts_stackbar(df,  # 传入数据df，应该是一个行索引为date的时间序列面板数据
                     df_gr=None,  # 传入同比增长率df，可以没有
                     datatype='ABS'  # 主Y轴形式是绝对值，增长率还是份额，用来确定一些标签格式，默认为绝对值
                     ) -> Bar:
    axislabel_format = '{value}'  # 主Y轴默认格式
    max = df[df > 0].sum(axis=1).max()  # 主Y轴默认最大值
    min = df[df <= 0].sum(axis=1).min()  # 主Y轴默认最小值
    if datatype in ['SHARE', 'GR']:  # 如果主数据不是绝对值形式而是份额或增长率如何处理
        df = df.multiply(100).round(2)
        axislabel_format = '{value}%'
        max = 100
        min = 0
    if df_gr is not None:
        df_gr = df_gr.multiply(100).round(2)  # 如果有同比增长率，原始数*100呈现

    if df.empty is False:
        stackbar = (
            Bar().add_xaxis(df.index.tolist())
        )
        for i, item in enumerate(df.columns):  # 预留的枚举，这个方法以后可以根据输入对象不同从单一柱状图变成堆积柱状图
            stackbar.add_yaxis(item,
                               df[item].values.tolist(),
                               stack='总量',
                               label_opts=opts.LabelOpts(is_show=False),
                               z_level=1,  # 指定渲染图层，低版本pyecharts可能因为没有该参数报错
                               )
        if df_gr is not None:  # 如果有同比增长率数据则加入次Y轴
            stackbar.extend_axis(
                yaxis=opts.AxisOpts(
                    name="同比增长率",
                    type_="value",
                    axislabel_opts=opts.LabelOpts(formatter="{value}%"),
                )
            )
        stackbar.set_global_opts(
            legend_opts=opts.LegendOpts(pos_top='5%', pos_left='10%', pos_right='60%'),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            tooltip_opts=opts.TooltipOpts(trigger='axis',
                                          axis_pointer_type='cross',
                                          ),
            xaxis_opts=opts.AxisOpts(type_='category',
                                     boundary_gap=True,
                                     axislabel_opts=opts.LabelOpts(rotate=90),  # x轴标签方向rotate有时能解决拥挤显示不全的问题
                                     splitline_opts=opts.SplitLineOpts(is_show=False,
                                                                       linestyle_opts=opts.LineStyleOpts(
                                                                           type_='dotted',
                                                                           opacity=0.5,
                                                                       )
                                                                       )
                                     ),
            yaxis_opts=opts.AxisOpts(max_=max,
                                     min_=min,
                                     type_="value",
                                     axislabel_opts=opts.LabelOpts(formatter=axislabel_format),
                                     # axistick_opts=opts.AxisTickOpts(is_show=True),
                                     splitline_opts=opts.SplitLineOpts(is_show=True,
                                                                       linestyle_opts=opts.LineStyleOpts(
                                                                           type_='dotted',
                                                                           opacity=0.5,
                                                                       )
                                                                       )
                                     ),
        )
        if df_gr is not None:
            line = (
                Line()
                    .add_xaxis(xaxis_data=df_gr.index.tolist())
                    .add_yaxis(
                    series_name="同比增长率",
                    yaxis_index=1,
                    y_axis=df_gr.values.tolist(),
                    label_opts=opts.LabelOpts(is_show=False),
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    symbol_size=8,
                    itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color='', border_color0='white'),
                    z_level=2  # 渲染图层大于柱状图，保证线图在上方，低版本pyecharts可能因为没有该参数报错
                )
            )
    else:
        stackbar = (Bar())

    if df_gr is not None:
        return stackbar.overlap(line)  # 如果有次坐标轴最后要用overlap方法组合
    else:
        return stackbar
