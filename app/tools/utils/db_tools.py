from ..scrappers import livingsocial as ls
from ..API_extract import foursquare as fs
from ..scrappers import groupon as gp
from text import markerFormat
from random import randint
from time import sleep
import MySQLdb as db
import csv




def connect_db():
	con = db.connect(host = "localhost", user = "cris", passwd = 'cris', db ="BargainMeal")
	return con

def db_setup():
	#To be run the first time.
	root_pass= "root"
	con = db.connect(host = "localhost", user = "root", passwd = root_pass)
	cur = con.cursor()
	cur.execute('''CREATE DATABASE BargainMeal''')
	cur.execute('''CREATE USER 'cris'@'localhost' IDENTIFIED BY 'cris' ''')
	cur.execute('''GRANT ALL ON *.* TO cris''')
	cur.close()
	con.close()

def create_coupons(cur):
	cur.execute('DROP TABLE IF EXISTS coupons')
	cur.execute("CREATE TABLE coupons( \
			id INT, \
			name VARCHAR(255) CHARACTER SET utf8, \
			title VARCHAR(255) CHARACTER SET utf8,\
			value FLOAT,\
			discount FLOAT,\
			url VARCHAR(255) CHARACTER SET utf8,\
			site VARCHAR(255) CHARACTER SET utf8,\
			PRIMARY KEY(id))")

def create_geocodes(cur):
	cur.execute('DROP TABLE IF EXISTS geocodes')
	cur.execute("CREATE TABLE geocodes( \
			city VARCHAR(255) CHARACTER SET utf8, \
			state VARCHAR(2) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT)")

def create_links(cur):
	cur.execute('DROP TABLE IF EXISTS ls_links')
	cur.execute("CREATE TABLE ls_links( \
			city VARCHAR(255) CHARACTER SET utf8, \
			link VARCHAR(255) CHARACTER SET utf8)")

def create_foursquare(cur):
	cur.execute('DROP TABLE IF EXISTS foursquare')
	cur.execute("CREATE TABLE foursquare( \
			id_coupon INT, \
			id_foursquare VARCHAR(255) CHARACTER SET utf8,\
			name_foursquare VARCHAR(255) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT,\
			rating INT)")
	cur.execute('DROP TABLE IF EXISTS fs_reviews')
	cur.execute("CREATE TABLE fs_reviews( \
			id_foursquare VARCHAR(255) CHARACTER SET utf8, \
			review TEXT CHARACTER SET utf8,\
			tasty VARCHAR(255) CHARACTER SET utf8\
			)")
	cur.execute('DROP TABLE IF EXISTS fs_foods')
	cur.execute("CREATE TABLE fs_foods( \
			id_foursquare VARCHAR(255) CHARACTER SET utf8, \
			tasty VARCHAR(255) CHARACTER SET utf8)")

def create_additional(cur):
	cur.execute('DROP TABLE IF EXISTS additional')
	cur.execute("CREATE TABLE additional( \
			id INT, \
			lat VARCHAR(20) CHARACTER SET utf8,\
			lng VARCHAR(20) CHARACTER SET utf8,\
			phone VARCHAR(10) CHARACTER SET utf8,\
			yelp_r FLOAT)")

def populate_additional(cur):
	cur.execute("SELECT id, url FROM coupons WHERE site='groupon'")
	links = cur.fetchall()
	additional_gp = []
	for link in links:
		sleep(randint(0,2))
		(ids,url) = link
		print ids
		try:
			(lat,lng,phone,rating) = gp.dealStrip(url)
		except AttributeError:
			print 'Skipping'
			continue
		additional_gp.append( (ids,lat,lng,phone,rating))
		if len(additional_gp)>20:
			print 'Saving............................'		
			cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) VALUES (%s,%s,%s,%s,%s)",additional_gp)
			additional_gp = []
	print 'Saving ...'
	cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) VALUES (%s,%s,%s,%s,%s)",additional_gp)
	cur.execute("SELECT id, url FROM coupons WHERE site='livingsocial'")
	links = cur.fetchall()
	additional_ls = []
	for link in links:
		sleep(randint(0,2))
		(ids,url) = link
		(lat,lng,phone,rating) = ls.dealStrip(url)
		additional_ls.append( (ids,lat,lng,phone,rating))
	cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) VALUES (%s,%s,%s,%s,%s)",additional_ls)

def populate_links(cur):
	create_links(cur)
	links = ls.cityExtractor()
	cur.executemany("INSERT INTO ls_links(city, link) VALUES (%s,%s)",links)

def populate_geocodes(cur):
	create_geocodes(cur)
	with open('tools/utils/cities.csv','r') as infile:
		geo_file = csv.reader(infile)
		for line in geo_file:
			cur.execute("INSERT INTO geocodes(city, state, lat, lng) VALUES (%s,%s,%s,%s)",line)

