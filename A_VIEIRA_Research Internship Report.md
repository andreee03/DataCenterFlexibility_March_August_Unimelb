# Research Internship Report — Flexibility for data centers
**Author:** A. Vieira | **Lab:** EEE team | **Period:** March–Aug 2026
**Supervisor:** Pr. Mancarella | **Repo:** `https://github.com/andreee03/DataCenterFlexibility_March_August_Unimelb` (Public)

## Summary (read this if you read nothing else)

## References - Litterature review

Here are all the articles I used for my internship, these could be a good entry point on the subject. 

- Ilager, S., Toosi, A. N., Jha, M. R., Brandic, I., & Buyya, R. (2023), "A Data-driven Analysis of a Cloud Data Center: Statistical Characterization of Workload, Energy and Temperature," *Proceedings of the 16th IEEE/ACM International Conference on Utility and Cloud Computing (UCC 2023)*, Messina, Italy.
  → Relevance: Statistical data on transmission/reception network, number of CPU/VM, %utilization CPU/RAM, power and Temperature. Correlation matrix, predictions with a machine learning model. 

- Munith Kumar, D., Catrini, P., & Piacentino, A. (2023), "Advanced modeling and energy-saving-oriented assessment of control strategies for air-cooled chillers in space cooling applications," *Energy and Buildings* (ScienceDirect). DOI: available via ScienceDirect.
  → Relevance: Cooling system model. Complete modelling of a chiller with a refrigerent loop, controller, heat exchangers, an inductive motor, with variable or constant speed. IMST-Art software is validated but not free

- Mamun, A., et al. (2016), "Battery health-conscious online power management for stochastic datacenter demand response," *IEEE Conference Publication* (related to: Mamun, A., et al., "A Stochastic Optimal Control Approach for Exploring Tradeoffs between Cost Savings and Battery Aging in Datacenter Demand Response," *IEEE Transactions on Control Systems Technology*, 2017). DOI: 10.1109/TCST.2016.2643569.
  → Relevance: Notions of Demand Response, use of Batteries Li-ion, stochastic control. Uses Batteries to allow a Demand Response for a datacenter. Modelling of the battery and its degradation.

- Govindan, S., Sivasubramaniam, A., & Urgaonkar, B. (2011), "Benefits and Limitations of Tapping into Stored Energy for Datacenters," *Proceedings of the 38th Annual International Symposium on Computer Architecture (ISCA 2011)*, pp. 341–351.
  → Relevance: Use of UPS as buffered energy, created eBuffer a software for existing UPS to reduce power consumption peaks.

- Wilde, T., et al. (2017), "CooLMUC-2: A supercomputing cluster with heat recovery for adsorption cooling," *IEEE Conference Publication* (Leibniz Supercomputing Centre).
  → Relevance: Showcases an adsorption chiller. Interesting for liquid-cooled servers. Not a common cooling system though.

- Al Kez, D., Foley, A., Ahmed, F., & Morrow, J. (2022), "Data Center Potential Flexibilities and Challenges for Demand Response to Facilitate 100% Inverter-Based Resources: A Review," SSRN preprint. DOI: 10.2139/ssrn.4269631.
  → Relevance: Integrated view of flexibility, explaining economic incentives, storage systems and other notions.

- Calheiros, R. N., et al., "Elastic Power Utilization in Sustainable Micro Cloud Data Centers," *IEEE Journals & Magazine*. DOI: available via IEEE Xplore (document 10016768).
  → Relevance: Workload management oriented. Several algorithms for task allocation (overbooking), runs different decision algorithms based on green nergy availability. 

- Hogade, N., & Pasricha, S. (2025), "Game-Theoretic Deep Reinforcement Learning to Minimize Carbon Emissions and Energy Costs for AI Inference Workloads in Geo-Distributed Data Centers," *IEEE Transactions on Sustainable Computing*, Vol. 10, No. 4, pp. 628–641. arXiv:2404.01459.
  → Relevance: 

- (2026), "Grid Integration of AI Data Centers: A Critical Review of Energy Storage Solutions," *ScienceDirect* (journal article, multi-layer energy storage taxonomy for AI data centers).
  → Relevance: 

- Sheikholeslami, S. M., Rabiei, A. M., Mohammad-Taheri, M., & Abouei, J. (2022), "Cloud data center participation in smart demand response programs for energy cost minimisation," *IET Smart Grid*, Vol. 5, No. 5, pp. 380–394. DOI: 10.1049/stg2.12082.
  → Relevance: Optimization framework, workload management regional and temporal. 

- F. Farzan, et al.,(2025), "Long-Duration Energy Storage: Planning and Operation to Enhance Power Grid Sustainability," *IEEE Journals & Magazine* (document 11230052).
  → Relevance: Proof of concept, energy storage, not specific to data centers.

- Choukse, E., Warrier, B., Heath, S., Belmont, L., Zhao, A., Khan, H. A., et al. (Microsoft); Hurst, A., Zamani, R., Li, X., Oden, G., Carmichael, R. (OpenAI); Li, T., Gupta, A., Dattani, N., Marwong, L., Nertney, R., Liott, J., Enev, M., Ramakrishnan, D., Buck, I., & Alben, J. (NVIDIA) (2025), "Power Stabilization for AI Training Datacenters," arXiv:2508.14318.
  → Relevance: Power profiles of GPUs in AI Data centers. Threatens grid stability and system strength. 

