

def hasher(item):
	#Considers mysql INT granularity.
	granularity = 2147483647
	return hash(item)%granularity