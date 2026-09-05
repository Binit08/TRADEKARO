import os
import runpy
from unittest.mock import patch

@patch("dotenv.load_dotenv")
def test_server_run_defaults(mock_load):
    with patch.dict(os.environ, {"BACKTEST_API_TOKEN": "test_token"}, clear=True), \
         patch("uvicorn.run") as mock_run:
        
        runpy.run_path("app/api/server.py", run_name="__main__")
        
        mock_run.assert_called_once_with("app.api.server:app", host="127.0.0.1", port=8002, reload=False)

@patch("dotenv.load_dotenv")
def test_server_run_env_overrides(mock_load):
    env_vars = {
        "API_HOST": "0.0.0.0",
        "API_PORT": "9000",
        "API_RELOAD": "true"
    }
    with patch.dict(os.environ, env_vars), \
         patch("uvicorn.run") as mock_run:
        
        runpy.run_path("app/api/server.py", run_name="__main__")
        
        mock_run.assert_called_once_with("app.api.server:app", host="0.0.0.0", port=9000, reload=True)
