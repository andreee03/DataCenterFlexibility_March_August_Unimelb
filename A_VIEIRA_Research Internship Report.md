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
