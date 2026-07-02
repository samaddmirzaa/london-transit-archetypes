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

The pipeline runs in stages, each in its own notebook. The guiding idea throughout is to separate shape from size. Raw passenger counts are dominated by how big a station is, so a few huge stations would drown out everything else. Almost every feature is therefore built as a proportion or a ratio that describes how a station behaves independently of how busy it is.

**1. Ingestion and EDA.** The five wide spreadsheets are reshaped into one long, tidy table (station, day type, quarter hour, count, metric) of just over 450,000 rows, plus a separate station dimension table holding names, zones and the active flag. 

**2. Feature engineering.** Eleven features are built per station, kept after cutting several that turned out to be redundant with each other:

* `log_total_weekday`: overall size, on a log scale because station sizes span orders of magnitude.
* `early_share`, `eve_share`, `late_share`: the share of the day's entries falling in the early morning, evening and late night windows.
* `peakness`: how concentrated the busiest single 15-minute slice is.
* `am_asym`, `pm_asym`: the balance of entries against exits at the morning and evening peaks, running from a pure origin (people leaving home) to a pure destination (people arriving at work).
* `weekend_shift`: how much the daily shape changes from a weekday to a Saturday.
* `weekend_ratio`: Saturday volume as a fraction of weekday volume.
* `lines_served`: how many lines serve the station, a simple proxy for how connected it is.
* `interchange_ratio`: the share of activity that is people changing trains rather than entering from the street.

**3. Scaling.** The eleven features live on very different scales, so they are put on a common footing before any distance based method sees them. RobustScaler was chosen over the more common alternatives after a direct comparison, because several features have long, informative tails (the big interchange hubs, the leisure destinations) that we want to stand out rather than be squashed.

**4. Clustering.** Three algorithms are run and compared. K-Means is the main model, with six clusters chosen using the elbow method, the silhouette score and, above all, how interpretable the resulting groups are. Hierarchical clustering (Ward linkage, with a dendrogram) is run as an independent cross check and agrees strongly with K-Means. DBSCAN is run too, and its result is itself a finding: it shows the data is one continuous gradient rather than a set of separated islands, which is why it works better later as an anomaly flagger than as a clustering method here.

**5. Evaluation and naming.** Because unsupervised clustering has no correct answer to check against, the six groups are validated with bootstrap stability: the data is resampled thirty times, re-clustered each time, and the groups are checked for consistency. K-Means will return six clusters even from pure noise, so this test, not the fact that the algorithm ran, is what shows the structure is real. The six clusters score a stability well clear of the noise level. Each is then named from its defining features rather than its cluster number, so the names survive the numbering shifting between runs.

**6. Anomaly detection.** An Isolation Forest flags the roughly five percent most unusual stations. These are cross checked against the DBSCAN noise points, a completely different definition of unusual, and the two methods agree on almost exactly the same stations, which is what makes the anomalies defensible.

**7. Visualisation.** A t-SNE plot shows the six archetypes separating in two dimensions, and an interactive folium map places every station in its real location, coloured by archetype. The map is where the whole typology becomes something you can look at on a map of the city.

**8. Recommender.** A cosine similarity search over the feature fingerprints answers a plain question: given a station, which others behave most like it? This is the first genuinely interactive piece of the project.

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

## Anomalies

The Isolation Forest flags 22 stations, and 20 of those are independently flagged by DBSCAN. They fall into three recognisable groups: the West End night and weekend cluster (Leicester Square, Piccadilly Circus, Covent Garden), the extreme interchange giants (West Ham, Bank, Stratford, Oxford Circus), and a few tiny outer oddities. None of these is an error to remove. They are London's genuinely distinctive stations, and every one is a place a Londoner would recognise as unusual.

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
│   └── processed/           parquet outputs of each stage (gitignored)
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
├── src/london_transit/      reusable code (in progress)
├── tests/                   tests (in progress)
├── environment.yml
└── README.md
```

Principal Component Analysis was also explored during the project. It was analysed in full, then deliberately set aside for the modelling because it slightly reduced cluster stability on these particular features, which is a small result in its own right about when a standard technique does and does not help.

## Running it

1. Create the environment from the file: `conda env create -f environment.yml`, then activate it with `conda activate london-transit`.
2. Place the five NUMBAT xlsx files and the station coordinates csv in `data/raw/`.
3. Run the notebooks in order from `01` through `08`. Each one reads the output of the previous stage and writes its own output to `data/processed/`.

The processed parquet files are not committed to the repository, so they are regenerated by running the notebooks.

## Roadmap

The analysis is complete. The next stages are about packaging it into something that can be used and shown, and about demonstrating the engineering side of the work:

* An interactive Streamlit app for exploring stations, archetypes and the recommender.
* A FastAPI service and a Docker container so the model can be served as an API.
* Lightweight experiment tracking and model registration with MLflow.
* A continuous integration workflow that runs the tests on every push.
* Possibly a retrieval based question answering companion over the archetype results.
* A final write up with the headline figures and the reasoning behind the main decisions.

## A note on the approach

A theme running through this project is that a technique being standard does not make it necessary for a given dataset. PCA was tested and set aside. The silhouette score was used to find a sensible range of cluster counts rather than blindly maximised, because on its own it favours a small number of tidy but useless clusters. DBSCAN was allowed to "fail" as a clustering method because that failure was itself informative about the shape of the data. Most of the decisions in the project were made by testing an option against the actual data rather than assuming it would work, and where a decision was a genuine trade off, the trade off is stated plainly rather than hidden.
