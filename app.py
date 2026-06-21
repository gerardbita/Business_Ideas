# ============================================================================
#  LONDON VENTURE MODELLER  —  a dynamic financial dashboard for <=£10k London
#  business ideas (Streamlit).
#
#  WHAT IT DOES
#  ------------
#  Lets you model any subscription / recurring-revenue-style small business with
#  a single, general "cohort" engine:
#     - new customers are ACQUIRED each month (and that acquisition can grow),
#     - existing customers CHURN at a monthly rate,
#     - each ACTIVE customer pays an average monthly revenue (ARPU),
#     - costs = variable %  +  fixed (rent + other)  +  marketing (CAC x new).
#  It then computes revenue, profit, cumulative cash, break-even month, ROI,
#  LTV/CAC, runs a best/base/worst scenario comparison and a one-at-a-time
#  sensitivity (tornado) analysis, and exports everything to CSV / Excel.
#
#  Five real, researched presets are built in (see PRESETS below) plus a blank
#  "Custom" slot. Defaults are seeded from the top recommendation (Greenwarden).
#
#  HOW TO RUN
#  ----------
#     pip install -r requirements.txt
#     streamlit run app.py
#
#  HOW TO EXTEND
#  -------------
#  Add a new business: append an entry to PRESETS with the same keys. That's it
#  — it appears in the selector and the Ideas tab automatically.
# ============================================================================
 
from __future__ import annotations
 
import io
from dataclasses import dataclass, asdict
 
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
 
# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="London Venture Modeller",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ---------------------------------------------------------------------------
# PRESETS
# ---------------------------------------------------------------------------
# Each preset is a full set of model inputs. `arpu` = average monthly revenue
# per ACTIVE customer — this single field generalises across business types:
#   * subscription/membership -> the monthly fee,
#   * repeat-job/per-event    -> the typical monthly run-rate per client,
#   * B2B per-unit (e.g. doors)-> the annual programme / 12 per account.
# The numbers are grounded in the strategy analysis; treat them as starting
# points and move the sliders to pressure-test.
# ---------------------------------------------------------------------------
PRESETS: dict[str, dict] = {
    "Greenwarden — botanical conservation (TOP PICK)": dict(
        rent=0.0, other_fixed=850.0, arpu=450.0, new_cust=1.5, growth=6.0,
        churn=1.5, cac=150.0, var_pct=22.0, upfront=4700.0,
        horizon=36, arpu_growth=3.0, ramp_months=2, capacity=30,
        note=("Care membership for the rare/mature indoor & terrace plant "
              "collections of prime-central London homes and embassies. "
              "Survived adversarial review as a strong but capacity-capped "
              "solo venture (~25-30 homes ≈ £100-150k). Customer = a home on a "
              "monthly care contract."),
    ),
    "DoorLedger — fire-door compliance (B2B)": dict(
        rent=0.0, other_fixed=400.0, arpu=400.0, new_cust=2.0, growth=10.0,
        churn=1.0, cac=200.0, var_pct=25.0, upfront=4500.0,
        horizon=36, arpu_growth=3.0, ramp_months=1, capacity=60,
        note=("Quarterly/annual fire-door inspection + evidence logging for "
              "London residential blocks (Fire Safety Regs 2022). Mandatory, "
              "very sticky audit-trail. Customer = a managed block (~150-250 "
              "doors). Fastest, most reliable £100k path — but a known "
              "post-Grenfell compliance market, so compete on the evidence "
              "dashboard, not novelty."),
    ),
    "PassPrep — landlord compliance concierge (B2B)": dict(
        rent=0.0, other_fixed=500.0, arpu=15.0, new_cust=25.0, growth=10.0,
        churn=1.5, cac=20.0, var_pct=15.0, upfront=3500.0,
        horizon=36, arpu_growth=4.0, ramp_months=1, capacity=1200,
        note=("Done-for-you certificate/compliance tracking (gas, EICR, EPC, "
              "HMO licensing) for small landlords, riding the Renters' Rights "
              "Bill. Customer = one let property (~£150/yr). Low ticket, so the "
              "£100k path needs ~600+ properties — win letting-agent channels "
              "early. Moat is trust/accountability, not the software."),
    ),
    "Saaya — diaspora death & repatriation concierge": dict(
        rent=0.0, other_fixed=1300.0, arpu=60.0, new_cust=12.0, growth=12.0,
        churn=1.0, cac=35.0, var_pct=20.0, upfront=8500.0,
        horizon=36, arpu_growth=2.0, ramp_months=2, capacity=250,
        note=("Faith-aligned funeral + overseas repatriation concierge for "
              "London's South Asian/African/Muslim/Hindu families. Huge, "
              "rising, AI-proof demand — BUT adversarial review FAILED the "
              "headline model: 'membership float' likely hits FCA pre-paid-plan "
              "rules, competition is fierce (mosque committees at near-cost), "
              "and working capital is ~10x under-budgeted. Model the de-risked, "
              "per-event-only version."),
    ),
    "Threshold — falls-proofing / stay-put membership": dict(
        rent=0.0, other_fixed=1700.0, arpu=110.0, new_cust=6.0, growth=12.0,
        churn=2.0, cac=140.0, var_pct=45.0, upfront=9000.0,
        horizon=36, arpu_growth=3.0, ramp_months=1, capacity=500,
        note=("Home falls-proofing installs + a 'stay-put reassurance' "
              "membership for outer-London ageing-in-place homeowners. "
              "Adversarial review: solid lifestyle install business, but the "
              "recurring-membership thesis is the weakest part (telecare/"
              "wearables own the reassurance wallet; the book decays as members "
              "die/move into care). Lead with installs; treat membership as a "
              "small add-on."),
    ),
    "Custom — blank slate": dict(
        rent=1000.0, other_fixed=500.0, arpu=80.0, new_cust=10.0, growth=8.0,
        churn=3.0, cac=60.0, var_pct=30.0, upfront=8000.0,
        horizon=36, arpu_growth=0.0, ramp_months=1, capacity=0,
        note="A blank, sensible starting point — e.g. your flower-shop example. "
             "Set every input yourself.",
    ),
}
 
