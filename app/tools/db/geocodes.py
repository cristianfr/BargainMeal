import csv

def create_geocodes(cur):
	cur.execute('DROP TABLE IF EXISTS geocodes')
	cur.execute("CREATE TABLE geocodes( \
			city VARCHAR(255) CHARACTER SET utf8, \
			state VARCHAR(2) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT)")

def populate_geocodes(cur):
	create_geocodes(cur)
	with open('tools/utils/cities.csv','r') as infile:
		geo_file = csv.reader(infile)
		for line in geo_file:
			cur.execute("INSERT INTO geocodes(city, state, lat, lng) \
				VALUES (%s,%s,%s,%s)",line)

def getGeocode(city_state,cur):
	(city,state) = city_state.split(",")
	cur.execute("SELECT lat,lng FROM geocodes WHERE city=%s AND state=%s",(city.strip(),state.strip()))
	(lat,lng) =  cur.fetchone()
	return str(lat)+','+str(lng)

def get_random_code(cur):
	#For testing purposes. I know it's a slow implementation.
	cur.execute("SELECT * FROM geocodes ORDER BY RAND() LIMIT 1")
	(city,state,lat,lng) =  cur.fetchone()
	return city + ' '+ state +' '+ str(lat)+' '+ str(lng)