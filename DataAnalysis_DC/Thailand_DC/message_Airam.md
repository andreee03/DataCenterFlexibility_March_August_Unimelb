Hi Airam,

I have analysed the dataset from Thailand.

# Thailand dataset

## COntent

The dataset contains approximately one measurement per minute over a period of four years.

It includes three categories of values:

-   CRAC energy consumption (6 CRAC units),
-   Server power consumption (12 server groups),
-   Total power consumption (the exact scope is unclear and seems to depend on the floor layout; at least 3 sensors, possibly up to 6).

## Opinion

The dataset seems good, the only limit is the lack of context of this data (no information on the components of the cooling system, the floor layout)

This information could be usefull to categorize, classify different datasets and try to find flexibility capabilities in function of the type of datacenter.

# What to ask?

## Granularity

I think a sampling period of 10–15 minutes is sufficient for my work. The relevant dynamics are mainly driven by cooling-system variations, which occur on much slower timescales than IT load fluctuations.

For example giving directly statistical data (mean, max, min, std) could be enough for a first approximation.
## Values

Priority order:

-   Overall facility power consumption,
-   Cooling-system power consumption,
-   IT hardware power consumption,
-   "Other" power consumption (e.g. rotary UPS, permanently running generators, lighting, auxiliary systems),
-   A description of the cooling architecture (cooling towers, chillers, DX units, air-cooled vs liquid-cooled systems, etc.).
- A description of the components of the IT room (to evaluate the utilisation, the size of the Data Center)

## Additional information of interest

Since the objective is to assess HPC data-center flexibility capabilities, it would also be useful to obtain:

-   IT workload information (or at least HPC cluster utilization rates): what kind of jobs, delays, complexity,
-   Outdoor weather data (temperature, humidity, wet-bulb temperature),