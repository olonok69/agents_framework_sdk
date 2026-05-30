# Estrategia de Momentum de Resultados

## Qué mide la estrategia
- Escanea una cesta de acciones en busca de **explosiones de momentum tras resultados**: sesiones con gran volumen y cierre alcista.
- Asume que la inercia positiva posterior a earnings puede extenderse durante varios días hábiles (por defecto 5).
- Limita las posiciones simultáneas para concentrarse en las señales más fuertes.

## Flujo de datos
- Fuente: Yahoo Finance mediante `yfinance` con velas diarias (`1d`).
- Símbolos: lista configurable separada por comas (por defecto `AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA`).
- Periodo: ventana flexible (`3mo`, `6mo`, `1y`, etc.).
- Indicadores por símbolo:
  - Media móvil simple de volumen de 20 días (configurable).
  - Ratio de volumen = `Volumen / SMA_volumen`.
  - Señal alcista cuando `Close > Open`.

## Pasos de cálculo
1. **Descarga y normalización** — Obtiene OHLCV de cada símbolo y calcula estadísticas de volumen agrupando por ticker.
2. **Detección de señales** — Marca sesiones con `ratio_volumen >= umbral` (2× por defecto) y cierre alcista.
3. **Gestión de posiciones** —
   - Entra en las señales más potentes hasta alcanzar `max_positions` (valor predeterminado 3).
   - Registra fecha de entrada, precio y ratio de volumen.
   - Cierra cada posición tras `hold_days` barras o al finalizar la muestra.
4. **Métricas de desempeño** — Calcula trades totales, tasa de aciertos, retornos promedio/medianos y líderes por símbolo.
5. **Señales recientes** — Conserva las últimas entradas para graficarlas en Streamlit.

## Salida del MCP Tool
- `summary`: texto en markdown con universo, parámetros, trades totales, líderes y entradas recientes.
- `metrics`:
  - `parameters`: configuración efectiva de la corrida.
  - `aggregate`: trades, win rate, retorno promedio, duración media de la posición.
  - `per_symbol`: estadísticas por ticker (número de trades, win rate, retornos).
  - `trades`: bitácora limitada de operaciones con fechas y retornos.
  - `signals`: lista reciente para visualizaciones (fecha, símbolo, ratio, close).
- Los errores se devuelven como `{"error": "mensaje"}` para manejo en la UI.

## Implementaciones en el repositorio
- **MCP Tool:** `analyze_earnings_momentum` en `server/strategies/earnings_momentum.py`.
- **ToolCallingAgent:** función `run_earnings_momentum_analysis` en `stock_analyzer_bot/main.py` (usa el tool bajo nivel pero formatea el reporte con GPT).
- **CodeAgent:** función homónima en `stock_analyzer_bot/main_codeagent.py` que parsea el JSON antes de redactar el resumen.
- **FastAPI:** endpoint `POST /earnings_momentum` en `stock_analyzer_bot/api.py` que elige el agente según `agent_type` y expone `timeseries` para la UI.
- **Streamlit:** pestaña "⚡ Earnings Momentum" en `streamlit_app.py` con sliders para ventana de volumen, umbral, días en posición y máximo de exposiciones, además de gráfico Altair.

## Parámetros configurables
| Parámetro | Valor por defecto | Descripción |
|-----------|------------------|-------------|
| `symbols` | `AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA` | Lista de tickers separados por comas |
| `period` | `6mo` | Cualquier periodo soportado por yfinance |
| `volume_window` | `20` | Ventana para SMA de volumen (mínimo 5) |
| `volume_multiplier` | `2.0` | Múltiplo mínimo para considerar spike |
| `hold_days` | `5` | Barras (días hábiles) a mantener la posición |
| `max_positions` | `3` | Límite de posiciones simultáneas |

## Ejemplos de uso
- **Python (wrapper MCP):**
  ```python
  from stock_analyzer_bot.tools import earnings_momentum_analysis
  payload = earnings_momentum_analysis(symbols="AAPL,MSFT,TSLA", period="6mo", volume_multiplier=1.8)
  print(payload)
  ```
- **FastAPI:**
  ```bash
  curl -X POST http://localhost:8000/earnings_momentum \
    -H "Content-Type: application/json" \
    -d '{
      "symbols": "AAPL,MSFT,NVDA",
      "period": "6mo",
      "volume_window": 20,
      "volume_multiplier": 2.2,
      "hold_days": 5,
      "max_positions": 3,
      "agent_type": "code_agent"
    }'
  ```
- **Streamlit:** pestaña "⚡ Earnings Momentum", ajustar parámetros y ejecutar el análisis.

## Notas operativas
- La herramienta es **de bajo nivel**: ambos agentes (ToolCalling y CodeAgent) dependen de la misma salida, garantizando consistencia.
- Limitar posiciones mantiene una exposición conservadora y evita sobreconcentración del portafolio.
- Se necesitan al menos `volume_window` barras para que exista SMA utilizable; periodos muy cortos pueden devolver pocas señales.
- Las listas de trades/señales se recortan a 200 elementos para evitar cargas excesivas en la UI.
