import pandas as pd
import sqlite3
import googlemaps

API_KEY = "AIzaSyDWGTPprhkEHMnHQjqJtp4BaH5ZgC14XjQ"   # Replace with your Google Maps API key
gmaps = googlemaps.Client(key=API_KEY)

DB_PATH = 'patients.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Drop and recreate table each run (clean import)
    c.execute("DROP TABLE IF EXISTS patients")
    c.execute('''
    CREATE TABLE patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        ip_number TEXT,
        age INTEGER,
        aqi INTEGER,
        sex TEXT,
        diagnosis TEXT,
        address TEXT,
        lat REAL,
        lng REAL
    )
    ''')
    conn.commit()
    conn.close()

def insert_patient(row):
    address = str(row['Address']).strip() if pd.notna(row['Address']) else ""
    
    # ✅ Skip if address is empty
    if not address:
        print(f"Skipping patient {row['Patient Names']} (no address).")
        return

    geocode_result = gmaps.geocode(address)
    if geocode_result:
        loc = geocode_result[0]['geometry']['location']
        lat, lng = loc['lat'], loc['lng']
    else:
        lat, lng = None, None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO patients (name, ip_number, age, aqi, sex, diagnosis, address, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['Patient Names'], row['IP Number'], row['Age'], row['AQI'],
          row['Sex'], row['Diagnosis'], address, lat, lng))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    df = pd.read_excel("D:\GeoMapping\Excel Data For Research.xlsx")
    for _, row in df.iterrows():
        insert_patient(row)
