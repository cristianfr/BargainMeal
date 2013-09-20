from ..API_extract import foursquare as fs

'''
Foursquare related tables. Tasty dishes, local info, etc.
'''

def create_foursquare(cur):
	#Create all the relevant foursquare tables.
	cur.execute('DROP TABLE IF EXISTS foursquare')
	cur.execute("CREATE TABLE foursquare( \
			id_coupon INT, \
			id_foursquare VARCHAR(255) CHARACTER SET utf8,\
			name_foursquare VARCHAR(255) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT,\
			rating INT, \
			PRIMARY KEY(id_foursquare))")
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

def populate_foursquare(cur):
	cur.execute("SELECT coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM coupons JOIN additional ON coupons.id=additional.id")
	coupons = cur.fetchall()
	
	places = []
	reviews = []
	dishes = []
	for coupon in coupons:
		( ids, name, title, value, discount, url, lat, lng, phone, yelp_r) = coupon
		try:
			foursquare_id = fs.phone_match( lat, lng, phone, name)
		except KeyError:
			print "KeyError"
			continue
		if foursquare_id == "no_id":
			continue
		( tasty_items, revs ) = fs.getTastyM( foursquare_id )		
		dishes.extend( [ ( foursquare_id, dish ) for dish in tasty_items ] )
		reviews.extend( [ ( foursquare_id, review[0], review[1] ) for review in revs ] )
		places.append( ( ids, foursquare_id, name, lat, lng, yelp_r ) )

	cur.executemany( "INSERT INTO fs_foods(id_foursquare, tasty) \
		VALUES (%s,%s)", dishes )
	cur.executemany( "INSERT INTO fs_reviews(id_foursquare, review, tasty) \
		VALUES (%s,%s,%s)", reviews )
	cur.executemany( "INSERT INTO foursquare(id_coupon, id_foursquare, name_foursquare, lat, lng, rating)\
															 VALUES (%s,%s,%s,%s,%s,%s)",places)


