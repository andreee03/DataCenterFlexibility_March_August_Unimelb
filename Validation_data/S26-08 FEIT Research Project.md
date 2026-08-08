
# QDC SLD, E00n

- E000: not important
- E001: is important to see where do the other DB-US go: Chillers, CRACs. Shows the data Hall 1 surrounded by CRAC 1, 3, 5, 7 and 2, 4, 6, 8. The data hall 2, with CRAC-DH2-1, 2, 3, 4. And the new UPS-NC1 room

- E002: is the gloabl architecture, it is the most important
- E003 : is a zoom of the DB-UPS-NC1
- E004 : is a diagram of the DB-UP-NC1. No usefull for understading connexions.

No precise information on which DB-UPS power the cooling system (CRACs, Chillers) 

# Time Series Excel files
Time resolution : 1 min

## Structure

Always come with 2 Sheets: 
- Sheet1 : the measurements, for time resolution, from start date to end date
- Sheet2 : the statistical treatment fo these measurements: min and max value and their corresponding date and time. And average. No standard deviation.

## Csv Files

It is an average temperature taken for one minute, however the start / stop times are not clean. 

## IT Power

Data Hall 1 is powereed by DB-UPS-A and B

Data Hall 2 is powereed by DB-UPS-NC1


| Filename | Sheet | Start date | End date | Detected column names |
|---|---|---|---|---|
| `AVR_DB-UPS-1_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `DB-UPS1.DB-UPS-1 Incomer-Active Power (kW)`<br>`DB-UPS1.DB-UPS-1 Incomer-Power Factor Total (PFTtl)`<br>`DB-UPS1.DB-UPS-1 Incomer-Reactive Power (kVAR)` |
| `AVR_DB-UPS-1_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_DB-UPS-2_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `DB-UPS2.DB-UPS-2 Incomer-Active Power (kW)`<br>`DB-UPS2.DB-UPS-2 Incomer-Reactive Power (kVAR)` |
| `AVR_DB-UPS-2_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_DB-UPS-3_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `DB-UPS3.DB-UPS-3 Incomer-Active Power (kW)`<br>`DB-UPS3.DB-UPS-3 Incomer-Reactive Power (kVAR)` |
| `AVR_DB-UPS-3_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_DB-UPS-A_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `DB-UPS1.DH1-UPS-A-Active Power (kW)`<br>`DB-UPS1.DH1-UPS-A-Reactive Power (kVAR)` |
| `AVR_DB-UPS-A_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_DB-UPS-B_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `DB-UPS2.DH1-UPS-B-Active Power (kW)`<br>`DB-UPS2.DH1-UPS-B-Reactive Power (kVAR)` |
| `AVR_DB-UPS-B_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_DB-UPS-NC-1_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `DB-UPS-NC-1.Main Supply-Active Power (kW)`<br>`DB-UPS-NC-1.Main Supply-Reactive Power (kVAR)` |
| `AVR_DB-UPS-NC-1_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_MDB-DH1-ESS_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `MDB-DH1-ESS.MDB-DH1-ESS Incomer-Active Power (kW)`<br>`MDB-DH1-ESS.MDB-DH1-ESS Incomer-Reactive Power (kVAR)` |
| `AVR_MDB-DH1-ESS_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_MSB-1A_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `MSB-1A.MSB-1A Incomer-Active Power (kW)`<br>`MSB-1A.MSB-1A Incomer-Power Factor Total (PFTtl)`<br>`MSB-1A.MSB-1A Incomer-Reactive Power (kVAR)` |
| `AVR_MSB-1A_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_MSB-1B_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `MSB-1B.MSB-1B Incomer-Active Power (kW)`<br>`MSB-1B.MSB-1B Incomer-Power Factor Total (PFTtl)`<br>`MSB-1B.MSB-1B Incomer-Reactive Power (kVAR)` |
| `AVR_MSB-1B_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_MSSB-DH2-G_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `MSSB-DH2-G.MSSB-DH2-G Incomer-Active Power (kW)`<br>`MSSB-DH2-G.MSSB-DH2-G Incomer-Reactive Power (kVAR)` |
| `AVR_MSSB-DH2-G_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_MSSB-DH2-R_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `MSSB-DH2-R.MSSB-DH2-R Incomer-Active Power (kW)`<br>`MSSB-DH2-R.MSSB-DH2-R Incomer-Reactive Power (kVAR)` |
| `AVR_MSSB-DH2-R_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_SDB-UPS-G1_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `DB-UPS1.SBD-UPS-G1-Active Power (kW)`<br>`DB-UPS1.SBD-UPS-G1-Reactive Power (kVAR)` |
| `AVR_SDB-UPS-G1_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 PM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_SDB-UPS-G2_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/01/2025 12:00:00 AM` | `13/07/2026 10:10:59 AM` | `DB-UPS2.SDB-UPS-G2-Active Power (kW)`<br>`DB-UPS2.SDB-UPS-G2-Reactive Power (kVAR)` |
| `AVR_SDB-UPS-G2_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/01/2025 12:00:00 AM` | `13/07/2026 10:10:59 AM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `AVR_SDB-UPS-R_2025-7-1_2026-6-30.xlsx` | `Sheet1` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `DB-UPS1.SBD-UPS-R-Active Power (kW)`<br>`DB-UPS1.SBD-UPS-R-Reactive Power (kVAR)` |
| `AVR_SDB-UPS-R_2025-7-1_2026-6-30.xlsx` | `Sheet2` | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `Min. Date`<br>`Min. Value`<br>`Max. Date`<br>`Max. Value`<br>`Average` |
| `REPORT___Feit_Room_Average_Intake____2026_07_16_15_23_18.csv` | ``  | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `Average Intake Temperature`|
| `REPORT___Feit_Room_Average_Exhaust_Temp__2026_07_16_15_27_24.csv` | ``  | `1/07/2025 12:00:00 AM` | `30/06/2026 12:00:00 AM` | `Average Exhaust Temperature` |
