import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path

st.set_page_config(page_title='London Transit Archetypes', page_icon='🚇', layout='wide')

tfl_colours = {
    'Outer Residential Origins': "#00782A",
    'Central Mega-Interchanges': "#E32017",
    'Inner Local Stations': "#0098D4",
    'Busy Commuter Interchanges': "#6950A1",
    'Central Workplace Destinations': "#EE7C0E",
    'Outer Transfer Hubs': "#00A4A7"
}

processed_dir = Path(__file__).parent/'data'/'processed'

@st.cache_data
def load_stations():
    stations = pd.read_parquet(processed_dir/'station_final.parquet')
    stations['daily_entries'] = np.expm1(stations['log_total_weekday'])
    return stations

@st.cache_data
def load_similarity():
    return pd.read_parquet(processed_dir/'station_similarity.parquet')

@st.cache_data
def load_profiles():
    return pd.read_parquet(processed_dir/'station_profiles.parquet')

stations = load_stations()
similarity = load_similarity()
profiles = load_profiles()

st.title('London Transit Archetypes')
st.write('Six behavioural station types discovered from TfL NUMBAT 2024 data using unsupervised machine learning.')

st.sidebar.header('Explore')
station_name = st.sidebar.selectbox(
    'Choose a Station',
    sorted(stations['station_name'])
)

shown_archetypes = st.sidebar.multiselect(
    'Show Archetypes',
    list(tfl_colours.keys()),
    default=list(tfl_colours.keys())
)

selected_nlc = stations[stations['station_name'] == station_name].index[0]
selected = stations.loc[selected_nlc]

visible = stations[stations['archetype'].isin(shown_archetypes)]

col_map, col_info = st.columns([3, 2])

with col_map:
    station_map = folium.Map(
        location=[51.505, -0.115],
        zoom_start=11,
        min_zoom=9,
        max_bounds=True,
        min_lat=51.20, max_lat=51.80,
        min_lon=-1.10, max_lon=0.45,
        tiles='cartodbvoyager',
    )

    size_min = stations['log_total_weekday'].min()
    size_max = stations['log_total_weekday'].max()

    for nlc, row in visible.iterrows():
        radius = 2 + 7 * (row['log_total_weekday'] - size_min) / (size_max - size_min)
        popup = (
            f"<b>{row['station_name']}</b><br>"
            f"{row['archetype']}<br>"
            f"{int(row['daily_entries']):,} entries/day<br>"
            f"{int(row['lines_served'])} line(s)"
        )
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            color=tfl_colours[row['archetype']],
            weight=1,
            fill=True,
            fill_color=tfl_colours[row['archetype']],
            fill_opacity=0.75,
            popup=folium.Popup(popup, max_width=250),
            tooltip=row['station_name'],
        ).add_to(station_map)

    folium.CircleMarker(
        location=[selected['Latitude'], selected['Longitude']],
        radius=10,
        color="#111111",
        weight=3,
        fill=False,
    ).add_to(station_map)

    legend = ("<div style='position:fixed; bottom:18px; left:18px; z-index:9999; "
              "background:rgba(255,255,255,0.95); color:#111111; padding:8px 12px; "
              "border-radius:4px; font-family:Arial; font-size:11px; line-height:1.5;'>")
    legend += "<b style='font-size:12px; color:#111111;'>Archetype</b><br>"

    for name, colour in tfl_colours.items():
        legend += (f"<div style='margin-top:3px; color:#111111;'>"
                   f"<span style='display:inline-block;width:9px;height:9px;background:{colour};"
                   f"border-radius:50%;margin-right:6px;'></span>{name}</div>")

    legend += "</div>"
    station_map.get_root().html.add_child(folium.Element(legend))

    st_folium(station_map, width=None, height=560, returned_objects=[])

with col_info:
    st.subheader(selected['station_name'])
    st.markdown(
        f"<span style='background:{tfl_colours[selected['archetype']]};color:white;"
        f"padding:4px 10px;border-radius:3px;font-size:14px;'>{selected['archetype']}</span>",
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)
    a.metric('Entries per day', f"{int(selected['daily_entries']):,}")
    b.metric('Lines served', int(selected['lines_served']))
    c.metric('Interchange', f"{selected['interchange_ratio']:.0%}")

    direction = 'Origin' if selected['am_asym'] > 0 else 'Destination'
    d, e = st.columns(2)
    d.metric('Morning role', direction, f"{selected['am_asym']:+.2f}")
    e.metric('Saturday vs weekday', f"{selected['weekend_ratio']:.0%}")

    if selected['anomaly'] == -1:
        st.warning('Flagged as one of London\'s most unusual stations.')

    st.markdown('**Most Similar Stations**')
    top = similarity[selected_nlc].drop(selected_nlc).sort_values(ascending=False).head(5)
    similar = pd.DataFrame({
        'Station': stations.loc[top.index, 'station_name'].values,
        'Archetype': stations.loc[top.index, 'archetype'].values,
        'Similarity': [f'{s:.2f}' for s in top.values],
    })
    st.dataframe(similar, hide_index=True)

    st.markdown('**Daily rhythm**')

    station_curve = profiles.loc[selected_nlc]
    archetype_members = stations[stations['archetype'] == selected['archetype']].index
    archetype_curve = profiles.loc[archetype_members].mean()

    fig, ax = plt.subplots(figsize=(6, 2.6))
    ax.fill_between(
        range(len(profiles.columns)),
        archetype_curve,
        color=tfl_colours[selected['archetype']],
        alpha=0.25,
        label=f"{selected['archetype']} average",
    )
    ax.plot(
        range(len(profiles.columns)),
        station_curve,
        color='#111111',
        linewidth=1.6,
        label=selected['station_name'],
    )

    ticks = range(0, len(profiles.columns), 12)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([profiles.columns[i][:2] + ':00' for i in ticks], fontsize=8)
    ax.set_ylabel('Share of daily entries', fontsize=8)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=8, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    st.pyplot(fig)

st.markdown('---')
st.subheader('The Six Archetypes')
counts = stations['archetype'].value_counts()
cols = st.columns(6)
for col, name in zip(cols, tfl_colours):
    col.markdown(
        f"<div style='border-top:4px solid {tfl_colours[name]};padding-top:8px;'>"
        f"<b style='font-size:13px;'>{name}</b><br>"
        f"<span style='font-size:22px;'>{counts.get(name, 0)}</span>"
        f"<span style='font-size:12px;color:grey;'> stations</span></div>",
        unsafe_allow_html=True,
    )