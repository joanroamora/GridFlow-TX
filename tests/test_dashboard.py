import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dashboard import filter_and_resample_dataset


def test_filter_and_resample_empty():
    empty_df = pd.DataFrame()
    res = filter_and_resample_dataset(empty_df)
    assert res.empty


def test_filter_and_resample_presets():
    now = datetime.now()
    times = [now - timedelta(hours=i) for i in range(48, 0, -1)]
    df = pd.DataFrame({
        "Time": times,
        "LMP": np.random.uniform(20, 100, len(times))
    })

    # Test 6h preset
    res_6h = filter_and_resample_dataset(df, preset="6h")
    assert len(res_6h) <= 7

    # Test 24h preset
    res_24h = filter_and_resample_dataset(df, preset="24h")
    assert len(res_24h) <= 25

    # Test 1h resampling
    res_1h = filter_and_resample_dataset(df, preset="all", resample_freq="1h")
    assert not res_1h.empty
