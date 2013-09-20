from ..scrappers import livingsocial as ls
from ..scrappers import groupon as gp
from random import randint
from time import sleep

'''
Create tables associated to coupons, this includes the 
additional table that compliments the data obtained from foursquare 
with data extrated from scrapping websites. 
'''

def create_coupons(cur):
	#Create coupon tables.
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

def create_links(cur):
	#Create links table for living social. Almost inmutable.
	cur.execute('DROP TABLE IF EXISTS ls_links')
	cur.execute("CREATE TABLE ls_links( \
			city VARCHAR(255) CHARACTER SET utf8, \
			link VARCHAR(255) CHARACTER SET utf8, \
			PRIMARY KEY(link))")

def populate_coupons(cur):
	#Populate coupon tables from scrapped data.
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
		id_key += 1
		sql_coupon.append( (str(id_key),) + coupon )
	cur.executemany("INSERT INTO coupons (id, name, title, value, discount, url, site) \
											VALUES (%s,%s,%s,%s,%s,%s,%s)",sql_coupon)

def create_additional(cur):
	#Create table with complementary data for foursquare table.
	cur.execute('DROP TABLE IF EXISTS additional')
	cur.execute("CREATE TABLE additional( \
			id INT, \
			lat VARCHAR(20) CHARACTER SET utf8,\
			lng VARCHAR(20) CHARACTER SET utf8,\
			phone VARCHAR(10) CHARACTER SET utf8,\
			yelp_r FLOAT)")

def populate_additional(cur):
	#Populate the additional table with scrapped data from coupons.
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
			#Prevent overloading database, or losing data due to ip blocking.
			print 'Saving............................'		
			cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) \
				VALUES (%s,%s,%s,%s,%s)",additional_gp)
			additional_gp = []
	print 'Saving ...'
	cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) \
		VALUES (%s,%s,%s,%s,%s)",additional_gp)
	cur.execute("SELECT id, url FROM coupons WHERE site='livingsocial'")
	links = cur.fetchall()
	additional_ls = []
	for link in links:
		sleep(randint(0,2))
		(ids,url) = link
		(lat,lng,phone,rating) = ls.dealStrip(url)
		additional_ls.append( (ids,lat,lng,phone,rating))
	cur.executemany("INSERT INTO additional(id,lat,lng,phone,yelp_r) \
		VALUES (%s,%s,%s,%s,%s)",additional_ls)

def populate_links(cur):
	#Populate links by scrapping livingsocial index.
	create_links(cur)
	links = ls.cityExtractor()
	cur.executemany("INSERT INTO ls_links(city, link) \
		VALUES (%s,%s)",links)

def getCoupons(cur):
	#Retrieve all coupons.
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