# The widget keys we drive from a preset. Kept in one place so loading a preset
# and reading inputs back stay in sync.
INPUT_KEYS = [
    "rent", "other_fixed", "arpu", "new_cust", "growth", "churn", "cac",
    "var_pct", "upfront", "horizon", "arpu_growth", "ramp_months", "capacity",
]
 
 
# ---------------------------------------------------------------------------
# THE MODEL  (pure functions — no Streamlit inside, so they're easy to test)
# ---------------------------------------------------------------------------
@dataclass
class Inputs:
    """All the levers of the business model."""
    rent: float            # £/month fixed premises cost
    other_fixed: float     # £/month other fixed costs (insurance, software, van...)
    arpu: float            # £/month average revenue per ACTIVE customer
    new_cust: float        # new customers acquired in month 1
    growth: float          # % monthly growth in new-customer acquisition
    churn: float           # % of active customers lost each month
    cac: float             # £ marketing cost to acquire one customer
    var_pct: float         # variable cost as % of revenue
    upfront: float         # £ one-off startup spend (month 0)
    horizon: int           # number of months to project
    arpu_growth: float     # % ANNUAL price increase on ARPU
    ramp_months: int       # months of acquisition before any revenue is billed
    capacity: float        # max active customers a solo operator can serve (0 = unlimited)
 
 
