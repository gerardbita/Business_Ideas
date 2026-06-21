# London Venture Modeller 📈
 
A dynamic Streamlit dashboard to financially model any of the researched
sub-£10k London business ideas — or your own.
 
## Get it

Clone the repository and move into the folder:

```bash
git clone https://github.com/gerardbita/Business_Ideas.git
cd Business_Ideas
```

## Run it
 
```bash
# option A: use the venv that's already set up
./.venv/bin/streamlit run app.py
 
# option B: fresh install
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/streamlit run app.py
```
 
> If **option A** doesn't work because the `.venv` environment with the
> requirements isn't there, use **option B** instead — it creates the venv,
> installs the requirements, and then runs the app.
 
Then open http://localhost:8501.
 
## What's inside
 
- **Sidebar** — pick a business preset (Greenwarden, DoorLedger, PassPrep,
  Saaya, Threshold, or Custom) and tune every lever: ARPU, new customers,
  growth, churn, CAC, variable %, rent, fixed costs, upfront, ramp, **capacity
  cap**, and horizon. A live guard flags if upfront exceeds £10,000.
- **📊 Model** — KPIs (break-even, Y1–Y3 revenue, ROI, LTV/CAC, time to £100k
  run-rate) + revenue/customer, cash-flow/break-even, and cost-stack charts,
  plus the full monthly table.
- **🎚️ Scenarios** — best/base/worst comparison driven by your own uplift /
  haircut / churn multipliers.
- **🌪️ Sensitivity** — one-at-a-time tornado: which assumption moves profit most.
- **💾 Export** — download the monthly model as CSV or a 3-sheet Excel workbook.
- **ℹ️ Ideas** — each business with its honest, stress-tested caveats.
 
## The model (one engine, generalised)
 
```
active[m] = active[m-1] · (1 − churn) + new[m]      (capped at `capacity`)
revenue   = active · ARPU
profit    = revenue − variable%·revenue − (rent+fixed) − CAC·new
```
 
`ARPU` = average **monthly revenue per active customer** — works for
subscriptions (the fee), repeat-job models (monthly run-rate per client), and
B2B per-unit (annual programme ÷ 12). Sanity-check against your real unit
economics before betting on any number.