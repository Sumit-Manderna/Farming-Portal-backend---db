from flask import Flask, request, jsonify,  make_response
from flask_cors import CORS
from py2neo import Graph, Node, Relationship
from pprint import pprint
import json
import glob
import csv
import requests
from collections import OrderedDict

app = Flask(__name__)
CORS(app)

@app.route('/makeKG', methods=['GET'])
def createDataGraph():
    # return "Hello, World!"
    setFilePath()
    data = "Node graph created successfully"
    response = make_response(jsonify(data))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/recommend', methods=['POST'])
def recommendCrop():
    # return "Hello, World!"
    requestData = request.get_json()
    data = scriptForRecommendation(requestData)
    # data = {'message': 'Hello, World!'}
    response = make_response(jsonify(data))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/diseasesList', methods=['POST'])
def getDiseaseList():
    # return "Hello, World!"
    requestData = request.get_json()
    print(requestData)
    data = show_disease_list(requestData['crop'])
    # data = {'message': 'Hello, World!'}

    response = make_response(jsonify(data))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/diseaseManagement', methods=['POST'])
def getRemedies():
    # return "Hello, World!"
    requestData = request.get_json()
    print(requestData)
    data = getRemediesList(requestData)
    # data = {'message': 'Hello, World!'}

    response = make_response(jsonify(data))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/diseaseSymptoms', methods=['POST'])
def getSymptoms():
    # return "Hello, World!"
    requestData = request.get_json()
    print(requestData)
    data = getSymptomsList(requestData)
    # data = {'message': 'Hello, World!'}

    response = make_response(jsonify(data))
    response.headers['Content-Type'] = 'application/json'
    return response

# 
# 
# 
# 
# program to make the graph in the neo4j 
# 
# 
# 
# 