- Mamun, A. A., Narayanan, I., Wang, D., & Fathy, H. (2016), "Multi-objective optimization of demand response in a datacenter with lithium-ion battery storage," *Journal of Energy Storage*, Vol. 7, pp. 258–269.
  → Relevance: Bi-optimization with the CAPEX and OPEX of a data center, using different controllers (P, IP, IP deadband)
  
- Xu, M., Toosi, A. N., Bahrani, B., Razzaghi, R., & Singh, M. (2019), "Optimized Renewable Energy Use in Green Cloud Data Centers," *Service-Oriented Computing: 17th International Conference (ICSOC 2019)*, Toulouse, France, Lecture Notes in Computer Science, Vol. 11895, pp. 314–330. DOI: 10.1007/978-3-030-33702-5_24. 
  → Relevance: Workload management,Markov Decision Processes

- Chakraborty, T., Kopp, C., & Toosi, A. N. (2025), "Optimizing Renewable Energy Utilization in Cloud Data Centers Through Dynamic Overbooking: An MDP-Based Approach," *IEEE Transactions on Cloud Computing*, Vol. 13, No. 1, pp. 1–17. DOI: 10.1109/TCC.2024.3487954.
  → Relevance: Notions of SLA, overbooking, Markov decision chain, modelling of sever utilization. Using an internal optimization process in servers (overbooking) to influence power consumption. At the end the status quo (overbooking 150%) is less power consuming for brown energy than any renewable aware model. But they ensure a better SLA, more availability, less delay. 

- Al-Qawasmeh, A. M., Pasricha, S., Maciejewski, A. A., & Siegel, H. J. (2015), "Power and Thermal-Aware Workload Allocation in Heterogeneous Data Centers," *IEEE Transactions on Computers*, Vol. 64, No. 2, pp. 477–491.
  → Relevance: Workload allocation, Cooling system presented, aisle containment, optimization with workload management

- Liu, Z., Lin, M., Wierman, A., Low, S. H., & Andrew, L. L. H. (2011), "Geographical Load Balancing with Renewables," *ACM SIGMETRICS Performance Evaluation Review*, Vol. 39, No. 3, pp. 62–66. DOI: 10.1145/2160803.2160862.
  → Relevance: Uses HAProxy to route requests between Lyon, Reims and Rennes depedning on the renewable energy available.

- Nadjaran Toosi, A., Qu, C., de Assunção, M. D., & Buyya, R. (2017), "Renewable-aware geographical load balancing of web applications for sustainable data centers," *Journal of Network and Computer Applications*, Vol. 83, pp. 155–168. DOI: 10.1016/j.jnca.2017.01.036.
    → Relevance:

- Xu, M., Nadjaran Toosi, A., & Buyya, R. (2021), "A Self-Adaptive Approach for Managing Applications and Harnessing Renewable Energy for Sustainable Cloud Computing," *IEEE Transactions on Sustainable Computing*, Vol. 6, No. 4, pp. 544–558. DOI: 10.1109/TSUSC.2020.3014943.
  → Relevance:






## Data research

### Time series Measurements

https://www.scidb.cn/en/detail?dataSetId=60dfb844a69842c1b7e7ca3ba8e09791

Google cluster-usage traces v3

ukpn-data-centre-demand-profiles

Thailand energydata-master-v2

NLR Energy Systems Integration Facility (ESIF) Data Center Power Usage Effectiveness (PUE) 

Marconi100 (20Pflops)

Grid’5000 Kwollect 

#### Workload and resource utilization

My work did not focus on worklod management for data centers. However there is a quite important amount of data sets and traces about data center requests. 
#### Data available

These data concerned more Workload management and utilisation profiles, less interesting for my work, but can be usefull for further projects.


| Entry        | Corresponding dataset/site               | What is actually observed| DC level represented    | Best use for DC-behaviour studies  |
| --- | --------- | - | - | --- |
| ScienceDB link                | **https://www.scidb.cn/en/detail?dataSetId=60dfb844a69842c1b7e7ca3ba8e09791** | Detailed three-phase electrical quantities at CRAC, rack-power and distribution-board meters (important metric: Active_Threephase_Power)| Building / room / rack electrical        | Cooling-vs-IT electricity, seasonality, load trends |
| Google cluster traces v3      | **https://github.com/google/cluster-data/blob/master/ClusterData2019.md**     | Jobs/tasks, scheduler events, CPU/RAM usage, machine state | Compute orchestration   | Production workload and scheduling behaviour; **not energy/cooling** |

| Marconi100   | **M100 ExaData**        | Jobs + node telemetry + temperatures + power + GPU + cooling + facility + alarms + weather   | Full cross-layer HPC system              | By far the richest production DC/HPC cross-layer dataset             |
| Grid'5000 Kwollect            | **Kwollect metrology service**           | Wattmeters, BMC, PDU, temperature, GPU, network, OS metrics, etc.           | Individual experimental nodes/components | Controlled power/performance/thermal experiments    |


#### UKPN

Need to login to access the data.