def run_model(inp: Inputs) -> pd.DataFrame:
    """Run the month-by-month cohort model and return a tidy DataFrame.
 
    The customer base evolves as:
        active[m] = active[m-1] * (1 - churn) + new[m]
    New-customer acquisition compounds at `growth`; ARPU compounds at
    `arpu_growth` (annualised). Revenue only starts being billed after
    `ramp_months` (you still pay CAC to acquire during the ramp).
    """
    H = int(inp.horizon)
    g = inp.growth / 100.0
    c = inp.churn / 100.0
    v = inp.var_pct / 100.0
    arpu_g_m = (1 + inp.arpu_growth / 100.0) ** (1 / 12) - 1  # monthly equiv.
 
    rows = []
    active = 0.0
    cum_cash = -inp.upfront          # upfront spent at month 0
    cum_profit = 0.0
    cum_marketing = 0.0
 
    for m in range(1, H + 1):
        new = inp.new_cust * ((1 + g) ** (m - 1))
        retained = active * (1 - c)
        # Capacity ceiling: a solo operator can only serve so many accounts.
        # Once near full you only acquire enough to backfill churn (and you
        # only pay CAC on customers you actually take on).
        if inp.capacity and inp.capacity > 0:
            room = max(inp.capacity - retained, 0.0)
            new = min(new, room)
        active = retained + new
 
        arpu_m = inp.arpu * ((1 + arpu_g_m) ** (m - 1))
        billing = m > inp.ramp_months            # revenue switched on after ramp
        revenue = active * arpu_m if billing else 0.0
 
        variable = revenue * v
        marketing = new * inp.cac
        fixed = inp.rent + inp.other_fixed
        ebitda = revenue - variable - fixed - marketing   # monthly operating profit
 
        cum_profit += ebitda
        cum_cash += ebitda
        cum_marketing += marketing
 
        rows.append(dict(
            Month=m,
            New_Customers=new,
            Active_Customers=active,
            Revenue=revenue,
            Variable_Cost=variable,
            Fixed_Cost=fixed,
            Marketing_Cost=marketing,
            Monthly_Profit=ebitda,
            Cumulative_Cash=cum_cash,
            Cumulative_Profit=cum_profit,
            Cumulative_Marketing=cum_marketing,
        ))
 
    return pd.DataFrame(rows)
 
 
def compute_kpis(df: pd.DataFrame, inp: Inputs) -> dict:
    """Headline KPIs derived from a model run."""
    # Break-even = first month cumulative cash turns non-negative.
    be = df.loc[df["Cumulative_Cash"] >= 0, "Month"]
    break_even = int(be.iloc[0]) if not be.empty else None
 
    def year_rev(year: int) -> float:
        lo, hi = (year - 1) * 12 + 1, year * 12
        return float(df.loc[(df.Month >= lo) & (df.Month <= hi), "Revenue"].sum())
 
    horizon = int(inp.horizon)
    final_cum_profit = float(df["Cumulative_Profit"].iloc[-1])
    total_invested = inp.upfront + float(df["Cumulative_Marketing"].iloc[-1])
 
    # Simple unit economics. LTV = ARPU * gross-margin / churn (months of life).
    gross_margin = 1 - inp.var_pct / 100.0
    churn = max(inp.churn / 100.0, 1e-6)
    ltv = inp.arpu * gross_margin / churn
    ltv_cac = ltv / inp.cac if inp.cac > 0 else float("inf")
 
    return {
        "Break-even month": break_even,
        "Year 1 revenue": year_rev(1),
        "Year 2 revenue": year_rev(2),
        "Year 3 revenue": year_rev(3),
        "Revenue (final month, annualised)": float(df["Revenue"].iloc[-1]) * 12,
        "Active customers (final month)": float(df["Active_Customers"].iloc[-1]),
        f"Cumulative profit @ month {horizon}": final_cum_profit,
        "ROI on total invested": (final_cum_profit / total_invested) if total_invested else 0.0,
        "Customer LTV (£)": ltv,
        "LTV / CAC": ltv_cac,
        "Months to £100k annual run-rate": _month_hits_runrate(df, 100_000),
    }
 
 
def _month_hits_runrate(df: pd.DataFrame, target_annual: float):
    """First month whose annualised revenue (x12) reaches a target, or None."""
    hit = df.loc[df["Revenue"] * 12 >= target_annual, "Month"]
    return int(hit.iloc[0]) if not hit.empty else None
 
 
# ---------------------------------------------------------------------------
# Small formatting + UI helpers
# ---------------------------------------------------------------------------
def gbp(x) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"£{x:,.0f}"
 
 
def load_preset_into_state(preset_name: str) -> None:
    """Copy a preset's numbers into session_state so the widgets pick them up."""
    p = PRESETS[preset_name]
    for k in INPUT_KEYS:
        st.session_state[k] = p[k]
 
 
