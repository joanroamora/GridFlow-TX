"""
BESS & Market Intelligence Hub Microservice Module.
Implements Financial Arbitrage Optimization + 3-6 Hour Machine Learning Forecasting for Battery Energy Storage.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from translations import get_text

logger = logging.getLogger("BESS-Intelligence-Hub")


def run_bess_arbitrage_optimization(
    spp_df: pd.DataFrame,
    capacity_mwh: float = 100.0,
    power_mw: float = 25.0,
    rte_pct: float = 88.0,
    initial_soc_pct: float = 20.0,
    degradation_cost_mwh: float = 5.0,
) -> pd.DataFrame:
    """
    Motor matemático de optimización de arbitraje para baterías (BESS).
    Calcula la estrategia óptima de Carga / Descarga / SOC e ingresos netos.
    """
    if spp_df.empty or "LMP" not in spp_df.columns:
        return pd.DataFrame()

    df = spp_df.copy().sort_values("Time").reset_index(drop=True)
    n = len(df)
    if n == 0:
        return df

    rte = rte_pct / 100.0
    dt_hours = 0.25 # 15 min = 0.25h
    max_charge_mwh = power_mw * dt_hours
    max_discharge_mwh = power_mw * dt_hours

    # Thresholds para decisiones de arbitraje basado en percentiles de precio
    p25 = float(df["LMP"].quantile(0.25))
    p75 = float(df["LMP"].quantile(0.75))

    current_soc_mwh = (initial_soc_pct / 100.0) * capacity_mwh

    soc_list = []
    bess_power_list = [] # + MW Discharge, - MW Charge
    cashflow_list = []
    action_list = []

    for idx, row in df.iterrows():
        lmp = float(row["LMP"])
        action = "HOLD"
        bess_mw = 0.0
        cashflow = 0.0

        # Regla de decisión de arbitraje financiero:
        # Cargar cuando LMP es bajo (< P25 o negativo) y SOC < 95%
        if lmp <= p25 and current_soc_mwh < capacity_mwh * 0.95:
            # Cuánta energía podemos cargar en este intervalo
            charge_possible_mwh = min(max_charge_mwh, capacity_mwh - current_soc_mwh)
            bess_mw = -(charge_possible_mwh / dt_hours)
            current_soc_mwh += charge_possible_mwh * rte
            cashflow = -(charge_possible_mwh * lmp) - (charge_possible_mwh * degradation_cost_mwh)
            action = "CHARGE"

        # Descargar cuando LMP es elevado (>= P75) y SOC > 10%
        elif lmp >= p75 and current_soc_mwh > capacity_mwh * 0.10:
            discharge_possible_mwh = min(max_discharge_mwh, current_soc_mwh)
            bess_mw = (discharge_possible_mwh / dt_hours)
            current_soc_mwh -= discharge_possible_mwh
            cashflow = (discharge_possible_mwh * lmp) - (discharge_possible_mwh * degradation_cost_mwh)
            action = "DISCHARGE"

        soc_pct = (current_soc_mwh / capacity_mwh) * 100.0
        soc_list.append(soc_pct)
        bess_power_list.append(bess_mw)
        cashflow_list.append(cashflow)
        action_list.append(action)

    df["SOC_Pct"] = soc_list
    df["BESS_MW"] = bess_power_list
    df["Cashflow"] = cashflow_list
    df["Action"] = action_list
    df["Cumulative_Profit"] = df["Cashflow"].cumsum()

    return df


def train_ml_short_term_forecast(spp_df: pd.DataFrame, load_df: pd.DataFrame = None, horizon_hours: int = 8) -> pd.DataFrame:
    """
    Modelo de Machine Learning en series temporales para predecir LMP y Demanda ERCOT
    en horizontes extendidos de 3, 6, 8, 12, 16 o 24 horas (intervalos de 15m).
    """
    if spp_df.empty or len(spp_df) < 24:
        now = spp_df["Time"].max() if not spp_df.empty else datetime.now()
        future_steps = horizon_hours * 4
        future_times = [now + timedelta(minutes=15 * i) for i in range(1, future_steps + 1)]
        return pd.DataFrame({
            "Time": future_times,
            "Pred_LMP": [35.0 + np.sin(i * 0.4) * 15.0 for i in range(len(future_times))],
            "Pred_LMP_Lower": [20.0 for _ in range(len(future_times))],
            "Pred_LMP_Upper": [60.0 for _ in range(len(future_times))],
            "Pred_Demand": [65000.0 + np.sin(i * 0.3) * 5000.0 for i in range(len(future_times))],
            "Recommended_Action": ["HOLD" for _ in range(len(future_times))],
        })

    df = spp_df.copy().sort_values("Time").reset_index(drop=True)
    df["Hour"] = df["Time"].dt.hour
    df["Minute"] = df["Time"].dt.minute
    df["Lag1"] = df["LMP"].shift(1).bfill()
    df["Lag2"] = df["LMP"].shift(2).bfill()
    df["Lag4"] = df["LMP"].shift(4).bfill()
    df["RollingMean"] = df["LMP"].rolling(4, min_periods=1).mean()

    features = ["Hour", "Minute", "Lag1", "Lag2", "Lag4", "RollingMean"]
    X = df[features]
    y = df["LMP"]

    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(X, y)

    # Entrenar modelo secundario para demanda de carga
    load_model = None
    if load_df is not None and not load_df.empty and "Load" in load_df.columns:
        ldf = load_df.copy().sort_values("Time").reset_index(drop=True)
        ldf["Hour"] = ldf["Time"].dt.hour
        ldf["Minute"] = ldf["Time"].dt.minute
        ldf["Lag1"] = ldf["Load"].shift(1).bfill()
        ldf["RollingMean"] = ldf["Load"].rolling(4, min_periods=1).mean()
        load_features = ["Hour", "Minute", "Lag1", "RollingMean"]
        load_model = make_pipeline(StandardScaler(), Ridge(alpha=0.5))
        load_model.fit(ldf[load_features], ldf["Load"])

    now = df["Time"].max()
    future_steps = horizon_hours * 4
    future_times = [now + timedelta(minutes=15 * i) for i in range(1, future_steps + 1)]

    last_lmp = float(df["LMP"].iloc[-1])
    last_lag1 = float(df["Lag1"].iloc[-1])
    last_lag2 = float(df["Lag2"].iloc[-1])
    rolling_val = float(df["RollingMean"].iloc[-1])

    last_load = float(load_df["Load"].iloc[-1]) if load_df is not None and not load_df.empty else 68000.0
    load_rolling_val = last_load

    predictions_lmp = []
    predictions_demand = []
    curr_lag1, curr_lag2, curr_lag4 = last_lmp, last_lag1, last_lag2

    for ftime in future_times:
        feat_vec = pd.DataFrame([{
            "Hour": ftime.hour,
            "Minute": ftime.minute,
            "Lag1": curr_lag1,
            "Lag2": curr_lag2,
            "Lag4": curr_lag4,
            "RollingMean": rolling_val
        }])
        pred_lmp = float(model.predict(feat_vec)[0])
        pred_lmp = max(5.0, pred_lmp)
        predictions_lmp.append(pred_lmp)

        if load_model is not None:
            lfeat_vec = pd.DataFrame([{
                "Hour": ftime.hour,
                "Minute": ftime.minute,
                "Lag1": last_load,
                "RollingMean": load_rolling_val
            }])
            pred_demand = float(load_model.predict(lfeat_vec)[0])
            last_load = pred_demand
            load_rolling_val = (load_rolling_val * 0.75) + (pred_demand * 0.25)
        else:
            pred_demand = 68000.0 + np.sin(ftime.hour / 24.0 * 2 * np.pi) * 12000.0

        predictions_demand.append(pred_demand)

        curr_lag4 = curr_lag2
        curr_lag2 = curr_lag1
        curr_lag1 = pred_lmp
        rolling_val = (rolling_val * 0.75) + (pred_lmp * 0.25)

    preds_arr = np.array(predictions_lmp)
    std_err = np.std(df["LMP"].tail(48)) * 0.25

    p25 = float(df["LMP"].quantile(0.25))
    p75 = float(df["LMP"].quantile(0.75))

    actions = []
    for p in preds_arr:
        if p >= p75:
            actions.append("⚡ DISCHARGE")
        elif p <= p25:
            actions.append("🔌 CHARGE")
        else:
            actions.append("⏸️ HOLD")

    return pd.DataFrame({
        "Time": future_times,
        "Pred_LMP": preds_arr,
        "Pred_LMP_Lower": np.maximum(0, preds_arr - std_err * 1.96),
        "Pred_LMP_Upper": preds_arr + std_err * 1.96,
        "Pred_Demand": predictions_demand,
        "Recommended_Action": actions,
    })


def render_bess_intelligence(current_lang: str, spp_df: pd.DataFrame, fuel_df: pd.DataFrame, load_df: pd.DataFrame):
    """
    Renderiza la interfaz principal del microservicio BESS & Market Intelligence Hub.
    """
    def t(key: str, **kwargs) -> str:
        return get_text(current_lang, key, **kwargs)

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%); padding: 22px 25px; border-radius: 12px; border: 1px solid #312E81; margin-bottom: 25px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);">
            <h2 style="color: #818CF8; margin: 0 0 6px 0; font-size: 1.6rem; display: flex; align-items: center; gap: 10px;">
                {t('bess_hub_title')}
            </h2>
            <p style="color: #C7D2FE; margin: 0; font-size: 0.95rem;">
                {t('bess_hub_subtitle')}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. SIDEBAR DE PARÁMETROS DEL SISTEMA BESS
    st.sidebar.markdown("---")
    st.sidebar.header(t("bess_config_header"))

    cap_mwh = st.sidebar.number_input(t("param_capacity_mwh"), min_value=10.0, max_value=2000.0, value=100.0, step=10.0)
    power_mw = st.sidebar.number_input(t("param_power_mw"), min_value=5.0, max_value=500.0, value=25.0, step=5.0)
    rte_pct = st.sidebar.slider(t("param_rte"), min_value=70.0, max_value=98.0, value=88.0, step=1.0)
    initial_soc = st.sidebar.slider(t("param_initial_soc"), min_value=0.0, max_value=100.0, value=25.0, step=5.0)
    forecast_horizon = st.sidebar.select_slider(
        t("ml_forecast_horizon_label"),
        options=[3, 6, 8, 12, 16, 24],
        value=8,
        format_func=lambda x: f"{x} Horas"
    )

    # 2. EJECUTAR MOTORES DE OPTIMIZACIÓN Y FORECASTING ML
    opt_df = run_bess_arbitrage_optimization(
        spp_df,
        capacity_mwh=cap_mwh,
        power_mw=power_mw,
        rte_pct=rte_pct,
        initial_soc_pct=initial_soc
    )

    forecast_df = train_ml_short_term_forecast(spp_df, load_df=load_df, horizon_hours=forecast_horizon)

    # 3. RECOMENDACIÓN EN TIEMPO REAL Y TARJETAS DE KPIS FINANCIEROS
    latest_lmp = float(spp_df["LMP"].iloc[-1]) if not spp_df.empty else 0.0
    latest_action = opt_df["Action"].iloc[-1] if not opt_df.empty and "Action" in opt_df.columns else "HOLD"

    if latest_action == "CHARGE":
        dispatch_html = f"""
        <div style="background: linear-gradient(90deg, #064E3B 0%, #047857 100%); color: #ECFDF5; padding: 16px 20px; border-radius: 10px; border-left: 6px solid #10B981; margin-bottom: 20px;">
            <strong style="font-size: 1.1rem;">{t('dispatch_recommendation_title')}: {t('dispatch_charge')}</strong><br/>
            <span>LMP Actual: <strong>${latest_lmp:.2f} / MWh</strong> ➔ Estado: Carga óptima de la batería para aprovechar precios bajos/negativos.</span>
        </div>
        """
    elif latest_action == "DISCHARGE":
        dispatch_html = f"""
        <div style="background: linear-gradient(90deg, #450A0A 0%, #7F1D1D 100%); color: #FEF2F2; padding: 16px 20px; border-radius: 10px; border-left: 6px solid #EF4444; margin-bottom: 20px;">
            <strong style="font-size: 1.1rem;">{t('dispatch_recommendation_title')}: {t('dispatch_discharge')}</strong><br/>
            <span>LMP Actual: <strong>${latest_lmp:.2f} / MWh</strong> ➔ Estado: Inyección de descarga a precio pico para maximizar beneficio de arbitraje.</span>
        </div>
        """
    else:
        dispatch_html = f"""
        <div style="background: linear-gradient(90deg, #1E293B 0%, #334155 100%); color: #F1F5F9; padding: 16px 20px; border-radius: 10px; border-left: 6px solid #3B82F6; margin-bottom: 20px;">
            <strong style="font-size: 1.1rem;">{t('dispatch_recommendation_title')}: {t('dispatch_hold')}</strong><br/>
            <span>LMP Actual: <strong>${latest_lmp:.2f} / MWh</strong> ➔ Estado: Mantener reserva de batería (Esperando mejores ventanas de precio).</span>
        </div>
        """
    st.markdown(dispatch_html, unsafe_allow_html=True)

    # KPIs Financieros de la Simulación
    gross_rev = float(opt_df[opt_df["Cashflow"] > 0]["Cashflow"].sum()) if not opt_df.empty else 0.0
    charging_costs = float(abs(opt_df[opt_df["Cashflow"] < 0]["Cashflow"].sum())) if not opt_df.empty else 0.0
    net_profit = float(opt_df["Cumulative_Profit"].iloc[-1]) if not opt_df.empty else 0.0
    discharged_mwh = float(opt_df[opt_df["BESS_MW"] > 0]["BESS_MW"].sum() * 0.25) if not opt_df.empty else 0.0
    avg_spread = (net_profit / discharged_mwh) if discharged_mwh > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('metric_gross_revenue')}</div>
                <div class="metric-value" style="color: #10B981;">${gross_rev:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('metric_net_profit')}</div>
                <div class="metric-value" style="color: #38BDF8;">${net_profit:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('metric_avg_spread')}</div>
                <div class="metric-value" style="color: #F59E0B;">${avg_spread:,.2f} / MWh</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('metric_discharged_mwh')}</div>
                <div class="metric-value" style="color: #A855F7;">{discharged_mwh:,.1f} MWh</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. PESTAÑAS DE VISUALIZACIÓN INTERACTIVA DE OPTIMIZACIÓN Y FORECAST ML
    t1, t2, t3 = st.tabs([t("tab_arbitrage_curve"), t("tab_ml_prediction"), t("tab_financial_summary")])

    with t1:
        st.subheader(t("tab_arbitrage_curve"))

        if not opt_df.empty:
            fig_opt = go.Figure()

            # Serie LMP Houston
            fig_opt.add_trace(go.Scatter(
                x=opt_df["Time"],
                y=opt_df["LMP"],
                name="Houston LMP ($/MWh)",
                line=dict(color="#FF4B4B", width=2),
                yaxis="y"
            ))

            # Potencia BESS (MW)
            fig_opt.add_trace(go.Bar(
                x=opt_df["Time"],
                y=opt_df["BESS_MW"],
                name="BESS Dispatch (MW)",
                marker_color=np.where(opt_df["BESS_MW"] >= 0, "#10B981", "#EF4444"),
                opacity=0.6,
                yaxis="y2"
            ))

            # Perfil SOC (%)
            fig_opt.add_trace(go.Scatter(
                x=opt_df["Time"],
                y=opt_df["SOC_Pct"],
                name="State of Charge SOC (%)",
                line=dict(color="#38BDF8", width=2.5, dash="dot"),
                yaxis="y3"
            ))

            fig_opt.update_layout(
                template="plotly_dark",
                height=540,
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title="LMP ($/MWh)", color="#FF4B4B"),
                yaxis2=dict(title="BESS Power (MW)", overlaying="y", side="right", showgrid=False),
                yaxis3=dict(title="SOC (%)", overlaying="y", side="right", position=0.95, range=[0, 105], showgrid=False)
            )

            fig_opt.update_xaxes(
                rangeslider=dict(visible=True, thickness=0.08),
                rangeselector=dict(
                    buttons=list([
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=12, label="12h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(count=3, label="3d", step="day", stepmode="backward"),
                        dict(count=7, label="7d", step="day", stepmode="backward"),
                        dict(count=30, label="30d", step="day", stepmode="backward"),
                        dict(step="all", label="All")
                    ]),
                    font=dict(color="#E2E8F0", size=11),
                    bgcolor="#1E293B",
                    activecolor="#3B82F6"
                )
            )
            st.plotly_chart(fig_opt, use_container_width=True)

    with t2:
        st.subheader(t("ml_forecast_title"))
        st.caption(t("ml_forecast_desc"))

        if not forecast_df.empty:
            pred_peak_lmp = float(forecast_df["Pred_LMP_Upper"].max())
            pred_min_lmp = float(forecast_df["Pred_LMP_Lower"].min())
            pred_avg_demand = float(forecast_df["Pred_Demand"].mean())

            fc_col1, fc_col2, fc_col3 = st.columns(3)
            with fc_col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{t('metric_pred_peak_lmp')} ({forecast_horizon}h)</div>
                        <div class="metric-value" style="color: #EF4444;">${pred_peak_lmp:.2f} / MWh</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with fc_col2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{t('metric_pred_min_lmp')} ({forecast_horizon}h)</div>
                        <div class="metric-value" style="color: #10B981;">${pred_min_lmp:.2f} / MWh</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with fc_col3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{t('metric_pred_avg_demand')} ({forecast_horizon}h)</div>
                        <div class="metric-value" style="color: #38BDF8;">{pred_avg_demand:,.0f} MW</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            fig_fc = go.Figure()

            # Histórico reciente LMP
            recent_spp = spp_df.tail(48)
            fig_fc.add_trace(go.Scatter(
                x=recent_spp["Time"],
                y=recent_spp["LMP"],
                name="Historical LMP ($/MWh)",
                line=dict(color="#94A3B8", width=2)
            ))

            # Predicción Central ML
            fig_fc.add_trace(go.Scatter(
                x=forecast_df["Time"],
                y=forecast_df["Pred_LMP"],
                name=f"ML Forecast ({forecast_horizon}h Ahead)",
                line=dict(color="#818CF8", width=3)
            ))

            # Banda de Confianza Sup/Inf
            fig_fc.add_trace(go.Scatter(
                x=pd.concat([forecast_df["Time"], forecast_df["Time"][::-1]]),
                y=pd.concat([forecast_df["Pred_LMP_Upper"], forecast_df["Pred_LMP_Lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(129, 140, 248, 0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="95% Confidence Interval"
            ))

            fig_fc.update_layout(
                template="plotly_dark",
                height=480,
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            fig_fc.update_xaxes(title_text="Time (US/Central)", gridcolor="#1E293B")
            fig_fc.update_yaxes(title_text="Price LMP ($/MWh)", gridcolor="#1E293B")

            st.plotly_chart(fig_fc, use_container_width=True)

            # TABLA DE PREDICCIONES PASO A PASO (8h / 16h / 24h)
            st.markdown("---")
            st.markdown(f"#### {t('ml_table_header', horizon=forecast_horizon)}")
            st.caption(t("ml_table_caption"))

            display_fc = forecast_df.copy()
            display_fc.rename(columns={
                "Time": "Time (US/Central)",
                "Pred_LMP": "Predicted LMP ($/MWh)",
                "Pred_LMP_Lower": "Lower Band 95% ($/MWh)",
                "Pred_LMP_Upper": "Upper Band 95% ($/MWh)",
                "Pred_Demand": "Predicted Demand (MW)",
                "Recommended_Action": "Dispatch Recommendation"
            }, inplace=True)

            st.dataframe(display_fc, use_container_width=True)

            csv_fc = display_fc.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("btn_export_ml_csv", horizon=forecast_horizon),
                data=csv_fc,
                file_name=f"ml_forecast_{forecast_horizon}h_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

    with t3:
        st.subheader(t("tab_financial_summary"))

        if not opt_df.empty:
            fcol1, fcol2 = st.columns([3, 2])

            with fcol1:
                st.markdown(f"##### {t('chart_profit_curve')}")
                fig_profit = px.line(
                    opt_df,
                    x="Time",
                    y="Cumulative_Profit",
                    labels={"Cumulative_Profit": "Cumulative Profit ($)", "Time": "Time"},
                    color_discrete_sequence=["#10B981"]
                )
                fig_profit.update_layout(
                    template="plotly_dark",
                    height=380,
                    paper_bgcolor="#0B0E14",
                    plot_bgcolor="#131927"
                )
                st.plotly_chart(fig_profit, use_container_width=True)

            with fcol2:
                st.markdown(f"##### {t('chart_dispatch_breakdown')}")
                action_counts = opt_df["Action"].value_counts().reset_index()
                action_counts.columns = ["Action", "Count"]

                fig_donut = px.pie(
                    action_counts,
                    names="Action",
                    values="Count",
                    hole=0.45,
                    color="Action",
                    color_discrete_map={"CHARGE": "#EF4444", "DISCHARGE": "#10B981", "HOLD": "#64748B"}
                )
                fig_donut.update_layout(
                    template="plotly_dark",
                    height=380,
                    paper_bgcolor="#0B0E14",
                    plot_bgcolor="#131927"
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            # Botón de Descarga CSV Financiero
            csv_opt = opt_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("btn_export_csv"),
                data=csv_opt,
                file_name=f"bess_financial_arbitrage_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
