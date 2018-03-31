import numpy as np
from data_reader import DataReader
from pathlib import Path
import pickle
from sklearn.preprocessing import MinMaxScaler
from multiprocessing.pool import ThreadPool
import itertools
from similarity import similarity
from timing_wrapper import timeit
from time import time
import line_profiler
from load_sim_matrix import load_similarity_matrix
from scipy.cluster.hierarchy import dendrogram
import matplotlib.pyplot as plt
import copy


class DivisiveClustering:
	def __init__(self):
		self.clusters={}
		self.sim_matrix=None
		self.mapping=None
		self.no_clusters=0
		self.linkage_matrix=None
		self.n=None
		self.i=None
		self.hierarchical_clusters={}
		self.last_index=None
		self.iters=1

	def initialize(self):
		self.n=len(self.mapping)
		self.last_index=2*self.n-2
		self.i=0
		self.clusters[self.last_index]=list(self.mapping.keys())
		self.linkage_matrix=np.zeros([self.n-1, 4])

	def splinter(self):
		cluster_diameters={k:(len(v)<1)*(-1)+(len(v)>1)*np.max(np.max(self.sim_matrix[np.ix_(v,v)], axis=1)) for k,v in self.clusters.items()}
		max_diameter_cluster=max(cluster_diameters, key=cluster_diameters.get)
		avg_within_cluster_distances={pt:np.mean(self.sim_matrix[:, pt]) for pt in self.clusters[max_diameter_cluster]}
		splinter_element=max(avg_within_cluster_distances, key=avg_within_cluster_distances.get)
		# self.clusters[max_diameter_cluster].remove(splinter_element)
		self.no_clusters+=1
		# self.clusters[self.no_clusters]=[splinter_element]
		return splinter_element, max_diameter_cluster

	def reassign(self, splinter_element, orig_cluster_key):
		# Create temp clusters
		temp_new_cluster=[splinter_element]
		self.clusters[orig_cluster_key].remove(splinter_element)
		temp_orig_cluster=self.clusters[orig_cluster_key]

		# Remove orig cluster from cluster dict
		del self.clusters[orig_cluster_key]

		# Calculate distances
		within_cluster_dist={pt:np.mean(np.delete(self.sim_matrix[:, pt], (pt, splinter_element))) for pt in temp_orig_cluster}
		dist_to_splinter={pt:self.sim_matrix[pt, splinter_element]  for pt in temp_orig_cluster}
		dist_diff={pt:(within_cluster_dist[pt] - dist_to_splinter[pt]) for pt in temp_orig_cluster} # if +ve, move to splinter
		
		# Reassign points
		for pt in temp_orig_cluster:
			if dist_diff[pt]>0 and len(temp_orig_cluster)>1:
				temp_new_cluster.append(pt)
				temp_orig_cluster.remove(pt)

		# Add temp clusters to cluster dict

		if len(temp_orig_cluster)==1:
			# print(temp_orig_cluster[0])
			self.clusters[temp_orig_cluster[0]]=temp_orig_cluster
			orig_cluster_key=temp_orig_cluster[0]
		else:
			# print(self.last_index)
			self.clusters[self.last_index]=temp_orig_cluster
			orig_cluster_key=self.last_index
			self.last_index-=1

		if len(temp_new_cluster)==1:
			self.clusters[temp_new_cluster[0]]=temp_new_cluster
			new_cluster_key=temp_new_cluster[0]
		else:
			self.clusters[self.last_index]=temp_new_cluster
			new_cluster_key=self.last_index
			self.last_index-=1

		# Append to hierarchical clusters
		self.hierarchical_clusters['iter_'+str(self.no_clusters)]=copy.deepcopy(self.clusters)

		# Make the linkage function
		# temp_print=2*self.n-self.no_clusters
		# print(orig_cluster_key, new_cluster_key, temp_print, orig_cluster_key>temp_print or new_cluster_key>temp_print )#, 2*self.n-1-self.no_clusters in self.clusters.keys())
		self.make_linkage_function(new_cluster_key, orig_cluster_key, 0, len(temp_new_cluster))


	def make_linkage_function(self, cluster_1, cluster_2, dist, len_cluster_2):
		# print(cluster_1, cluster_2, dist, len_cluster_2)
		self.linkage_matrix[self.n-self.no_clusters-1, 0]=cluster_2
		self.linkage_matrix[self.n-self.no_clusters-1, 1]=cluster_1
		self.linkage_matrix[self.n-self.no_clusters-1, 2]=dist
		self.linkage_matrix[self.n-self.no_clusters-1, 3]=len_cluster_2
		print(self.linkage_matrix[self.n-self.no_clusters-1, :])

	def termination(self):
		for k, v in self.clusters.items():
			if len(v)>1:
				return 0
		return 1

	def fit(self, sim_matrix, mapping):
		self.sim_matrix=sim_matrix
		self.mapping=mapping
		self.initialize()
		while not self.termination():
			splinter_element, orig_cluster_key=self.splinter()
			self.reassign(splinter_element, orig_cluster_key)
			# print(self.iters)
			self.iters+=1
		print('Clustering done!')

	def create_dendrogram(self):
		np.savetxt('temp_matrix', self.linkage_matrix)
		fig=plt.figure()
		#self.linkage_matrix=self.linkage_matrix[self.linkage_matrix[:,3].argsort()]
		print(self.linkage_matrix)
		dendrogram(self.linkage_matrix, orientation='top')
		plt.show()
		fig.savefig('dendrogram.png')

@timeit
def read_data():
	dataDict={}
	rawData=None
	with open('data/data.txt', 'r') as f:
		rawData=f.read()
	dataSegments = rawData.split('>')
	for segment in dataSegments:
		try:
			lines = segment.split('\n', 1)
			dataDict[lines[0]] = lines[1].replace('\n', '')
		except:
			pass
	mapping={ind:k for ind, k in enumerate(dataDict.keys())}
	return dataDict, mapping

if __name__=='__main__':
	data, mapping=read_data()
	sim_matrix=np.random.random(size=[311,311])#load_similarity_matrix(data, mapping)

	model=DivisiveClustering()
	model.fit(sim_matrix, mapping)
	# print(model.hierarchical_clusters)
	model.create_dendrogram()