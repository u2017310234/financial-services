def test_bsm_price():
    from risk_toolkit import api

    result = api.run(
        "options.bsm_price",
        {
            "spot": 100,
            "strike": 100,
            "tau": 1,
            "rate": 0.03,
            "vol": 0.2,
            "div_yield": 0,
        },
    )

    assert result["status"] == "ok"
    assert result["result"]["call"] > 0
    assert result["result"]["put"] > 0