# Initialise session state on first run with the top-pick preset.
if "preset" not in st.session_state:
    st.session_state["preset"] = list(PRESETS.keys())[0]
    load_preset_into_state(st.session_state["preset"])
    st.session_state["_active_preset"] = st.session_state["preset"]
 
 
# ---------------------------------------------------------------------------
# SIDEBAR — preset selector + every input lever
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📈 London Venture Modeller")
    st.caption("Model any of the researched <=£10k London businesses — or your own.")
 
    st.selectbox(
        "Business preset",
        options=list(PRESETS.keys()),
        key="preset",
        help="Pick an idea to load grounded defaults, then tweak below.",
    )
    # Reconcile the inputs to the chosen preset on EVERY rerun. This is more
    # robust than an on_change callback (which can occasionally be skipped on a
    # fast click, leaving the main panel showing the new name but the old
    # numbers). It MUST run before the input widgets below are instantiated —
    # Streamlit forbids writing a widget's session_state key after the widget
    # exists. Manual tweaks are preserved because we only reload when the preset
    # actually changes.
    if st.session_state.get("_active_preset") != st.session_state["preset"]:
        load_preset_into_state(st.session_state["preset"])
        st.session_state["_active_preset"] = st.session_state["preset"]
 
    if st.button("↺ Reset to preset defaults", width="stretch"):
        load_preset_into_state(st.session_state["preset"])
 
    st.divider()
    st.subheader("Revenue drivers")
    st.number_input("Avg monthly revenue per customer (£)", 0.0, 100_000.0,
                    step=10.0, key="arpu",
                    help="Subscription fee, or per-client monthly run-rate.")
    st.number_input("New customers in month 1", 0.0, 10_000.0, step=0.5,
                    key="new_cust")
    st.slider("Monthly growth in acquisition (%)", -10.0, 40.0, step=0.5,
              key="growth")
    st.slider("Monthly churn (%)", 0.0, 25.0, step=0.5, key="churn",
              help="Share of active customers lost each month.")
    st.slider("Annual price increase on ARPU (%)", 0.0, 20.0, step=0.5,
              key="arpu_growth")
    st.number_input("Capacity cap — max active customers (0 = unlimited)",
                    0.0, 100_000.0, step=10.0, key="capacity",
                    help="Solo operators have a ceiling. Every stress-test "
                         "flagged this as the real limit on these businesses.")
 
    st.subheader("Cost drivers")
    st.number_input("Monthly rent (£)", 0.0, 50_000.0, step=50.0, key="rent")
    st.number_input("Other fixed monthly costs (£)", 0.0, 50_000.0, step=50.0,
                    key="other_fixed",
                    help="Insurance, software, van, phone, subscriptions…")
    st.slider("Variable cost (% of revenue)", 0.0, 95.0, step=1.0, key="var_pct")
    st.number_input("Customer acquisition cost — CAC (£)", 0.0, 10_000.0,
                    step=5.0, key="cac")
 
    st.subheader("Capital & horizon")
    st.number_input("Upfront startup spend (£)", 0.0, 100_000.0, step=250.0,
                    key="upfront")
    st.slider("Months before billing starts (ramp)", 0, 12, step=1,
              key="ramp_months")
    st.slider("Projection horizon (months)", 12, 60, step=6, key="horizon")
 
    over_budget = st.session_state["upfront"] > 10_000
    if over_budget:
        st.error(f"⚠️ Upfront {gbp(st.session_state['upfront'])} exceeds the "
                 f"£10,000 cap.")
    else:
        st.success(f"✅ Upfront {gbp(st.session_state['upfront'])} — within the "
                   f"£10,000 cap.")
 
 
# Build the Inputs object from session state.
inp = Inputs(**{k: st.session_state[k] for k in INPUT_KEYS})
df = run_model(inp)
kpis = compute_kpis(df, inp)
 
 
# ---------------------------------------------------------------------------
# MAIN AREA
# ---------------------------------------------------------------------------
st.header(st.session_state["preset"])
 
