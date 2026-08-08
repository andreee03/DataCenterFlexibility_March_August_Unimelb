# Timeseries of Energy Systems Integration Facility (ESIF) Data Center Power Usage Effectiveness (PUE) 

Data provided in Parquet and compressed CSV formats

### Power Metrics Timeseries Fields

- `ts`:  Timestamp
- `cooling_kw`:  Cooling (kilowatts) - Captures the power used by fans and pipe trace heaters associated with outdoor cooling equipment. The dedicated tower filter pump power is also captured as cooling load.
- `energy_reuse`:  Energy Reuse Effectiveness
- `hvac_kw`:  Heating, ventilation, and air conditioning (kilowatts) - Captures fan walls, fan coils that support the data center electrical rooms, and the make-up air unit.
- `it_power_kw`:  IT equipment (kilowatts) - Captures power used by the IT equipment on the data center floor.
- `plug_and_light_kw`:  Lights and utility plugs (kilowatts) - Captures power associated with the data center and dedicated mechanical room. The crank-case heater for the emergency standby generator is also captured as light and plug load.
- `pue`:  Power Usage Effectiveness
- `pump_kw`:  Pumps (kilowatts) - Captures power from pumps that move water in the data center Energy Recover Water loop and the Tower Water loops, and also captures power used by the boost pumps that circulate water through the fan walls. Note: The tower filter pump runs constantly to filter water from the data center cooling tower system, so 2.67 kilowatts are attributed to this pump and that is not reflected in this data field. (Andre adds: but it is taken in the 'cooling_kW')
- `day`:  Day of month

### Outside Weather Station Timeseries Fields

- `ts`:  Timestamp
- `outside_air_humidity`:  Outside air humidity - Relative humidity percent
- `outside_air_temp`:  Outside air temperature - Degrees Fahrenheit
- `day`:  Day of month

###  More Detail

- [High-Performance Computing Data Center Power Usage Effectiveness](https://www.nlr.gov/computational-science/measuring-efficiency-pue)
 

# Added by Andre: Notes_about_DataSet
Source: https://data.nlr.gov/submissions/300

## Granularity

The time is divided into N = 4.569.542 points.

It covers from 2015-11-10 at 3 am to 2025-08-29 at 4 am.

Around: 10 years - 3 months + 19 days = 117 months + 19 days around 3529 j

This means N/days = 1230 data per day.

You have 86 400 s in 24 hours, so about one measure every 80 seconds = 1 min and 20 s. 3 data every 4 mins

For manipulation of data like zoom in .html figures I decided to take N/100 points. Instead of 3 data every 4 mins, you have 3 data every 400 mins = 6h + 40 mins. 
About 1 data every 2h 14 mins

We can also take the full granularity for five weeks which is almost equivalent in points to N/100

## Aberrations

For cooling data there are some very high values (mean around 20 kW and pic values in 600-1300 kW). They are probably errors (it occurs at the end of 2019 December), keeping it shrinks all the other data. Taking N/100 removes those data. 

### ERE, 
Source: https://datacenters.lbl.gov/sites/default/files/EREmetric_GreenGrid.pdf

Energy reuse and ERE make no sense: in the README " - `energy_reuse`:  Energy Reuse Effectiveness"

Internet definition: ERE = Cooling+Power+Lighting+IT- Reuse/ IT,  ERE = PUE - Reuse/IT, ERE = PUE (1-Reuse_Energy/Total_Energy)

And Reuse_Energy/Total_Energy belongs to [0,1], so ERE belongs to [0, PUE]. And ERE = f(PUE, Reuse), but plot of energy_reuse starts in end 2023 and before ERE != PUE. Illogical

ERE effectiveness should be with no units and 

## Explanations

Source: https://www.nlr.gov/computational-science/hpc-data-center

Summary: Yes the values are real, it is a state-of-the-art DC, with 44 Pflops and a PUE of 1.036, Very optimized. 
We have no infomation about Workloads. The idea is to showcase a high efficient DC (very efficient cooling).

After superposing the power curves of 'hvac_kw', 'it_power_kw', 'plug_and_light_kw', 'cooling_kw', 'pump_kw', we see that it_power_kw ~ 1000 all other powers. Which is absurd..., but makes sense with the constant PUE of 1.04 

The DC uses warm-water liquid cooling
Reuses the heat for heating other buildings (offices, laboratories)

There are no mechanical or compressor-based cooling systems for NLR's HPC Data Center.
 Cooling liquid is supplied indirectly from evaporative cooling towers, and the thermosyphon—an advanced dry cooler that uses refrigerant in a passive cycle to dissipate heat—reduces on-site water consumption in the cooling towers without negative impacts on the data center's efficiency. (Expresso machines use thermosyphon...)