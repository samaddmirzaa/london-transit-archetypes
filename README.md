# London Transit Archetypes

Unsupervised machine learning applied to Transport for London's rail network. The project takes a year of quarter-hourly passenger data and asks a simple question: if you ignore where stations are and look only at how people use them, what kinds of station does London actually have?

TfL already knows where every station sits and which lines serve it. What is far less obvious is the behavioural pattern of a station: when people tap in and out, which way the flow runs at rush hour, how the rhythm changes at the weekend, and how much of the traffic is people changing trains rather than starting or ending a journey. Stations that sit miles apart on the map can behave almost identically, and next door neighbours can behave nothing alike.

## The data

The source is TfL's NUMBAT 2024 dataset, a detailed model of rail demand across the London Underground, Overground, DLR, Elizabeth line and Trams.

* Five files, one per day type: Monday, an average Tuesday to Thursday (the typical mid week day), Friday, Saturday and Sunday.
* Each station's day is split into 96 quarter-hour slices, running on the traffic day from 05:00 to 04:59 rather than midnight to midnight.
* Entries and exits are recorded separately. This separation is what makes the directional features possible.
* There are 471 stations in the raw files. These are filtered down to the 432 that are active. The 39 that are removed are Croydon tram stops with no gatelines, so they record no entries or exits at all.

Station coordinates come from a separate TfL Freedom of Information release, joined to the passenger data on the National Location Code (NLC). That file covers all 432 active stations with no gaps, which is why the geographic map has complete coverage.

## Approach

The pipeline runs in stages, each in its own notebook. The guiding idea throughout is to separate shape from size. Raw passenger counts are dominated by how big a station is, so a few huge stations would drown out everything else. Almost every feature is therefore built as a proportion or a ratio that describes how a station behaves independently of how busy it is. Most of the decisions in the project were made by testing with trial and error.

**1. Ingestion and EDA.** The five wide spreadsheets are reshaped into one long, tidy table (station, day type, quarter hour, count, metric) of just over 450,000 rows, plus a separate station dimension table holding names, zones and the active flag. 

**2. Feature engineering.** Eleven features are built per station:

* `log_total_weekday`: overall size, on a log scale because station sizes span orders of magnitude.
* `early_share`, `eve_share`, `late_share`: the share of the day's entries falling in the early morning, evening and late night windows.
* `peakness`: how concentrated the busiest single 15-minute slice is.
* `am_asym`, `pm_asym`: the balance of entries against exits at the morning and evening peaks, running from an origin (people leaving home) to a destination (people arriving at work).
* `weekend_shift`: how much the daily shape changes from a weekday to a Saturday.
* `weekend_ratio`: Saturday volume as a fraction of weekday volume.
* `lines_served`: how many lines serve the station.
* `interchange_ratio`: the share of activity that is people changing trains rather than entering from the street.

**3. Scaling.** The eleven features live on very different scales, so they are put on a common footing before any distance based method sees them. RobustScaler was chosen over the more common alternatives after a direct comparison, because several features have long tails (the big interchange hubs, the leisure destinations) that we want to stand out.

**4. Clustering.** Three algorithms are run and compared. K-Means is the main model, with six clusters chosen using the elbow method, the silhouette score and, above all, how interpretable the resulting groups are. Hierarchical clustering (Ward linkage, with a dendrogram) is run as an independent cross check and agrees strongly with K-Means. DBSCAN is run too, and its result is itself a finding: it shows the data is one continuous gradient rather than a set of separated islands, which is why it works better later as an anomaly flagger than as a clustering method here.

**5. Evaluation and naming.** Because unsupervised clustering has no correct answer to check against, the six groups are validated with bootstrap stability: the data is resampled thirty times, re-clustered each time, and the groups are checked for consistency. Each cluster is then named from its defining features rather than its cluster number.

**6. Anomaly detection.** An Isolation Forest flags the roughly five percent most unusual stations. These are cross checked against the DBSCAN noise points, a completely different definition of unusual, and the two methods agree on almost exactly the same stations.

**7. Visualisation.** A t-SNE plot shows the six archetypes separating in two dimensions, and an interactive folium map places every station in its real location, coloured by archetype. The map is where the whole typology becomes something you can look at on a map of the city.

**8. Recommender.** A cosine similarity search over the feature fingerprints answers a plain question: given a station, which others behave most like it? 

## The six archetypes

Each type is named from its behaviour, with a few well known stations given as anchors.

| Archetype | What defines it | Example stations |
| --- | --- | --- |
| Outer Residential Origins | Small, single line, strong morning outflow, outer zones. People live here and commute out. | Romford, Morden, Turnpike Lane |
| Central Mega-Interchanges | The largest by volume, most lines, central, morning destination. | King's Cross, Bank and Monument, Oxford Circus |
| Inner Local Stations | Ordinary neighbourhood stations, used across the whole day, inner zones. | Brixton, Vauxhall, Tooting Broadway |
| Busy Commuter Interchanges | Large, multi line, commuter leaning with real interchange traffic. | Waterloo, Victoria, London Bridge |
| Central Workplace Destinations | People arrive in the morning and leave in the evening, central, low interchange. | Canary Wharf, Moorgate, South Kensington |
| Outer Transfer Hubs | The highest interchange share of all, multi line, but outside the centre. | Stratford, Clapham Junction, Whitechapel |


## Tech stack

* Python 3.11
* pandas and NumPy for data handling
* scikit-learn for scaling, clustering, anomaly detection and t-SNE
* SciPy for hierarchical clustering and the dendrogram
* matplotlib for static charts
* folium for the interactive map
* Parquet (via pyarrow) for fast intermediate storage
* joblib for saving fitted models
* Developed in PyCharm with a conda environment

## Repository structure

```
london-transit-archetypes/
├── data/
│   ├── raw/                 NUMBAT xlsx files and the station coordinates csv
│   └── processed/           
├── notebooks/
│   ├── 01_data_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_feature_scaling.ipynb
│   ├── 04_clustering.ipynb
│   ├── 05_evaluation.ipynb
│   ├── 06_anomaly_detection.ipynb
│   ├── 07_visualisation.ipynb
│   └── 08_recommender.ipynb
├── models/                  saved scaler and clustering model
├── reports/figures/         saved charts and the interactive map
├── src/london_transit/      
├── tests/                   
├── environment.yml
└── README.md
```


## Running it

1. Create the environment from the file: `conda env create -f environment.yml`, then activate it with `conda activate london-transit`.
2. Place the five NUMBAT xlsx files and the station coordinates csv in `data/raw/`.
3. Run the notebooks in order from `01` through `08`. Each one reads the output of the previous stage and writes its own output to `data/processed/`.
 