| Dataset | Exact UKPN link | Description| Size / scale| Duration / temporal resolution | Metrics / variables shown|
| --- | ----- | --- | ---------- | - | --- |
| **Data Centre Demand Profiles**            | https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-data-centre-demand-profiles/information/         | The most granular dataset. Contains **half-hourly electricity-demand/load profiles for individual anonymised operational data centres** connected in UKPN's licence areas. Utilisation is calculated by comparing observed site import against maximum import capacity. Sites are anonymised.             | UKPN says **nearly 100 operational data-centre sites**, with at least 10 per voltage group. CSV + JSON exports exist. | **From 1 Jan 2023 onward**; **30-minute resolution**. Dataset reviewed quarterly.      | **Half-hourly utilisation % / load factor**; timestamp; anonymised data-centre/site identifier; **connection voltage level**; estimated **data-centre type** (enterprise vs co-located). Calculation is based on apparent power **kVA**: half-hourly import ÷ maximum import capacity.|
| **Data Centre Utilisation** — **ARCHIVED** | https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-data-centre-utilisation/information/| UKPN explicitly says this dataset is now archived and directs users to Demand Profiles instead.|         |  |   |
| **Data Centres by Local Authority**        | https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-data-centres-by-local-authority/information/ | Geographic/planning dataset showing **operational and pipeline data-centre capacity aggregated by Local Authority District**. Pipeline means projects that have accepted an offer, paid the application fee and are committed to UKPN's delivery plans. Individual sites are deliberately not disclosed. | Exact rows/bytes not exposed. This is a **small aggregated geography-level table**, much smaller than the demand-profile dataset. CSV + JSON available. UKPN aggregates sites to LAD level to protect customer identity.           |   | **Operational data-centre capacity (MVA)** by Local Authority District; **pipeline data-centre capacity (MVA)** by LAD; Local Authority geography/identifier and corresponding county/unitary authority. The published data is capacity aggregated geographically, rather than individual-site capacity. |

I treated the *Data Centre Demand Profiles* data in end of May 2026, and the data set was not updated since then, so a more recent alayzis may require to re download the dataset after login to UKPN. 
Some values are wrong (utilization ratio above 1)
Usefull for seeing the paterns of data centers consumption.


![UKPN_extract1](./pictures/UKPN_screenshot_hhutilization1.png)
![UKPN_extract2](./pictures/UKPN_screenshot_hhutilization2.png)

#### NLR
NLR HPC Facility ESIF with metrics (ere, pue) and powers from their very efficient data center.

Showcases a very advanced cooling system. Extremely low PUE

![NLR_All](./pictures/NLR_all_powers.png)
![NLR_Cooilng](./pictures/NLR_without_IT.png)









#### Cooling system validation

Looking for Chiller power, input & output temperature of the cooling system (air in the CRACs) in a data center.

| Candidate          | Relevant measurements      |        Public numerical files | Main reason rejected          |
|  | --- | --: | --------- |
| **POLCOM Skawina, Poland**          | Cooling-source electrical power, on-site outdoor temperature, cooling capacity, operating mode | **No confirmed public files** | Strongest near-match, but only figures and statistical tables are public; exact meter boundary is partly undocumented               |
| **NLR/NREL ESIF HPC PUE dataset**   | Public `cooling_kw`, pump power, IT load and on-site weather |              Yes, CSV/Parquet | `cooling_kw` is explicitly fans, pipe-trace heaters and a tower filter pump—not chiller power ([data.nlr.gov][1])  |
| **Guangzhou data-centre chiller dataset**            | Compressor power, water temperatures and flows at 10-minute resolution        |           No | Authors state that they do not have permission to share the data; outdoor temperature is absent ([PubMed Central (PMC)][2])         |
| **Taiwan campus data centre**       | Measured power for two chillers and outdoor temperature in article figures    |          No confirmed dataset | Numerical observations, timestamps, equipment specifications and measurement boundary are not deposited ([MDPI][3])|
| **Kaggle “Data Center Cold Source Control Dataset”** | Ambient temperature and cooling-unit power at hourly resolution               |          Yes | Facility, original source, sensors, chiller specifications and electrical boundary are untraceable; the signal cannot be verified as real chiller power ([Kaggle][4]) |
| **NLR/Frontier and other HPC datasets**              | Facility power, coolant temperatures and weather in some cases                |          Yes | No measured vapor-compression chiller electrical-power channel  |

[1]: https://data.nlr.gov/submissions/300 "https://data.nlr.gov/submissions/300"
[2]: https://pmc.ncbi.nlm.nih.gov/articles/PMC13210669/ "https://pmc.ncbi.nlm.nih.gov/articles/PMC13210669/"
[3]: https://www.mdpi.com/1996-1073/12/8/1474 "https://www.mdpi.com/1996-1073/12/8/1474"
[4]: https://www.kaggle.com/datasets/programmer3/data-center-cold-source-control-dataset "https://www.kaggle.com/datasets/programmer3/data-center-cold-source-control-dataset"

Looking for the same measures in any kind of building where there is at least an air conditionning unit with a chiller.


