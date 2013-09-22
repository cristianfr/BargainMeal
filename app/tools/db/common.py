from ..utils.text import markerFormat
import MySQLdb as db
import foursquare as fs

'''
Common methods. Connect to databases, create the database if necessary, 
give the markers that are cached in the database.
'''

def connect_db():
	# Connect to the database.
	con = db.connect(host = "localhost", user = "cris", passwd = 'cris', db ="BargainMeal")
	return con

def db_setup():
	# To be run the first time. Create db, user, permissions
	root_pass = "root"
	con = db.connect( host = "localhost", user = "root", passwd = root_pass )
	cur = con.cursor()
	cur.execute( '''CREATE DATABASE BargainMeal''' )
	cur.execute( '''CREATE USER 'cris'@'localhost' IDENTIFIED BY 'cris' ''' )
	cur.execute( '''GRANT ALL ON *.* TO cris''' )
	cur.close()
	con.close()

def queryMarkers(cur):
	# Fetch the coupon/retaurant data cached in the database.
	markers = []
	cur.execute( "SELECT name, value, discount, url, id_foursquare, lat, lng, id \
		FROM coupons JOIN foursquare ON coupons.id = foursquare.id_coupon" )
	coupons = cur.fetchall()
	
	for coupon in coupons:
		( name, value, discount, url, id_foursquare, lat, lng, ids) = coupon
		cur.execute( "SELECT tasty, count(tasty) FROM fs_foods WHERE id_foursquare = %s \
		 GROUP BY tasty ORDER BY 2 DESC", ( id_foursquare, ) )
		tasty_items = cur.fetchall()
		
		if tasty_items == ():
			continue
		if tasty_items[0][0].strip() == '':
			continue
		cur.execute( "SELECT review, tasty FROM fs_reviews WHERE id_foursquare = %s", ( id_foursquare,) )
		revs = cur.fetchall()
		
		cur.execute( "SELECT yelp_r FROM additional WHERE id = %s", ( ids, ) )
		rating = cur.fetchone()
		
		( m_label, m_revs ) = markerFormat( name, value, discount, tasty_items, revs)
		markers.append( ( lat, lng , m_label, m_revs, ids, url, rating[0]*1.0/5 ) ) 
	return markers

def main():
	con = connect_db()
	cur = con.cursor()

if __name__=='__main__':
	main()