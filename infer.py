from ut import * 

from elasticsearch2 import Elasticsearch
import re
from gensim.models import Word2Vec
from SOM import SOM 
import json
import time
import os
from matplotlib import pyplot as plt
import numpy as np
from pandas.io.json import json_normalize
from sklearn.externals import joblib
from scipy.spatial.distance import cosine
import sys




def main():

	c = Load_Map("map.sav")
	mod = Load_Map("W2V.models")

	mapp = c[0]
	meta_data = c[1]
	maxx = meta_data[2]
	stdd = meta_data[1]



	endpointUrl = 'http://elasticsearch.perf.lab.eng.bos.redhat.com:9280'
	index = 'logstash-2018.07.18'

	while True:

		then = time.time()

		print("Reading in Logs from ", endpointUrl)
		test = get_data_from_ES(endpointUrl,index,3000, 60)

		print(len(test['hits']['hits']), "logs loaded from the last minute.")


		print("Preprocessing logs")

		new_D = json_normalize(test['hits']['hits'])

		for lines in range(len(new_D["_source.message"])):
			new_D["_source.message"][lines] = Clean(new_D["_source.message"][lines]) 

		Update_W2V_Models(mod,new_D)


		transforms = Transform_Text(mod,new_D)


		v = One_Vector(transforms)

		dist = []
		for i in v:
			dist.append(Get_Anomaly_Score(mapp,i))

		count = 0
		anom = []


		for i in range(5):
		 	loc = np.argmax(dist)
		 	anom.append(loc)

		 	if dist[loc] > (3.5*stdd):
		 		print(dist[loc], test['hits']['hits'][loc]['_source']['message'], "\n")


		 	dist[loc] = 0

		#print(count)

		now = time.time()

		print("Analyzed one minute of data in ",(now-then)," seconds")

		print("waiting for next minute to start...", "\n", "press ctrl+c to stop process")


		time.sleep(60-(now-then))





if __name__ == "__main__":
    main()