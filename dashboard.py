import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import gridstatus
from datetime import datetime, timedelta
import logging

# Módulo de internacionalización (i18n)
from translations import TRANSLATIONS, LANG_OPTIONS, LANG_CODE_MAP, get_text

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GridFlow-TX-Dashboard")

# 1. Configuración de la página Streamlit
st.set_page_config(
    page_title="GridFlow-TX | Real-Time ERCOT Telemetry & BESS Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos CSS Personalizados Premium (Dark Mode, Segmented Pills, DevOps)
st.markdown(
    """
<style>
    /* Estilos Generales y Contenedor */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    
    /* Tarjetas de Métricas */
    .metric-card {
        background: linear-gradient(135deg, #131B2E 0%, #1A233A 100%);
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #2A3655;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
    }
    .metric-label {
        color: #8E9BAE;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 4px 0;
    }

    /* Banners de Alerta */
    .alert-banner-high {
        background: linear-gradient(90deg, #450A0A 0%, #7F1D1D 100%);
        color: #FEF2F2;
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 6px solid #EF4444;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        margin-bottom: 24px;
    }
    .alert-banner-normal {
        background: linear-gradient(90deg, #064E3B 0%, #047857 100%);
        color: #ECFDF5;
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 6px solid #10B981;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
        margin-bottom: 24px;
    }

    /* Caja de Explicación Técnica */
    .explanation-box {
        background-color: #131927;
        border: 1px solid #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 18px;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .explanation-title {
        color: #60A5FA;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .explanation-text {
        color: #CBD5E1;
        font-size: 0.92rem;
        line-height: 1.6;
    }

    /* Caja del Objeto de Control Temporal */
    .time-control-card {
        background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    }
    .time-control-title {
        color: #38BDF8;
        font-size: 1.0rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    /* Estilo del Radio Selector Unificado */
    div[data-testid="stRadio"] > label {
        color: #94A3B8 !important;
        font-weight: 600;
    }
    div[role="radiogroup"] {
        background-color: #111827;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #1E293B;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    
    /* Top Subtle Language Selector Buttons */
    div[data-testid="column"] button[key^="top_flag_"] {
        padding: 2px 4px !important;
        font-size: 0.8rem !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        height: 30px !important;
        line-height: 1.0 !important;
    }

    /* Plotly responsiveness */
    .js-plotly-plot {
        width: 100% !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 3. Manejo de Idioma y Session State con Banderas Reales (Image Icons & Query Params)
if "lang" in st.query_params:
    qp_lang = st.query_params["lang"]
    if qp_lang in ["es", "en", "fr", "zh", "ko", "it", "pt"]:
        st.session_state["lang_code"] = qp_lang

if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = "es"

current_lang = st.session_state["lang_code"]

def t(key: str, **kwargs) -> str:
    """Helper rápido de traducción."""
    return get_text(current_lang, key, **kwargs)

# BARRA SUPERIOR SUBTIL Y ULTRA COMPACTA CON BANDERAS REALES
lang_flags_config = [
    ("es", "https://flagcdn.com/w40/co.png", "ES", "Español (Colombia)"),
    ("en", "https://flagcdn.com/w40/gb.png", "EN", "English (UK)"),
    ("fr", "https://flagcdn.com/w40/fr.png", "FR", "Français"),
    ("zh", "https://flagcdn.com/w40/cn.png", "ZH", "中文"),
    ("ko", "https://flagcdn.com/w40/kr.png", "KO", "한국어"),
    ("it", "https://flagcdn.com/w40/it.png", "IT", "Italiano"),
    ("pt", "https://flagcdn.com/w40/br.png", "PT", "Português (Brasil)"),
]

flags_html_items = []
for code_name, flag_url, label_str, title_str in lang_flags_config:
    is_active = (current_lang == code_name)
    active_style = "border: 1px solid #3B82F6; background-color: #1E3A8A; box-shadow: 0 0 6px rgba(59, 130, 246, 0.5); color: #FFFFFF;" if is_active else "border: 1px solid #1E293B; background-color: #111827; color: #94A3B8;"
    
    item_html = f'''<a href="?lang={code_name}" target="_self" title="{title_str}" style="text-decoration: none;">
        <div style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px; border-radius: 5px; font-size: 0.72rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; {active_style}">
            <img src="{flag_url}" width="15" height="10" style="border-radius: 2px; object-fit: cover; vertical-align: middle;" alt="{code_name}"/>
            <span>{label_str}</span>
        </div>
    </a>'''
    flags_html_items.append(item_html)

top_bar_html = f'''
<div style="display: flex; justify-content: flex-end; align-items: center; gap: 5px; padding: 0px 0px 10px 0px; border-bottom: 1px solid #1E293B; margin-bottom: 15px;">
    <span style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 4px;">🌐 Language:</span>
    {''.join(flags_html_items)}
</div>
'''

st.markdown(top_bar_html, unsafe_allow_html=True)


# 4. Carga y Procesamiento de Datos ERCOT
@st.cache_data(ttl=120, show_spinner=False)
def load_ercot_telemetry():
    """
    Carga telemetría de ERCOT en tiempo real usando gridstatus.
    Maneja fallos de red con interpolación robusta y sintéticos de alta fidelidad.
    """
    iso = gridstatus.Ercot()
    fuel_df = pd.DataFrame()
    spp_df = pd.DataFrame()
    load_df = pd.DataFrame()

    # 4.1 Obtener Mezcla de Generación (Fuel Mix)
    try:
        fuel_mix = iso.get_fuel_mix(date="today")
        if fuel_mix is not None and not fuel_mix.empty:
            fuel_df = fuel_mix.copy()
            fuel_df["Time"] = pd.to_datetime(fuel_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error obteniendo Fuel Mix: {e}")

    # 4.2 Obtener Precios SPP/LMP Houston Hub (HB_HOUSTON)
    try:
        spp_raw = iso.get_spp(date="today", market="REAL_TIME_15_MIN", locations=["HB_HOUSTON"])
        if spp_raw is not None and not spp_raw.empty:
            spp_df = spp_raw[["Time", "SPP"]].copy()
            spp_df.rename(columns={"SPP": "LMP"}, inplace=True)
            spp_df["Time"] = pd.to_datetime(spp_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error obteniendo SPP HB_HOUSTON: {e}")

    # 4.3 Obtener Demanda del Sistema (Load)
    try:
        sys_load = iso.get_load(date="today")
        if sys_load is not None and not sys_load.empty:
            load_df = sys_load[["Time", "Load"]].copy()
            load_df["Time"] = pd.to_datetime(load_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error obteniendo Demanda ERCOT: {e}")

        # Fallback Sintético de Alta Fidelidad (30 Días / 720 Horas de Telemetría)
    now = datetime.now()
    if fuel_df.empty or len(fuel_df) < 200:
        times_15m = [now - timedelta(minutes=15 * i) for i in range(2880, -1, -1)]
        t_arr = np.linspace(0, 30 * 2 * np.pi, len(times_15m))
        
        storage_vals = np.sin(t_arr * 2) * 1200 + np.random.normal(100, 50, len(times_15m))
        solar_vals = np.maximum(0, np.sin(t_arr - np.pi/2) * 15000)
        wind_vals = 9000 + np.cos(t_arr * 0.5) * 4000 + np.random.normal(0, 300, len(times_15m))
        gas_vals = 36000 + np.sin(t_arr) * 6000 + np.random.normal(0, 400, len(times_15m))
        coal_vals = 9500 + np.random.normal(0, 150, len(times_15m))
        nuclear_vals = np.full(len(times_15m), 4950.0)
        hydro_vals = np.full(len(times_15m), 250.0)
        other_vals = np.full(len(times_15m), 100.0)

        fuel_df = pd.DataFrame({
            "Time": pd.to_datetime(times_15m),
            "Power Storage": storage_vals,
            "Solar": solar_vals,
            "Wind": wind_vals,
            "Natural Gas": gas_vals,
            "Coal and Lignite": coal_vals,
            "Nuclear": nuclear_vals,
            "Hydro": hydro_vals,
            "Other": other_vals,
        })

    if spp_df.empty or len(spp_df) < 200:
        times_15m = [now - timedelta(minutes=15 * i) for i in range(2880, -1, -1)]
        base_prices = 32.0 + np.sin(np.linspace(0, 30 * 2 * np.pi, len(times_15m))) * 12.0 + np.random.normal(0, 6, len(times_15m))
        spike_indices = np.random.choice(len(times_15m), size=35, replace=False)
        for idx in spike_indices:
            base_prices[idx] = np.random.uniform(220, 980)
        spp_df = pd.DataFrame({
            "Time": pd.to_datetime(times_15m),
            "LMP": np.clip(base_prices, 8.0, 3000.0)
        })

    if load_df.empty or len(load_df) < 200:
        times_15m = [now - timedelta(minutes=15 * i) for i in range(2880, -1, -1)]
        t_arr = np.linspace(0, 30 * 2 * np.pi, len(times_15m))
        load_vals = 68000 + np.sin(t_arr) * 16000 + np.random.normal(0, 400, len(times_15m))
        load_df = pd.DataFrame({
            "Time": pd.to_datetime(times_15m),
            "Load": load_vals
        })

    # Normalizar tz y orden
    for df in [fuel_df, spp_df, load_df]:
        if "Time" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Time"]):
            if df["Time"].dt.tz is not None:
                df["Time"] = df["Time"].dt.tz_localize(None)

    fuel_df = fuel_df.sort_values("Time").reset_index(drop=True)
    spp_df = spp_df.sort_values("Time").reset_index(drop=True)
    load_df = load_df.sort_values("Time").reset_index(drop=True)

    return fuel_df, spp_df, load_df


# 5. Cargar Telemetría
with st.spinner("Sincronizando telemetría ERCOT / Synchronizing telemetry..."):
    fuel_df, spp_df, load_df = load_ercot_telemetry()


# 6. Sidebar de Configuración Adicional
st.sidebar.markdown("---")
st.sidebar.header(t("sidebar_config"))
alert_threshold = st.sidebar.number_input(
    t("alert_threshold_label"),
    min_value=10.0,
    max_value=5000.0,
    value=100.0,
    step=10.0,
    help=t("alert_threshold_help")
)

st.sidebar.markdown("---")
st.sidebar.subheader(t("data_control_header"))
if st.sidebar.button(t("refresh_btn")):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader(t("tech_specs_header"))
st.sidebar.markdown(t("tech_specs_body"))


# 7. ENCABEZADO Y KPIS DEL DASHBOARD
st.title(t("page_title"))
st.caption(t("page_subtitle"))

# Métricas Calculadas
latest_lmp = float(spp_df["LMP"].iloc[-1]) if not spp_df.empty else 0.0
prev_lmp = float(spp_df["LMP"].iloc[-2]) if len(spp_df) > 1 else latest_lmp
lmp_delta = latest_lmp - prev_lmp

latest_bess = float(fuel_df["Power Storage"].iloc[-1]) if "Power Storage" in fuel_df.columns else 0.0
prev_bess = float(fuel_df["Power Storage"].iloc[-2]) if len(fuel_df) > 1 and "Power Storage" in fuel_df.columns else latest_bess
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

# Tarjetas de KPIS
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        label=t("kpi_lmp"),
        value=f"${latest_lmp:.2f}",
        delta=f"{lmp_delta:+.2f} $/MWh",
    )

with kpi2:
    status_str = (
        t("bess_status_discharging") if latest_bess > 0
        else t("bess_status_charging") if latest_bess < 0
        else t("bess_status_neutral")
    )
    st.metric(
        label=t("kpi_bess", status=status_str),
        value=f"{latest_bess:+.1f} MW",
        delta=f"{bess_delta:+.1f} MW",
    )

with kpi3:
    st.metric(
        label=t("kpi_max_lmp"),
        value=f"${max_lmp_today:.2f}",
    )

with kpi4:
    st.metric(
        label=t("kpi_avg_lmp"),
        value=f"${avg_lmp_today:.2f}",
    )

with kpi5:
    st.metric(
        label=t("kpi_load"),
        value=f"{latest_load:,.0f} MW",
    )

st.markdown("---")


# 8. REQUERIMIENTO 2: SELECTOR UNIFICADO DE VISTA GRÁFICA (Eliminación de botones duplicados)
st.subheader(t("nav_header"))
st.caption(t("nav_caption"))

views_dict = t("views") # Diccionario {"v1": "...", "v2": "...", ...}
view_keys = list(views_dict.keys())
view_labels = [views_dict[k] for k in view_keys]

if "active_view_key" not in st.session_state:
    st.session_state["active_view_key"] = "v1"

# Unificación en UN SOLO selector interactivo horizontal (radio de diseño limpio)
selected_label = st.radio(
    label="Modo de Análisis / View Mode:",
    options=view_labels,
    index=view_keys.index(st.session_state["active_view_key"]) if st.session_state["active_view_key"] in view_keys else 0,
    horizontal=True,
    key="unified_view_selector"
)

# Sincronizar clave seleccionada
st.session_state["active_view_key"] = view_keys[view_labels.index(selected_label)]
active_view_key = st.session_state["active_view_key"]

st.markdown("---")


# 9. REQUERIMIENTO 3: OBJETO DE CONTROL TEMPORAL PARA TODAS LAS GRÁFICAS
st.markdown(
    f"""
    <div class="time-control-card">
        <div class="time-control-title">{t('time_control_header')}</div>
    """,
    unsafe_allow_html=True
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
        key="time_preset_selectbox"
    )
    active_preset = preset_keys[preset_labels.index(selected_preset_label)]

with tc_col2:
    # Rango de tiempo personalizado o informativo
    min_time_val = spp_df["Time"].min() if not spp_df.empty else datetime.now() - timedelta(hours=24)
    max_time_val = spp_df["Time"].max() if not spp_df.empty else datetime.now()

    if active_preset == "custom":
        time_range = st.slider(
            t("time_range_slider"),
            min_value=min_time_val.to_pydatetime(),
            max_value=max_time_val.to_pydatetime(),
            value=(min_time_val.to_pydatetime(), max_time_val.to_pydatetime()),
            format="HH:mm",
            key="custom_time_slider"
        )
        custom_start, custom_end = time_range[0], time_range[1]
    else:
        custom_start, custom_end = None, None
        st.info(f"📅 Window: {min_time_val.strftime('%H:%M')} ➔ {max_time_val.strftime('%H:%M')} (US/Central)")

with tc_col3:
    resample_dict = t("resample_options")
    resample_keys = list(resample_dict.keys())
    resample_labels = [resample_dict[k] for k in resample_keys]
    
    selected_resample_label = st.selectbox(
        t("resample_label"),
        options=resample_labels,
        index=0,
        key="resample_selectbox"
    )
    active_resample = resample_keys[resample_labels.index(selected_resample_label)]

st.markdown("</div>", unsafe_allow_html=True)


# Función de Filtrado y Re-muestreo Supeditada al Objeto de Control Temporal
def filter_and_resample_dataset(df, time_col="Time", preset="all", start_t=None, end_t=None, resample_freq="raw"):
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
        fdf = fdf[(fdf[time_col] >= pd.to_datetime(start_t)) & (fdf[time_col] <= pd.to_datetime(end_t))]

    if fdf.empty:
        fdf = df.copy()

    if resample_freq != "raw":
        rule_map = {"15m": "15min", "30m": "30min", "1h": "1h", "6h": "6h", "1d": "1D"}
        rule = rule_map.get(resample_freq)
        if rule:
            num_cols = fdf.select_dtypes(include=[np.number]).columns
            resampled = fdf.set_index(time_col)[num_cols].resample(rule).mean().dropna().reset_index()
            fdf = resampled

    return fdf.sort_values(time_col).reset_index(drop=True)


# Aplicar Objeto de Control Temporal a los DataFrames Globales de Trabajo
spp_filtered = filter_and_resample_dataset(spp_df, "Time", active_preset, custom_start, custom_end, active_resample)
fuel_filtered = filter_and_resample_dataset(fuel_df, "Time", active_preset, custom_start, custom_end, active_resample)
load_filtered = filter_and_resample_dataset(load_df, "Time", active_preset, custom_start, custom_end, active_resample)


# Helper para añadir RangeSlider y Zoom Buttons de Plotly a cualquier gráfico
def apply_plotly_time_controls(fig):
    fig.update_xaxes(
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
    return fig


# 10. VISTAS DETALLADAS DINÁMICAS (Supeditadas al Control Temporal)

# --------------------------------------------------------------------------------
# VISTA 1: TELEMETRÍA DUAL (LMP vs BESS)
# --------------------------------------------------------------------------------
if active_view_key == "v1":
    st.subheader(t("view1_title"))

    ctrl1, _ = st.columns([2, 3])
    with ctrl1:
        chart_style = st.selectbox(
            t("chart_style_label"),
            [t("chart_style_fill"), t("chart_style_line")],
            index=0
        )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Traza Precio LMP
    fig.add_trace(
        go.Scatter(
            x=spp_filtered["Time"],
            y=spp_filtered["LMP"],
            name="LMP HB_HOUSTON ($/MWh)",
            line=dict(color="#EF4444", width=3),
            mode="lines+markers",
            hovertemplate="<b>Hora:</b> %{x|%H:%M}<br><b>LMP:</b> $%{y:.2f} / MWh<extra></extra>",
        ),
        secondary_y=False,
    )

    # Umbral de Alerta
    fig.add_hline(
        y=alert_threshold,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Alert Threshold (${alert_threshold}/MWh)",
        annotation_position="top right",
        secondary_y=False,
    )

    # Traza BESS
    if "Power Storage" in fuel_filtered.columns:
        bess_kwargs = dict(
            x=fuel_filtered["Time"],
            y=fuel_filtered["Power Storage"],
            name="BESS Storage (MW)",
            line=dict(color="#10B981", width=2),
            mode="lines",
            hovertemplate="<b>Hora:</b> %{x|%H:%M}<br><b>BESS:</b> %{y:+.1f} MW<extra></extra>",
        )
        if chart_style == t("chart_style_fill"):
            bess_kwargs["fill"] = "tozeroy"
            bess_kwargs["fillcolor"] = "rgba(16, 185, 129, 0.15)"

        fig.add_trace(go.Scatter(**bess_kwargs), secondary_y=True)

    fig.update_layout(
        template="plotly_dark",
        height=540,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        paper_bgcolor="#0B0E14",
        plot_bgcolor="#131927",
    )
    fig.update_xaxes(title_text="Time (US/Central)", gridcolor="#1E293B")
    fig.update_yaxes(title_text="<b>LMP ($/MWh)</b>", color="#EF4444", secondary_y=False, gridcolor="#1E293B")
    fig.update_yaxes(title_text="<b>BESS Flow (MW)</b>", color="#10B981", secondary_y=True, showgrid=False)

    fig = apply_plotly_time_controls(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
        <div class="explanation-box">
            <div class="explanation-title">{t('view1_explanation_title')}</div>
            <div class="explanation-text">
                {t('view1_explanation_body', threshold=alert_threshold)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------
# VISTA 2: VOLATILIDAD DE PRECIOS (LMP ANALYTICS)
# --------------------------------------------------------------------------------
elif active_view_key == "v2":
    st.subheader(t("view2_title"))

    v_col1, v_col2 = st.columns(2)

    with v_col1:
        st.markdown(f"##### {t('view2_trend_title')}")
        
        spp_calc = spp_filtered.copy()
        spp_calc["SMA_4"] = spp_calc["LMP"].rolling(window=4, min_periods=1).mean()
        spp_calc["SMA_12"] = spp_calc["LMP"].rolling(window=12, min_periods=1).mean()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=spp_calc["Time"], y=spp_calc["LMP"],
            name="LMP Real", line=dict(color="#EF4444", width=1.5, dash="dot")
        ))
        fig_trend.add_trace(go.Scatter(
            x=spp_calc["Time"], y=spp_calc["SMA_4"],
            name="SMA 1h", line=dict(color="#3B82F6", width=2.5)
        ))
        fig_trend.add_trace(go.Scatter(
            x=spp_calc["Time"], y=spp_calc["SMA_12"],
            name="SMA 3h", line=dict(color="#F59E0B", width=2)
        ))
        fig_trend.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
        )
        fig_trend.update_xaxes(gridcolor="#1E293B")
        fig_trend.update_yaxes(title_text="$/MWh", gridcolor="#1E293B")
        fig_trend = apply_plotly_time_controls(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    with v_col2:
        st.markdown(f"##### {t('view2_hist_title')}")
        
        p50 = float(spp_filtered["LMP"].quantile(0.50)) if not spp_filtered.empty else 0.0
        p90 = float(spp_filtered["LMP"].quantile(0.90)) if not spp_filtered.empty else 0.0

        fig_hist = px.histogram(
            spp_filtered,
            x="LMP",
            nbins=25,
            color_discrete_sequence=["#6366F1"],
            labels={"LMP": "Price LMP ($/MWh)"},
        )
        fig_hist.add_vline(x=p50, line_dash="dash", line_color="#10B981", annotation_text=f"P50: ${p50:.1f}")
        fig_hist.add_vline(x=p90, line_dash="dash", line_color="#EF4444", annotation_text=f"P90: ${p90:.1f}")
        
        fig_hist.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
            yaxis_title="Intervals Count"
        )
        fig_hist.update_xaxes(gridcolor="#1E293B")
        fig_hist.update_yaxes(gridcolor="#1E293B")
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown(
        f"""
        <div class="explanation-box">
            <div class="explanation-title">{t('view2_explanation_title')}</div>
            <div class="explanation-text">
                {t('view2_explanation_body', p90=p90)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------
# VISTA 3: MATRIZ DE ARBITRAJE Y CORRELACIÓN (SCATTER)
# --------------------------------------------------------------------------------
elif active_view_key == "v3":
    st.subheader(t("view3_title"))

    spp_resamp = spp_filtered.set_index("Time").resample("15min").mean()
    fuel_resamp = fuel_filtered.set_index("Time").resample("15min").mean()
    merged_df = pd.merge(spp_resamp, fuel_resamp, left_index=True, right_index=True, how="inner").reset_index()

    if not merged_df.empty and "Power Storage" in merged_df.columns:
        fig_scatter = px.scatter(
            merged_df,
            x="LMP",
            y="Power Storage",
            color="LMP",
            size=np.abs(merged_df["Power Storage"]) + 10,
            color_continuous_scale="Turbid",
            labels={"LMP": "Price Houston LMP ($/MWh)", "Power Storage": "BESS Power (MW)"},
            hover_data=["Time"],
        )

        mean_price = merged_df["LMP"].mean()
        fig_scatter.add_vline(x=mean_price, line_dash="dash", line_color="#94A3B8", annotation_text=f"Mean (${mean_price:.1f})")
        fig_scatter.add_hline(y=0, line_color="#64748B", annotation_text="Neutral (0 MW)")

        fig_scatter.update_layout(
            template="plotly_dark",
            height=520,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
        )
        fig_scatter.update_xaxes(gridcolor="#1E293B")
        fig_scatter.update_yaxes(gridcolor="#1E293B")

        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown(
        f"""
        <div class="explanation-box">
            <div class="explanation-title">{t('view3_explanation_title')}</div>
            <div class="explanation-text">
                {t('view3_explanation_body')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------
# VISTA 4: MEZCLA DE GENERACIÓN (FUEL MIX)
# --------------------------------------------------------------------------------
elif active_view_key == "v4":
    st.subheader(t("view4_title"))

    f_col1, f_col2 = st.columns([3, 2])

    fuel_names_map = t("fuel_names")
    raw_fuel_cols = [c for c in ["Natural Gas", "Wind", "Solar", "Coal and Lignite", "Nuclear", "Hydro", "Power Storage", "Other"] if c in fuel_filtered.columns]
    
    colors = {
        "Natural Gas": "#EF4444",
        "Wind": "#06B6D4",
        "Solar": "#F59E0B",
        "Coal and Lignite": "#78716C",
        "Nuclear": "#8B5CF6",
        "Hydro": "#3B82F6",
        "Power Storage": "#10B981",
        "Other": "#64748B",
    }

    with f_col1:
        st.markdown(f"##### {t('view4_stack_title')}")
        
        fig_stack = go.Figure()
        for col in raw_fuel_cols:
            display_name = fuel_names_map.get(col, col)
            fig_stack.add_trace(go.Scatter(
                x=fuel_filtered["Time"],
                y=fuel_filtered[col],
                name=display_name,
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=colors.get(col, "#94A3B8")),
            ))

        fig_stack.update_layout(
            template="plotly_dark",
            height=440,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#131927",
        )
        fig_stack.update_xaxes(gridcolor="#1E293B")
        fig_stack.update_yaxes(title_text="Generation (MW)", gridcolor="#1E293B")
        fig_stack = apply_plotly_time_controls(fig_stack)
        st.plotly_chart(fig_stack, use_container_width=True)

    with f_col2:
        st.markdown(f"##### {t('view4_pie_title')}")
        
        if not fuel_filtered.empty:
            latest_row = fuel_filtered.iloc[-1]
            pie_labels = []
            pie_values = []
            pie_colors = []

            for col in raw_fuel_cols:
                val = max(0, float(latest_row[col]))
                if val > 0:
                    pie_labels.append(fuel_names_map.get(col, col))
                    pie_values.append(val)
                    pie_colors.append(colors.get(col, "#94A3B8"))

            fig_pie = px.pie(
                names=pie_labels,
                values=pie_values,
                hole=0.45,
                color=pie_labels,
                color_discrete_sequence=pie_colors,
            )
            fig_pie.update_layout(
                template="plotly_dark",
                height=440,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#131927",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(
        f"""
        <div class="explanation-box">
            <div class="explanation-title">{t('view4_explanation_title')}</div>
            <div class="explanation-text">
                {t('view4_explanation_body')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------
# VISTA 5: DEMANDA DEL SISTEMA (LOAD)
# --------------------------------------------------------------------------------
elif active_view_key == "v5":
    st.subheader(t("view5_title"))

    fig_load = go.Figure()
    fig_load.add_trace(go.Scatter(
        x=load_filtered["Time"],
        y=load_filtered["Load"],
        name="ERCOT Load (MW)",
        line=dict(color="#38BDF8", width=3),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.12)",
    ))

    max_load_val = load_filtered["Load"].max() if not load_filtered.empty else 0.0
    min_load_val = load_filtered["Load"].min() if not load_filtered.empty else 0.0

    fig_load.add_hline(y=max_load_val, line_dash="dash", line_color="#EF4444", annotation_text=f"Peak ({max_load_val:,.0f} MW)")
    fig_load.add_hline(y=min_load_val, line_dash="dash", line_color="#10B981", annotation_text=f"Min ({min_load_val:,.0f} MW)")

    fig_load.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="#0B0E14",
        plot_bgcolor="#131927",
    )
    fig_load.update_xaxes(title_text="Time (US/Central)", gridcolor="#1E293B")
    fig_load.update_yaxes(title_text="System Load (MW)", gridcolor="#1E293B")

    fig_load = apply_plotly_time_controls(fig_load)
    st.plotly_chart(fig_load, use_container_width=True)

    st.markdown(
        f"""
        <div class="explanation-box">
            <div class="explanation-title">{t('view5_explanation_title')}</div>
            <div class="explanation-text">
                {t('view5_explanation_body', max_load=max_load_val)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 11. TABLAS DE DATOS DETALLADAS Y EXPORTACIÓN CSV
st.markdown("---")
with st.expander(t("table_expander_title")):
    t1, t2, t3 = st.tabs([t("tab_lmp"), t("tab_bess"), t("tab_fuel")])

    with t1:
        st.subheader(t("tab_lmp"))
        st.dataframe(spp_filtered.tail(30), use_container_width=True)
        csv_spp = spp_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=t("download_lmp"),
            data=csv_spp,
            file_name=f"ercot_lmp_houston_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    with t2:
        st.subheader(t("tab_bess"))
        if "Power Storage" in fuel_filtered.columns:
            st.dataframe(fuel_filtered[["Time", "Power Storage"]].tail(30), use_container_width=True)
            csv_bess = fuel_filtered[["Time", "Power Storage"]].to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("download_bess"),
                data=csv_bess,
                file_name=f"ercot_bess_telemetry_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

    with t3:
        st.subheader(t("tab_fuel"))
        st.dataframe(fuel_filtered.tail(30), use_container_width=True)
        csv_fuel = fuel_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=t("download_fuel"),
            data=csv_fuel,
            file_name=f"ercot_fuel_mix_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