| Candidate            | Building and HVAC configuration   |         Public data | Result               |
| -- | ---------- | ---------: | ----- |
| **KUBIK experimental cooling dataset**| Experimental building; two indoor fan-coil units; two air-condensed chillers; on-site weather station |            XLSX, 10 min, four months | **Strongest candidate—partially compliant**            |
| University of Cincinnati instrumented chiller facility | Three conditioned zones, three fan-coils and a VAV AHU served by a 4-ton air-cooled chiller           | No public numerical repository found | Technically excellent, but inaccessible                |
| LBNL HVAC FDD chiller-plant dataset   | Simulated chiller plant with extensive fault metadata               |          Public CSV | Rejected: chiller plant data are simulated             |
| LBNL Building 59     | Real office building with fan-coils, HVAC telemetry, energy meters and weather       |          Public ZIP | Rejected: no confirmed chiller electrical-power meter  |
| FLEXLAB two-cell dataset              | Two test rooms with chilled-water AHU coils and common chiller      |              Public | Rejected: chiller electricity was estimated from thermal load and assumed COP            |
| Building Data Genome 2                | Thousands of non-residential building meters and weather            |              Public | Rejected: “cooling” meters generally represent thermal cooling energy, not chiller electrical power       |
| ASHRAE chiller fault datasets         | Instrumented chillers and detailed refrigerant/water-side measurements               |Public in some cases | Rejected: laboratory/fault-test focus and no matching building outdoor-temperature series|
| COLLECTiEF/public-building BMS datasets                | Multiple real public buildings with HVAC and weather                |              Public | Rejected: no verified chiller-specific active-power channels            |
| Challenger/building comfort-system datasets            | Zone cooling electricity and weather               |              Public | Rejected: electrical boundary is terminal or comfort-system consumption, not chiller input                |
| Long-term district/campus datasets    | Cooling production, loads and weather              |              Public | Rejected: thermal energy, district supply or absorption-chiller input rather than electric vapor-compression chiller power |

I started to treat the data *KUBIK experimental cooling dataset* at https://scienceportal.tecnalia.com/en/datasets/experimental-cooling-data-in-kubik-lab-building-during-the-2020-s/

But the data is of a bad quality. Flow rates come without units. Don't know the type of the chiller. The water loop is not closed, hydrolic balance not respected (Algebraic sum of all flow rates is not equal to 0)

![Active_power_chillers](./pictures/Active_power_chillers.png)
![flow_rates](./pictures/flow_rates.png)
![temperatures_chiller](./pictures/temperatures_chiller.png)
![temperature_fans](./pictures/temperature_fans.png)

### Parameters

#### For cooling system

Cooling system devices are 

#### For server components


## 1. Context & Objective

- Production pipeline (`sensor-clustering/prod/`) uses streaming DBSCAN to group sensor readings in real time.
- Known issue since Nov 2025: cluster count silently collapses to 1 after long uptime, degrading downstream alerts.
- Objective: identify root cause and propose/validate a fix.

## 2. What Was Already Known (starting point)

- Ticket #4021 suspected a memory leak — ruled out early (see 4.1), noted here so it isn't re-investigated.
- Prior intern (2024) suspected `epsilon` was too static; this internship builds on that hypothesis rather than repeating the memory profiling work.

## 3. Method

1. Replayed 3 weeks of archived sensor logs (`data/replay_logs/2025-11/`) through an isolated instance of the pipeline.
2. Instrumented `epsilon` and cluster count over time (`analysis/eps_drift_plot.py`).
3. Correlated drift events against sensor dropout timestamps (`data/dropout_events.csv`).

## 4. What Was Tried and Rejected (do not repeat without new evidence)

### 4.1 Memory leak hypothesis — rejected
Profiled with `tracemalloc` over a 12h replay (`analysis/memprofile_run3.log`). Memory usage flat after warm-up. Not the cause. ~2 days spent here; can be skipped in future.

### 4.2 Fixed larger epsilon — rejected
Tried statically raising `epsilon` from 0.3 to 0.5 (`experiments/fixed_eps_05/`). Drift disappeared but merged genuinely distinct clusters in dense regions — unacceptable false-negative rate (see `experiments/fixed_eps_05/false_negative_report.md`). Do not pursue static epsilon increases as a fix.

## 5. What Worked

`adaptive_eps_v2` (`sensor-clustering/experimental/adaptive_eps_v2.py`) recalculates `epsilon` per-window but **excludes windows containing dropout events** from the calibration sample — this was the missing piece.

- Offline replay results: drift reduced from ~85% cluster collapse rate to ~15% over 3-week replay (`analysis/results_adaptive_v2.ipynb`, Section 3).
- Not yet tested on live streaming data — offline replay only.

## 6. Where Everything Lives

| Item | Location |
|---|---|
| Fix implementation | `sensor-clustering/experimental/adaptive_eps_v2.py` |
| Replay test harness | `sensor-clustering/tools/replay_runner.py` |
| Analysis notebooks | `analysis/*.ipynb` |
| Rejected experiment logs | `experiments/` (each folder has a `README.md` with verdict) |
| Raw drift/dropout data | `data/replay_logs/`, `data/dropout_events.csv` |

# Cooling system & Server thermal Modelling

Scope of the modelling: 

- A data center with an operating cooling system and server farm, that represents a set of intial conditions
- A demand response program from grid operator
- An active cooling system power reduction by increasing the setpoint of the chilled water
- A new steady-state temperature situation for the data center, determined as a trade-off between SLA contract and grid compensations.
- A change in the chiller setpoint to return back to usual operating conditions.

The scope of this modelling focuses on the transitional periods for different situations, detailled in Situations Part.


Time slot for modelling and equations : several tens of minutes : 10 - 30 mins.

Reasons : 
- Stabilisation of cooling system depending on the initial situation
- Enough time window to see the thermal inertia behavior for the new setpoint and the return to the origin nominal setpoint.

