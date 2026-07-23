"""
GridFlow Live Analytics Microservice Module.
Monitors real-time ERCOT telemetry: Houston LMP nodal pricing, fuel generation mix, system demand, and BESS activity.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging

from translations import get_text
from observability.telemetry_tracer import trace_span

logger = logging.getLogger("Live-Analytics-Service")


@trace_span("render_live_analytics")
def render_live_analytics(
    current_lang: str,
    spp_df: pd.DataFrame,
    fuel_df: pd.DataFrame,
    load_df: pd.DataFrame,
):
    """
    Renderiza la interfaz principal del microservicio GridFlow Live Analytics.
    """

    def t(key: str, **kwargs) -> str:
        return get_text(current_lang, key, **kwargs)

    # 1. SIDEBAR CONFIGURATION & ALERT THRESHOLD
    st.sidebar.markdown("---")
    st.sidebar.header(t("sidebar_config"))
    alert_threshold = st.sidebar.number_input(
        t("alert_threshold_label"),
        min_value=10.0,
        max_value=5000.0,
        value=100.0,
        step=10.0,
        help=t("alert_threshold_help"),
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader(t("data_control_header"))
    if st.sidebar.button(t("refresh_btn")):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader(t("tech_specs_header"))
    st.sidebar.markdown(t("tech_specs_body"))

    # 2. METRICAS CALCULADAS & BANNERS
    latest_lmp = float(spp_df["LMP"].iloc[-1]) if not spp_df.empty else 0.0
    prev_lmp = float(spp_df["LMP"].iloc[-2]) if len(spp_df) > 1 else latest_lmp
    lmp_delta = latest_lmp - prev_lmp

    latest_bess = (
        float(fuel_df["Power Storage"].iloc[-1])
        if "Power Storage" in fuel_df.columns
        else 0.0
    )
    prev_bess = (
        float(fuel_df["Power Storage"].iloc[-2])
        if len(fuel_df) > 1 and "Power Storage" in fuel_df.columns
        else latest_bess
    )
    bess_delta = latest_bess - prev_bess

    max_lmp_today = float(spp_df["LMP"].max()) if not spp_df.empty else 0.0
    avg_lmp_today = float(spp_df["LMP"].mean()) if not spp_df.empty else 0.0
    latest_load = float(load_df["Load"].iloc[-1]) if not load_df.empty else 0.0

    # Banner de Alerta Dinámico
    if latest_lmp > alert_threshold:
        st.markdown(
            f"""
            <div class="alert-banner-high">
                <strong>{t('alert_high_title')}</strong><br/>
                {t('alert_high_body', lmp=latest_lmp, threshold=alert_threshold)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="alert-banner-normal">
                <strong>{t('alert_normal_title')}</strong><br/>
                {t('alert_normal_body', lmp=latest_lmp, threshold=alert_threshold)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tarjetas de KPIS en 5 Columnas
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_lmp')}</div>
                <div class="metric-value">${latest_lmp:.2f}</div>
                <div style="color: {'#10B981' if lmp_delta <= 0 else '#EF4444'}; font-size: 0.85rem; font-weight: 600;">
                    {'▼' if lmp_delta < 0 else '▲'} {abs(lmp_delta):.2f} (Interval 15m)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        bess_status_str = (
            t("bess_status_discharging")
            if latest_bess > 50
            else (
                t("bess_status_charging")
                if latest_bess < -50
                else t("bess_status_neutral")
            )
        )
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_bess', status=bess_status_str)}</div>
                <div class="metric-value">{latest_bess:+,.0f} MW</div>
                <div style="color: {'#10B981' if bess_delta >= 0 else '#F59E0B'}; font-size: 0.85rem; font-weight: 600;">
                    {'▲' if bess_delta >= 0 else '▼'} {abs(bess_delta):,.0f} MW (Interval 5m)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_max_lmp')}</div>
                <div class="metric-value">${max_lmp_today:.2f}</div>
                <div style="color: #8E9BAE; font-size: 0.82rem;">Houston Hub RT 15m</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_avg_lmp')}</div>
                <div class="metric-value">${avg_lmp_today:.2f}</div>
                <div style="color: #8E9BAE; font-size: 0.82rem;">Promedio Móvil</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_load')}</div>
                <div class="metric-value">{latest_load:,.0f} MW</div>
                <div style="color: #38BDF8; font-size: 0.82rem;">ERCOT System Total</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 3. CONTROL TEMPORAL DINÁMICO
    st.markdown(
        f"""
        <div class="time-control-card">
            <div class="time-control-title">{t('time_control_header')}</div>
        """,
        unsafe_allow_html=True,
    )

    tc_col1, tc_col2, tc_col3 = st.columns([2, 3, 2])

    with tc_col1:
        preset_dict = t("time_presets")
        preset_keys = list(preset_dict.keys())
        preset_labels = [preset_dict[k] for k in preset_keys]

        selected_preset_label = st.selectbox(
            t("time_preset_label"),
            options=preset_labels,
            index=0,
            key="time_preset_selectbox",
        )
        active_preset = preset_keys[preset_labels.index(selected_preset_label)]

    with tc_col2:
        min_time_val = (
            spp_df["Time"].min()
            if not spp_df.empty
            else datetime.now() - timedelta(hours=24)
        )
        max_time_val = spp_df["Time"].max() if not spp_df.empty else datetime.now()

        if active_preset == "custom":
            time_range = st.slider(
                t("time_range_slider"),
                min_value=min_time_val.to_pydatetime(),
                max_value=max_time_val.to_pydatetime(),
                value=(min_time_val.to_pydatetime(), max_time_val.to_pydatetime()),
                format="HH:mm",
                key="custom_time_slider",
            )
            custom_start, custom_end = time_range[0], time_range[1]
        else:
            custom_start, custom_end = None, None
            st.info(
                f"📅 Window: {min_time_val.strftime('%H:%M')} ➔ {max_time_val.strftime('%H:%M')} (US/Central)"
            )

    with tc_col3:
        resample_dict = t("resample_options")
        resample_keys = list(resample_dict.keys())
        resample_labels = [resample_dict[k] for k in resample_keys]

        selected_resample_label = st.selectbox(
            t("resample_label"),
            options=resample_labels,
            index=0,
            key="resample_selectbox",
        )
        active_resample = resample_keys[resample_labels.index(selected_resample_label)]

    st.markdown("</div>", unsafe_allow_html=True)

    # Filtrado Supeditado
    def filter_and_resample_dataset(
        df, time_col="Time", preset="all", start_t=None, end_t=None, resample_freq="raw"
    ):
        if df.empty or time_col not in df.columns:
            return df.copy()

        fdf = df.copy()
        max_t = fdf[time_col].max()

        if preset == "6h":
            cutoff = max_t - timedelta(hours=6)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "12h":
            cutoff = max_t - timedelta(hours=12)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "24h":
            cutoff = max_t - timedelta(hours=24)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "3d":
            cutoff = max_t - timedelta(days=3)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "7d":
            cutoff = max_t - timedelta(days=7)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "14d":
            cutoff = max_t - timedelta(days=14)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "30d":
            cutoff = max_t - timedelta(days=30)
            fdf = fdf[fdf[time_col] >= cutoff]
        elif preset == "custom" and start_t and end_t:
            fdf = fdf[
                (fdf[time_col] >= pd.to_datetime(start_t))
                & (fdf[time_col] <= pd.to_datetime(end_t))
            ]

        if fdf.empty:
            fdf = df.copy()

        if resample_freq != "raw":
            rule_map = {
                "15m": "15min",
                "30m": "30min",
                "1h": "1h",
                "6h": "6h",
                "1d": "1D",
            }
            rule = rule_map.get(resample_freq)
            if rule:
                num_cols = fdf.select_dtypes(include=[np.number]).columns
                resampled = (
                    fdf.set_index(time_col)[num_cols]
                    .resample(rule)
                    .mean()
                    .dropna()
                    .reset_index()
                )
                fdf = resampled

        return fdf.sort_values(time_col).reset_index(drop=True)

    spp_filtered = filter_and_resample_dataset(
        spp_df, "Time", active_preset, custom_start, custom_end, active_resample
    )
    fuel_filtered = filter_and_resample_dataset(
        fuel_df, "Time", active_preset, custom_start, custom_end, active_resample
    )
    load_filtered = filter_and_resample_dataset(
        load_df, "Time", active_preset, custom_start, custom_end, active_resample
    )

    # 4. SELECCIÓN DE VISTA DE GRÁFICO
    st.subheader(t("nav_header"))
    st.caption(t("nav_caption"))

    views_dict = t("views")
    view_keys = list(views_dict.keys())
    view_labels = [views_dict[k] for k in view_keys]

    selected_view_label = st.radio(
        "Vistas disponibles:",
        options=view_labels,
        index=0,
        horizontal=True,
        key="view_radio_selector",
        label_visibility="collapsed",
    )
    active_view_key = view_keys[view_labels.index(selected_view_label)]

    st.markdown("---")

    def apply_plotly_time_controls(fig):
        fig.update_xaxes(
            rangeslider=dict(visible=True, thickness=0.08),
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=12, label="12h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(count=3, label="3d", step="day", stepmode="backward"),
                        dict(count=7, label="7d", step="day", stepmode="backward"),
                        dict(count=30, label="30d", step="day", stepmode="backward"),
                        dict(step="all", label="All"),
                    ]
                ),
                font=dict(color="#E2E8F0", size=11),
                bgcolor="#1E293B",
                activecolor="#3B82F6",
            ),
        )
        return fig

    # VISTA 1: TELEMETRÍA DUAL
    if active_view_key == "v1":
        st.subheader(t("view1_title"))

        ctrl1, _ = st.columns([2, 3])
        with ctrl1:
            chart_style = st.selectbox(
                t("chart_style_label"),
                [t("chart_style_fill"), t("chart_style_line")],
                index=0,
            )

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=spp_filtered["Time"],
                y=spp_filtered["LMP"],
                name="Houston LMP ($/MWh)",
                line=dict(color="#FF4B4B", width=2.5),
                mode="lines",
            ),
            secondary_y=False,
        )

        if "Power Storage" in fuel_filtered.columns:
            if chart_style == t("chart_style_fill"):
                fig.add_trace(
                    go.Scatter(
                        x=fuel_filtered["Time"],
                        y=fuel_filtered["Power Storage"],
                        name="BESS Potencia (MW)",
                        line=dict(color="#00D4B1", width=1.5),
                        fill="tozeroy",
                        fillcolor="rgba(0, 212, 177, 0.15)",
                        mode="lines",
                    ),
                    secondary_y=True,
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=fuel_filtered["Time"],
                        y=fuel_filtered["Power Storage"],
                        name="BESS Potencia (MW)",
                        line=dict(color="#00D4B1", width=2.5),
                        mode="lines",
                    ),
                    secondary_y=True,
                )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            hovermode="x unified",
        )
        fig.update_xaxes(title_text="Hora del Día (US/Central)", gridcolor="#1E293B")
        fig.update_yaxes(
            title_text="Precio LMP ($/MWh)",
            color="#FF4B4B",
            secondary_y=False,
            gridcolor="#1E293B",
        )
        fig.update_yaxes(
            title_text="Potencia BESS (MW)",
            color="#00D4B1",
            secondary_y=True,
            showgrid=False,
        )

        fig = apply_plotly_time_controls(fig)
        st.plotly_chart(fig, use_container_width=True)

    # VISTA 2: VOLATILIDAD DE PRECIOS
    elif active_view_key == "v2":
        st.subheader(t("view2_title"))
        v2_col1, v2_col2 = st.columns([3, 2])

        p50 = spp_filtered["LMP"].quantile(0.50) if not spp_filtered.empty else 0.0
        p90 = spp_filtered["LMP"].quantile(0.90) if not spp_filtered.empty else 0.0

        with v2_col1:
            st.markdown(f"##### {t('view2_timeseries_title')}")
            fig_vol = go.Figure()
            fig_vol.add_trace(
                go.Scatter(
                    x=spp_filtered["Time"],
                    y=spp_filtered["LMP"],
                    name="Houston LMP",
                    line=dict(color="#F59E0B", width=2),
                )
            )
            fig_vol.add_hline(
                y=p50,
                line_dash="dash",
                line_color="#10B981",
                annotation_text=f"P50: ${p50:.1f}",
            )
            fig_vol.add_hline(
                y=p90,
                line_dash="dash",
                line_color="#EF4444",
                annotation_text=f"P90: ${p90:.1f}",
            )

            fig_vol.update_layout(
                template="plotly_dark",
                height=420,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
            )
            fig_vol = apply_plotly_time_controls(fig_vol)
            st.plotly_chart(fig_vol, use_container_width=True)

        with v2_col2:
            st.markdown(f"##### {t('view2_histogram_title')}")
            fig_hist = px.histogram(
                spp_filtered,
                x="LMP",
                nbins=25,
                color_discrete_sequence=["#6366F1"],
                labels={"LMP": "Price LMP ($/MWh)"},
            )
            fig_hist.update_layout(
                template="plotly_dark",
                height=420,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # VISTAS RESTANTES
    elif active_view_key == "v3":
        st.subheader(t("view3_title"))
        spp_resamp = spp_filtered.set_index("Time").resample("15min").mean()
        fuel_resamp = fuel_filtered.set_index("Time").resample("15min").mean()
        merged_df = pd.merge(
            spp_resamp, fuel_resamp, left_index=True, right_index=True, how="inner"
        ).reset_index()

        if not merged_df.empty and "Power Storage" in merged_df.columns:
            fig_scatter = px.scatter(
                merged_df,
                x="LMP",
                y="Power Storage",
                color="LMP",
                size=np.abs(merged_df["Power Storage"]) + 10,
                color_continuous_scale="Turbid",
                labels={
                    "LMP": "Price Houston LMP ($/MWh)",
                    "Power Storage": "BESS Power (MW)",
                },
            )
            fig_scatter.update_layout(
                template="plotly_dark",
                height=520,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
            )
            fig_scatter = apply_plotly_time_controls(fig_scatter)
            st.plotly_chart(fig_scatter, use_container_width=True)

    elif active_view_key == "v4":
        st.subheader(t("view4_title"))
        f_col1, f_col2 = st.columns([3, 2])
        raw_fuel_cols = [
            c
            for c in [
                "Natural Gas",
                "Wind",
                "Solar",
                "Coal and Lignite",
                "Nuclear",
                "Hydro",
                "Power Storage",
                "Other",
            ]
            if c in fuel_filtered.columns
        ]

        with f_col1:
            fig_stack = go.Figure()
            for col in raw_fuel_cols:
                fig_stack.add_trace(
                    go.Scatter(
                        x=fuel_filtered["Time"],
                        y=fuel_filtered[col],
                        name=col,
                        mode="lines",
                        stackgroup="one",
                    )
                )
            fig_stack.update_layout(
                template="plotly_dark",
                height=440,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
            )
            st.plotly_chart(fig_stack, use_container_width=True)

        with f_col2:
            if not fuel_filtered.empty:
                latest_row = fuel_filtered.iloc[-1]
                pie_labels = [c for c in raw_fuel_cols if float(latest_row[c]) > 0]
                pie_values = [float(latest_row[c]) for c in pie_labels]
                fig_pie = px.pie(names=pie_labels, values=pie_values, hole=0.45)
                fig_pie.update_layout(
                    template="plotly_dark", height=440, paper_bgcolor="#0B0E14"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

    elif active_view_key == "v5":
        st.subheader(t("view5_title"))
        fig_load = go.Figure()
        fig_load.add_trace(
            go.Scatter(
                x=load_filtered["Time"],
                y=load_filtered["Load"],
                name="ERCOT Load (MW)",
                line=dict(color="#38BDF8", width=3),
                fill="tozeroy",
            )
        )
        fig_load.update_layout(
            template="plotly_dark",
            height=500,
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
        )
        fig_load = apply_plotly_time_controls(fig_load)
        st.plotly_chart(fig_load, use_container_width=True)

    # 5. TABLAS DE DATOS DETALLADAS Y EXPORTACIÓN CSV
    st.markdown("---")
    with st.expander(t("table_expander_title")):
        t1, t2, t3 = st.tabs([t("tab_lmp"), t("tab_bess"), t("tab_fuel")])
        with t1:
            st.dataframe(spp_filtered.tail(30), use_container_width=True)
        with t2:
            if "Power Storage" in fuel_filtered.columns:
                st.dataframe(
                    fuel_filtered[["Time", "Power Storage"]].tail(30),
                    use_container_width=True,
                )
        with t3:
            st.dataframe(fuel_filtered.tail(30), use_container_width=True)
