# Bitstamp BTC/USD — datos diarios verificables

Este repositorio publica **únicamente datos públicos de mercado** desde la API oficial de Bitstamp. No almacena información de cuentas, compras ni importes de inversión.

## Funcionamiento

- Fuente directa: `https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=60&exclude_current_candle=true`.
- Validación: par BTC/USD, medianoche UTC, coherencia OHLC, ausencia de huecos y vela más reciente **cerrada ayer UTC**.
- Si la API falla o devuelve datos incoherentes, **no modifica** el histórico.
- GitHub Actions ejecuta el programa automáticamente y publica `data/bitstamp_btcusd_daily.json`.
- No necesita claves API, no opera con dinero y no emite órdenes de trading.

Consulta JSON (después de la primera ejecución satisfactoria):

https://raw.githubusercontent.com/MarianoSevilla/bitstamp-btc-monitor/main/data/bitstamp_btcusd_daily.json

### Puesta en marcha

En GitHub → **Actions** → **Bitstamp BTCUSD daily OHLC** → **Run workflow**. Revisar el resultado del trabajo y comprobar la fecha del último cierre UTC en el archivo JSON. Los trabajos programados pueden retrasarse.

**Importante:** el repositorio publica datos, pero no activa por sí mismo las alertas de ChatGPT; esa integración debe validarse aparte. Una alerta de inversión solo puede declararse usando los cierres originales verificados y las reglas ya aprobadas.

Documentación oficial: https://www.bitstamp.net/api/ y https://docs.github.com/en/actions
