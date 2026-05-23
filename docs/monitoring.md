# Monitoring

Threat-Lock monitors multiple real sources and feeds discovered signals into the
threat pipeline via `POST /api/threats/ingest`.

## Sources
1. **Explorer** (`integrations/explorer_client.py`) — Etherscan-style. Watches a
   protocol/treasury address for tx spikes, repeated/large outflows, and
   interactions with suspicious wallets. Disabled (gracefully) if no API key.
2. **News / RSS** (`integrations/news_client.py`) — public security RSS feeds,
   matched against `SECURITY_KEYWORDS`. No API key needed.
3. **Security feed** (`integrations/security_feed_client.py`) — protocol-targeted:
   items mentioning BOTH a security keyword AND your monitored protocol/keywords.

## Env (root `.env`)
```
EXPLORER_PROVIDER=etherscan
EXPLORER_API_KEY=...
EXPLORER_BASE_URL=https://api.etherscan.io/api
WATCHED_CHAIN=ethereum
WATCHED_PROTOCOL_ADDRESS=0x...
WATCHED_TREASURY_ADDRESS=0x...
MONITORED_PROTOCOL_NAME=YourProtocol
MONITORED_PROTOCOL_KEYWORDS=yourprotocol,yourtoken
SUSPICIOUS_WALLETS=0xbad1,0xbad2
NEWS_RSS_URLS=https://cointelegraph.com/rss/tag/security,https://www.theblock.co/rss.xml
SECURITY_KEYWORDS=hack,exploit,drain,...
```
If explorer keys are missing, that source reports `enabled:false` and the scan
continues with news/security feeds.

## Running
```powershell
# one-off worker (live sources):
.\.venv\Scripts\python.exe -m monitoring.worker
# demo signals (no keys/feeds needed):
.\.venv\Scripts\python.exe -m monitoring.worker --mock
# scheduled loop:
.\.venv\Scripts\python.exe -m monitoring.scheduler --interval 60 --mock
# or trigger from the dashboard / API:
curl -X POST http://localhost:8000/api/monitoring/run-scan
```

## Signal → threat report
Each signal is an ingest payload (`protocol, source, event_type, evidence,
wallet?, amount_usd?, tx_count?, severity_hint, source_url?, metadata`). The
backend scores it; only `critical` escalates to the GenLayer AI judge. Every scan
is recorded in `monitoring_runs` and shown on the Monitoring page.
