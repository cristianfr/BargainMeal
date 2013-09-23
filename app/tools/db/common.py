from ..utils.text import markerFormat
import foursquare as fs
import coupons as cp
import MySQLdb as db


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
	cur.execute( "SELECT name, value, discount, url, restaurantId, lat, lng, id \
		FROM Coupons JOIN Restaurants ON Coupons.id = Restaurants.idCoupon" )
	coupons = cur.fetchall()
	
	for coupon in coupons:
		( name, value, discount, url, id_foursquare, lat, lng, ids) = coupon
		cur.execute( "SELECT mItem, count(mItem) FROM Tasties WHERE restaurantId = %s \
		 GROUP BY mItem ORDER BY 2 DESC", ( id_foursquare, ) )
		tasty_items = cur.fetchall()
		
		if tasty_items == ():
			continue
		if tasty_items[0][0].strip() == '':
			continue
		cur.execute( "SELECT review, mItem FROM Reviews WHERE restaurantId = %s", ( id_foursquare,) )
		revs = cur.fetchall()
		
		cur.execute( "SELECT yelp_r FROM additional WHERE id = %s", ( ids, ) )
		rating = cur.fetchone()
		
		( m_label, m_revs ) = markerFormat( name, value, discount, tasty_items, revs)
		markers.append( ( lat, lng , m_label, m_revs, ids, url, rating[0]*1.0/5 ) ) 
	return markers

def main():
	con = connect_db()
	cur = con.cursor()
	print 'Connected to the database .-.-.--.-.-.-.-.-.-.-.-.-.'
	#cp.create_coupons(cur)
	#cp.populate_coupons(cur)
	#print 'Populated Coupons .-.-.--.-.-.-.-.-.-.-.-.-.'
	#cp.create_additional(cur)
	#cp.populate_additional(cur,'livingsocial')
	#print 'Populated Additional .-.-.--.-.-.-.-.-.-.-.-.-.'
	fs.create_foursquare(cur)
	fs.populate_foursquare(cur)
	print 'Populated Restaurants ..-.-.-....-..-.--.-.-.-.-.'
	print 'Commiting changes .-.-.-.-.--.-.-.-.-.-.-.'
	con.commit()


if __name__=='__main__':
	main()