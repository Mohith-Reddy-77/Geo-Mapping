from flask import Flask, render_template
import folium
from folium.plugins import MarkerCluster
import sqlite3

app = Flask(__name__)
DB_PATH = "patients.db"


# Fetch patients from DB
def get_all_patients():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, name, ip_number, age, aqi, sex, diagnosis, address, lat, lng FROM patients"
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "ip_number": r[2],
            "age": r[3],
            "aqi": r[4],
            "sex": r[5],
            "diagnosis": r[6],
            "address": r[7],
            "lat": r[8],
            "lng": r[9],
        }
        for r in rows
    ]


def get_age_groups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT age FROM patients WHERE age IS NOT NULL")
    ages = [row[0] for row in c.fetchall()]
    conn.close()

    bins = [
        (25, 35),
        (35, 45),
        (45, 55),
        (55, 65),
        (65, 75),
        (75, 85),
        (85, 95),
        (95, 105),
    ]
    groups = {f"{b[0]}-{b[1]}": 0 for b in bins}

    for age in ages:
        for b in bins:
            if b[0] <= age < b[1]:
                groups[f"{b[0]}-{b[1]}"] += 1
                break

    return groups


@app.route("/")
def dashboard():
    patients = get_all_patients()
    age_groups = get_age_groups()

    # build map
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    marker_cluster = MarkerCluster(
        icon_create_function="""
        function(cluster) {
            var count = cluster.getChildCount();
            var color = 'blue';
            if (count < 5) color = 'green';
            else if (count < 10) color = 'orange';
            else color = 'red';
            return new L.DivIcon({
                html: '<div style="background-color:'+color+';border-radius:50%;padding:10px;color:white;">'+count+'</div>',
                className: 'marker-cluster'
            });
        }
        """
    ).add_to(m)

    for p in patients:
        if p["lat"] and p["lng"]:
            popup_text = f"<b>{p['name']}</b><br>Age: {p['age']}<br>Diagnosis: {p['diagnosis']}"
            folium.Marker([p["lat"], p["lng"]], popup=popup_text).add_to(marker_cluster)

    # Save map for iframe
    m.save("templates/map.html")

    return render_template(
        "dashboard.html", age_groups=age_groups, patients=patients
    )

@app.route("/map")
def map_page():
    patients = get_all_patients()
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, control_scale=True)
    marker_cluster = MarkerCluster(
        icon_create_function="""
        function(cluster) {
            var count = cluster.getChildCount();
            var color = 'blue';
            if (count < 5) color = 'green';
            else if (count < 10) color = 'orange';
            else color = 'red';
            return new L.DivIcon({
                html: '<div style="background-color:'+color+';border-radius:50%;padding:10px;color:white;">'+count+'</div>',
                className: 'marker-cluster'
            });
        }
        """
    ).add_to(m)

    marker_locations = []
    for p in patients:
        if p["lat"] and p["lng"]:
            folium.Marker(
                [p["lat"], p["lng"]],
                icon=folium.Icon(color="green", icon="plus", prefix="fa")
            ).add_to(marker_cluster)
            marker_locations.append([p["lat"], p["lng"]])

    # Automatically center map on clusters
    if marker_locations:
        m.fit_bounds(marker_locations)

    return m._repr_html_()

if __name__ == "__main__":
    app.run(debug=True)
