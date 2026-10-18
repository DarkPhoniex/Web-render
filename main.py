from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Layers, low -> high precedence (hardcoded so deployment can't break them)
DEFAULTS = {"port": "8000", "workers": "1", "debug": "false",
            "log_level": "info", "api_key": "default-secret-000"}
YAML_LAYER = {"port": "8759"}
DOTENV = {"APP_PORT": "8486", "NUM_WORKERS": "1",
          "APP_DEBUG": "true", "APP_API_KEY": "key-38mrbwocta"}
OS_ENV = {"APP_DEBUG": "true", "APP_LOG_LEVEL": "info"}


def normalize(layer):
    out = {}
    for k, v in layer.items():
        key = k[4:] if k.startswith("APP_") else k
        key = key.lower()
        if key == "num_workers":      # alias
            key = "workers"
        out[key] = v
    return out


def coerce(key, val):
    val = str(val)
    if key in ("port", "workers"):
        return int(val)
    if key == "debug":
        return val.strip().lower() in ("true", "1", "yes", "on")
    return val


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    cfg = {}
    for layer in (DEFAULTS, YAML_LAYER, DOTENV, OS_ENV):
        cfg.update(normalize(layer))

    for item in set:                       # CLI overrides, highest precedence
        k, _, v = item.partition("=")      # split on FIRST '=' only
        k = k.strip().lower()
        if k == "num_workers":
            k = "workers"
        if k:
            cfg[k] = v

    result = {}
    for k, v in cfg.items():
        try:
            result[k] = coerce(k, v)
        except ValueError:
            result[k] = DEFAULTS.get(k)    # ignore a bad int rather than crash
    result["api_key"] = "****"             # always masked
    return result