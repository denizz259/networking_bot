def test_database_url_is_sqlite():
    import config

    # В любом случае (дефолт или из env) у нас сейчас sqlite
    assert config.DATABASE_URL.startswith("sqlite:")