def MAKE_KG(filename):
	graph = Graph("bolt://localhost:7687",auth = ("neo4j" , "12345678"))
	#cypher = graph.cypher


	#filename = input("Enter json_data_file path : ")
	#filename = 'output_kg_wheat.json'

	data_dict = {}
	with open(filename, 'r') as f:
		data_dict = json.load(f)


	for superkey, supervalue in data_dict.items(): # superkey is crop_name
		crop_name = superkey
		crop_node = Node("Crop", name=crop_name)
		graph.create(crop_node)
		print("\n")
		print("created a node with name " + crop_name)
		print("\n")
		for key,value in supervalue.items():
			if(key == "diseases"):
				key_node = Node(key, name = key)
				graph.create(key_node)
				graph.create(Relationship(crop_node, "may_suffer_from", key_node))
				print("created a node with name " + key + " and connected to crop_node")
				for disease_name in value: # value is of list type here
					for k,v in disease_name.items(): # k is disease name here and v in dict with keys: symptom, management
						k_node = Node(k, name = k)
						graph.create(k_node)
						graph.create(Relationship(key_node, "which_may_be", k_node))
						print("created a node with name " + k + " and connected to disease_node")
						for k1,v1 in v.items(): # k1 is symptom or management
							k1_node = Node(k1, name=k1, descrp=v1)
							graph.create(k1_node)
							graph.create(Relationship(k_node, "about_disease", k1_node))
							print("created a node with name " + k1 + " and connected to " + k + " named node")

			elif(key == "postProductionTechnique"):
				key_node = Node(key, name = key, descrp = value)
				graph.create(key_node)
				graph.create(Relationship(crop_node, "has_PPT", key_node))
				print("create_node with name " + key + " and connect to crop_node")

			elif(key == "pestManagement"):
				key_node = Node(key, name = key)
				graph.create(key_node)
				graph.create(Relationship(crop_node, "has_pestManagement", key_node))
				for k,v in value.items():
					k_node = Node(k, name=k, descrp=v)
					graph.create(k_node)
					graph.create(Relationship(key_node, "about_pestManagement", k_node))
					print("created a node with name " + k + " and connected to " + key + " named node")

			elif(key=="CropGrownIn" or key=="climateRequirement" or key=="soilRequirement" or key=="totalGrowingPeriod"):
				descriptions = value.split(',')
				queryInitial = "MATCH(n) WHERE n.name="
				queryMiddle = " and n.descrp="
				queryEnd = " RETURN n"
				qry = "MATCH(n) WHERE n.name={b} and n.descrp={a} RETURN n"
				for i in descriptions:
					#res = cypher.execute(qry,a=i,b=key)
					#qry = queryInitial + key + queryMiddle + i + queryEnd
					key_node = Node( key , name= key , descrp= i )
					try:
						res = graph.run(queryInitial + "'" + key + "'" + queryMiddle + "'" + i + "'" + queryEnd)
						#print("yha hui h" + len(res))
					except:
						graph.create(key_node)
					#if(len(res) == 0): # if node doesn't exists create it
					#	key_node = Node(key, name=key, descrp=i)
					#	graph.create(key_node)
					#else:
					#	key_node = res[0].n
					graph.create(Relationship(crop_node, "requires", key_node))
					#graph.create(Relationship(key_node, "favours", crop_node))
					print("created a node with name "+key+" and connected to crop_node having descrp = "+i)

			elif(key=="waterRequirement" or key=="rainfallRequirement" or key=="temperatureRequirement"):
				descriptions = value.split(' to ')
				if(descriptions[0]=="NA"):
					descriptions = ['0','0']
				qry = "MATCH(n) WHERE n.name={b} and n.descrp={a} RETURN n"
				key_node = Node("min" + key , name="min" + key , descrp= descriptions[0])
				try:
					res1 = graph.run(queryInitial + "'min" + key + "'" +  queryMiddle +  "'" + descriptions[0] +  "'" + queryEnd)
				except:
					graph.create(key_node)
				#if(len(res1)==0):
				#	nm = "min"+key
				#	key_node = Node(nm, name=nm, descrp=descriptions[0])
				#	graph.create(key_node)
				#else:
				#	key_node = res1[0].n
				graph.create(Relationship(crop_node, "requires", key_node))
				#graph.create(Relationship(key_node, "favours", crop_node))
				print("created a node with name "+"min"+key+" and connected to crop_node having descrp = "+descriptions[0])
				key_node = Node("max" + key , name="max" + key , descrp= descriptions[1])
				try:
					res2 = graph.run(queryInitial + "'max" + key +  "'" + queryMiddle +  "'"+ descriptions[1] +  "'" + queryEnd)
				except:
					graph.create(key_node)
				#if(len(res2)==0):
				#	nm = "max"+key
				#	key_node = Node(nm, name=nm, descrp=descriptions[1])
				#	graph.create(key_node)
				#else:
				#	key_node = res2[0].n
				graph.create(Relationship(crop_node, "requires", key_node))
				#graph.create(Relationship(key_node, "favours", crop_node))
				print("created a node with name "+"max"+key+" and connected to crop_node having descrp = "+descriptions[1])

			else:
				key_node = Node(key, name=key, descrp=value)
				graph.create(key_node)
				graph.create(Relationship(crop_node, "has", key_node))
				print("created a node with name " + key +" and connected to crop_node")


def setFilePath():
	directory = "C:/Users/Sumit Manderna/Downloads/FarmingAdvisoryPortal-master/create_graph/json_graphs"
	print("data folder path : ", directory)
	files = glob.glob(directory+"/*.json")
	for filename in files:
		MAKE_KG(filename)  
    # return "Hello from Python!"

# 
# 
# 
# program to  recommendCrop in the basis of given intput by the user
# 
# 
# 

def initialise_votes(graph, vote):
    qry = "MATCH(n:Crop) RETURN n"
    res = graph.run(qry).data()
    for i in range(len(res)):
        crop_name = res[i]['n']['name']
        vote[crop_name] = 0.0
    print("\nVotes_initialized")

def show_climate_req(graph):
    qry = "MATCH(n:climateRequirement) RETURN n"
    res = graph.run(qry).data()
    conditions = []
    for i in range(len(res)):
        conditions.append(res[i]['n']['descrp'])
    print(conditions)


def show_soil_req(graph):
    qry = "MATCH(n:soilRequirement) RETURN n"
    res = graph.run(qry).data()
    conditions = []
    for i in range(len(res)):
        conditions.append(res[i]['n']['descrp'])
    print(conditions)


