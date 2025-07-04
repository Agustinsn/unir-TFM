import os
import pytest

@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ['USER_POOL_ID'] = 'dummy_pool'
    os.environ['USER_POOL_CLIENT_ID'] = 'dummy_client'
