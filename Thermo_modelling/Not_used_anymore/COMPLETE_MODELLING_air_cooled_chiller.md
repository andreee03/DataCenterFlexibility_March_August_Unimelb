# Air-Cooled Chiller Condenser — Equation Reference Sheet

## Why this is a different model, not a variant of the cooling tower one

In the cooling tower case, **air** picked up moisture (latent heat) from evaporating **water**. In an air-cooled chiller, the ambient air stays dry from start to finish — it only ever exchanges **sensible** heat across a finned coil. The phase change instead happens **inside the tubes**, where the **refrigerant** condenses from superheated vapor to subcooled liquid. So:

- No Merkel model, no enthalpy-potential driving force, no $C_s$, no Magnus formula, no $h_{sat}(T)$/$w_{sat}(T)$ — none of that psychrometric machinery is needed, because air never approaches saturation.
- The latent heat is now on the **refrigerant** side, governed by its own equation of state (pressure-temperature-enthalpy relations specific to whichever refrigerant you use — R134a, R410A, R1234ze, etc.) rather than water/steam tables.
- The heat exchanger becomes a straightforward **cross-flow, phase-change-on-one-side** exchanger — a much simpler and more standard piece of heat-exchanger theory than Merkel/Poppe.

---

## 1. Air-Side Sensible Heat Balance

### 1. Equation
$$
\dot{Q} = G_{air}\,c_{pa}\,(T_{air,out}-T_{air,in})
$$

### 2. Solid scientific sources
- Standard sensible-only heat exchanger energy balance — any heat transfer textbook, e.g., **Incropera, F.P., DeWitt, D.P.**, *Fundamentals of Heat and Mass Transfer*, chapter on heat exchangers.
- Applied specifically to air-cooled condensers in: **Browne, M.W., Bansal, P.K. (1998)**, "Challenges in Modelling Vapour-Compression Liquid Chillers," or the follow-up **"An elemental NTU-ε model for vapour-compression liquid chillers"**, *International Journal of Refrigeration*, which models both the condenser and evaporator with this style of energy balance.

### 3. Quick check
Search: `air cooled condenser sensible heat balance G cpa air outlet temperature` — this is the most basic possible energy balance for a dry-air stream, reproduced identically in any HVAC or refrigeration textbook chapter on air-cooled heat exchangers.

### 4. Assumptions
- Air is treated as **dry** throughout — no condensation of atmospheric moisture on the coil (valid unless the coil surface temperature drops below the ambient dew point, which essentially never happens on the *hot* side of a condenser).
- $c_{pa}\approx1.006$ kJ/(kg·K), constant over the modest temperature range involved.
- No heat leakage to/from the casing or ductwork outside the coil itself.

### 5. Validity domain
Valid for any dry-coil, forced-convection air-cooled condenser operating with ambient air below its dew point at the coil surface — essentially all normal operating conditions. It **would** break down (need a wet-coil/latent term added back in) only in the unusual case of condensation forming on the coil fins themselves, which is not a normal air-cooled condenser design condition (that's a symptom, not a design assumption).

---

## 2. Effectiveness-NTU Model for a Condenser (One-Side Phase Change)

### 1. Equation
$$
\varepsilon = 1-\exp(-NTU), \qquad NTU = \frac{UA}{C_{min}} = \frac{UA}{G_{air}\,c_{pa}}
$$

This is the general counterflow/crossflow ε-NTU formula reduced to the special case $C_r = C_{min}/C_{max} \to 0$.

### 2. Solid scientific sources
- General derivation of $\varepsilon=1-\exp(-NTU)$ for $C_r=0$: **Kays, W.M., London, A.L.**, *Compact Heat Exchangers*; **Incropera & DeWitt**, *Fundamentals of Heat and Mass Transfer* — standard textbook result, valid for parallel-flow, counterflow, or crossflow arrangements alike when one fluid's capacity rate is effectively infinite (a condensing or evaporating pure fluid at constant temperature).
- Applied directly to air-cooled condensers/evaporators: **Bourdouxhe, J.P., Grodent, M., Lebrun, J. (1994)**, *HVAC1 Toolkit: A Toolkit for Primary HVAC System Energy Calculation*, ASHRAE — models chiller condensers/evaporators with a constant-UA effectiveness approach.
- Also: **Browne, M.W., Bansal, P.K. (2001)**, "An elemental NTU-ε model for vapour-compression liquid chillers," *International Journal of Refrigeration*, which extends this to an "elemental" (multi-zone) version — see equation 3 below.

### 3. Quick check
Search: `effectiveness NTU condenser Cr=0 epsilon 1-exp(-NTU)` — this exact reduced formula appears in every standard heat-exchanger textbook's summary table (it's one of the most commonly quoted special cases of the ε-NTU method, alongside the counterflow and crossflow general forms you used for the cooling tower).