# for state, climate and soil based votes
# name : condition name
# type : climate/soil/states
def UpdateVote1(graph, name, vote_prior, type, vote):
    qry = "MATCH(n2:Crop)-[r:requires]->(n) WHERE n.name='" + type + "' and n.descrp='" + name + "' RETURN n2"
    res = graph.run(qry).data()
    if(type=="CropGrownIn"):
        q = "MATCH(n2:Crop)-[r:requires]->(n) WHERE n.descrp='" + name + "' RETURN n2"
        name = "ALL_INDIAN_STATES"
        r = graph.run(q).data()
        for i in range(len(r)):
            vote[r[i]['n2']['name']] += vote_prior
    for i in range(len(res)):
        crop_name = res[i]['n2']['name']
        vote[crop_name] += vote_prior



# for rainfall, temperature
# type : rain/temp
# req : temp in C or rainfall in cm
def UpdateVote2(graph, vote_prior, type, vote, req):
    qry = "MATCH(n2:Crop)-[r:requires]->(n) WHERE n.name={a} RETURN n,n2"
    res_min = graph.run("MATCH(n2:Crop)-[r:requires]->(n) WHERE n.name='min"+type+"' RETURN n,n2").data()
    res_max = graph.run("MATCH(n2:Crop)-[r:requires]->(n) WHERE n.name='max"+type+"' RETURN n,n2").data()
    if(len(res_min) != len(res_max)):
        print("\nSOME ERROR OCCURED!!! >>>>> length mismatched\n")

    else:
        for i in range(len(res_min)):
            min_req = int(res_min[i]['n']['descrp'])
            max_req = int(res_max[i]['n']['descrp'])
            if(req>=(min_req-5) and req<=(max_req+5)):
                crop_name = res_min[i]['n2']['name'] # same as res_max[i].n2['name']
                vote[crop_name] += vote_prior/2
            if(req>=min_req and req<=max_req):
                crop_name = res_min[i]['n2']['name'] # same as res_max[i].n2['name']
                vote[crop_name] += vote_prior/2


