# Final-year report guide

Use this as the skeleton of your written report. Every formula below is the one the code uses.

## Chapter 1: Introduction
- Problem: farmers over- or under-irrigate, wasting water and losing yield.
- Aim: a tool that converts field data into a specific irrigation decision.
- Objectives: (1) compute crop water demand, (2) track soil water, (3) decide when to irrigate, (4) convert depth to litres and pump hours, (5) keep a history.
- Scope: single field, daily decision, manual inputs. Out of scope: live sensors, weather APIs, multi-field scheduling.

## Chapter 2: Literature review
Cover and cite: FAO-56 (Allen et al., 1998); Hargreaves and Samani (1985); crop coefficients; soil water balance; drip vs sprinkler vs flood efficiency; existing apps and IoT irrigation systems. Compare them with your tool in a table.

## Chapter 3: Requirements
- Functional: enter inputs, validate, compute, display, save, export CSV.
- Non-functional: runs on a basic laptop, answers in under a second, works on mobile screens, readable in dark mode.
- Use cases: Get recommendation, View history, Export history, Clear history.

## Chapter 4: Design
- Architecture: Browser (HTML/CSS/JS) → Flask routes → validators → engine → SQLite.
- Draw: block diagram, data-flow diagram, ER diagram for the `records` table, flowchart of the decision.
- Table `records`: id, created_at, crop, stage, soil, method, inputs (JSON), level, message, litres, hours.

## Chapter 5: Methodology (the formulas)
1. Extraterrestrial radiation: Ra = (24·60/π) · Gsc · dr · [ωs sinφ sinδ + cosφ cosδ sinωs] × 0.408
   with dr = 1 + 0.033 cos(2πJ/365) and δ = 0.409 sin(2πJ/365 − 1.39).
2. Reference ET: ET0 = 0.0023 · (Tmean + 17.8) · √(Tmax − Tmin) · Ra, then × (1 − (RH − 60)/200) when RH > 60%.
3. Crop water use: ETc = Kc × ET0.
4. Total available water: TAW = AWC × root depth.
5. Readily available water: RAW = p × TAW.
6. Soil water remaining: (θ − θwp) / (θfc − θwp), limited to 0–1. Depletion Dr = (1 − remaining) × TAW.
7. Effective rain: 0.8 × forecast if forecast ≥ 5 mm, else 0.
8. Projected depletion: Dp = max(0, Dr + ETc − rain_eff).
9. Decision: irrigate when Dp ≥ RAW. Urgent when remaining < 25%. Skip when rain alone keeps Dp below RAW.
10. Net depth = min(Dp, TAW). Gross depth = net / efficiency. Litres = gross × area. Pump hours = litres / flow.

Worked example (Wheat, mid stage, Loam, 20% moisture, 32/18 °C, 45% RH, no rain, 1000 m², drip, 2000 L/h, 1 March, 25.4°N):
TAW 150 mm, RAW 82.5 mm, remaining 47%, Dr 80 mm, ETc about 5.3 mm, Dp about 85 mm ≥ RAW so irrigate; gross about 95 mm, about 94,800 L, about 47 h.

## Chapter 6: Implementation
One section each: data tables, engine, validators, models, routes, templates, CSS/JS. Screenshot every page. Explain why Flask and SQLite were chosen.

## Chapter 7: Testing
Run `python -m unittest discover -v` and paste the output. Tabulate:
| Type | File | What it proves |
|---|---|---|
| Unit | tests/test_engine.py | formulas, decisions, clamping, efficiency ordering |
| Unit | tests/test_validators.py | rejects missing, text, out-of-range, NaN, inf, tmax<tmin |
| Integration | tests/test_routes.py | pages load, API saves, errors return 400, CSV and clear work |
Add a manual test table: input, expected output, actual output, pass/fail (at least 10 rows across all crops and soils).

## Chapter 8: Results and discussion
Compare drip, sprinkler and flood for the same field (litres saved). Show a rain-skip case. Show how the decision changes with soil type.

## Chapter 9: Limitations
- Hargreaves is less accurate than Penman-Monteith where humidity, wind and radiation are measured.
- Constants are generic, not calibrated to your district.
- Soil moisture is typed in, not read from a sensor.
- Rain forecast is entered by hand.
- No authentication; one shared history.

## Chapter 10: Future work
Open-Meteo weather API, soil-moisture sensor on ESP32/Arduino, Penman-Monteith, multiple fields, user accounts, SMS alerts, machine-learning moisture prediction.

## References
Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). Crop evapotranspiration, FAO Irrigation and Drainage Paper 56.
Hargreaves, G.H., Samani, Z.A. (1985). Reference crop evapotranspiration from temperature. Applied Engineering in Agriculture 1(2).

## Likely viva questions
1. Why Hargreaves and not Penman-Monteith? It needs only temperature and latitude.
2. What is Kc? Ratio of crop water use to reference ET, changing with growth stage.
3. Why does rice have p = 0.20? It is sensitive to water stress, so only 20% depletion is allowed.
4. Why divide by efficiency? Some applied water is lost to runoff, evaporation and deep percolation.
5. How would you add sensors? Post readings to `/api/recommend` or read them inside `routes.py`.
