from django.http import HttpResponse
from django.shortcuts import render
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import json
import six


# 创建数据库连接引擎
ENGINE = create_engine('mysql+pymysql://root:111111@localhost:3306/dap')
DB_TABLE = 'chpa_data_data'

# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    'TC I': 'I',
    'TC II': 'II',
    'TC III': 'III',
    'TC IV': 'IV',
    '通用名|MOLECULE': 'MOLECULE',
    '商品名|PRODUCT': 'PRODUCT',
    '包装|PACKAGE': 'PACKAGE',
    '生产企业|CORPORATION': 'CORPORATION',
    '企业类型': 'MANUF_TYPE',
    '剂型': 'FORMULATION',
    '剂量': 'STRENGTH'
}


# 获取筛选数据
# period, unit 必选的两个筛选字段;filter_sql 为其它可选的筛选字段
# def sqlparse(period, unit, filter_sql=None):
#     sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % (DB_TABLE, period, unit)
#     if filter_sql is not None:
#         # 其它可选的筛选字段，如有则以 And 连接自定义字符串
#         sql = "%s And %s" % (sql, filter_sql)
#     return sql
def sqlparse(context):

    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % \
          (DB_TABLE, context['PERIOD_select'][0], context['UNIT_select'][0])  # 先处理单选部分

    # 下面循环处理多选部分
    for k, v in context.items():
        if k not in ['csrfmiddlewaretoken', 'DIMENSION_select', 'PERIOD_select', 'UNIT_select']:
            field_name = k[:-9]  # 字段名
            selected = v  # 选择项
            # 未来可以通过进一步拼接字符串动态扩展sql语句
            sql = sql_extent(sql, field_name, selected)
    return sql


def sql_extent(sql, field_name, selected, operator=" AND "):
    if selected is not None:
        statement = ''
        for data in selected:
            statement = statement + "'" + data + "', "
        statement = statement[:-2]
        if statement != '':
            sql = sql + operator + field_name + " in (" + statement + ")"
    return sql


# market_size 市场规模; market_gr 同比增长率; market_cagr 年复合增长率
def kpi(df):
    # 按列求和为市场总值的Series
    market_total = df.sum(axis=1)
    # 最后一行（最后一个DATE）就是最新的市场规模
    market_size = market_total.iloc[-1]
    # 市场按列求和，倒数第5行（倒数第5个DATE）就是同比的市场规模，可以用来求同比增长率
    market_gr = market_total.iloc[-1] / market_total.iloc[-5] - 1
    # 因为数据第一年是四年前的同期季度，时间序列收尾相除后开四次方根可得到年复合增长率
    market_cagr = (market_total.iloc[-1] / market_total.iloc[0]) ** 0.25 - 1
    if market_size == np.inf or market_size == -np.inf:
        market_size = "N/A"
    if market_gr == np.inf or market_gr == -np.inf:
        market_gr = "N/A"
    if market_cagr == np.inf or market_cagr == -np.inf:
        market_cagr = "N/A"

    return [market_size, market_gr, market_cagr]


def ptable(df):
    # 份额
    df_share = df.transform(lambda x: x / x.sum(), axis=1)

    # 同比增长率，要考虑分子为0的问题
    df_gr = df.pct_change(periods=4)
    df_gr.dropna(how='all', inplace=True)
    df_gr.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 最新滚动年绝对值表现及同比净增长
    df_latest = df.iloc[-1, :]
    df_latest_diff = df.iloc[-1, :] - df.iloc[-5, :]

    # 最新滚动年份额表现及同比份额净增长
    df_share_latest = df_share.iloc[-1, :]
    df_share_latest_diff = df_share.iloc[-1, :] - df_share.iloc[-5, :]

    # 进阶指标EI，衡量与市场增速的对比，高于100则为跑赢大盘
    df_gr_latest = df_gr.iloc[-1, :]
    df_total_gr_latest = df.sum(axis=1).iloc[-1] / df.sum(axis=1).iloc[-5] - 1
    df_ei_latest = (df_gr_latest + 1) / (df_total_gr_latest + 1) * 100

    df_combined = pd.concat(
        [df_latest, df_latest_diff, df_share_latest, df_share_latest_diff, df_gr_latest, df_ei_latest], axis=1)
    df_combined.columns = ['最新滚动年销售额',
                           '净增长',
                           '份额',
                           '份额同比变化',
                           '同比增长率',
                           'EI']

    return df_combined


