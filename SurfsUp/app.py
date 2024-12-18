# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime, timedelta

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

print(Base.classes.keys())

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>" 
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the 
    # key and prcp as the value.
    most_recent_date_row = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = datetime.strptime(most_recent_date_row[0], '%Y-%m-%d')
    one_year_ago = most_recent_date - timedelta(days=365)
    results = session.query(Measurement.station, Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    session.close()

    last_year_dict = {}
    for station, date, prcp in results:
        last_year_dict[date] = prcp

    # Return the JSON representation of your dictionary.
    return jsonify(last_year_dict)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    #Return a JSON list of stations from the dataset.
    all_stations = session.query(Station.station).all()

    session.close()

    all_stations = [station[0] for station in all_stations]

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    most_recent_date_row = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = datetime.strptime(most_recent_date_row[0], '%Y-%m-%d')
    one_year_ago = most_recent_date - timedelta(days=365)
    results = session.query(Measurement.station, Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()


    # Query the dates and temperature observations of the most-active station for the previous year of data.
    station_counts = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()

    most_active_station = station_counts[0][0]
    most_active_station_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
        filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).first()
    most_active_station_stats = list(most_active_station_stats)

    session.close()

    #Return a JSON list of temperature observations for the previous year.
    return jsonify(most_active_station_stats)


@app.route("/api/v1.0/<start>")
def start_date(start):
    # Convert start date from string to date object
    start_date = datetime.strptime(start, '%Y-%m-%d')

    # Query for TMIN, TAVG, and TMAX from the start date to the most recent date
    results = session.query(
        func.min(Measurement.tobs).label('TMIN'),
        func.avg(Measurement.tobs).label('TAVG'),
        func.max(Measurement.tobs).label('TMAX')
    ).filter(Measurement.date >= start_date).all()

    # Structure the response
    temperature_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    session.close()
    
    return jsonify(temperature_stats)


@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Convert start and end dates from strings to date objects
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')

    # Query for TMIN, TAVG, and TMAX between the start and end dates
    results = session.query(
        func.min(Measurement.tobs).label('TMIN'),
        func.avg(Measurement.tobs).label('TAVG'),
        func.max(Measurement.tobs).label('TMAX')
    ).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

    # Structure the response
    temperature_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    session.close()

    return jsonify(temperature_stats)


if __name__ == '__main__':
    app.run(debug=True)