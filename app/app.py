from tools.API_extract import foursquare as fs
from tools.API_extract import groupon as gp
from tools.utils.text import markerFormat
from tools.db import geocodes as gc
from tools.API_extract import yelp
from tools.db import common as db
from flask import *
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(100)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/offline")
def offline():
	location = 'San Francisco, CA'
	con = db.connect_db()
	#Query database for info.
	with con:
		cur = con.cursor()
		latlng = gc.getGeocode(location,cur)
		markers = db.queryMarkers(cur)
	#Query foursquare for info to create markers
	(lat,lng) = latlng.split(",")
	return render_template("map.html",latitude = lat,longitude = lng, markers = markers)


@app.route("/query", methods = ['POST'])
def query():
    session['location'] = request.form['location']
    (deals,latlng) = gp.getDeals(session['location'])
    foodDeals = gp.filterFoods(deals)
    markers = createMarkers(foodDeals,latlng)
    (lat,lng) = latlng.split(",")
    return render_template("map.html", location = session['location'], latitude= lat, longitude = lng, markers= markers )
	
@app.route("/about")
def about():
	return redirect("http://www.mit.edu/~cfiguero")
	
@app.route("/slides")
def slides():
	return render_template("slides.html")

@app.route("/code")
def code():
	return redirect("https://github.com/cristianfr/BargainMeal")

def createMarkers(coupons, latlng):
	#First version uses one location per item.
	#Step one find the local_id in foursquare.
	con = db.connect_db()
	#Query database for info.
	with con:
		cur = con.cursor()
		markers= db.queryMarkers(cur)
	#Query foursquare for info to create markers
	return markers


if __name__ == "__main__":
	if (len(sys.argv) >1 ):
		app.run(port=8888)
	else:
		app.run(host="0.0.0.0",port=80)