tab_model, tab_scenarios, tab_sens, tab_export, tab_ideas = st.tabs(
    ["📊 Model", "🎚️ Scenarios", "🌪️ Sensitivity", "💾 Export", "ℹ️ Ideas"]
)
 
# ============================ TAB 1 — MODEL ================================
with tab_model:
    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    be = kpis["Break-even month"]
    c1.metric("Break-even", f"Month {be}" if be else "Not in horizon")
    c2.metric("Year 1 revenue", gbp(kpis["Year 1 revenue"]))
    c3.metric("Year 2 revenue", gbp(kpis["Year 2 revenue"]))
    c4.metric("Year 3 revenue", gbp(kpis["Year 3 revenue"]))
 
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Cumulative profit", gbp(kpis[f"Cumulative profit @ month {inp.horizon}"]))
    c6.metric("ROI on capital", f"{kpis['ROI on total invested']*100:,.0f}%")
    c7.metric("LTV / CAC", f"{kpis['LTV / CAC']:.1f}×"
              if np.isfinite(kpis["LTV / CAC"]) else "∞")
    hit = kpis["Months to £100k annual run-rate"]
    c8.metric("£100k run-rate by", f"Month {hit}" if hit else "Not reached")
 
    st.divider()
 
    left, right = st.columns(2)
 
    # Revenue & active customers
    with left:
        st.subheader("Revenue & active customers")
        fig = go.Figure()
        fig.add_bar(x=df.Month, y=df.Revenue, name="Monthly revenue",
                    marker_color="#2E7D32", opacity=0.6)
        fig.add_trace(go.Scatter(x=df.Month, y=df.Active_Customers,
                                 name="Active customers", yaxis="y2",
                                 line=dict(color="#1565C0", width=3)))
        fig.update_layout(
            yaxis=dict(title="Revenue (£/mo)"),
            yaxis2=dict(title="Active customers", overlaying="y", side="right",
                        showgrid=False),
            xaxis_title="Month", legend=dict(orientation="h"),
            margin=dict(t=10, b=10), height=380,
        )
        st.plotly_chart(fig, width="stretch")
 
    # Cash flow + break-even
    with right:
        st.subheader("Cash flow & break-even")
        fig = go.Figure()
        fig.add_bar(x=df.Month, y=df.Monthly_Profit, name="Monthly profit",
                    marker_color=np.where(df.Monthly_Profit >= 0, "#43A047",
                                          "#E53935"))
        fig.add_trace(go.Scatter(x=df.Month, y=df.Cumulative_Cash,
                                 name="Cumulative cash",
                                 line=dict(color="#6A1B9A", width=3)))
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        if be:
            fig.add_vline(x=be, line_dash="dash", line_color="#6A1B9A")
            fig.add_annotation(x=be, y=0, text=f"break-even M{be}",
                               showarrow=True, arrowhead=2, yshift=20)
        fig.update_layout(xaxis_title="Month", yaxis_title="£",
                          legend=dict(orientation="h"),
                          margin=dict(t=10, b=10), height=380)
        st.plotly_chart(fig, width="stretch")
 
    # Cost stack
    st.subheader("Where the money goes (monthly)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.Month, y=df.Variable_Cost, name="Variable",
                             stackgroup="c", line=dict(width=0),
                             fillcolor="rgba(229,57,53,0.6)"))
    fig.add_trace(go.Scatter(x=df.Month, y=df.Fixed_Cost, name="Fixed",
                             stackgroup="c", line=dict(width=0),
                             fillcolor="rgba(255,179,0,0.6)"))
    fig.add_trace(go.Scatter(x=df.Month, y=df.Marketing_Cost, name="Marketing",
                             stackgroup="c", line=dict(width=0),
                             fillcolor="rgba(30,136,229,0.6)"))
    fig.add_trace(go.Scatter(x=df.Month, y=df.Revenue, name="Revenue",
                             line=dict(color="#2E7D32", width=3)))
    fig.update_layout(xaxis_title="Month", yaxis_title="£/mo",
                      legend=dict(orientation="h"), margin=dict(t=10, b=10),
                      height=360)
    st.plotly_chart(fig, width="stretch")
 
    with st.expander("See the full monthly model table"):
        st.dataframe(
            df.style.format({c: "{:,.0f}" for c in df.columns if c != "Month"}),
            width="stretch", height=320,
        )
 
 