def populate_coupons(cur):
	#Refresh table.
	create_coupons(cur)
	cur.execute("SELECT * FROM ls_links WHERE city LIKE 'San Francisco%'")
	ls_coupons = []
	links = cur.fetchall()
	for link in links:
		sleep(randint(0,2))
		ls_coupons.extend( ls.dealExtractorURL( link[1]+'/food-deals' ) )
	unique_ls = list(set(ls_coupons))
	gp_coupons = gp.dealExtractor( open(gp.LOCAL, 'r'))
	coupons = unique_ls + gp_coupons
	id_key = 0
	sql_coupon = []
	for coupon in coupons:
		id_key+=1
		sql_coupon.append( (str(id_key),) + coupon )
	cur.executemany("INSERT INTO coupons (id, name, title, value, discount, url, site) \
											VALUES (%s,%s,%s,%s,%s,%s,%s)",sql_coupon)

def populate_foursquare(cur):
	cur.execute("SELECT coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM coupons JOIN additional ON coupons.id=additional.id")
	coupons = cur.fetchall()
	places = []
	reviews = []
	dishes = []
	for coupon in coupons:
		(ids,name,title,value,discount,url,lat,lng,phone,yelp_r) = coupon
		try:
			foursquare_id = fs.phone_match(lat,lng,phone,name)
		except KeyError:
			print "KeyError"
			continue
		if foursquare_id=="no_id":
			continue
		(tasty_items, revs ) = fs.getTastyM( foursquare_id )		
		dishes.extend([(foursquare_id, dish) for dish in tasty_items] )
		reviews.extend([(foursquare_id, review[0],review[1]) for review in revs])
		places.append( (ids, foursquare_id, name, lat, lng, yelp_r))
	cur.executemany("INSERT INTO fs_foods(id_foursquare, tasty) VALUES (%s,%s)",dishes)
	cur.executemany("INSERT INTO fs_reviews(id_foursquare, review, tasty) VALUES (%s,%s,%s)",reviews)
	cur.executemany("INSERT INTO foursquare(id_coupon, id_foursquare, name_foursquare, lat, lng, rating)\
															 VALUES (%s,%s,%s,%s,%s,%s)",places)

def queryMarkers(cur):
	markers = []
	cur.execute("SELECT name, value, discount, url, id_foursquare, lat, lng, id \
		FROM coupons JOIN foursquare ON coupons.id=foursquare.id_coupon")
	coupons = cur.fetchall()
	for coupon in coupons:
		(name, value, discount, url, id_foursquare, lat, lng, ids) = coupon
		cur.execute("SELECT tasty, count(tasty) FROM fs_foods WHERE id_foursquare=%s GROUP BY tasty ORDER BY 2 DESC",(id_foursquare,))
		tasty_items = cur.fetchall()
		if tasty_items == ():
			continue
		if tasty_items[0][0].strip()=='':
			continue
		cur.execute("SELECT review,tasty FROM fs_reviews WHERE id_foursquare=%s",(id_foursquare,))
		revs = cur.fetchall()
		cur.execute("SELECT yelp_r FROM additional WHERE id=%s",(ids,))
		rating = cur.fetchone()
		(m_label, m_revs) = markerFormat(name,value,discount, tasty_items,revs)
		markers.append( (lat,lng ,m_label, m_revs , ids, url,rating[0]*1.0/5) ) 
	return markers

def getGeocode(city_state,cur):
	(city,state) = city_state.split(",")
	cur.execute("SELECT lat,lng FROM geocodes WHERE city=%s AND state=%s",(city.strip(),state.strip()))
	(lat,lng) =  cur.fetchone()
	return str(lat)+','+str(lng)

def getCoupons(cur):
	cur.execute("SELECT * FROM coupons")
	return cur.fetchall()

def get_random_link(cur):
	#For testing purposes. I know it's a slow implementation.
	cur.execute("SELECT * FROM ls_links ORDER BY RAND() LIMIT 1")
	(city,url) =  cur.fetchone()
	return city + ' '+ url

def get_random_coupon(cur):
	#For testing purposes. I know it's a slow implementation.
	cur.execute("SELECT * FROM coupons ORDER BY RAND() LIMIT 1")
	(ids, name,title,value,discount,url,site) =  cur.fetchone()
	return name + ' '+ title

def get_random_code(cur):
	#For testing purposes. I know it's a slow implementation.
	cur.execute("SELECT * FROM geocodes ORDER BY RAND() LIMIT 1")
	(city,state,lat,lng) =  cur.fetchone()
	return city + ' '+ state +' '+ str(lat)+' '+ str(lng)

def main():
	con = connect_db()
	cur = con.cursor()
	#create_additional(cur)
	#populate_additional(cur)
	create_foursquare(cur)
	populate_foursquare(cur)
	con.commit()
	cur.close()
	con.close()

if __name__=='__main__':
	main()