Simplifications:

- T_outdoor and Relative_Humidity are constant, for weather timescale >> 30 min event window.
- The shape of the chiller setpoint over time will be represented as a discontinuous step function (pulse) with two or three steps: 1/ nominal setpoint 2/ flexibility setpoint 3/ precooling setpoint

### Situations

To catch variability...

: 4 different seasons : (temperature, humidity)
: 2 different situations : precooling (lower setpoint)+ reduce cooling until operting situation / increase setpoint then, reduce until operating situation. ( these 2 situations will not differ for the power curtailment duration but more for Power saved)
: 5 different setpoint levels (from )

#### Outdoor conditions


A defensible set of values is:
| Season     | Months      | Representative `(T_outdoor, RH)` |
| ---------- | ----------- | -------------------------------: |
| **Summer** | Dec–Jan–Feb |               **(23.8 °C, 47%)** |
| **Autumn** | Mar–Apr–May |               **(19.6 °C, 53%)** |
| **Winter** | Jun–Jul–Aug |               **(13.7 °C, 60%)** |
| **Spring** | Sep–Oct–Nov |               **(18.3 °C, 51%)** |


Justification:

These are simple seasonal averages of the BoM **3 pm monthly climatological values**:

-   Summer: T\=(22.4+24.2+24.7)/3\=23.8∘C, RH \=(47+47+48)/3\=47.3%
-   Autumn: T\=(22.8+19.6+16.3)/3\=19.6∘C, RH \=(49+52+59)/3\=53.3%
-   Winter: T\=(13.7+13.0+14.3)/3\=13.7∘C, RH \=(63+61+56)/3\=60.0%
-   Spring: T\=(16.1+18.3+20.4)/3\=18.3∘C, RH \=(53+50+49)/3\=50.7%

Those underlying monthly figures come directly from the BoM Melbourne Regional Office station.
cite{BOM}


### Equations 

#### Cooling system
P_elec_chiller including T_outdoor : Cooling Tower or Air cooled chiller

Aim: flexibility capabilities depending on the season.


T_chilled_water to P_elec_chiller : Chiller Modelling, COP, EIR, CAP

Aim: Compute P_saved

T_chilled_water to T_inlet_ITRoom : CRAC equation, dry coil heat exchanger, secondary loop delta T

Aim: link setpoint change to IT hardware conditions

#### Server
T_inlet_ITRoom to T_heatsink: heat exchanger,

Aim: Take into account time scale of heatsink, smallest significant time scale of the modelling.

T_heatsink and Power_CPU to T_junction: Steady State assumption, thermal resistances

Aim: Compute T_junction and compare it to Physical / Hardware limits (T_jmax, T_THERMTRIP)

Assumptions: Resistances and capacitances are constant, independent on the Temperature for the range of temperature considered. 

#### On the Validity of a Quasi-Steady-State Approximation for Sub-Heatsink Components in Server Thermal Modeling

**Thesis.** When modeling the thermal architecture of a server for the purpose of evaluating cooling-system changes, it is sound, as a first approximation, to treat every component above the heatsink (die, TIM, IHS/case) as being in instantaneous thermal equilibrium at each simulation time step, and to reserve dynamic (capacitive) behavior for the heatsink alone. This report derives and sources the parameters needed to support that thesis at a time resolution of 10 s.

##### 1. Modeling Framework

To model the thermal path from silicon junction to ambient air, we adopt a lumped-parameter network — a Cauer-type RC ladder — rather than a pure steady-state resistor chain, so that transients introduced by cooling-system changes (fan-speed steps, airflow reduction, etc.) can be captured:

```
T_j —[R_jc]— T_case (IHS) —[R_cs, TIM2]— T_sink —[Ψ_ca]— T_ambient
      C_j              C_case                  C_s
```

Each node carries a thermal resistance to its neighbor and a thermal capacitance to ground (ambient reference). This is the same general modeling approach used in transient thermal analysis of semiconductor packages more broadly, including SPICE-based RC extraction methods [14] and lumped RC models used for LED and power-device packages [13].

##### 2. Parameter-Sourcing Strategy

The two families of parameters in this network are treated differently, per the logic of the original problem:

- **Thermal resistances (R_jc, R_cs, Ψ_ca):** these were available as parameters (from datasheets / vendor literature) and are **cross-checked** here against independent published figures for components of comparable size and construction.
- **Thermal capacitances (C_j, C_TIM, C_case, C_s):** no datasheet values were available. They are **computed** from first principles (C = ρ·c_p·V) using literature-sourced material properties and literature-sourced representative package geometries, then **validated** by checking that the resulting time constants fall within the ranges reported for structurally similar RC-modeled electronic packages.

##### 3. Thermal Resistances — Confirmation Against Literature

