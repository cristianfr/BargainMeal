from tools.API_extract import foursquare as fs
from tools.API_extract import groupon as gp
from tools.utils.text import markerFormat
from tools.utils import db_tools as db
from tools.API_extract import yelp
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
		latlng = db.getGeocode(location,cur)
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
	return render_template("about.html")

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
	for coupon in coupons:
		(ids, name, title, value, discount, url,site) = coupon
		((foursquare_id, foursquare_name, lat, lng, phone),score) = fs.venue_match((latlng,name))
		if score == 0:
			continue
		(tasty_items, revs ) = fs.getTastyM( foursquare_id )
		try:
			rating = yelp.getRating(phone)
		except IndexError:
			rating=0
		counter = dict([(m_item , 0 ) for m_item in tasty_items])
		for m_item in tasty_items:
			counter[m_item] += 1
		tastyLabel = [ (m_item, counter[m_item]) for m_item in tasty_items]
		(m_label, m_revs) = markerFormat(name,value,discount, tastyLabel,revs)
		markers.append( (lat,lng ,m_label, m_revs , ids, url,(rating-1)/4) ) 
	return markers

if __name__ == "__main__":
    app.run(port=8888)