# ============================ TAB 2 — SCENARIOS ============================
with tab_scenarios:
    st.subheader("Best / Base / Worst comparison")
    st.caption("Each scenario multiplies the key drivers off your current "
               "(base) inputs. Drag to explore how fragile the plan is.")
 
    cc1, cc2 = st.columns(2)
    with cc1:
        opt = st.slider("Optimistic uplift on ARPU & acquisition (%)", 0, 100,
                        25, 5)
        opt_churn = st.slider("Optimistic churn multiplier", 0.1, 1.0, 0.6, 0.1)
    with cc2:
        pess = st.slider("Pessimistic haircut on ARPU & acquisition (%)", 0, 80,
                         30, 5)
        pess_churn = st.slider("Pessimistic churn multiplier", 1.0, 4.0, 1.8, 0.1)
 
    def scaled(mult_rev: float, mult_churn: float) -> Inputs:
        d = asdict(inp)
        d["arpu"] *= mult_rev
        d["new_cust"] *= mult_rev
        d["churn"] = min(d["churn"] * mult_churn, 90.0)
        return Inputs(**d)
 
    scenarios = {
        "Worst":  scaled(1 - pess / 100, pess_churn),
        "Base":   inp,
        "Best":   scaled(1 + opt / 100, opt_churn),
    }
    colours = {"Worst": "#E53935", "Base": "#1565C0", "Best": "#2E7D32"}
 
    runs = {name: run_model(i) for name, i in scenarios.items()}
 
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        for name, r in runs.items():
            fig.add_trace(go.Scatter(x=r.Month, y=r.Revenue, name=name,
                                     line=dict(color=colours[name], width=3)))
        fig.update_layout(title="Monthly revenue", xaxis_title="Month",
                          yaxis_title="£/mo", legend=dict(orientation="h"),
                          height=380, margin=dict(t=40, b=10))
        st.plotly_chart(fig, width="stretch")
    with g2:
        fig = go.Figure()
        for name, r in runs.items():
            fig.add_trace(go.Scatter(x=r.Month, y=r.Cumulative_Cash, name=name,
                                     line=dict(color=colours[name], width=3)))
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title="Cumulative cash", xaxis_title="Month",
                          yaxis_title="£", legend=dict(orientation="h"),
                          height=380, margin=dict(t=40, b=10))
        st.plotly_chart(fig, width="stretch")
 
    # Scenario KPI comparison table
    comp = []
    for name, i in scenarios.items():
        k = compute_kpis(runs[name], i)
        comp.append({
            "Scenario": name,
            "Break-even (month)": k["Break-even month"] or "—",
            "Year 1 rev": gbp(k["Year 1 revenue"]),
            "Year 2 rev": gbp(k["Year 2 revenue"]),
            "Year 3 rev": gbp(k["Year 3 revenue"]),
            f"Cum. profit @ M{inp.horizon}": gbp(k[f"Cumulative profit @ month {inp.horizon}"]),
            "ROI": f"{k['ROI on total invested']*100:,.0f}%",
        })
    st.dataframe(pd.DataFrame(comp), width="stretch", hide_index=True)
 
 
