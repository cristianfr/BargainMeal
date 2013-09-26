from ..text_classifiers.multinomialBayes import featx
from ..utils.text import markerFormat
import foursquare as fs
import coupons as cp
import heuristic
import MySQLdb as db
import pickle



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
	cur.execute( "SELECT Coupons.name, value, discount, url, restaurantId, lat, lng, id \
		FROM Coupons JOIN Restaurants ON Coupons.id = Restaurants.idCoupon" )
	coupons = cur.fetchall()
	
	for coupon in coupons:
		( name, value, discount, url, id_foursquare, lat, lng, ids) = coupon
		
		cur.execute( "SELECT itemName, itemPrice, review, counter.county FROM Reviews \
		 JOIN Menus ON Menus.itemId = Reviews.itemId \
		 JOIN \
		 (SELECT itemId, count(itemId) as county FROM Reviews WHERE sentiment='pos' GROUP BY itemId ) as counter ON counter.itemId=Reviews.itemId\
		 WHERE Reviews.restaurantId = %s AND \
		 Reviews.sentiment='pos' \
		 GROUP BY itemName,itemPrice,itemDesc, review ORDER BY counter.county DESC", ( id_foursquare, ) )
		html_info = cur.fetchall()
		tasty_items = []
		revs = []
		for item in html_info:
			(iName, iPrice, rev, county) = item
			strName = iName.replace('"','\\"')+" $"+str(iPrice)
			toAppend = (strName, county)
			if toAppend not in tasty_items:
				tasty_items.append(toAppend)
			revs.append( (rev.replace('"','\\"') , strName) )

		cur.execute( "SELECT yelp_r FROM Additional WHERE id = %s", ( ids, ) )
		rating = cur.fetchone()
		
		( m_label, m_revs ) = markerFormat( name, value, discount, tasty_items, revs)
		markers.append( ( lat, lng , m_label, m_revs, ids, url, rating[0]*1.0/5 ) ) 
	return markers

def assign(cur):
	cur.execute('SELECT restaurantId FROM Restaurants')
	rIds = cur.fetchall()
	for rId in rIds:
		print rId
		assignations = heuristic.itemAssign(rId,cur)
		if (len(assignations)>0):
			cur.executemany("UPDATE Reviews SET itemId ='%s' WHERE reviewId=%s",assignations)
		print str(len(assignations)) +' values updated '

def assignSentiment(cur):
	#Assign sentiment given the classifier.
	with open('tools/text_classifiers/mbclassif.pickle','r') as infile:
		classif =  pickle.load(infile)
	cur.execute("SELECT reviewId, review FROM Reviews WHERE sentiment='unk' ")
	reviews = cur.fetchall()
	classified_rev = [ ( classif.classify( featx( review[1] ) ), review[0]) for review in reviews]
	cur.executemany('UPDATE Reviews SET sentiment=%s WHERE reviewId=%s', classified_rev)
	

def main():
	con = connect_db()
	cur = con.cursor()
	print 'Connected to the database .-.-.--.-.-.-.-.-.-.-.-.-.'
	#cp.create_coupons(cur)
	#cp.populate_coupons(cur)
	print 'Populated Coupons .-.-.--.-.-.-.-.-.-.-.-.-.'
	#cp.create_additional(cur)
	#cp.populate_additional(cur,'livingsocial')
	#cp.populate_additional(cur,'groupon')
	print 'Populated Additional .-.-.--.-.-.-.-.-.-.-.-.-.'
	#fs.create_foursquare(cur)
	#fs.populate_foursquare(cur)
	print 'Populated Restaurants ..-.-.-....-..-.--.-.-.-.-.'
	assign(cur)
	#assignSentiment(cur)
	cur.execute('SELECT review, sentiment FROM Reviews')
	reply = cur.fetchall()
	for text in reply:
		print text
	print 'Commiting changes .-.-.-.-.--.-.-.-.-.-.-.'
	con.commit()
	con.close()


if __name__=='__main__':
	main()