import sqlite3
import os
import pandas as pd

# change to the directory where the files are stored
os.chdir("../Downloads/dataverse_files")

try:
    os.remove('airline2.db')
except OSError:
    pass

# ======= create database =======
conn = sqlite3.connect('airline2.db')

# ======= create tables =======

airports = pd.read_csv("airports.csv")
carriers = pd.read_csv("carriers.csv")
planes = pd.read_csv("plane-data.csv")

airports.to_sql('airports', con = conn, index = False)
carriers.to_sql('carriers', con = conn, index = False)
planes.to_sql('planes', con = conn, index = False)

c = conn.cursor()
c.execute('''
CREATE TABLE ontime (
  Year int,
  Month int,
  DayofMonth int,
  DayOfWeek int,
  DepTime  int,
  CRSDepTime int,
  ArrTime int,
  CRSArrTime int,
  UniqueCarrier varchar(5),
  FlightNum int,
  TailNum varchar(8),
  ActualElapsedTime int,
  CRSElapsedTime int,
  AirTime int,
  ArrDelay int,
  DepDelay int,
  Origin varchar(3),
  Dest varchar(3),
  Distance int,
  TaxiIn int,
  TaxiOut int,
  Cancelled int,
  CancellationCode varchar(1),
  Diverted varchar(1),
  CarrierDelay int,
  WeatherDelay int,
  NASDelay int,
  SecurityDelay int,
  LateAircraftDelay int
)
''')
conn.commit()

for year in range(2000, 2006):
    ontime = pd.read_csv(str(year)+".csv")
    ontime.to_sql('ontime', con = conn, if_exists = 'append', index = False)

conn.commit()

# ======= run queries =======

c.execute('''
SELECT model AS model, AVG(ontime.DepDelay) AS avg_delay
FROM planes JOIN ontime USING(tailnum)
WHERE ontime.Cancelled = 0 AND ontime.Diverted = 0 AND ontime.DepDelay > 0
GROUP BY model
ORDER BY avg_delay
''')


print(c.fetchone()[0], "has the lowest associated average departure delay.")

c.execute('''
SELECT airports.city AS city, COUNT(*) AS total
FROM airports JOIN ontime ON ontime.dest = airports.iata
WHERE ontime.Cancelled = 0
GROUP BY airports.city
ORDER BY total DESC
''')

print(c.fetchone()[0], "has the highest number of inbound flights (excluding cancelled flights)")

c.execute('''
SELECT carriers.Description AS carrier, COUNT(*) AS total
FROM carriers JOIN ontime ON ontime.UniqueCarrier = carriers.Code
WHERE ontime.Cancelled = 1
AND carriers.Description IN ('United Air Lines Inc.', 'American Airlines Inc.', 'Pinnacle Airlines Inc.', 'Delta Air Lines Inc.')
GROUP BY carriers.Description
ORDER BY total DESC
''')

print(c.fetchone()[0],"has the highest number of cancelled flights")

c.execute('''
SELECT
q1.carrier AS carrier, (CAST(q1.numerator AS FLOAT)/ CAST(q2.denominator AS FLOAT)) AS ratio
FROM
(
  SELECT carriers.Description AS carrier, COUNT(*) AS numerator
  FROM carriers JOIN ontime ON ontime.UniqueCarrier = carriers.Code
  WHERE ontime.Cancelled = 1 AND carriers.Description IN ('United Air Lines Inc.', 'American Airlines Inc.', 'Pinnacle Airlines Inc.', 'Delta Air Lines Inc.')
  GROUP BY carriers.Description
) AS q1 JOIN
(
  SELECT carriers.Description AS carrier, COUNT(*) AS denominator
  FROM carriers JOIN ontime ON ontime.UniqueCarrier = carriers.Code
  WHERE carriers.Description IN ('United Air Lines Inc.', 'American Airlines Inc.', 'Pinnacle Airlines Inc.', 'Delta Air Lines Inc.')
  GROUP BY carriers.Description
) AS q2 USING(carrier)
ORDER BY ratio DESC
''')
print(c.fetchone()[0], "highest number of cancelled flights, relative to their number of total flights")

conn.close()