'''
def index(request):
    sql = sqlparse('MAT', 'Value', " III = 'C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂，单一用药'")  # 读取ARB市场的滚动年销售额数据
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    pivoted = pd.pivot_table(df,
                             values='AMOUNT',  # 数据透视汇总值为AMOUNT字段，一般保持不变
                             index='DATE',  # 数据透视行为DATE字段，一般保持不变
                             columns='MOLECULE',  # 数据透视列为MOLECULE字段，该字段以后应跟随分析需要动态传参
                             aggfunc=np.sum)  # 数据透视汇总方式为求和，一般保持不变
    if pivoted.empty is False:
        pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)  # 结果按照最后一个DATE表现排序

    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]['select'] = value

        # 以后可以后端通过列表为每个多选控件传递备选项
        # option_list可以通过sql Distinct语句或Pandas的Unique方法获得，在此不再赘述
        mselect_dict[key]['options'] = get_distinct_list(value, DB_TABLE)

    context = {
        'market_size': kpi(pivoted)[0],
        'market_gr': kpi(pivoted)[1],
        'market_cagr': kpi(pivoted)[2],
        'ptable': ptable(pivoted).to_html(),

        'mselect_dict': mselect_dict
    }
    return render(request, 'chpa_data/analysis.html', context)
'''


# 只保留初始化表单备选项的功能
def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]['select'] = value
        mselect_dict[key]['options'] = get_distinct_list(value, DB_TABLE)

    context = {
        'mselect_dict': mselect_dict
    }
    return render(request, 'chpa_data/display.html', context)


# 下面是一个获得各个字段option_list的简单方法
def get_distinct_list(column, db_table):
    sql = "Select DISTINCT " + column + " From " + db_table
    df = pd.read_sql_query(sql, ENGINE)
    op_list = df.values.flatten().tolist()
    return op_list


def query(request):

    # 动态获取筛选参数,并处理成sql语句
    form_dict = dict(six.iterlists(request.GET))
    sql = sqlparse(form_dict)  # sql拼接

    # 将sql语句结果读取至Pandas Dataframe
    df = pd.read_sql_query(sql, ENGINE)

    dimension_selected = form_dict['DIMENSION_select'][0]
    #  如果字段名有空格为了SQL语句在预设字典中加了中括号的，这里要去除
    if dimension_selected[0] == '[':

        column = dimension_selected[1:][:-1]
    else:
        column = dimension_selected
    pivoted = pd.pivot_table(df,
                             values='AMOUNT',  # 数据透视汇总值为AMOUNT字段，一般保持不变
                             index='DATE',  # 数据透视行为DATE字段，一般保持不变
                             columns=column,  # 数据透视列为前端选择的分析维度
                             aggfunc=np.sum)  # 数据透视汇总方式为求和，一般保持不变
    if pivoted.empty is False:
        # 结果按照最后一个DATE表现排序
        pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)

    # 调整数据格式
    table = ptable(pivoted)
    table = table.to_html(formatters=build_formatters_by_col(table))

    context = {
        'market_size': str(kpi(pivoted)[0]),
        'market_gr': str(kpi(pivoted)[1]),
        'market_cagr': str(kpi(pivoted)[2]),
        # 'ptable': ptable(pivoted).to_html(),

        'ptable': table,
    }

    # 使用AJAX返回结果必须是json格式,不渲染具体页面
    return HttpResponse(json.dumps(context, ensure_ascii=False),
                        content_type="application/json charset=utf-8")


def build_formatters_by_col(df):
    format_abs = (lambda x: '{:,.0f}'.format(x))
    format_share = (lambda x: '{:.1%}'.format(x))
    format_gr = (lambda x: '{:.1%}'.format(x))
    format_currency = (lambda x: '¥{:,.0f}'.format(x))
    d = {}
    for column in df.columns:
        if '份额' in column or '贡献' in column:
            d[column] = format_share
        elif '价格' in column or '单价' in column:
            d[column] = format_currency
        elif '同比增长' in column or '增长率' in column or 'CAGR' in column or '同比变化' in column:
            d[column] = format_gr
        else:
            d[column] = format_abs
    return d


'''
def search(request, column, kw):
    # 最简单的单一字符串like，返回不重复的前10个结果
    sql = "SELECT DISTINCT %s FROM %s WHERE %s like '%%%s%%' LIMIT 0,10" % \
          (column, DB_TABLE, column, kw)

    try:
        df = pd.read_sql_query(sql, ENGINE)

        l = df.values.flatten().tolist()
        print(df, l, type(df), type(l))

        results_list = []
        for element in l:
            option_dict = {'name': element,
                           'value': element,
                           }
            results_list.append(option_dict)
        res = {
            "success": True,
            "results": results_list,
            "code": 200,
        }

    except Exception as e:

        res = {
            "success": False,
            "errMsg": e,
            "code": 0,
        }

    # 返回结果必须是json格式
    return HttpResponse(json.dumps(res, ensure_ascii=False),
                        content_type="application/json charset=utf-8")
'''
