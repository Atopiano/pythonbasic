import streamlit as st
from datetime import datetime, timedelta
from pykrx import stock
import pandas as pd
import os
from pytz import timezone
import plotly.express as px
from pandas_datareader import data as pdr
import yfinance as yfin
yfin.pdr_override()
from   sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot    as plt
import seaborn              as sns


def stock_price(stock_name, code, start_day, end_day):
    '''
    검색 종목 주식의 날짜별 고가, 저가, 종가와 실시간 가격을 시각화합니다.
    '''
    try:
        df = stock.get_market_ohlcv(start_day.strftime('%Y%m%d'), end_day.strftime('%Y%m%d'), code)
        st.metric(stock_name, value = df.iloc[-1, 3], delta = str(df.iloc[-1, 6]) + '%')
        st.line_chart(df[['고가','저가','종가']], use_container_width= True)
    except Exception as E:
        st.write('stock_price 함수 오류')
        st.write(E)

def get_world_index(ticker, start_day, end_day):
    '''
    세계 주요 주가 지수의 일별 OHCLV(Open, High, Close, Low, Volume) 데이터를 담은 DataFrame을 반환한다.
    '''
    return pdr.get_data_yahoo(ticker, start_day, end_day)

def get_normalization(df_ts):
    """
    데이터를 MinMaxScaler로 정규화한 결과를 반환한다.
    """
    return MinMaxScaler().fit_transform(df_ts)

def main():
    
    # 경로 세팅
    filePath, fileName = os.path.split(__file__)
    
    # 페이지 세팅
    st.set_page_config(page_title = "대국민 주식 분석 프로젝트", layout='wide', initial_sidebar_state='collapsed',)
    
    # 날짜
    now = datetime.today()
    end_day = datetime(now.year, now.month, now.day)
    start_day = end_day - timedelta(days = 365)

    # 사이드바 정보
    with st.sidebar:
        # 코스피 정보
        kospi_df = stock.get_index_fundamental(start_day.strftime('%Y%m%d'), end_day.strftime('%Y%m%d'), "1001") # 코스피
        st.metric('코스피 지수', value = kospi_df.iloc[-1, 0], delta = str(kospi_df.iloc[-1, 1]) + '%')
        st.line_chart(kospi_df['종가'], use_container_width = True)

        # 세계 주가 종가 정보
        # Tickers of World Indexes
        WORLD_INDEX_TICKERS = [ {'ticker':'^GSPC',     'nation':'US',          'name':'S&P 500'},
                                {'ticker':'^IXIC',     'nation':'US',          'name':'NASDAQ Composite'},
                                {'ticker':'^N225',     'nation':'Japan',       'name':'Nikkei 225'},
                                {'ticker':'399001.SZ', 'nation':'China',       'name':'Shenzhen Index'},
                                {'ticker':'^KS11',     'nation':'Korea',       'name':'KOSPI Composite Index'},
        ]
        fig = plt.figure(figsize=(20, 10)) # 그래프 크기 조절
        for index in WORLD_INDEX_TICKERS:
            index_df    = get_world_index(index['ticker'], start_day, end_day)[['Close']][::30]
            index_df[:]    = get_normalization(index_df)
            if index['ticker'] == '^KS11':
                st.line_chart(index_df['Close'], use_container_width = True)
            else:
                st.line_chart(index_df['Close'], use_container_width = True)

    # 필요 데이터 불러오기
    base_df = pd.read_csv(os.path.join(filePath, 'data', '상장법인목록.csv'))
    
    # 입력 받은 종목명 저장
    stock_name = st.text_input('정확한 종목명을 입력해주세요😊', '삼성전자')
    
    if stock_name in tuple(base_df['cooperation']):
        # 종목명으로 티커 찾기
        code = base_df.loc[base_df['cooperation'] == stock_name].iloc[0,0]
        
        # 화면 분할
        col1, col2 = st.columns(2)
        with col1:
            # 시각화
            stock_price(stock_name, code, start_day, end_day)
        with col2:
            st.write(' ')
            st.write(' ')
            st.markdown('###### 최근 종목 보조지표')
            st.write(' ')
            st.write(' ')
            
            st.dataframe(stock.get_market_fundamental(start_day, end_day, code).tail(1).T, use_container_width= True)
        
        number = st.slider('거래일 기준 며칠의 정보를 조회하시겠습니까?', 0, 365, 30)
        start_day = end_day - timedelta(days = number)
        
        
        col3, col4, col5 = st.columns(3)
        maesoo = pd.DataFrame(stock.get_market_trading_volume_by_date(start_day, end_day, code, on='매수').sum()).reset_index()[:-1]
        maedo = pd.DataFrame(stock.get_market_trading_volume_by_date(start_day, end_day, code, on='매도').sum()).reset_index()[:-1]
        with col3:
            fig1 = px.pie(maesoo, values = 0, names = 'index', title = '순매수 점유율')
            st.plotly_chart(fig1, use_container_width= True)
        with col4:
            fig2 = px.pie(maedo, values = 0, names = 'index', title = '순매도 점유율')
            st.plotly_chart(fig2, use_container_width= True)
        with col5:
            st.write(' ')
            st.write(' ')
            st.markdown('###### 매수/매도 비교 그래프')
            st.write(' ')
            data_mae = pd.merge(maesoo, maedo, how = 'inner', on = 'index')
            data_mae.columns = ['주체','매수','매도']
            st.bar_chart(data_mae, x = '주체', y = ['매수', '매도'], use_container_width= True)
            
            
            
    elif stock_name not in tuple(base_df['cooperation']):
        st.write('❗정확한 종목명을 입력하세요❗')

if __name__ == "__main__":
    main()