### 4. Assumptions
- The refrigerant side has an **effectively infinite heat capacity rate** ($C_{max}\to\infty$) because it changes phase at (nearly) constant pressure and therefore constant saturation temperature — true for the **condensing zone only**, not for the desuperheating or subcooling zones (see equation 3).
- $UA$ (overall conductance) is treated as a single lumped constant across the whole coil — a simplification, since in reality the refrigerant-side heat transfer coefficient differs substantially between the desuperheating, condensing, and subcooling zones.
- No axial conduction along the tube/fin metal; fin efficiency is folded into the $U$ value.

### 5. Validity domain
Excellent approximation for the **condensing zone**, which usually accounts for 70–85% of a typical air-cooled condenser's surface area and heat duty. It should **not** be applied as a single lumped $UA$ across the entire coil including desuperheat/subcooling if you need better than a few °C accuracy — for that, a 3-zone (or "elemental") model is standard practice (equation 3). Given your ±1°C tolerance, decide whether one lumped zone is acceptable or whether you need the 3-zone split.

---

## 3. Multi-Zone Refrigerant-Side Energy Balance (Desuperheat / Condensing / Subcooling)

### 1. Equation
$$
\dot{Q}_{total} = \dot{Q}_{desup}+\dot{Q}_{cond}+\dot{Q}_{sub} = \dot{m}_{ref}\big[(h_{in}-h_{sat,vap})+(h_{sat,vap}-h_{sat,liq})+(h_{sat,liq}-h_{out})\big]
$$

i.e. simply $\dot{Q}_{total} = \dot{m}_{ref}(h_{in}-h_{out})$, split into three physically distinct zones, each with its own local heat transfer coefficient and therefore its own local $UA_i$ and $\varepsilon_i$.

### 2. Solid scientific sources
- **Browne, M.W., Bansal, P.K. (2001)**, "An elemental NTU-ε model for vapour-compression liquid chillers," *International Journal of Refrigeration*, 25(3) — the standard reference for splitting a condenser (and evaporator) into these three zones, each solved with its own local ε-NTU relation, then linked by matching the air temperature leaving one zone to the air temperature entering the next.
- **Van Houte, S., Van den Bulck, E.** — a steady-state centrifugal chiller model using this same "3-zone" refrigerant-side decomposition (saturated liquid, two-phase, superheated vapor), an approach also referenced by later reviews of chiller modeling.
- The refrigerant-side enthalpy values themselves ($h_{in}, h_{sat,vap}, h_{sat,liq}, h_{out}$) come from the specific refrigerant's **equation of state** — see equation 4.

### 3. Quick check
Search: `Browne Bansal elemental NTU epsilon model vapour compression liquid chiller desuperheating condensing subcooling` — this is the standard citation for the 3-zone refrigerant condenser decomposition used across later chiller-modeling literature.