| Parameter | Given value | Cross-check | Source |
|---|---|---|---|
| R_jc (die→case) | 0.2 °C/W (range 0.1–0.3) | Published spreading-resistance analysis of a solid copper IHS of comparable size reports resistances of the same order: 0.28 °C/W for a 2 mm-thick spreader, rising to 1.44 °C/W at 5 mm. This does not reproduce R_jc exactly (R_jc is measured with an idealized cold plate at the case and mostly captures die + internal TIM1 + local spreading), but it shows that resistances in the tenths-of-a-°C/W range are physically consistent with copper-spreader elements of this scale. | *Integrated vapor chamber heat spreader for high power processors*, IEEE EuroSimE [4] |
| R_cs (case→sink, TIM2) | 0.1 °C/W | Bulk-conduction-only estimate for a standard silicone paste (k = 1–4 W/m·K), 50 µm bond line, 1600 mm² contact area: R = t/(k·A) ≈ 0.008–0.03 °C/W. The remaining ≈0.07–0.09 °C/W of the stated 0.1 °C/W is therefore interface/contact resistance, consistent with a well-applied high-performance TIM rather than bulk conduction alone. | ARCTIC — *Thermal Interfaces for CPUs and GPUs* [6] |
| Ψ_ca,worst (sink→ambient) | 0.295 °C/W | Commercial 1U server heatsinks (200–600 g) are rated at 0.15–0.25 °C/W under nominal airflow. 0.295 °C/W lies just above this band, consistent with a *worst-case* (reduced fan speed / degraded airflow) operating point rather than the nominal rating. | Rapidaccu — *1U Heatsink* product specification [7] |

**Verdict: all three resistances are defensible**, with the caveat that R_jc's confirmation is directional (order-of-magnitude) rather than an exact reproduction, since the cited IHS study characterizes the spreader in isolation rather than the full die+TIM1+near-IHS path that R_jc represents by definition.

##### 4. Thermal Capacitances — Derivation and Validation

###### 4.1 Material properties used

| Material | ρ (kg/m³) | c_p (J/kg·K) | Source |
|---|---|---|---|
| Silicon | 2330 | 710 | Density: WaferPro [11]. Specific heat: Engineering ToolBox — *Metals, Specific Heats* [9] |
| Copper | 8940 | 390 | Engineering ToolBox — *Metals and Alloys, Densities* [10] and *Metals, Specific Heats* [9] |
| Aluminum | 2712 | 910 | Engineering ToolBox — *Metals and Alloys, Densities* [10] and *Metals, Specific Heats* [9] |
| TIM2 (paste) | ≈2700 (assumed) | ≈800 (assumed) | **Not independently sourced** — order-of-magnitude engineering estimate for filled silicone paste. Immaterial to the conclusion (see §4.2/§6). |

###### 4.2 Geometry, computation (C = ρ·c_p·V), and resulting capacitances

| Node | Geometry (source) | C (nominal) | Range |
|---|---|---|---|
| C_j (die) | 13×13 mm footprint [3]; thickness 725 µm, "typical die for a microprocessor" [1], thinning to ≤150 µm reported for compact packages [2] | **0.20 J/K** (unthinned) | 0.04–0.20 J/K |
| C_TIM (TIM2 only\*) | 40×40 mm contact area [3]; 50 µm bond line (assumed, not sourced) | **≈0.17 J/K** | Not rigorously bounded — order 0.1–0.2 J/K |
| C_case (IHS) | 40×40 mm, 2.5 mm thickness, stated as representative of modern high-power CPUs [3]; sweep range 1.0–5.0 mm also given in [3] | **14.0 J/K** | 5.6–27.9 J/K |
| C_s (heatsink) | 450 g, specific 1U product with copper vapor-chamber base + copper fin stack [8]; general 1U category spans 200–600 g with Al-6063 fins over Cu/Al base [7] | **175.5–409.5 J/K** (450 g, bounded by pure-Cu vs. pure-Al c_p) | 78–546 J/K over the full 200–600 g / material-mix span |

