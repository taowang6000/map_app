#!/usr/bin/env python3
import sys
from PIL import Image, ImageDraw
from lxml import etree


class Node:
	def __init__(self, node_id, lat, lon, intKey):
		self.id = node_id
		self.lat = lat
		self.lon = lon
		self.key = intKey

# "intKey_list" is a list of integer
class Way:
	def __init__(self, way_id, intKey_list):
		self.id = way_id
		self.intKeys = intKey_list

class Graph:
	def __init__(self, vertexCount):
		self.vertexCount = vertexCount
		self.a_list = dict.fromkeys(range(vertexCount))

	def addEdge(self, i, j):
		if (i >= 0) and (i <= self.vertexCount) and (j >= 0) and (j <= self.vertexCount):
			if self.a_list[i]:
				self.a_list[i].append(j)
			else:
				self.a_list[i] = [j]
			if self.a_list[j]:
				self.a_list[j].append(i)
			else:
				self.a_list[j] = [i]

	def removeEdge(self, i, j):
		if ((i >= 0) and (i <= self.vertexCount) and (j >= 0) and (j <= self.vertexCount)):
			if self.a_list[i]:
				self.a_list[i].remove(j)
				self.a_list[j].remove(i)

	def isEdge(self, i, j):
		if ((i >= 0) and (i <= self.vertexCount) and (j >= 0) and (j <= self.vertexCount)):
			return (j in self.a_list[i])
		else:
			return False

class OSM_Map:
	def __init__(self, osmFileName):
		self.doc = etree.parse(osmFileName)
		self.root = self.doc.getroot()

		# get the bounds value
		bounds = self.doc.xpath("/osm/bounds[1]")
		self.minlat = float(bounds[0].get("minlat"))
		self.minlon = float(bounds[0].get("minlon"))
		self.maxlat = float(bounds[0].get("maxlat"))
		self.maxlon = float(bounds[0].get("maxlon"))

		# get node value, put in dictionaries
		self.node_dict = {}
		self.node_name2int = {}
		i = 0
		for e in self.root.findall("node"):
			self.node_dict[i] = Node(e.get("id"), float(e.get("lat")), float(e.get("lon")), i)
			self.node_name2int[e.get("id")] = i
			i += 1

		#create a graph object
		self.highways = Graph(len(self.node_dict))

		#get highway value, put in dictionaries
		#setup highway networks through add edges to adjacency list
		self.way_dict = {}
		i = 0
		for w in self.root.findall("way"):
			for tag in w.findall("tag"):
				if (tag.get("k") == "highway"):
					int_list = []
					for nd in w.findall("nd"):
						int_list.append(self.node_name2int[nd.get("ref")])
					new_way = Way(w.get("id"), int_list)
					self.way_dict[i] = new_way
					assert len(int_list) > 1
					for j in range(len(int_list) - 1):
						self.highways.addEdge(int_list[j], int_list[j+1])
					i += 1
					break

	def route(self, start, end):
		start_point = str(start)
		end_point = str(end)
		# BFS path-finding algorithm
		Tree = dict.fromkeys(range(self.highways.vertexCount))
		Discoverd = dict.fromkeys(range(self.highways.vertexCount))
		Discoverd[self.node_name2int[start_point]] = True
		Layers = []
		this_layer = [self.node_name2int[start_point]]
		Layers.append(this_layer)
		self.target_find = False
		while Layers[-1] and not self.target_find:
			#print("processing new layer: ")
			next_layer = []
			for u in Layers[-1]:
				if self.highways.a_list[u]:
					for v in self.highways.a_list[u]:
						if Discoverd[v] != True:
							Discoverd[v] = True
							Tree[v] = u
							if v == self.node_name2int[end_point]:
								self.target_find = True
								break
							next_layer.append(v)
							#print("node {0} added to layer".format(v))
			Layers.append(next_layer)

		# print out the result
		self.path_list =[]
		if self.target_find:
			this_node = self.node_name2int[end_point]
			self.path_list.append(this_node)
			while Tree[this_node]:
				this_node = Tree[this_node]
				self.path_list.append(this_node)
			#print(self.path_list)
		else:
			print("Path not found")

	def save(self, filename):
		# draw all the highways
		size = (1000, 1000)
		im = Image.new("L", size, color = 255)
		draw = ImageDraw.Draw(im)
		lat_diff = self.maxlat - self.minlat
		lon_diff = self.maxlon - self.minlon
		for i in range(len(self.way_dict)):
			for j in range(len(self.way_dict[i].intKeys) - 1):
				start_lat = self.node_dict[self.way_dict[i].intKeys[j]].lat 
				start_lon = self.node_dict[self.way_dict[i].intKeys[j]].lon 
				end_lat = self.node_dict[self.way_dict[i].intKeys[j+1]].lat
				end_lon = self.node_dict[self.way_dict[i].intKeys[j+1]].lon
				x1 = int((start_lat - self.minlat) / lat_diff * 1000)
				y1 = int((start_lon - self.minlon) / lon_diff * 1000)
				x2 = int((end_lat - self.minlat) / lat_diff * 1000)
				y2 = int((end_lon - self.minlon) / lon_diff * 1000)
				draw.line((x1, y1, x2, y2), fill = 150)

		# highlight the selected way
		if self.target_find:
			if self.path_list:
				for i in range(len(self.path_list) - 1):
					start_lat = self.node_dict[self.path_list[i]].lat 
					start_lon = self.node_dict[self.path_list[i]].lon 
					end_lat = self.node_dict[self.path_list[i+1]].lat 
					end_lon = self.node_dict[self.path_list[i+1]].lon 
					x1 = int((start_lat - self.minlat) / lat_diff * 1000)
					y1 = int((start_lon - self.minlon) / lon_diff * 1000)
					x2 = int((end_lat - self.minlat) / lat_diff * 1000)
					y2 = int((end_lon - self.minlon) / lon_diff * 1000)
					draw.line((x1, y1, x2, y2), fill = 50, width = 4)
		del draw
		im.show()
		im.save(filename, format = "PPM")


if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("Correct command: mypath.py source_point destination_point map_file output_file")
		sys.exit()    
	map = OSM_Map(sys.argv[3])
	map.route(sys.argv[1], sys.argv[2])
	map.save(sys.argv[4])
	