# ============================ TAB 3 — SENSITIVITY =========================
with tab_sens:
    st.subheader("Sensitivity — what moves the needle?")
    st.caption("Each driver is flexed ±X% (churn flexed inversely). Bars show "
               "the change in cumulative profit at the end of the horizon. "
               "Longest bars = the assumptions to validate first.")
 
    swing = st.slider("Flex each driver by ± (%)", 5, 50, 20, 5)
    base_profit = df["Cumulative_Profit"].iloc[-1]
 
    def profit_with(**overrides) -> float:
        d = asdict(inp)
        d.update(overrides)
        return run_model(Inputs(**d))["Cumulative_Profit"].iloc[-1]
 
    s = swing / 100.0
    drivers = {
        "ARPU (price)":        ("arpu", inp.arpu),
        "New customers":       ("new_cust", inp.new_cust),
        "Acquisition growth":  ("growth", inp.growth),
        "Churn":               ("churn", inp.churn),
        "Variable cost %":     ("var_pct", inp.var_pct),
        "CAC":                 ("cac", inp.cac),
        "Fixed cost":          ("other_fixed", inp.other_fixed),
    }
 
    labels, los, his = [], [], []
    for label, (key, val) in drivers.items():
        # For "good" drivers up = +swing; for cost/churn, up = -swing (improvement).
        if key in ("churn", "var_pct", "cac", "other_fixed"):
            low, high = val * (1 + s), val * (1 - s)   # worse, better
        else:
            low, high = val * (1 - s), val * (1 + s)
        p_low = profit_with(**{key: low}) - base_profit
        p_high = profit_with(**{key: high}) - base_profit
        labels.append(label)
        los.append(p_low)
        his.append(p_high)
 
    order = np.argsort([abs(h - l) for l, h in zip(los, his)])
    labels = [labels[i] for i in order]
    los = [los[i] for i in order]
    his = [his[i] for i in order]
 
    fig = go.Figure()
    fig.add_bar(y=labels, x=los, orientation="h", name=f"-{swing}% (downside)",
                marker_color="#E53935")
    fig.add_bar(y=labels, x=his, orientation="h", name=f"+{swing}% (upside)",
                marker_color="#2E7D32")
    fig.update_layout(barmode="overlay", xaxis_title="Δ cumulative profit (£)",
                      legend=dict(orientation="h"), height=420,
                      margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.info(f"Base-case cumulative profit at month {inp.horizon}: "
            f"**{gbp(base_profit)}**")
 
 
# ============================ TAB 4 — EXPORT ==============================
with tab_export:
    st.subheader("Export the model")
 
    kpi_df = pd.DataFrame(
        [(k, v) for k, v in kpis.items()], columns=["KPI", "Value"]
    )
 
    st.download_button(
        "⬇️ Download monthly model (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{st.session_state['preset'].split(' —')[0]}_model.csv",
        mime="text/csv", width="stretch",
    )
 
    # Excel with three sheets: Inputs, Model, KPIs.
    def build_excel() -> bytes:
        buf = io.BytesIO()
        try:
            writer = pd.ExcelWriter(buf, engine="xlsxwriter")
        except Exception:                       # fallback if xlsxwriter missing
            writer = pd.ExcelWriter(buf, engine="openpyxl")
        with writer:
            pd.DataFrame([asdict(inp)]).T.rename(columns={0: "value"}).to_excel(
                writer, sheet_name="Inputs")
            df.to_excel(writer, sheet_name="Model", index=False)
            kpi_df.to_excel(writer, sheet_name="KPIs", index=False)
        return buf.getvalue()
 
    st.download_button(
        "⬇️ Download full workbook (Excel)",
        build_excel(),
        file_name=f"{st.session_state['preset'].split(' —')[0]}_model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
 
    st.divider()
    st.write("**Current KPIs**")
    st.dataframe(kpi_df, width="stretch", hide_index=True)
 
 
# ============================ TAB 5 — IDEAS ==============================
with tab_ideas:
    st.subheader("The modelled businesses (with the honest caveats)")
    st.caption("Defaults are seeded from the strategy analysis. The notes "
               "include what the adversarial stress-test found — read them "
               "before believing any projection.")
    for name, p in PRESETS.items():
        with st.expander(name, expanded=name.startswith("Greenwarden")):
            a, b, c = st.columns(3)
            a.metric("Upfront", gbp(p["upfront"]))
            b.metric("ARPU (£/mo)", gbp(p["arpu"]))
            c.metric("Churn", f"{p['churn']:.1f}%/mo")
            st.write(p["note"])
 
    st.divider()
    st.caption("Model logic: active[m] = active[m-1]·(1−churn) + new[m]; "
               "revenue = active·ARPU; profit = revenue − variable − fixed − "
               "CAC·new. A generalisation — sanity-check it against your real "
               "unit economics before betting on it.")