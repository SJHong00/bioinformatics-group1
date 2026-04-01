import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1. 고정 데이터 설정
FIXED_PORTFOLIO = {
    '068270.KS': 145.63,  # 셀트리온 (종목코드 068270)
    'CELC': 94.32,
    'VERA': 514.67,
    'VRTX': 38.48
}
START_DATE = "2026-03-27"
FINAL_TARGET_DATE = datetime(2026, 6, 19)

st.title("🧪 1조 바이오 포트폴리오 성과 분석기")
st.info(f"투자 시작일: {START_DATE} | 최종 평가일: 2026-06-19")

# 2. 사용자 입력: 중간 점검 날짜
check_date = st.date_input("중간 점검 날짜를 선택하세요", datetime(2026, 3, 31))

if st.button("성과 분석 실행"):
    try:
        tickers = list(FIXED_PORTFOLIO.keys())
        shares = list(FIXED_PORTFOLIO.values())
        
        # 데이터 다운로드 (시작일 ~ 오늘/최종일 중 빠른 날까지)
        all_tickers = tickers + ['KRW=X']
        # 미래 날짜 데이터를 요청하면 야후 파이낸스는 현재까지의 데이터만 제공함
        data = yf.download(all_tickers, start=START_DATE, end=check_date.strftime('%Y-%m-%d'), auto_adjust=True)['Close']
        
        if data.empty:
            st.warning("선택하신 날짜에 대한 데이터가 아직 없습니다.")
        else:
            fx_rates = data['KRW=X']
            stock_data = data.drop(columns=['KRW=X'])

            # 원화 환산 가치 계산
            portfolio_val_df = pd.DataFrame(index=stock_data.index)
            for ticker in tickers:
                share_count = FIXED_PORTFOLIO[ticker]
                if '.KS' in ticker:
                    portfolio_val_df[ticker] = stock_data[ticker] * share_count
                else:
                    portfolio_val_df[ticker] = stock_data[ticker] * fx_rates * share_count

            portfolio_val_df = portfolio_val_df.ffill().dropna()
            total_val_krw = portfolio_val_df.sum(axis=1)

            # 수익률 계산
            initial_val = total_val_krw.iloc[0]
            current_val = total_val_krw.iloc[-1]
            current_return = (current_val / initial_val - 1) * 100

            # 3. 화면 표시
            col1, col2 = st.columns(2)
            col1.metric("초기 투자금", f"₩{initial_val:,.0f}")
            col1.metric(f"{check_date} 기준 자산", f"₩{current_val:,.0f}")
            
            # 최종 수익률 조건부 표시
            if datetime.now() < FINAL_TARGET_DATE:
                col2.metric("최종 수익률 (2026-06-19)", "Not available")
                st.write("⚠️ 최종 수익률은 2026년 6월 19일 이후에 공개됩니다.")
            else:
                # 6월 19일 이후일 경우의 로직 (현재는 도달 전이므로 안내만)
                col2.metric("최종 수익률", "데이터 집계 중...")

            st.subheader(f"📈 {START_DATE} ~ {check_date} 수익률 추이")
            portfolio_pct = (total_val_krw / initial_val - 1) * 100
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(portfolio_pct.index, portfolio_pct, color='green', linewidth=2)
            ax.set_ylabel("Return (%)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

            # 종목별 상세 현황
            with st.expander("종목별 원화 환산 가치 상세"):
                st.dataframe(portfolio_val_df.tail())

    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
