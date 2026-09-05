from prometheus_client import Counter

# Custom metric for tracking kite api retry count per symbol
KITE_RETRIES = Counter(
    "kite_retries_total",
    "Total number of Kite data download retries",
    ["symbol"]
)
