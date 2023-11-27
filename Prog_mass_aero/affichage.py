from explorateur_models import Explorateur
from Prog_data_frame.mass_aero_dataframe import *
import models
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os


class HangarVsp3:
    def __init__(self, path_dossier):
        self.path_dossier = path_dossier
        self.listeAvions = list()
        self.listeGroupes = list()
        listePaths = list()
        self.listeNames = list()
        for element in os.listdir(self.path_dossier):  # parcourt l'ensemble des elements dans le dossier demandé
            sousDossier = os.path.join(self.path_dossier, element)
            if os.path.isdir(sousDossier):  # vérifie que ce soit un dossier et non un fichier
                for dossier_groupe in os.listdir(sousDossier):
                    self.listeGroupes.append(dossier_groupe[7:9])  # récupère le num de groupe sur le nom du
                    # dossier
                    for (repertoire, sousRepertoire, fichiers) in os.walk(os.path.join(sousDossier, dossier_groupe)):
                        # os.walk : parcourt le dossier et tous ses sous dossiers en donnant le chemin relatif
                        # du dossier traité, la liste des sous dossiers et les fichiers présents
                        for fichier in fichiers:
                            if ".vsp3" in fichier:
                                self.listeNames.append(fichier[:-5])
                                listePaths.append(os.path.join(repertoire, fichier))  # grâce à os.join récupère
                                # le chemin relatif depuis le tout premier dossier ("IENAC17")
                                self.listeAvions.append(element)  # la liste récupère le sous dossier dans IENAC17
        self.listeInstances = [Explorateur(path) for path in listePaths]  # crée une instance pour chaque fichier
        self.listeFuselage = [instance.fuselage() for instance in self.listeInstances]
        self.listeWing = [instance.wing()[0] for instance in self.listeInstances]
        self.listeHorz = [instance.horz()[0] for instance in self.listeInstances]
        self.listeVert = [instance.vert()[0] for instance in self.listeInstances]
        self.index = [self.listeAvions[i][6] + self.listeGroupes[i] for i in range(len(self.listeAvions))]  # Numéro du groupe précédé de la première lettre du dossier : d pour "dimensionné", e pour "existant"
        self.indice_oaci = 30
        self.data_excel = pd.read_excel("C:/Users/adric/Desktop/Stage/caracteristiques_techniques.xltx")

    def data_mass(self):  # Data frame des masses des différents composants de l'avion avec comme indices les numoéros de groupe.
        global_spe = list()
        for i in range(len(self.listeInstances)):
            avion = self.listeInstances[i]
            wing = self.listeWing[i]
            spe_wing = [avion.get_span(wing), avion.get_aspect_ratio(wing), avion.get_area(wing), avion.get_sweep(wing)] + avion.get_thickchords(wing)[:3]
            global_spe.append(spe_wing)
        # Crée une liste avec les informations du dossier dimensionné
        liste_cabin_mass = list()
        liste_fuse_mass = list()
        liste_wing_mass = list()
        liste_horz_mass = list()
        liste_vert_mass = list()
        liste_engines_mass = list()
        liste_lg_mass = list()
        liste_system_mass = list()
        for i in range(len(h.listeNames)):
            for index, row in h.data_excel.iterrows():
                if row["GEN_Code_OACI_Avion"] == h.listeNames[i]:
                    liste_cabin_mass.append(cabin_mass(row["GEN_Max_PAX"], row["FUS_Cabin_Length_m"]))
                    liste_fuse_mass.append(fuselage_mass(row["FUS_Length_m"], self.listeInstances[i].fuselage_diameter(self.listeFuselage[i])))
                    liste_wing_mass.append(wing_mass(global_spe[i], row["MAS_MTOM_kg"], row["MAS_MZFM_kg"]))
                    liste_horz_mass.append(horz_mass(row["HTP_Surface_m2"]))
                    liste_vert_mass.append(vert_mass(row["VTP_Surface_m2"]))
                    liste_engines_mass.append(engines_mass(row["ENG_Number"], row["ENG_Max_Thrust_kN"]))
                    liste_lg_mass.append(lg_mass(row["MAS_MTOM_kg"], row["MAS_MLM_kg"]))
                    liste_system_mass.append(system_mass(row["MAS_MTOM_kg"]))
        return pd.DataFrame({"fuse_mass": liste_fuse_mass,
                             "cabin_mass": liste_cabin_mass,
                             "wing_mass": liste_wing_mass,
                             "horz_mass": liste_horz_mass,
                             "vert_mass": liste_vert_mass,
                             "engines_mass": liste_engines_mass,
                             "Lg_mass": liste_lg_mass,
                             "system": liste_system_mass})

    def get_fd_cx_lod(self, indice, mach=0.82, cz=0.5):
        avion = self.listeInstances[indice]
        wing = self.listeWing[indice]
        length = avion.length
        width = avion.fuselage_diameter(self.listeFuselage[indice])[1]
        moteurs = avion.get_moteurs()
        nacelles = list()
        for element in moteurs:
            nb = avion.nb_moteurs(element)
            d_nacelle = avion.diameter(element)
            l_nacelle = avion.length_moteur(element)
            for k in range(nb):
                nacelles.append([l_nacelle, d_nacelle])
        spe_wing = [avion.get_span(wing), avion.get_aspect_ratio(wing), avion.get_area(wing), avion.get_root_chord(wing), avion.get_mac(wing)]
        horz_area = avion.get_area(self.listeHorz[indice])
        vert_area = avion.get_area(self.listeVert[indice])
        if indice >= self.indice_oaci:
            altp = self.data_excel.PER_Cruise_Altitude.m[indice]
            cruise_mach = self.data_excel.PER_Mach_Cruise
            wing_ref = self.data_excel.WIN_Ref_Surface_m2
        else:
            altp = 8000
            cruise_mach = 0.82
            wing_ref = avion.get_area(indice)
        fd, cx, lod = fd_cx_lod([length, width], nacelles, spe_wing, horz_area, vert_area, wing_ref, altp, cruise_mach, mach=mach, cz=cz)
        return fd, cx, lod

    def cx_mach(self, indice):  # graphique cx en fonction du mach de vol pour cz fixé
        x = np.linspace(0.1, 0.9, 50)
        plt.figure()  # Create a figure
        for i in range(12, 1, -1):
            y = [self.get_fd_cx_lod(indice, mach=point, cz=i / 10)[1] for point in x]
            plt.plot(x, y, label=f"cz={i / 10}")
        plt.xlabel("mach")
        plt.ylabel("cx")
        plt.title("coefficient de trainée en fonction du mac pour différente valeur de coefficient de portance")
        plt.legend()
        plt.show()

    def data_cx_mach(self, liste_mach=None):  # dataframe de cx en fonction de différents machs pour une altitude donnée
        if liste_mach is None:
            liste_mach = [0.7, 0.8, 0.85, 0.9]
        assert type(liste_mach) == list
        liste_colonne = list()
        for mach in liste_mach:
            liste_cx = list()
            for i in range(len(self.listeInstances)):
                fd, cx, lod = self.get_fd_cx_lod(i, mach=mach)
                liste_cx.append(cx)
            liste_colonne.append(liste_cx)
        return pd.DataFrame({f"mach={liste_mach[i]}": pd.Series(liste_colonne[i], index=[self.listeAvions[i][6] + self.listeGroupes[i] for i in range(len(self.listeAvions))]) for i in range(len(liste_colonne))})

    def get_cz(self, indice, mach=0.82, altp=8000):
        avion = self.listeInstances[indice]
        wing = self.listeWing[indice]
        moteurs = avion.get_moteurs()
        liste = list()
        total_moteurs = 0
        for element in moteurs:
            nb = avion.nb_moteurs(element)
            total_moteurs += nb
            diametre = avion.diameter(element)
            longueur = avion.length_moteur(element)
            for i in range(nb):
                liste.append([longueur, diametre])
        spe_wing = [avion.get_span(wing), avion.get_aspect_ratio(wing), avion.get_area(wing), avion.get_sweep(wing)] + avion.get_thickchords(wing)[:3]
        total_mass = fuselage_mass(avion.length, avion.fuselage_diameter(self.listeFuselage[indice])) \
                     + wing_mass(spe_wing, 0, 0, cz_max_ld=1.2) \
                     + horz_mass(avion.get_area(self.listeHorz[indice])) \
                     + vert_mass(avion.get_area(self.listeVert[indice])) \
                     + engines_mass(total_moteurs, 35000)
        pamb, tamb, g = atmosphere_g(altp)
        gam = gas_data()[1]
        return (2 * total_mass * g) / (gam * avion.get_area(self.listeWing[indice]) * pamb * (mach ** 2))

    def cz_cx(self, indice):
        plt.figure()  # Create a figure
        cz = np.linspace(0, 1.2, 20)
        mach = [0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.82, 0.84, 0.86, 0.88, 0.9]
        for m in mach:
            cx = [self.get_fd_cx_lod(indice, mach=m, cz=ccz)[1] for ccz in cz]
            plt.plot(cx, cz, label=f"mach={m}")
        plt.xlabel("cx")
        plt.ylabel("cz")
        plt.title("coefficient de trainée en fonction du mac pour différente valeur de coefficient de portance")
        plt.legend()
        plt.show()

    def data_cz(self, liste_mach=None, altp=8000):
        if liste_mach is None:
            liste_mach = [0.7, 0.8, 0.85, 0.9]
        return pd.DataFrame({f"mach={liste_mach[i]}": [self.get_cz(j, liste_mach[i], altp) for j in range(len(self.listeInstances))] for i in range(len(liste_mach))})

    def models_cxi_graphique(self, indice, sweep=None, aspect_ratio=None):
        avion = self.listeInstances[indice]
        wing = self.listeWing[indice]
        width = avion.fuselage_diameter(self.listeFuselage[indice])[1]
        if not(sweep is None) and not(aspect_ratio is None):
            span = avion.get_span(wing)
            spe_wing = [span, aspect_ratio, sweep]
        else:
            sweep = avion.get_sweep(wing)
            aspect_ratio = avion.get_aspect_ratio(wing)
            span = avion.get_span(wing)
            spe_wing = [span, aspect_ratio, sweep]
        cz = np.linspace(0, 1.2, 50)
        plt.figure()
        plt.plot(cz, [models.cxi_druot(point, width, spe_wing) for point in cz], label="druot_model")
        plt.plot(cz, [models.cxi_basic_model(point, spe_wing) for point in cz], label="model_e=0.8")
        plt.plot(cz, [models.cxi_model_1(point, width, spe_wing) for point in cz], label="model_1")
        plt.plot(cz, [models.cxi_model_2(point, spe_wing) for point in cz], label="model_2")
        plt.plot(cz, [models.cxi_model_3(point, 0, spe_wing) for point in cz], label="model_3_0", linestyle="--")
        plt.plot(cz, [models.cxi_model_3(point, 0.9, spe_wing) for point in cz], label="model_3_0.9", linestyle="--")
        plt.xlabel("cz")
        plt.ylabel("cxi")
        plt.title(f"coefficient de trainée induite en fonction du cz pour 4 models différents\n flèche : {sweep}, allongement : {aspect_ratio}")
        plt.legend()
        plt.show()

    def models_cxf_graphique(self, indice):
        avion = self.listeInstances[indice]
        wing = self.listeWing[indice]
        width = avion.fuselage_diameter(self.listeFuselage[indice])[1]
        spe_wing = [avion.get_area(wing), avion.get_root_chord(wing), avion.get_sweep(wing), avion.get_thickchords(wing)[3]]
        pamb, tamb, g = atmosphere_g(8000)
        mach = np.linspace(0, 0.9, 20)
        plt.figure()
        plt.plot(mach, [models.cxf_druot_model(point, reynolds_number(pamb, tamb, point), width, spe_wing) for point in mach], label="druot_model")
        plt.plot(mach, [models.cxf_model_1(point, reynolds_number(pamb, tamb, point), width, spe_wing) for point in mach], label="model_1")
        plt.plot(mach, [models.cxf_model_2(point, reynolds_number(pamb, tamb, point), width, spe_wing) for point in mach], label="model_2")
        plt.xlabel("mach")
        plt.ylabel("cxf_wing")
        plt.title(f"coefficient de trainée de frottement en fonction du mach des ailes avec re > 10 ** 5")
        plt.legend()
        plt.show()


if __name__ == "__main__":
    path_dossier = input("- Pour copier le chemin d'accès d'un dossier : click droit --> Copier en tant que chemin d'accès\nChemin d'accès du dossier IENAC :")
    if path_dossier[0] == "\"":  # Pour enlever les guillements autour du chemin d'accès
        path_dossier = path_dossier[1:-1]
    h = HangarVsp3(path_dossier)
    h.models_cxf_graphique(9)
