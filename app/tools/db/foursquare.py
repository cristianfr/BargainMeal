from ..API_extract import foursquare as fs
from util import hasher
import pickle
'''
Foursquare related tables. Tasty dishes, local info, etc.
TastyDishes originally was created for storing the best dishes
of each restaurant. However, later on with the objective of improving
accuracy a new table was created to contain the whole menu.

-- To do --
Given the update one can add the itemId to the fs_foods.
Add a key for review. ReviewId

-- Ultimate to do -- 
Get the keys from a hash function.
'''

def create_foursquare(cur):
	#Create all the relevant foursquare tables.
	cur.execute('DROP TABLE IF EXISTS Restaurants')
	cur.execute("CREATE TABLE Restaurants( \
			idCoupon INT, \
			restaurantId VARCHAR(255) CHARACTER SET utf8,\
			name VARCHAR(255) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT,\
			rating INT, \
			PRIMARY KEY(restaurantId))")
	cur.execute('DROP TABLE IF EXISTS Reviews')
	cur.execute("CREATE TABLE Reviews( \
			reviewId INT, \
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			review TEXT CHARACTER SET utf8,\
			mItem VARCHAR(255) CHARACTER SET utf8\
			)")
	cur.execute('DROP TABLE IF EXISTS Tasties')
	cur.execute("CREATE TABLE Tasties( \
			itemId INT,\
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			mItem VARCHAR(255) CHARACTER SET utf8)")
	cur.execute('DROP TABLE IF EXISTS Menus')
	cur.execute('CREATE TABLE Menus( \
			itemId INT , \
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			itemName VARCHAR(255) CHARACTER SET utf8, \
			itemPrice FLOAT, \
			itemDesc TEXT, \
			PRIMARY KEY(itemId) )')

	
def populate_foursquare(cur):
	cur.execute("SELECT Coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM Coupons JOIN Additional ON Coupons.id=Additional.id")
	coupons = cur.fetchall()
	errors = ""
	places, reviews, mItems =  [],[],[]
	for coupon in coupons:
		( ids, name, title, value, discount, url, lat, lng, phone, yelp_r) = coupon
		foursquare_id = fs.phoneMatch( lat, lng, phone, name)
		if foursquare_id[0] == "no_id":
			errors += ','.join(foursquare_id) +'\n'
			continue
		( name, revs, menuItems ) = fs.localInfo( foursquare_id )		
		for item in menuItems:
			if (len(str(item))<2):
				continue
			itemKey = hasher( item ) 
			try:
				(iName, iDesc, iPrice) = item
			except KeyError:
				print item
				continue
			except ValueError:
				print item
				continue
			mItems.append( ( itemKey, foursquare_id , iName, iPrice, iDesc) )
		reviews.extend( [ ( hasher( (review,foursquare_id) ), foursquare_id, review, "unassigned " ) for review in revs if (len(review.strip())>0)] )
		places.append( ( ids, foursquare_id, name, lat, lng, yelp_r ) )
	with open('populate_foursquare.log','w') as outfile:
		outfile.write(errors)

	cur.executemany('INSERT IGNORE INTO Menus\
		(itemId, restaurantId, itemName, itemPrice, itemDesc) \
		VALUES (%s,%s,%s,%s,%s)',mItems)

	cur.executemany( "INSERT IGNORE INTO Reviews(reviewId, restaurantId, review, mItem) \
		VALUES (%s,%s,%s,%s)", reviews )
	cur.executemany( "INSERT IGNORE INTO Restaurants(idCoupon, restaurantId, name, lat, lng, rating)\
															 VALUES (%s,%s,%s,%s,%s,%s)",places)
def createRequestsFile(cur):
	cur.execute("SELECT Coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM Coupons JOIN Additional ON Coupons.id=Additional.id")
	coupons = cur.fetchall()
	line = ""
	for coupon in coupons:
		( ids, name, title, value, discount, url, lat, lng, phone, yelp_r) = coupon
		line += fs.phoneRequest(lat,lng,phone,name)+'\n'
	with open('PhoneRequests.txt', 'w') as outfile:
		outfile.write(line)


