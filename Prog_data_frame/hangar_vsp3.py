from models_dataframe import cxi_druot, cxi_model_1, cxi_model_2, cxi_model_3
from explorateur_dataframe import Explorateur
from fonctions_dataframe import score_jaro
from mass_aero_dataframe import *
import pandas as pd
import jaro
import os


class HangarVsp3:
    def __init__(self, path_dossier):
        self.path_dossier = path_dossier
        self.listePaths = []
        self.listeGroupes = []
        self.listeAvions = []
        self.listeNames = []
        for element in os.listdir(self.path_dossier):  # parcourt l'ensemble des elements dans le dossier demandé
            sousDossier = os.path.join(self.path_dossier, element)
            if os.path.isdir(sousDossier):  # vérifie que ce soit un dossier et non un fichier
                for dossier_groupe in os.listdir(sousDossier):
                    self.listeGroupes.append(int(dossier_groupe[7:9]))  # récupère le num de groupe sur le nom du
                    # dossier
                    for (repertoire, sousRepertoire, fichiers) in os.walk(os.path.join(sousDossier, dossier_groupe)):
                        # os.walk : parcourt le dossier et tous ses sous dossiers en donnant le chemin relatif
                        # du dossier traité, la liste des sous dossiers et les fichiers présents
                        for fichier in fichiers:
                            if ".vsp3" in fichier:
                                self.listeNames.append(fichier[:-5].upper())  # récupère le nom de l'avion qui est celui du
                                # fichier
                                # sans l'extension
                                self.listePaths.append(os.path.join(repertoire, fichier))  # grâce à os.join récupère
                                # le chemin relatif depuis le tout premier dossier ("IENAC17")
                                self.listeAvions.append(element)  # la liste récupère le sous dossier dans IENAC17
        self.listeInstances = [Explorateur(path) for path in self.listePaths]  # crée une instance pour chaque fichier
        self.listeFuselage = [instance.fuselage() for instance in self.listeInstances]  # Récupère l'indice des fuselages de chaque avion
        self.listeWing = [instance.wing() for instance in self.listeInstances]
        self.listeHorz = [instance.horz() for instance in self.listeInstances]
        self.listeVert = [instance.vert() for instance in self.listeInstances]
        self.data_excel = pd.read_excel("C:/Users/adric/Desktop/Stage/caracteristiques_techniques.xltx", usecols="B:CD")
        self.data_excel = self.data_excel.drop_duplicates(subset="GEN_Code_OACI_Avion")  # supprimer les lignes dans la dataframe qui ont la même valeur

    def data_carateristiques(self):
        # Liste des caractéristiques qui vont être mise dans la dataframe pour les ailes, l'empennage horizontal et vertical
        listeSpeWingName = ["ID", "Span", "Xloc", "Twist", "Sweep", "Sweep_Loc", "Sweep/Sec", "Dihedral", "Dihedral/Sec", "Root_Chord", "Tip_Chord", "Taper", "Area", "ThickChords", "Aspect_Ratio"]

        liste_moteurs = list()
        for i in range(len(self.listeInstances)):
            if None in self.listeInstances[i].get_moteurs():
                liste_moteurs.append("Aucun")
            else:
                liste_moteurs.append(self.listeInstances[i].get_moteurs())

        # Création d'une data frame avec toutes les informations sur les fichiers et les avions modélisés
        return pd.DataFrame({"Paths": self.listePaths,
                             "Avions": self.listeAvions,
                             "Group": self.listeGroupes,
                             "Noms": self.listeNames,
                             "Instances": self.listeInstances,
                             "ID_Fuselage": [self.listeInstances[i].vehicle.findall("Geom")[self.listeFuselage[i]].find("ParmContainer").find("ID").text for i in range(len(self.listeInstances))],
                             "Length": [self.listeInstances[i].length for i in range(len(self.listeInstances))],
                             "D/(H,W)_max": [self.listeInstances[i].fuselage_diameters(self.listeFuselage[i])[0] for i in range(len(self.listeInstances))],
                             "D/(H,W) par section": [self.listeInstances[i].fuselage_diameters(self.listeFuselage[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[0] + "_Wing": [self.listeInstances[i].get_id(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[1] + "_Wing": [self.listeInstances[i].get_total_span(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[2] + "_Wing": [self.listeInstances[i].get_x_location(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[3] + "_Wing": [self.listeInstances[i].get_twist(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[4] + "_Wing": [self.listeInstances[i].get_sweeps(self.listeWing[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[5] + "_Wing": [self.listeInstances[i].get_sweeps(self.listeWing[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[6] + "_Wing": [self.listeInstances[i].get_sweeps(self.listeWing[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[7] + "_Wing": [self.listeInstances[i].get_dihedrals(self.listeWing[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[8] + "_Wing": [self.listeInstances[i].get_dihedrals(self.listeWing[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[9] + "_Wing": [self.listeInstances[i].get_chords(self.listeWing[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[10] + "_Wing": [self.listeInstances[i].get_chords(self.listeWing[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[11] + "_Wing": [self.listeInstances[i].get_chords(self.listeWing[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[12] + "_Wing": [self.listeInstances[i].get_area(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[13] + "_Wing": [self.listeInstances[i].get_thickchords(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[14] + "_Wing": [self.listeInstances[i].get_aspect_ratio(self.listeWing[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[0] + "_Horz": [self.listeInstances[i].get_id(self.listeHorz[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[1] + "_Horz": [self.listeInstances[i].get_total_span(self.listeHorz[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[2] + "_Horz": [self.listeInstances[i].get_x_location(self.listeHorz[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[3] + "_Horz": [self.listeInstances[i].get_twist(self.listeHorz[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[4] + "_Horz": [self.listeInstances[i].get_sweeps(self.listeHorz[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[5] + "_Horz": [self.listeInstances[i].get_sweeps(self.listeHorz[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[6] + "_Horz": [self.listeInstances[i].get_sweeps(self.listeHorz[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[7] + "_Horz": [self.listeInstances[i].get_dihedrals(self.listeHorz[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[8] + "_Horz": [self.listeInstances[i].get_dihedrals(self.listeHorz[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[9] + "_Horz": [self.listeInstances[i].get_chords(self.listeHorz[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[10] + "_Horz": [self.listeInstances[i].get_chords(self.listeHorz[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[11] + "_Horz": [self.listeInstances[i].get_chords(self.listeHorz[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[12] + "_Horz": [self.listeInstances[i].get_area(self.listeHorz[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[0] + "_Vert": [self.listeInstances[i].get_id(self.listeVert[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[1] + "_Vert": [self.listeInstances[i].get_total_span(self.listeVert[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[2] + "_Vert": [self.listeInstances[i].get_x_location(self.listeVert[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[3] + "_Vert": [self.listeInstances[i].get_twist(self.listeVert[i]) for i in range(len(self.listeInstances))],
                             listeSpeWingName[4] + "_Vert": [self.listeInstances[i].get_sweeps(self.listeVert[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[5] + "_Vert": [self.listeInstances[i].get_sweeps(self.listeVert[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[6] + "_Vert": [self.listeInstances[i].get_sweeps(self.listeVert[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[7] + "_Vert": [self.listeInstances[i].get_dihedrals(self.listeVert[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[8] + "_Vert": [self.listeInstances[i].get_dihedrals(self.listeVert[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[9] + "_Vert": [self.listeInstances[i].get_chords(self.listeVert[i])[0] for i in range(len(self.listeInstances))],
                             listeSpeWingName[10] + "_Vert": [self.listeInstances[i].get_chords(self.listeVert[i])[1] for i in range(len(self.listeInstances))],
                             listeSpeWingName[11] + "_Vert": [self.listeInstances[i].get_chords(self.listeVert[i])[2] for i in range(len(self.listeInstances))],
                             listeSpeWingName[12] + "_Vert": [self.listeInstances[i].get_area(self.listeVert[i]) for i in range(len(self.listeInstances))],
                             "ID_Engines": liste_moteurs
                             })

    def code_oaci(self):
        for i in range(len(self.listeNames)):
            for index, row in self.data_excel.iterrows():
                # Condition pour éviter les erreurs de majuscule ou de malécriture d'un code oaci par un étudiant
                if score_jaro(row["GEN_Code_OACI_Avion"].lower(), self.listeNames[i].lower(), 0.9):
                    self.listeNames[i] = row["GEN_Code_OACI_Avion"]

    def data_total(self):
        # remplace les noms d'avion des étudiants par le code oaci s'il y a une correspondance pour permettre la jointure des dataframes sans erreurs de noms
        self.code_oaci()

        self.data_excel.insert(0, "Excel", "|")  # Colonne pour la séparation entre les data frames (visuel)
        # Concaténation des caractéristiques récupérées sur openvsp et du fichier excel selon le code oaci de l'avion
        df_total = pd.merge(self.data_carateristiques(), self.data_excel, how="left", left_on="Noms", right_on="GEN_Code_OACI_Avion")
        df_total.drop(["GEN_Code_OACI_Avion"], axis=1, inplace=True)  # retire la colonne des codes OACI car correspond à la colonne "Noms" du data frame
        df_total.insert(len(df_total.columns), "Calcul_Mass/Aero", "|")  # Colonne pour la séparation entre les data frames (visuel)

        # Calcul la masse de chaque composant en utilisant les informations de chaque avion qui se trouvent sur une même ligne de la data frame
        df_total.insert(len(df_total.columns), "Cabin_Mass", pd.Series([cabin_mass(row["GEN_Max_PAX"], row["FUS_Cabin_Length_m"]) for indew, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Fuselage_Mass", pd.Series([fuselage_mass(row["FUS_Length_m"], row["D/(H,W)_max"]) for indew, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Wing_Mass", pd.Series([wing_mass([row["WIN_Span_m"], row["WIN_Aspect_Ratio"], row["WIN_Ref_Surface_m2"], row["Sweep_Wing"], row["ThickChords_Wing"]], row["MAS_MTOM_kg"], row["MAS_MZFM_kg"]) for index, row in  df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Horz_Mass", pd.Series([horz_mass(row["HTP_Surface_m2"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Vert_Mass", pd.Series([vert_mass(row["VTP_Surface_m2"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "LG_Mass", pd.Series([lg_mass(row["MAS_MTOM_kg"], row["MAS_MLM_kg"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "System_Mass", pd.Series([system_mass(row["MAS_MTOM_kg"]) for index, row in df_total.iterrows()]))

        # Calcul le coefficient de trainée induite selon 3 modèles, cf. "models_dataframe.py"
        df_total.insert(len(df_total.columns), "Cxi_Druot_Model", pd.Series([cxi_druot(0.55, row["D/(H,W)_max"][1], row["Span_Wing"], row["Aspect_Ratio_Wing"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Model_1", pd.Series([cxi_model_1(0.55, row["D/(H,W)_max"][1], row["Span_Wing"], row["Aspect_Ratio_Wing"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Model_2", pd.Series([cxi_model_2(0.55, row["Aspect_Ratio_Wing"], row["Sweep_Wing"]) for index, row in df_total.iterrows()]))
        df_total.insert(len(df_total.columns), "Model_3", pd.Series([cxi_model_3(0.55, 0.82, row["Aspect_Ratio_Wing"], row["Sweep_Wing"]) for index, row in df_total.iterrows()]))
        return df_total

    def data_similarity_name(self):
        jar = [instance.names(["fuselage", "aile", "empennage_vertical", "empennage_vertical"]) for instance in self.listeInstances]
        return pd.Series({"Same_name_fuse": [jar[j][0] for j in range(len(jar))],
                          "Same_name_wing": [jar[j][1] for j in range(len(jar))],
                          "Same_name_horz": [jar[j][2] for j in range(len(jar))],
                          "Same_name_vert": [jar[j][3] for j in range(len(jar))]})

    def jaro_score(self):
        l_sup = list()
        l_inf = list()
        for i in range(len(self.listeInstances)):
            for j in range(len(self.listeInstances[i].vehicle.findall("Geom"))):
                moteurs = jaro.jaro_metric(self.listeInstances[i].vehicle.findall("Geom")[j].find("ParmContainer").find("Name").text.lower(), "moteurs")
                duct = jaro.jaro_metric(self.listeInstances[i].vehicle.findall("Geom")[j].find("ParmContainer").find("Name").text.lower(), "duct")
                PowerFace = jaro.jaro_metric(self.listeInstances[i].vehicle.findall("Geom")[j].find("ParmContainer").find("Name").text.lower(), "powerface")
                reacteur = jaro.jaro_metric(self.listeInstances[i].vehicle.findall("Geom")[j].find("ParmContainer").find("Name").text.lower(), "reacteurs")
                name = self.listeInstances[i].vehicle.findall("Geom")[j].find("ParmContainer").find("Name").text
                if moteurs > 0.819 or duct > 0.9:
                    l_sup.append([name, self.listeGroupes[i], moteurs, duct, PowerFace, reacteur])
                elif PowerFace > 0.9 or reacteur > 0.85:
                    l_sup.append([name, self.listeGroupes[i], moteurs, duct, PowerFace, reacteur])
                else:
                    l_inf.append([name, self.listeGroupes[i], moteurs, duct, PowerFace, reacteur])
        data_sup = pd.DataFrame({"Noms": [l_sup[i][0] for i in range(len(l_sup))],
                                 "Groupe": [l_sup[i][1] for i in range(len(l_sup))],
                                 "score_moteurs": [l_sup[i][2] for i in range(len(l_sup))],
                                 "score_duct": [l_sup[i][3] for i in range(len(l_sup))],
                                 "score_powerface": [l_sup[i][4] for i in range(len(l_sup))],
                                 "score_reacteurs": [l_sup[i][5] for i in range(len(l_sup))]})
        data_inf = pd.DataFrame({"Noms": [l_inf[i][0] for i in range(len(l_inf))],
                                 "Groupe": [l_inf[i][1] for i in range(len(l_inf))],
                                 "score_moteurs": [l_inf[i][2] for i in range(len(l_inf))],
                                 "score_duct": [l_inf[i][3] for i in range(len(l_inf))],
                                 "score_powerface": [l_inf[i][4] for i in range(len(l_inf))],
                                 "score_reacteur": [l_inf[i][5] for i in range(len(l_inf))]})
        return data_inf, data_sup


if __name__ == "__main__":
    h = HangarVsp3("../IENAC17")
    total = h.data_total()

