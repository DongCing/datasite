from django.http import HttpResponse
from django.shortcuts import render
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

# 创建数据库连接引擎
ENGINE = create_engine('mysql+pymysql://root:111111@localhost:3306/dap')
DB_TABLE = 'chpa_data_data'

'''
def index(request):
    # 标准sql语句，此处为测试返回数据库data表的数据条目n，之后可以用python处理字符串的方式动态扩展
    sql = "Select count(*) from chpa_data_data"
    # 将sql语句结果读取至Pandas Dataframe
    df = pd.read_sql_query(sql, ENGINE)

    context = {'data': df}
    return render(request, 'chpa_data/display.html', context)
    # return HttpResponse(df.to_html())
'''


# 获取筛选数据
# period, unit 必选的两个筛选字段;filter_sql 为其它可选的筛选字段
def sqlparse(period, unit, filter_sql=None):
    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % (DB_TABLE, period, unit)
    if filter_sql is not None:
        # 其它可选的筛选字段，如有则以 And 连接自定义字符串
        sql = "%s And %s" % (sql, filter_sql)
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

    context = {
        'market_size': kpi(pivoted)[0],
        'market_gr': kpi(pivoted)[1],
        'market_cagr': kpi(pivoted)[2],
        'ptable': ptable(pivoted).to_html()
    }
    return render(request, 'chpa_data/display.html', context)
