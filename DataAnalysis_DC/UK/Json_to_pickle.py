## Create an adapted dataset, for portability, converted the JSON file into pickle. 
# Best to directly use csv.

import json

import re

import pickle
import copy
with open("C:\\Users\\andre\\UniMelb\\ukpn-data-centre-demand-profiles.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)


# Data:
n_DC = 96
dict_default = {'utc_timestamp': [], 'hh_utilisation_ratio': [] , 'cleansed_voltage_level' : [] }
def rassembler_parDC(dataDC):
    i = 0
    data_parDC = [copy.deepcopy(dict_default) for _ in range(n_DC)]

    pat = r"\d+"  # match digits
    for elt in dataDC:
        i+=1
        numero_DC = re.search(pat, elt['anonymised_data_centre_name'])
        numero_DC = int(numero_DC.group()) -1 
        for key in ['utc_timestamp','hh_utilisation_ratio', 'cleansed_voltage_level' ]: # Une liste donnee par exemple utc timestamp ne sera a priori pas ordonnee, tant pis tant qua il y a bine la correspondance temps - valeur
            # print(elt[key])
            data_parDC[numero_DC][key].append(elt[key])
        if len(data_parDC[numero_DC]) ==3 :
            data_parDC[numero_DC]['dc_type'] = elt['dc_type']
    return data_parDC


with open("ukpn-data-centre-demand-profiles-perDC.pkl", "wb") as f:
    pickle.dump(rassembler_parDC(dataset), f)