def scriptForRecommendation(requestData):

    API_key = requestData['city']
    print(requestData)

    graph = Graph("bolt://localhost:7687",auth = ("neo4j" , "12345678"))

    vote = {} # dict containing votes for each crop e.g. "wheat":3
    state_vote = 3.0
    climate_vote1 = 1.5
    climate_vote2 = 1.0
    soil_vote1 = 1.5
    soil_vote2 = 1.0
    temp_vote = 1.2
    rain_vote = 1.0

    initialise_votes(graph, vote)

    states_SF = {}
    states_FF = {}

    with open('indian_states.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            states_SF[row[1]] = row[2]
            states_FF[row[2]] = row[1]

    print("states_name : ")
    for k,v in states_SF.items():
        print(k,end=', ')


    print("\n")
    state_name = requestData['state']
    state_name = states_SF[state_name]
    UpdateVote1(graph, state_name, state_vote, "CropGrownIn",vote)
    #print("\n")
    district_name = requestData['city']
    print('\n')
    #print("votes : ", vote)
    #print("\n")

    print("Possible climatic conditions : ")
    show_climate_req(graph)
    print("\nYou can select two options from the list\n")
    climate_cnd1 = requestData['climate']
    climate_cnd2 = requestData['climate']
    print("\n")
    UpdateVote1(graph, climate_cnd1, climate_vote1, "climateRequirement", vote)
    UpdateVote1(graph, climate_cnd2, climate_vote2, "climateRequirement", vote)
    #print("votes : ", vote)
    #print("\n")

    print("Possible soil conditions : ")
    show_soil_req(graph)
    print("\nYou can select two options from the list\n")
    soil_cnd1 = requestData['soil']
    soil_cnd2 = requestData['soil']
    print("\n")
    UpdateVote1(graph, soil_cnd1, soil_vote1, "soilRequirement", vote)
    UpdateVote1(graph, soil_cnd2, soil_vote2, "soilRequirement", vote)
    #print("votes : ", vote)
    #print("\n")


    temp_ip = '30'
    try:
        url = 'http://api.openweathermap.org/data/2.5/weather?q='+district_name+',IN&APPID='+ API_key
        r = requests.get(url)
        a = r.json()
        if(a['cod'] == '404'):
            url = 'http://api.openweathermap.org/data/2.5/weather?q='+states_FF[state_name]+',IN&APPID='+API_key
            r = requests.get(url)
            a = r.json()
        tp = a['main']
        temp_ip = str(int(tp['temp']) - 273)
    except:
        temp_ip = '28'

    if(temp_ip != '28'):
        print("Today's temperature in C : ", temp_ip)
    temp_ip = requestData['temperature']
    req = int(temp_ip)
    UpdateVote2(graph, temp_vote, "temperatureRequirement", vote, req)
    #print("\n")
    #print("votes : ", vote)
    #print("\n")


    rain_ip = requestData['rainfall']
    req = int(rain_ip)
    UpdateVote2(graph, rain_vote, "rainfallRequirement", vote, req)
    print("\n")
    #print("votes : ", vote)
    #print("\n")


    print("Final_votes :")
    final_vote = OrderedDict(sorted(vote.items(), key=lambda item: item[1],reverse=True))
    for i in final_vote:
        print(i + " : " + str(round(final_vote[i],1)))
    print("Higher votes recommended\n")
    return final_vote	



# 
# 
# 
# program to get Remedies of the various decised found in the crop in the basis of given intput by the user
# 
# 
# 
def show_disease_list(crop_name):
    graph = Graph("bolt://localhost:7687",auth = ("neo4j" , "12345678"))
    result = graph.run("MATCH(n1:Crop) - [r1:may_suffer_from] -> (n2) - [r2:which_may_be] -> (n3) WHERE n1.name='" + crop_name + "' RETURN n3").data()
    disease_list = []
    for i in range(len(result)):
        disease_list.append(str(result[i]['n3']['name']))

    print("disease names : ")
    print(disease_list)
    return disease_list



def getRemediesList(requestData):
    graph = Graph("bolt://localhost:7687",auth = ("neo4j" , "12345678"))
    #graph = graph.graph

    crop_name = requestData['crop']
    
    disease_name = requestData['disease']

    # query1 = "MATCH(n1:Crop) - [r1:may_suffer_from] -> (n2) - [r2:which_may_be] -> (n3) - [r3:about_disease] -> (n4:symptom) WHERE n1.name='" + crop_name + "' and n3.name='" + disease_name + "' RETURN n4"
    query2 = "MATCH(n1:Crop) - [r1:may_suffer_from] -> (n2) - [r2:which_may_be] -> (n3) - [r3:about_disease] -> (n4:management) WHERE n1.name='" + crop_name + "' and n3.name='" + disease_name + "' RETURN n4"
    # result1 = graph.run(query1).data()
    result2 = graph.run(query2).data()

   
    Manage_list = result2[0]['n4']['descrp'].split('::')
    print("Management(s) : ")
    for i in range(len(Manage_list)):
        print(">>> ", Manage_list[i])
    return Manage_list


def getSymptomsList(requestData):
    graph = Graph("bolt://localhost:7687",auth = ("neo4j" , "12345678"))
    #graph = graph.graph

    crop_name = requestData['crop']
    
    disease_name = requestData['disease']

    query1 = "MATCH(n1:Crop) - [r1:may_suffer_from] -> (n2) - [r2:which_may_be] -> (n3) - [r3:about_disease] -> (n4:symptom) WHERE n1.name='" + crop_name + "' and n3.name='" + disease_name + "' RETURN n4"
    query2 = "MATCH(n1:Crop) - [r1:may_suffer_from] -> (n2) - [r2:which_may_be] -> (n3) - [r3:about_disease] -> (n4:management) WHERE n1.name='" + crop_name + "' and n3.name='" + disease_name + "' RETURN n4"
    result1 = graph.run(query1).data()
    result2 = graph.run(query2).data()
    symptomList =  result1[0]['n4']['descrp']
    
    print("\n")
    print("Symptom(s) : ", result1[0]['n4']['descrp'])
    print("\n")
    return symptomList


if __name__ == '__main__':
    app.run(debug=True,port=8000)