### 4. Assumptions
- Refrigerant flow is assumed **uniform and single-pass** through each zone in sequence (no flow mal-distribution across parallel circuits, which real multi-circuit coils do have in practice).
- Pressure drop across the coil is neglected (or treated separately) — the whole zone split assumes a single, well-defined saturation temperature/pressure for the condensing zone.
- Each zone's heat transfer coefficient (and thus $UA_i$) is treated as locally uniform, computed from standard refrigerant-side correlations (e.g., **Shah's correlation** for in-tube condensation, **Dittus-Boelter/Gnielinski** for single-phase desuperheat/subcooling) combined with an air-side finned-tube correlation.

### 5. Validity domain
This is the standard approach for **any vapor-compression refrigerant condenser** (air-cooled or water-cooled) and is valid across the whole normal chiller operating envelope. The main practical limitation: it requires you to know (or estimate) the relative surface-area split between the three zones, which is a **design detail specific to the coil**, not a universal constant — this is analogous to how $NTU_{design}$ was tower-specific in the water-cooling case.

---

## 4. Refrigerant Saturation Pressure-Temperature Relation

### 1. Equation
There is **no simple closed-form Magnus-style formula** here — refrigerant saturation curves are refrigerant-specific and are computed via full **equations of state** (typically Helmholtz-energy-based formulations), not a single universal exponential:
$$
P_{sat,ref} = f_{EOS}(T_{sat}; \text{refrigerant-specific coefficients})
$$
practically evaluated via **NIST REFPROP** (or an equivalent simplified cubic EOS such as Peng-Robinson) rather than a hand-typed formula.

### 2. Solid scientific sources
- **Lemmon, E.W., Huber, M.L., McLinden, M.O.**, *NIST Standard Reference Database 23: Reference Fluid Thermodynamic and Transport Properties (REFPROP)*, NIST, Gaithersburg, MD — the authoritative source; built on Helmholtz-energy equations of state fitted to experimental P-V-T-h-s data for each specific refrigerant.
- For a lighter-weight closed-form alternative: **Peng, D.Y., Robinson, D.B. (1976)**, "A New Two-Constant Equation of State," *Industrial & Engineering Chemistry Fundamentals*, 15(1), 59–64 — the classic cubic EOS; shown to track R134a saturation behavior well in the automotive-refrigerant literature (see the Peng-Robinson vs. Patel-Teja comparison study for R134a).

### 3. Quick check
For quick verification without running an EOS: refrigerant manufacturers (Honeywell, Chemours/DuPont, Danfoss) publish **pressure-temperature charts/tables** for each refrigerant, generated directly from REFPROP — e.g., search `R134a pressure temperature chart NIST REFPROP` or `R410A P-T chart` for the specific refrigerant in your model; these are free, standard reference tables (not something you need to derive yourself).

### 4. Assumptions
- Equilibrium (saturated) conditions — the refrigerant is assumed to be at true thermodynamic equilibrium between liquid and vapor phases at the tube wall/bulk conditions used.
- No refrigerant blend "glide" — if you're using a **zeotropic blend** (e.g., R410A's near-negligible glide, or R407C's more significant ~5°C glide), the saturation "temperature" is no longer a single value at a given pressure but a range (bubble point to dew point) — this significantly complicates the simple single-$T_{sat}$ assumption used in equation 3 above.
- Pure/near-azeotropic refrigerants (R134a, R410A, R32) behave closely enough to a single-component fluid that a single $T_{sat}(P)$ curve is an excellent approximation.

### 5. Validity domain
NIST REFPROP is validated against experimental data typically from around −100°C to well above typical condensing temperatures (up to 100–150°C) for common HVAC refrigerants — comfortably covers any realistic air-cooled condenser operating range. **Practical recommendation for a lumped, "no-fit" model in the spirit of what you wanted for the cooling tower:** rather than hand-deriving an EOS, pull a small P-T lookup table (10–20 points spanning your expected condensing range) directly from the refrigerant manufacturer's published chart or REFPROP, and interpolate — this is the refrigerant-side equivalent of using the Magnus formula, except here the "formula" is genuinely refrigerant-specific reference data rather than one universal equation.

---

## 5. Second Time Scale — Coil/Refrigerant Thermal Capacitance (replaces the basin residence time)

