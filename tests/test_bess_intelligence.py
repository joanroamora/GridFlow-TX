import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from services.bess_intelligence import (
    run_bess_arbitrage_optimization,
    train_ml_short_term_forecast,
)


def test_bess_arbitrage_optimization():
    now = datetime.now()
    times = [now - timedelta(minutes=15 * i) for i in range(48, 0, -1)]
    # Prices with low and high values to trigger charge and discharge
    prices = [10.0] * 12 + [50.0] * 12 + [300.0] * 12 + [40.0] * 12

    spp_df = pd.DataFrame({"Time": times, "LMP": prices})

    opt_df = run_bess_arbitrage_optimization(
        spp_df, capacity_mwh=100.0, power_mw=25.0, rte_pct=88.0, initial_soc_pct=20.0
    )

    assert not opt_df.empty
    assert "SOC_Pct" in opt_df.columns
    assert "BESS_MW" in opt_df.columns
    assert "Cumulative_Profit" in opt_df.columns
    assert "Action" in opt_df.columns

    # Test SOC remains within 0% to 100% bounds
    assert opt_df["SOC_Pct"].min() >= 0.0
    assert opt_df["SOC_Pct"].max() <= 100.0


def test_ml_short_term_forecast():
    now = datetime.now()
    times = [now - timedelta(minutes=15 * i) for i in range(96, 0, -1)]
    prices = 30.0 + np.sin(np.linspace(0, 4 * np.pi, len(times))) * 15.0

    spp_df = pd.DataFrame({"Time": times, "LMP": prices})

    fc_df = train_ml_short_term_forecast(spp_df, horizon_hours=4)

    assert not fc_df.empty
    assert len(fc_df) == 16  # 4 hours * 4 intervals
    assert "Pred_LMP" in fc_df.columns
    assert "Pred_LMP_Upper" in fc_df.columns
    assert "Pred_LMP_Lower" in fc_df.columns
