from ut import * 

from elasticsearch2 import Elasticsearch
import re
from gensim.models import Word2Vec
from SOM import SOM 
import json
import time
import os
import matplotlib
matplotlib.use("agg")
from matplotlib import pyplot as plt
import numpy as np
from pandas.io.json import json_normalize
from sklearn.externals import joblib
from scipy.spatial.distance import cosine
import sys
import datetime




def infer():


	endpointUrl = os.environ.get("LADI_ELASTICSEARCH_ENDPOINT")
	outpoint = os.environ.get("LADI_OUTDEX")
	model = os.environ.get("LADI_MODEL")
	index_prefix = os.environ.get("LADI_INDEX")
	time_span = int(os.environ.get("LADI_TIME_SPAN"))
	max_entries = int(os.environ.get("LADI_MAX_ENTRIES"))
	service = os.environ.get("LADI_SERVICE")
	threshold = float(os.environ.get("LADI_THRESHOLD"))
	max_anoms = int(os.environ.get("LADI_MAX_ANOMALIES"))









	c = Load_Map(model)
	mod = Load_Map("W2V.models")

	mapp = c[0]
	meta_data = c[1]
	maxx = meta_data[2]
	stdd = meta_data[1]



	#endpointUrl = 'http://elasticsearch.perf.lab.eng.bos.redhat.com:9280'

	while True:

		then = time.time()

		now = datetime.datetime.now()
		date = now.strftime("%Y.%m.%d")
		#index = 'logstash-'+date
		index = index_prefix + date


		print("Reading in Logs from ", endpointUrl)
		test = get_data_from_ES(endpointUrl,index,service,max_entries, time_span)

		print(len(test['hits']['hits']), "logs loaded from the last", time_span ," seconds")


		print("Preprocessing logs")

		new_D = json_normalize(test['hits']['hits'])

		for lines in range(len(new_D["_source.message"])):
			new_D["_source.message"][lines] = Clean(new_D["_source.message"][lines]) 

		new_D, nothing = Update_W2V_Models(mod,new_D)


		transforms = Transform_Text(mod,new_D)


		v = One_Vector(transforms)

		dist = []
		for i in v:
			dist.append(Get_Anomaly_Score(mapp,i))

		count = 0
		anom = []

		es = Elasticsearch(endpointUrl)
		for i in range(max_anoms):
		 	loc = np.argmax(dist)
		 	anom.append(loc)

		 	if dist[loc] > (threshold*maxx):
		 		#m_push = test['hits']['hits'][loc]['_source']['message'] 
		 		m_push = '0'
		 		print(dist[loc], test['hits']['hits'][loc]['_source']['message'], "\n")


		 		body_p = {"Message": m_push, "Anomaly_Score": dist[loc]}
		 		res = es.index(index = outpoint, doc_type="log", body=body_p)


		 	dist[loc] = 0

		#print(count)

		now = time.time()

		print("Analyzed one minute of data in ",(now-then)," seconds")

		print("waiting for next minute to start...", "\n", "press ctrl+c to stop process")


		time.sleep(60-(now-then))





if __name__ == "__main__":
    infer()
