"""
GridFlow-TX | Multi-Service Platform Gateway Launcher.
Acts as a unified Gateway / Landing UI with dynamic microservice registration and routing.
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import importlib
from datetime import datetime, timedelta

import gridstatus
from translations import get_text
from services.service_registry import get_all_services, get_service_by_id

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GridFlow-Gateway")

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="GridFlow-TX | Gateway & Multi-Service Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. GLOBAL CSS STYLES (Dark Mode, Glassmorphism, Microservice Cards)
st.markdown(
    """
<style>
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    
    /* Service Card Styling (Minimalist & Sleek) */
    .service-card {
        background: linear-gradient(145deg, #111827 0%, #1E293B 100%);
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid #1E293B;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
        transition: all 0.25s ease-in-out;
    }
    .service-card:hover {
        border-color: #38BDF8;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.12);
    }
    .service-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .service-title {
        color: #F8FAFC;
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .service-desc {
        color: #94A3B8;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    .status-badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .tag-pill {
        background-color: #0F172A;
        color: #38BDF8;
        border: 1px solid #1E293B;
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.70rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    
    /* Top Subtle Language Selector Buttons */
    div[data-testid="column"] button[key^="top_flag_"] {
        padding: 2px 4px !important;
        font-size: 0.8rem !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        height: 30px !important;
    }

    /* General Cards */
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
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 4px 0;
    }
    .alert-banner-high {
        background: linear-gradient(90deg, #450A0A 0%, #7F1D1D 100%);
        color: #FEF2F2;
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 6px solid #EF4444;
        margin-bottom: 24px;
    }
    .alert-banner-normal {
        background: linear-gradient(90deg, #064E3B 0%, #047857 100%);
        color: #ECFDF5;
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 6px solid #10B981;
        margin-bottom: 24px;
    }
    .time-control-card {
        background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .time-control-title {
        color: #38BDF8;
        font-size: 1.0rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 3. MANEJO DE IDIOMA Y SESSION STATE
if "lang" in st.query_params:
    qp_lang = st.query_params["lang"]
    if qp_lang in ["es", "en", "fr", "zh", "ko", "it", "pt"]:
        st.session_state["lang_code"] = qp_lang

if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = "en"

if "active_service" not in st.session_state:
    st.session_state["active_service"] = "hub"

current_lang = st.session_state["lang_code"]
active_service_id = st.session_state["active_service"]


def t(key: str, **kwargs) -> str:
    """Helper rápido de traducción."""
    return get_text(current_lang, key, **kwargs)


# 4. BARRA SUPERIOR SUBTIL DE BANDERAS DE IDIOMA (TOPMOST)
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
<div style="display: flex; justify-content: space-between; align-items: center; padding: 0px 0px 10px 0px; border-bottom: 1px solid #1E293B; margin-bottom: 15px;">
    <div>
        <span style="font-size: 0.90rem; font-weight: 700; color: #38BDF8; letter-spacing: 0.5px;">⚡ GridFlow-TX</span>
        <span style="font-size: 0.75rem; color: #64748B; margin-left: 8px;">v2.5 Enterprise</span>
    </div>
    <div style="display: flex; align-items: center; gap: 5px;">
        <span style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 4px;">🌐 Language:</span>
        {''.join(flags_html_items)}
    </div>
</div>
'''
st.markdown(top_bar_html, unsafe_allow_html=True)


# 5. CARGA DE DATOS COMPARTIDA (SHARED TELEMETRY PIPELINE)
@st.cache_data(ttl=120, show_spinner=False)
def load_ercot_telemetry_dataset():
    """Carga y procesa telemetría ERCOT (30 días de cobertura) para todos los microservicios."""
    iso = gridstatus.Ercot()
    fuel_df = pd.DataFrame()
    spp_df = pd.DataFrame()
    load_df = pd.DataFrame()

    try:
        fuel_mix = iso.get_fuel_mix(date="today")
        if fuel_mix is not None and not fuel_mix.empty:
            fuel_df = fuel_mix.copy()
            fuel_df["Time"] = pd.to_datetime(fuel_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error Fuel Mix: {e}")

    try:
        spp_raw = iso.get_spp(date="today", market="REAL_TIME_15_MIN", locations=["HB_HOUSTON"])
        if spp_raw is not None and not spp_raw.empty:
            spp_df = spp_raw[["Time", "SPP"]].copy()
            spp_df.rename(columns={"SPP": "LMP"}, inplace=True)
            spp_df["Time"] = pd.to_datetime(spp_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error SPP: {e}")

    try:
        sys_load = iso.get_load(date="today")
        if sys_load is not None and not sys_load.empty:
            load_df = sys_load[["Time", "Load"]].copy()
            load_df["Time"] = pd.to_datetime(load_df["Time"]).dt.tz_convert("US/Central")
    except Exception as e:
        logger.error(f"Error Load: {e}")

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

    for df in [fuel_df, spp_df, load_df]:
        if "Time" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Time"]):
            if df["Time"].dt.tz is not None:
                df["Time"] = df["Time"].dt.tz_localize(None)

    fuel_df = fuel_df.sort_values("Time").reset_index(drop=True)
    spp_df = spp_df.sort_values("Time").reset_index(drop=True)
    load_df = load_df.sort_values("Time").reset_index(drop=True)

    return fuel_df, spp_df, load_df


with st.spinner("Sincronizando pipeline de datos ERCOT / Synchronizing dataset..."):
    fuel_df, spp_df, load_df = load_ercot_telemetry_dataset()


# 6. HEADER NAVEGACIÓN ENTRE SERVICIOS
if active_service_id != "hub":
    nav_col1, nav_col2 = st.columns([2, 5])
    with nav_col1:
        if st.button(t("nav_back_to_hub"), key="btn_nav_hub", type="secondary"):
            st.session_state["active_service"] = "hub"
            st.rerun()
    with nav_col2:
        srv_info = get_service_by_id(active_service_id)
        st.markdown(
            f"""
            <div style="text-align: right; font-size: 0.85rem; color: #94A3B8; padding-top: 6px;">
                Módulo Activo: <strong style="color: #38BDF8;">{srv_info['icon']} {t(srv_info['title_key'])}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )


# 7. ROUTER PRINCIPAL DE MICROSERVICIOS
if active_service_id == "hub":
    # --------------------------------------------------------------------------------
    # GATEWAY LANDING HUB (SELECTOR MODULAR DE MICROSERVICIOS)
    # --------------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #131927 0%, #1A233A 100%); padding: 30px; border-radius: 16px; border: 1px solid #2A3655; margin-bottom: 30px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);">
            <h1 style="color: #F8FAFC; margin: 0 0 10px 0; font-size: 2.2rem; font-weight: 800; display: flex; align-items: center; gap: 12px;">
                {t('gateway_title')}
            </h1>
            <p style="color: #94A3B8; margin: 0; font-size: 1.05rem; line-height: 1.6;">
                {t('gateway_subtitle')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(t("gateway_header"))
    st.caption(t("gateway_caption"))

    registered_services = get_all_services()
    cols = st.columns(len(registered_services))

    for idx, service in enumerate(registered_services):
        with cols[idx]:
            tags_html = "".join([f'<span class="tag-pill">{tag}</span>' for tag in service["tags"]])
            
            st.markdown(
                f"""
                <div class="service-card">
                    <div>
                        <div class="service-header">
                            <span class="service-title">{service['icon']} {t(service['title_key'])}</span>
                            <span class="status-badge" style="background-color: {service['badge_color']}20; color: {service['badge_color']}; border: 1px solid {service['badge_color']}50;">
                                {service['status_badge']}
                            </span>
                        </div>
                        <div class="service-desc">{t(service['desc_key'])}</div>
                    </div>
                    <div>
                        <div style="margin-bottom: 15px;">{tags_html}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            if st.button(t("launch_btn"), key=f"launch_srv_{service['id']}", type="primary", use_container_width=True):
                st.session_state["active_service"] = service["id"]
                st.rerun()

else:
    # --------------------------------------------------------------------------------
    # DISPATCHER DINÁMICO DE MICROSERVICIOS
    # --------------------------------------------------------------------------------
    srv_config = get_service_by_id(active_service_id)
    mod_path = srv_config["module_path"]
    func_name = srv_config["handler_func"]

    try:
        mod = importlib.import_module(mod_path)
        render_func = getattr(mod, func_name)
        render_func(current_lang, spp_df, fuel_df, load_df)
    except Exception as err:
        logger.error(f"Error cargando microservicio {active_service_id}: {err}", exc_info=True)
        st.error(f"Error al cargar el microservicio '{active_service_id}': {err}")

# 8. SLEEK MINIMALIST ENTERPRISE FOOTER
st.markdown("---")
footer_html = f"""
<div style="margin-top: 30px; padding: 20px 0; border-top: 1px solid #1E293B; text-align: center; font-size: 0.85rem; color: #64748B;">
    <div style="display: flex; justify-content: center; align-items: center; gap: 15px; flex-wrap: wrap; margin-bottom: 8px;">
        <span style="font-weight: 700; color: #38BDF8;">⚡ GridFlow-TX Enterprise Platform</span>
        <span>•</span>
        <span style="color: #94A3B8;">{t('footer_created_by')}</span>
        <span>•</span>
        <a href="https://github.com/joanroamora/GridFlow-TX" target="_blank" style="color: #60A5FA; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
            <svg height="14" width="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            {t('footer_github')}
        </a>
    </div>
    <div style="font-size: 0.75rem; color: #475569;">
        © {datetime.now().year} GridFlow-TX | Texas Nodal ERCOT Market & Energy Storage Intelligence
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