\*TIM1 (die–IHS, factory-applied, 9–16 mil per Intel's own packaging patent [5]) is already folded into R_jc by standard datasheet convention and is not modeled as a separate node.

##### 5. Time-Constant Analysis

For a series RC network, each node's local time constant is τ = R_downstream × C_node, and a node is considered settled once approximately five time constants have elapsed — the standard engineering rule of thumb, stated explicitly in SPICE-based thermal-modeling documentation as the time needed for an RC curve to reach steady state [14].

| Node | τ = R·C | Δt/τ at Δt = 10 s | Settled (need Δt/τ ≥ 5)? |
|---|---|---|---|
| Die (R_jc·C_j) | 0.040 s | 250 | ✅ yes, very large margin |
| TIM2 (R_cs·C_TIM) | 0.017 s | 588 | ✅ yes, very large margin |
| IHS/case (R_cs·C_case) | 1.40 s (nominal); 0.56–2.79 s over the sourced thickness range | 7.1 (nominal); 3.6–17.9 over range | ✅ yes at nominal thickness (2.5 mm); **only marginal/failing at the upper end (5 mm) of the studied design-space sweep**, which the source paper itself treats as a parametric bound rather than a typical shipped value |
| Heatsink (Ψ_ca·C_s) | 51.8–120.8 s over the sourced mass/material range | 0.08–0.19 | ❌ no, by roughly an order of magnitude, across the entire plausible parameter range |

This ordering — die and TIM in the millisecond range, package/case in the low-single-digit-second range, heatsink in the tens-of-seconds-to-minutes range — mirrors what is reported independently for other RC-modeled electronic packages. One patent describing thermal modeling of IC packages states directly that junction capacitance can be neglected (time constant ≈10 µs) and that the package's own thermal time constant is "10 seconds or more," such that if the pulse duration is significantly less than 10 seconds the package capacitance is essentially a short circuit [12] — the same 10 s threshold used in this study, applied to an analogous package structure. A separate analysis of LED packages reports the same qualitative separation: package time constant on the order of tens of seconds, heatsink time constant on the order of hundreds of seconds [13]. A SPICE transient-thermal case study likewise shows the heatsink dominating the response after the first ~0.5 s, with the full system requiring on the order of 850 s (5τ) to reach steady state [14].

##### 6. Discussion and Conclusion

Given a simulation time resolution of **Δt = 10 s**, the analysis supports the thesis stated at the outset:

- **Die and TIM2** can be treated as instantaneously at equilibrium with overwhelming margin (Δt/τ in the hundreds). Their contribution to the network's dynamics is negligible regardless of the residual uncertainty in TIM2's unsourced material properties, since even an order-of-magnitude error in C_TIM leaves Δt/τ far above the settling threshold.
- **The IHS/case** is also well approximated as quasi-static at the *representative* IHS thickness reported in the literature (2.5 mm, Δt/τ ≈ 7.1) [3]. This conclusion is **sensitive to IHS thickness**: at the thick end of the studied design-space sweep (5 mm), the margin inverts (Δt/τ ≈ 3.6 < 5). This is a legitimate boundary condition to flag, though 5 mm is presented in the source study as an exploratory upper bound rather than a typical production value.
- **The heatsink** cannot be approximated as quasi-static at any point in its sourced mass/material range (Δt/τ ≈ 0.08–0.19, roughly 30–60× short of settling). It is the network's dominant dynamic element, consistent both with the direct 10 s-threshold precedent found in package-thermal-modeling literature [12] and with the general package-vs-heatsink time-constant separation reported for comparable RC-modeled systems [13, 14].

**Reduced-order model implied by this result** (one ODE, two algebraic equations):

```
C_s · dT_s/dt = Q − (T_s − T_amb) / Ψ_ca
T_case = T_s + Q·R_cs
T_j    = T_case + Q·R_jc  =  T_s + Q·(R_jc + R_cs)
```

This retains full transient fidelity where the physics requires it (the heatsink) while eliminating three stiff, sub-second-to-low-second states that would otherwise force an unnecessarily small integration step without changing the accuracy of a 10 s-resolution simulation of cooling-system changes.

##### References

1. USPTO Patent 6,417,068 — *Semiconductor device navigation using laser scribing* (die thickness, 725 ± 15 µm typical for a microprocessor). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6417068
2. Semiconductor Digest — *The back-end process: Step 3 – Wafer backgrinding* (720 µm → ≤150 µm typical thinning). https://sst.semiconductor-digest.com/2002/03/the-back-end-process-step-3-wafer-backgrinding/
3. Fabbri, M. et al. — *Optimising integrated heat spreaders with distributed heat transfer coefficients: A case study for CPU cooling*, ScienceDirect (2022). https://www.sciencedirect.com/science/article/pii/S2214157X22005949
4. *Integrated vapor chamber heat spreader for high power processors*, IEEE EuroSimE / ResearchGate. https://ieeexplore.ieee.org/abstract/document/6826719/ ; https://www.researchgate.net/publication/269303770
5. Intel — *Variable-Thickness Integrated Heat Spreader (IHS)*, patent application. https://patents.justia.com/patent/20210028084
6. ARCTIC — *Thermal Interfaces for CPUs and GPUs*. https://www.arctic.de/en/products/cooling/thermal-interfaces/
7. Rapidaccu — *1U Heatsink – Ultra-Low Profile Server CPU Coolers*. https://rapidaccu.com/heatsink/1u-heatsink/
8. Amazon / Boartechs — *CPU Cooler Server heatsink 1U Passive Server heatsink LGA4189*. https://www.amazon.com/Boartechs-heatsink-Passive-LGA4189-sockets/dp/B0F47J5L3Y
9. Engineering ToolBox — *Metals - Specific Heats*. https://www.engineeringtoolbox.com/specific-heat-metals-d_152.html
10. Engineering ToolBox — *Metals and Alloys - Densities*. https://www.engineeringtoolbox.com/metal-alloys-densities-d_50.html
11. WaferPro — *What's the Density of Silicon—And Why Does It Matter?* https://www.waferworld.com/post/whats-the-density-of-silicon--and-why-does-it-matter
12. USPTO Patent 4,588,945 — *High throughput circuit tester and test technique avoiding overdriving damage* (package time constant "10 seconds or more"). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4588945
13. USPTO Patent 9,107,267 — *Method and numerical tool for optimizing light emitting diode systems* (package τ, tens of seconds, ≪ heatsink τ, hundreds of seconds). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9107267
14. Luminus Devices — *Thermal: Using SPICE to Perform Transient Thermal Modeling* (5τ settling rule; heatsink dominant after 511 ms; ~854 s full-system settling). https://luminusdevices.zendesk.com/hc/en-us/articles/44419356146701-Thermal-Using-SPICE-to-Perform-Transient-Thermal-Modeling

### Time of flexibility

There are 2 different durations : 
- steady state, all components of the cooling system and IT Room (servers and racks) are at equilibrium
- dynamic transcient from one setpoint value to another. 

##### Steady-state time

For a given new temperature equilibrium inside a server. The amount of time allowed at the new temperature depends on CPUs utilization. Only a stochastic model, with statistical oriented methods can evaluate the increase of the risk of a potential CPU Thermtrip under these new conditions.

The final decision for a specific steady-state time duration is then a trade-off between the risk management of a CPU throttling down because of heat surcharge, affecting availability and SLA conditions, and grid-side compensations.

##### Transitional time

The transitional time is determined by all components of the system that move towards new equilibrium and other more specific durations.

My estimation includes:
- Convexion times both for the cooling fluid in the evaporator loop and the air in the IT Room.
- IT Room thermal resistances and capacities (Racks, cabinets and servers components)
- Heat exchanger resistances and capacities (Heatsink and CRAC coil)
- time of compressor modulation

###### Compressor modulation time scale

We take an interval: [30, 120] s for a setpoint change for a water cooled and air cooled chiller


Justification:
For scroll compressor that represent 83% of the chiller models in the simulation, the effective capacity change settles within tens of seconds, one to a few 20 s cycles. \cite{HPAC} \cite{Scroll_Compressor} We will therefore consider power reduction as immediate.
In fact, capacity modulation in digital scroll compressors is achieved through a pulse-width-modulated loading/unloading cycle, typically 10–30 s in duration (commonly cited as 20 s), during which the scroll set is mechanically engaged and disengaged to vary the loaded fraction of the cycle. This cycle time is deliberately kept 4–8 times shorter than the thermal time constant of the load it serves, precisely so that the compressor's own switching does not interact with the thermal dynamics of the system \cite{Scroll_Compressor}. We can take an interval of the order of minutes.

For centrifugal water cooled chillers (representing 68% of the water cooled models), there are no measured data about compressor modulation. There are two common cases for centrifugal chiller, fixed speed or VFD.
For the first one, the motor rotational speed remains essentially constant, but capacity is modulated using the inlet guide vanes (IGVs). Closing the vanes reduces refrigerant flow and compressor loading, so the motor torque and therefore its electrical power decrease. Trane explicitly describes conventional centrifugal chillers as reducing capacity by closing the inlet guide vanes while maintaining constant motor speed. \cite{TRANE}. The change is quick, of the order of one minute.

For VFD, there is less information available, but modern Chillers can act very quickly. In fact Trane advertises its current data-center centrifugal CenTraVac machines as restoring cooling after a complete power interruption in as little as 43 seconds, with near-full load in less than four minutes. A normal load reduction while the compressor is already running is fundamentally easier than starting from zero after a power interruption. So \cite{Trane_43}

For this reason we can defensibly put an interval of [30, 120] s for a setpoint change.
###### Room volume

Intensive coefficient range from [1.35, 8.6] m³/kW

Justification:

For the room volume, we look for an intensive coefficient that can link volume with power consummed by IT. A defensible interval is [0.5–2] kW/m² for the areal power density .
In fact, the lower bound is anchored to measured operating data: a DOE-funded field study of a real facility found an installed rack load density of 63 W/ft², roughly 678 W/m²\cite{OSTI} page 7/25, which we round down slightly to 0.5 kW/m² to stay conservative for legacy or lightly-loaded rooms. The upper bound is set not by a design aspiration but by a physical constraint: a data-center-cooling patent notes that the maximum heat density deliverable through a standard raised-floor underfloor-air duct is below roughly 2,000 W/m² before the plenum itself becomes the airflow bottleneck \cite{USPatent_volume} end of 3rd column. This is defensible as an upper bound specifically because it is a *distribution* limit, not a marketing figure: densities above it (e.g. Vantage's 300 W/gross ft² ≈ 3,229 W/m²) exist in the field but require containment or supplemental cooling that changes the convective problem being modelled, so 2 kW/m² is the right ceiling for a room still cooled by "plain" underfloor air.

[2.6, 4.3] m for Room height. In fact, the lower bound follows directly from cabinet dimensions rather than an arbitrary number: server-room design references state that equipment racks are typically six to seven feet tall, with the ceiling typically about nine to 9.5 feet above the raised floor (US Patent 9,347,834, "Infrared sensor array... for data centers" — keyword "nine or 9.5 feet"), i.e. only ~0.6–1 m of clearance above the rack itself for cable trays and return air. This converges with the independently sourced minimum recommended clear height of 2.6 m for 42U racks, so we take **≈2.7 m** as the lower bound: a room barely taller than the equipment it houses. 
The upper bound reflects modern hyperscale practice, where extra height accommodates stacked cable-tray pathways and containment rather than the racks themselves: Vantage specifies a minimum ceiling height of 12'6" (≈3.81 m) for its high-density modules, and a modular-data-center patent describes interior clear space up to 14'0" (≈4.27 m) when multiple stacked cable-tray pathways are required (US Patent 12,356,579 — keyword "14′0″"). We take **≈4.3 m** as the upper bound.

Resulting interval volume per power : [1.35, 8.6] m³/kW
Indeed, combining the extremes of each parameter — pairing the *minimum* height with the *maximum* density (tightest, most compact room) and the *maximum* height with the *minimum* density (most spacious, legacy-style room) — gives the intensive volume-per-power ratio v = H/density: v_min = 2.7 m / 2.0 kW/m² ≈ **1.35 m³/kW**, and v_max = 4.3 m / 0.5 kW/m² ≈ **8.6 m³/kW**, a spread of roughly 6.4×. 

### Find parameters



#### Initial conditions



#### Steady-State justification


### Results