There is no water basin in an air-cooled system, so the relevant "how fast can the output actually change" time constant is different. Two candidate time scales:

### 1. Equation

**(a) Refrigerant residence time in the coil:**
$$
\tau_{ref} = \frac{M_{ref,charge\ in\ coil}}{\dot{m}_{ref}}
$$

**(b) Coil metal + refrigerant thermal capacitance time constant (usually the dominant, slower one):**
$$
\tau_{coil} = \frac{M_{metal}\,c_{p,metal}+M_{ref}\,c_{p,ref}}{UA}
$$

### 2. Solid scientific sources
- Both are direct applications of standard **lumped thermal capacitance** modeling — see **Incropera & DeWitt**, *Fundamentals of Heat and Mass Transfer*, chapter on transient (lumped-capacitance) heat conduction, for the general form $\tau = mc_p/(hA)$.
- Applied specifically to refrigeration-cycle transient/dynamic modeling: **Rasmussen, B.P., Alleyne, A.G. (2004)** and related vapor-compression system dynamic modeling literature use exactly this style of lumped coil thermal-mass time constant to characterize condenser/evaporator response speed in control-oriented models.

### 3. Quick check
Search: `lumped capacitance time constant mc_p/hA heat exchanger` for the general form, or `vapor compression cycle dynamic model condenser thermal mass time constant control-oriented` for the refrigeration-specific application (Rasmussen & Alleyne is a widely-cited starting point for control-oriented chiller/AC dynamic models).

### 4. Assumptions
- Treats the coil (tube + fin metal, plus refrigerant charge held up in it at any instant) as a **single lumped thermal mass** — ignores spatial temperature gradients along the coil, same simplification as the basin's "well-mixed" assumption in the water-cooling case.
- Assumes $UA$ (the same conductance from equation 2) is roughly constant near the operating point used to evaluate $\tau$.

### 5. Validity domain
Both time scales are typically **much shorter** than the cooling-tower basin residence time was — a typical air-cooled condenser coil holds a much smaller thermal mass than a tower sump. Order-of-magnitude expectation: $\tau_{ref}$ (refrigerant transit) is on the order of a few seconds; $\tau_{coil}$ (metal + charge capacitance) is typically tens of seconds to a couple of minutes depending on coil size. **Practical implication for your lumped model:** compare whichever of these is larger (usually $\tau_{coil}$) against your simulation timestep $\Delta t$, exactly as you did for $\tau_{basin}$ — if $\Delta t \gg \tau_{coil}$, a quasi-steady (instantaneous ε-NTU) solve at each step is justified; if $\Delta t$ is comparable to or smaller than $\tau_{coil}$, you'd need to actually integrate the coil's transient thermal state rather than assuming instantaneous equilibrium.

---

## Summary Table

| # | Equation | Primary Source | Validity Range |
|---|---|---|---|
| 1 | $\dot{Q}=G_{air}c_{pa}\Delta T_{air}$ | Incropera & DeWitt; Browne & Bansal | Dry-coil operation (no condensation on fins) |
| 2 | $\varepsilon=1-\exp(-NTU)$, $C_r=0$ | Kays & London; Bourdouxhe et al. (1994) HVAC1 Toolkit | Condensing zone only; single-zone lumped $UA$ |
| 3 | 3-zone refrigerant energy balance | Browne & Bansal (2001), *Int. J. Refrigeration* | Any vapor-compression condenser; needs zone area split |
| 4 | Refrigerant $P_{sat}(T)$ via EOS/REFPROP | Lemmon, Huber & McLinden, NIST REFPROP; Peng-Robinson (1976) | −100°C to 100–150°C depending on refrigerant |
| 5 | $\tau_{coil}=(M_{metal}c_{p,metal}+M_{ref}c_{p,ref})/UA$ | Incropera & DeWitt (lumped capacitance); Rasmussen & Alleyne (control-oriented VCC models) | Order of seconds to ~2 min; compare against your $\Delta t$ |
