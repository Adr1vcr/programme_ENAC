import xml.etree.ElementTree as et
import pandas as pd
import jaro
import os


class Verification:
    def __init__(self):
        self.vehicle = None
        self.parts = dict()
        self.file_name = ""
        self.path = False

    def find_all(self, name, liste_types):
        score = dict()
        for i in range(len(self.vehicle.findall("Geom"))):
            Name_composant = self.vehicle.findall("Geom")[i].find("ParmContainer").find("Name").text
            Type = self.vehicle.findall("Geom")[i].find("GeomBase").find("TypeName").text
            if Type in liste_types:
                if Name_composant.lower() == name.lower():
                    self.parts[name] = "ok"
                    return
                else:
                    score[i] = jaro.jaro_metric(Name_composant.lower(), name.lower())
        serie_score = pd.Series([score[key] for key in score], index=score.keys())
        score_max = serie_score.max()
        if score_max > 0.8:
            name_composant = self.vehicle.findall("Geom")[serie_score.idxmax()].find("ParmContainer").find("Name").text
            self.parts[name] = f"{name_composant} !!!"
        else:
            self.parts[name] = "INTROUVABLE"

    def find_engine(self, name, liste_types):
        score = dict()
        for i in range(len(self.vehicle.findall("Geom"))):
            Name_composant = self.vehicle.findall("Geom")[i].find("ParmContainer").find("Name").text
            Type = self.vehicle.findall("Geom")[i].find("GeomBase").find("TypeName").text
            if Type in liste_types:
                if len(Name_composant) > len(name) and Name_composant[:-1] == name:
                    self.parts[name] = "ok"
                    return
                else:
                    score[i] = jaro.jaro_metric(Name_composant.lower(), name.lower())
        serie_score = pd.Series([score[key] for key in score], index=score.keys())
        score_max = serie_score.max()
        if score_max > 0.8:
            name_composant = self.vehicle.findall("Geom")[serie_score.idxmax()].find("ParmContainer").find("Name").text
            self.parts[name] = f"{name_composant} !!!"
        else:
            self.parts[name] = "INTROUVABLES"

    def check_path(self):
        while not self.path:  # Boucle while pour vérifier que le chemin d'accès est correcte et mène à un fichier d'openvsp
            # Pour copier le chemin d'accès d'un fichier : click droit --> "Copier en tant que chemin d'accès"
            file_path = input("- Pour copier le chemin d'accès d'un fichier : click droit --> Copier en tant que chemin d'accès\nChemin d'accès jusqu'au projet OpenVsp :")
            if file_path[0] == "\"":  # Pour enlever les guillements autour du chemin d'accès
                file_path = file_path[1:-1]
            if file_path[-4:] == "vsp3":
                try:
                    with open(file_path):
                        self.path = True
                except IOError:
                    print("--------------------------------------------\nERREUR DANS LE CHEMIN D'ACCES DU FICHIER :\n", file_path)
            else:
                print("--------------------------------------------\nERREUR DANS L'EXTENSION DU FICHIER :\n", file_path)
        self.file_name = os.path.basename(file_path)[:-5]  # Récupère le nom du fichier à partir de son chemin d'accès et sans l'extension avec [:-5]
        self.vehicle = et.parse(file_path).getroot().find("Vehicle")

    def determine(self):
        self.check_path()
        self.find_all("Aile", ["Wing"])
        self.find_all("Fuselage", ["Fuselage", "Pod", "TransportFuse", "Custom"])
        self.find_all("Empennage_Horizontal", ["Wing"])
        self.find_all("Empennage_Vertical", ["Wing"])
        self.find_engine("Moteur_", ["Fuselage", "Pod", "TransportFuse", "Custom", "Stack"])

    def resume(self):
        print("\n-", self.file_name)
        for key in self.parts:
            print(key, ":", self.parts[key])
        print("\nSi un élément n'est pas ok, vérifier le nom du composant avec celui demandé ou le type de géométrie utilisé")
