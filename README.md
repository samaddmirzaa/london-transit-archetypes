# London Transit Archetypes

**[Explore the live app](https://samaddmirzaa-london-transit-archetypes-app-l8vnmv.streamlit.app/)**

The project takes a year of quarter-hourly passenger data and asks a simple question: if you ignore where stations are and look only at how people use them, what kinds of station does London actually have?

The answer turns out to be six. This project finds those six types, checks how they came to be by the algorithm, gives them names, flags the handful of stations that fit none of them, and finishes with an interactive app where you can search any station and see its type, its daily rhythm and the stations most like it.

TfL already knows where every station sits and which lines serve it. What is far less obvious is the behavioural pattern of a station: when people tap in and out, which way the flow runs at rush hour, how the rhythm changes at the weekend, and how much of the traffic is people changing trains rather than starting or ending a journey. Stations that sit miles apart on the map can behave similar to one another, and next door neighbours can behave nothing alike.

This project groups stations by behaviour alone. No location information is used anywhere in the modelling. The fact that the resulting groups then line up cleanly with real London geography, with residential types ringing the outer zones, workplace types clustered in the centre and interchange types sitting on the real junctions, is one of the main results and good evidence that the patterns are genuine.

## Data

The source is TfL's NUMBAT 2024 dataset, a detailed model of rail demand across the London Underground, Overground, DLR, Elizabeth line and Trams.

* Five files, one per day type: Monday, an average Tuesday to Thursday (the typical mid week day), Friday, Saturday and Sunday.
* Each station's day is split into 96 quarter-hour slices, running on the traffic day from 05:00 to 04:59 rather than midnight to midnight.
* Entries and exits are recorded separately. This separation is what makes the directional features possible.
* There are 471 stations in the raw files. These are filtered down to the 432 that are active. The 39 that are removed are Croydon tram stops with no gatelines, so they record no entries or exits at all.

Station coordinates come from a separate TfL Freedom of Information release, joined to the passenger data on the National Location Code. That file covers all 432 active stations with no gaps, which is why the map has complete coverage.

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

**4. Clustering.** Three algorithms are run and compared. K-Means is the main model, with six clusters chosen using the elbow method, the silhouette score and, above all, how interpretable the resulting groups are. Hierarchical clustering with Ward linkage is run as an independent cross check and agrees strongly with K-Means on the clear archetypes. DBSCAN is run too, and its result is itself a finding: it shows the data is one continuous gradient rather than a set of separated islands, which is why it works better later as an anomaly flagger than as a clustering method here.

**5. Evaluation and naming.** Because unsupervised clustering has no correct answer to check against, the six groups are validated with bootstrap stability. The data is resampled thirty times, re-clustered each time, and the groups are checked for consistency using the Adjusted Rand Index. K-Means will return six clusters even from pure noise, so this test, and not the fact that the algorithm ran, is what shows the structure is real. The six clusters score around 0.77, well clear of the 0.2 that random noise produces. Each cluster is then named from its defining features rather than its cluster number, so the names survive the numbering shifting between runs.

**6. Anomaly detection.** An Isolation Forest flags the roughly five percent most unusual stations, 22 in total. These are cross checked against the DBSCAN noise points, a completely different definition of unusual, and 20 of the 22 are flagged by both methods.

**7. Visualisation.** A t-SNE plot shows the six archetypes separating in two dimensions, and an interactive map places every station in its real location, coloured by archetype.

**8. Recommender.** A cosine similarity search over the feature fingerprints answers a plain question: given a station, which others behave most like it? Cosine rather than straight-line distance, because it compares the shape of a station's behaviour rather than its size.

## The Archetypes

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

The 22 flagged stations fall into three recognisable groups. There is the West End night and weekend cluster, with Leicester Square, Piccadilly Circus and Covent Garden, which combine very high late night activity with being busier at weekends than on weekdays. There are the extreme interchange giants, including West Ham with the highest interchange share in the network, along with Bank, Stratford and Oxford Circus. And there are a few tiny outer oddities that sit far from everything else in the opposite direction. These are not errors to remove and are distinct in behaviour due to their characteristics.

## The App

The Streamlit app is where the whole thing becomes usable. Pick any of the 432 stations and it shows:

* Where it sits on a map of London, with every station coloured by archetype using TfL's own line colours and sized by daily volume.
* Its archetype, daily entries, lines served, interchange share, whether it acts as a morning origin or destination, and how its Saturday compares to its weekday.
* Its daily rhythm plotted against the average rhythm of its archetype, so you can see how closely it matches its type. 
* The five stations that behave most like it.

## Tech stack

* Python 3.11
* pandas and NumPy for data handling
* scikit-learn for scaling, clustering, anomaly detection and t-SNE
* SciPy for hierarchical clustering and the dendrogram
* matplotlib for static charts
* folium for the interactive map
* Streamlit for the app, deployed on Streamlit Community Cloud
* Parquet via pyarrow for fast intermediate storage
* joblib for saving fitted models
* Developed in PyCharm with a conda environment

## Repository structure

```
london-transit-archetypes/
├── app.py                   the Streamlit app
├── requirements.txt         dependencies for the deployed app
├── data/
│   ├── raw/                 NUMBAT xlsx files and the station coordinates csv
│   └── processed/           parquet outputs of each stage
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
├── environment/             conda environment file
└── README.md
```

## Running it

To explore the results, just open the [live app](https://samaddmirzaa-london-transit-archetypes-app-l8vnmv.streamlit.app/). To run the analysis yourself:

1. Create the environment: `conda env create -f environment/environment.yml`, then activate it with `conda activate london-transit`.
2. Place the five NUMBAT xlsx files and the station coordinates csv in `data/raw/`.
3. Run the notebooks in order from `01` through `08`. Each one reads the output of the previous stage and writes its own output to `data/processed/`.

To run the app locally, `pip install -r requirements.txt` and then `streamlit run app.py` from the project root.
