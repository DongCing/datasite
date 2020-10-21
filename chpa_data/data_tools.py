from django.shortcuts import render
from sqlalchemy import create_engine
import pandas as pd


# 创建数据库连接引擎
ENGINE = create_engine('mysql+pymysql://root:111111@localhost:3306/dap')
DB_TABLE = 'chpa_data_data'


# 获取筛选数据
# period, unit 必选的两个筛选字段;filter_sql 为其它可选的筛选字段
'''def sqlparse(period, unit, filter_sql=None):
    
    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % (DB_TABLE, period, unit)
    if filter_sql is not None:
        # 其它可选的筛选字段，如有则以 And 连接自定义字符串
        sql = "%s And %s" % (sql, filter_sql)
    return sql'''


# 未来跟前端结合后更复杂的SQL语句拼接会写成下面这个趋势
'''
def sqlparse(context):
    # context为前端通过表单传来的字典
    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % \
          (DB_TABLE, context['period_selected'], context['unit_selected']) 
    # 未来可以通过进一步拼接字符串动态扩展sql语句
    # sql = sql_extent(sql, '[TC I]', context['tc_i_selected']) 
    return sql
'''
