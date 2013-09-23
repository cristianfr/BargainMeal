

def hasher(item):
	#Considers mysql INT granularity.
	granularity = 2147483647
	mod = 2*granularity
	return hash(item)%mod - granularity