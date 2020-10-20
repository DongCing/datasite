from django.http import HttpResponse
from django.shortcuts import render
from sqlalchemy import create_engine
import pandas as pd

# 创建数据库连接引擎
ENGINE = create_engine('mysql+pymysql://root:111111@localhost:3306/dap')


def index(request):
    # 标准sql语句，此处为测试返回数据库data表的数据条目n，之后可以用python处理字符串的方式动态扩展
    sql = "Select count(*) from chpa_data_data"
    # 将sql语句结果读取至Pandas Dataframe
    df = pd.read_sql_query(sql, ENGINE)

    context = {'data': df}
    return render(request, 'chpa_data/display.html', context)
    # return HttpResponse(df.to_html())
