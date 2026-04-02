import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1. 고정 포트폴리오 데이터 설정 (신규 이미지 반영)
FIXED_PORTFOLIO = {
    '068270.KS': 145.63, # 셀트리온
    'CELC': 94.32,       # 셀큐리티
    'VERA': 514.67,      # 베라 테라퓨틱스
    'VRTX': 38.48        # 버텍스 파마슈티컬스
}
START_DATE = "2026-03-27"
FINAL_TARGET_DATE = datetime(2026, 6, 19)

st.set_page_config(page_title="바이오 주식 포트폴리오 분석", layout="wide")

st.title("🧬 1조 BIT 포트폴리오 성과 분석")
st.markdown(f"""
* **투자 시작일**: {START_DATE}
* **구성 종목**: 셀트리온, 셀큐리티, 베라 테라퓨틱스, 버텍스 파마슈티컬스
* **최종 평가 예정일**: 2026-06-19
""")

# 2. 사용자 입력: 중간 점검 날짜 (현재 날짜인 4월 2일 기준으로 설정)
check_date = st.date_input("중간 점검 날짜를 선택하세요", datetime(2026, 4, 2))

if st.button("📈 성과 분석 실행"):
    try:
        tickers = list(FIXED_PORTFOLIO.keys())
        all_tickers = tickers + ['KRW=X']
        
        with st.spinner('최신 시장 데이터를 불러오는 중...'):
            # 야후 파이낸스 데이터 추출
            data = yf.download(all_tickers, start=START_DATE, end=check_date.strftime('%Y-%m-%d'), auto_adjust=True)['Close']
        
        if data.empty or len(data) < 1:
            st.warning("선택하신 날짜에 대한 시장 데이터가 아직 없습니다. 날짜를 확인해 주세요.")
        else:
            fx_rates = data['KRW=X']
            stock_data = data.drop(columns=['KRW=X'])

            # 자산 가치 계산 (원화 환산 통합)
            portfolio_val_df = pd.DataFrame(index=stock_data.index)
            for ticker in tickers:
                share_count = FIXED_PORTFOLIO[ticker]
                if '.KS' in ticker or '.KQ' in ticker:
                    # 국내 주식 (셀트리온)
                    portfolio_val_df[ticker] = stock_data[ticker] * share_count
                else:
                    # 해외 주식 (달러 주가 * 환율 * 주식수)
                    portfolio_val_df[ticker] = stock_data[ticker] * fx_rates * share_count

            # 결측치 보정 (휴장일 처리)
            portfolio_val_df = portfolio_val_df.ffill().dropna()
            total_val_krw = portfolio_val_df.sum(axis=1)

            # 핵심 성과 지표 계산
            initial_val = total_val_krw.iloc[0]
            current_val = total_val_krw.iloc[-1]
            current_return = (current_val / initial_val - 1) * 100

            # 3. 결과 대시보드 표시
            col1, col2, col3 = st.columns(3)
            col1.metric("초기 투자금 (03/27)", f"₩{initial_val:,.0f}")
            col2.metric(f"현재 자산 가치 ({check_date})", f"₩{current_val:,.0f}", f"{current_return:.2f}%")
            
            # 6월 19일 기준 수익률 공개 제한
            if datetime.now() < FINAL_TARGET_DATE:
                col3.metric("최종 수익률 (06/19)", "Not available")
            else:
                final_ret = (current_val / initial_val - 1) * 100
                col3.metric("최종 수익률 (06/19)", f"{final_ret:.2f}%")

            # 그래프 시각화
            st.subheader("📊 포트폴리오 누적 수익률 추이 (원화 기준)")
            cumulative_ret_pct = (total_val_krw / initial_val - 1) * 100
            
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(cumulative_ret_pct.index, cumulative_ret_pct, color='#27ae60', linewidth=3, label='Portfolio')
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5) # 원금 기준선
            ax.set_ylabel("Return (%)")
            ax.grid(True, alpha=0.2)
            st.pyplot(fig)

            # 상세 데이터 확인
            with st.expander("📝 상세 종목별 평가 금액 확인"):
                st.write("각 종목의 주가와 환율이 반영된 실시간 원화 평가 금액입니다.")
                st.dataframe(portfolio_val_df.tail().style.format("₩{:,.0f}"))

    except Exception as e:
        st.error(f"분석 도중 오류가 발생했습니다: {e}")
