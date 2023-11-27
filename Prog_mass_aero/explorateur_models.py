from fonctions_models import converti, score_jaro
import xml.etree.ElementTree as et
import pandas as pd
import jaro


class Explorateur:  # Classe qui contient toutes les méthodes pour le traitement et l'extraction de données des
    # fichiers .vsp3
    def __init__(self, path):
        super().__init__()
        self.vehicle = et.parse(path).getroot().find("Vehicle")  # enregistre le chemin d'accès au dossier contenant
        # toutes les informations sur la modélisation
        self.composants = [i for i in range(len(self.vehicle.findall("Geom")))]
        self.id_fuselage = 0
        self.length = 0
        self.span = 0

    def fuselage(self):  # Détermine l'indice de la balise "Geom" correspondant à celui du fuselage de l'avion
        n = 0
        lengths = list()
        indices = list()
        for i in range(len(self.vehicle.findall("Geom"))):
            Type = self.vehicle.findall("Geom")[i].find("GeomBase").find("TypeName").text
            if Type in ["Fuselage", "Pod", "TransportFuse"]:
                n += 1
                indices.append(i)
                lengths.append(converti(self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length").attrib["Value"]))
            elif Type == "Custom":
                if not (self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length") is None):
                    n += 1
                    indices.append(i)
                    lengths.append(converti(
                        self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length").attrib[
                            "Value"]))
        if n > 0:
            s_length = pd.Series(lengths, index=indices)
            self.length = s_length.max()
            self.id_fuselage = int(s_length.idxmax())
            self.composants.remove(int(s_length.idxmax()))
            return s_length.idxmax()
        return None

    def fuselage_diameter(self, indice):  # Trouve l'indice du fuselage dans la liste des balises "Geom"
        TypeName = self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text
        if TypeName == "Fuselage":
            l_Height = []
            l_Width = []
            l_diameter = []
            for i in range(1, len(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec"))):
                if not (self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Width") is None):
                    l_Height.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Height").attrib["Value"]))
                    l_Width.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Width").attrib["Value"]))
                elif not (self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Width") is None):
                    l_Height.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Height").attrib["Value"]))
                    l_Width.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Width").attrib["Value"]))
                elif not (self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Circle_Diameter") is None):
                    l_diameter.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Circle_Diameter").attrib["Value"]))
            if len(l_Height) > 0 and len(l_Width) > 0:
                return [max(l_Height), max(l_Width)]
            elif len(l_diameter) > 0:
                return [max(l_diameter) for i in range(2)]  # retourne [Height_max, Width_max]
        elif TypeName == "Custom" or "TransportFuse":
            return [converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Diameter").attrib["Value"]) for i in range(2)]  # retourne [Diameter, Diameter]

    def wing(self):  # Détermine l'indice de la balise "Geom" correspondant à celui des ailes de l'avion
        span = dict()
        for indice in self.composants:
            if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text == "Wing":
                span[indice] = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find(
                    "TotalSpan").attrib["Value"])
        s_span = pd.Series([span[key] for key in span], index=span.keys())
        indice = int(s_span.idxmax())
        self.composants.remove(indice)
        self.span = s_span.max()
        return [indice, self.vehicle.findall("Geom")[indice].find("ParmContainer").find("ID").text]

    def vert(self):  # Trouve l'indice de l'empennage vertical
        Xloc = dict()
        for indice in self.composants:
            if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text == "Wing":
                angle = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find(
                    "X_Rotation").attrib["Value"])
                dihedral = converti(self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")[1].find(
                    "ParmContainer").find("XSec").find("Dihedral").attrib["Value"])
                if angle + dihedral == 90:
                    Xloc[indice] = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find(
                        "X_Location").attrib["Value"])
        if len(Xloc) > 0:
            s_vert = pd.Series([Xloc[key] for key in Xloc], index=Xloc.keys())
            indice = int(s_vert.idxmax())
            self.composants.remove(indice)
            return [indice, self.vehicle.findall("Geom")[indice].find("ParmContainer").find("ID").text]
        return [None, None]

    def horz(self):  # Trouve l'indice de l'empennage horizontal

        Xloc = dict()
        for indice in self.composants:
            if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text == "Wing":
                angle = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find(
                    "X_Rotation").attrib["Value"])
                dihedral = converti(self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")[1].find(
                    "ParmContainer").find("XSec").find("Dihedral").attrib["Value"])
                if angle + dihedral < 30:
                    Xloc[indice] = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find(
                        "X_Location").attrib["Value"])
        if len(Xloc) > 0:
            s_horz = pd.Series([Xloc[key] for key in Xloc], index=Xloc.keys())
            indice = int(s_horz.idxmax())
            self.composants.remove(indice)
            return [indice, self.vehicle.findall("Geom")[indice].find("ParmContainer").find("ID").text]
        return [None, None]

    def get_span(self, indice):
        Y_loc = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("Y_Location").attrib["Value"])
        span = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalSpan").attrib["Value"]) + 2 * Y_loc
        return span

    def get_aspect_ratio(self, indice):
        Y_loc = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("Y_Location").attrib["Value"])
        span = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalSpan").attrib["Value"]) + 2 * Y_loc
        area = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalArea").attrib["Value"])
        return span ** 2 / area

    def get_area(self, indice):
        if indice is None:
            return 0
        return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalArea").attrib["Value"])

    def get_root_chord(self, indice):  # Pour trouver la corde à l'emplanture de l'avion
        return converti(self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")[0].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("ThickChord").attrib["Value"])

    def get_sweep(self, indice):
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        sweeps = list()
        for i in range(len(X_sec)):
            sweeps.append(converti(X_sec[i].find("ParmContainer").find("XSec").find("Sweep").attrib["Value"]))
        return pd.Series(sweeps).mean()

    def get_thickchords(self, indice):
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        sweep_prec = 0
        k = 0
        for i in range(len(X_sec)):
            sweep = converti(X_sec[i].find("ParmContainer").find("XSec").find("Sweep").attrib["Value"])
            if i > 1 and k == 0 and sweep != sweep_prec:
                k = i
            sweep_prec = sweep
        thickchords = list()
        for i in range(len(X_sec)):
            thickchords.append(converti(X_sec[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("ThickChord").attrib["Value"]))
        return [thickchords[0], thickchords[k], thickchords[-1], max(thickchords)]

    def get_mac(self, indice):
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        s_corde = pd.Series([converti(self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("ThickChord").attrib["Value"]) for i in range(len(X_sec))])
        return s_corde.mean()

    def names(self, verif):  # Vérifie la concordance des noms des composants avec ceux demandés
        recap = [None for i in range(len(verif))]
        for i in range(len(verif)):
            scores = pd.Series([jaro.jaro_metric(geom.find("ParmContainer").find("Name").text.lower(), verif[i]) for
                                geom in self.vehicle.findall("Geom")])
            recap[i] = scores.max()
        return recap

    def name_moteur(self, liste):  # Trouve si les moteurs de l'avion ont le bon nom
        l_indice = list()
        l_engine = [("moteurs", 0.819), ("reacteurs", 0.8), ("duct", 0.9), ("nacelle", 0.9)]
        i = 0
        while i < len(l_engine) and len(l_indice) == 0:  # Compare les composants avec une suite de noms de moteurs du plus au moins pertinent dès qu'une correspodance est trouvé la boucle s'arrète.
            for indice in liste:
                if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text != "Wing":
                    if score_jaro(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Name").text, l_engine[i][0], l_engine[i][1]):
                        l_indice.append(indice)
            i += 1
        return l_indice

    def position(self):  # Renvoie une 2 listes : les composants à l'avant et les composants à l'arriere de l'avion
        avant = []
        arriere = []
        for indice in self.composants:
            X_loc = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("X_Location").attrib["Value"])
            Y_loc = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("Y_Location").attrib["Value"])
            if abs(Y_loc) < self.span // 2:  # Retient que les éléments qui sont à moins d'une envergure d'aile du fuselage.
                if X_loc < self.length * 4 / 5:  # Sépare l'avion au 4/5 de la longueur du fuselage pour distinguer des moteurs de réacteurs.
                    avant.append(indice)
                else:
                    arriere.append(indice)
        return [avant, arriere]

    def get_moteurs(self):  # Détermine les moteurs de l'avion parmi les composants restant. Nécessite au moins l'appel des méthodes fuselage() et wing() avant.
        moteurs_indice = []
        for liste in self.position():  # Itère les étapes suivantes pour les composants à l'avant et à l'arriere de l'avion
            if len(self.name_moteur(liste)) > 0:
                moteurs_indice.extend(self.name_moteur(liste))
                continue  # Si la méthode trouve des composants avec les bons noms pas besoin de faire les étapes qui suivent.
            liste_indice = list()
            liste_diameter_moteurs = list()
            for indice in liste:  # Détermine pour chaque composant s'il contient des paramètres liés au diamètre ou à la hauteur et largeur d'un cerlce ou d'une ellipse.
                if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text != "Wing":
                    liste_indice.append(indice)
                    liste_diameter_moteurs.append(self.diameter(indice))
            if len(liste_diameter_moteurs) > 0:
                s_liste_moteurs = pd.Series(liste_diameter_moteurs, index=liste_indice)
                moteurs_indice.extend([liste_indice[i] for i in range(len(liste_indice)) if liste_diameter_moteurs[i] == s_liste_moteurs.max()])  # Ne retiens les composants avec la plus grande longueur identique.
        if len(moteurs_indice) > 0:
            return moteurs_indice
        return [None]

    def max_xsec_diameter(self, indice):  # Détermine le diametre max dans un composant qui a plusieurs valeurs par section
        l_diameter = []
        for i in range(1, len(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec"))):
            TypeCurve = int(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("XSecCurve").find("Type").text)
            if TypeCurve == 1:  # 1 -> Circle
                # Circle_Diameter = diameter of the circle
                l_diameter.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Circle_Diameter").attrib["Value"]))
            elif TypeCurve == 2:  # 2 -> Ellipse
                l_diameter.append(max(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Width").attrib["Value"]),
                                      converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Height").attrib["Value"])))
            elif TypeCurve == 6:  # 6 -> Fuse_File
                # Height/Width = diameter
                l_diameter.append(max(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Width").attrib["Value"]),
                                      converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Height").attrib["Value"])))
        if len(l_diameter) > 0:
            return max(l_diameter)
        return 0

    def max_design_diameter(self, indice):  # Renvoie le diamètre d'un composant qui n'a qu'une seule section.
        # Height/Width = diameter
        if not(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Height") is None):
            return max(converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Height").attrib["Value"]),
                       converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Width").attrib["Value"]))
        elif not(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Diameter") is None):
            return converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Diameter").attrib["Value"])
        else:
            return 0

    def diameter(self, indice):  # Détermine le diamètre d'un composant en fonction de son type de géométrie
        TypeName = self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text
        if TypeName == "Fuselage" or TypeName == "Stack":
            return self.max_xsec_diameter(indice)
        elif TypeName == "Custom" or TypeName == "Duct":
            return self.max_design_diameter(indice)
        elif TypeName == "Ellipsoid":
            # B Radius : rayon de l'ellipsoide selon Y, C Radius : rayon de l'ellipsoide selon Z
            return 2 * max(converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("B_Radius").attrib["Value"]),
                           converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("B_Radius").attrib["Value"]))
        elif TypeName == "Pod":
            # FineRatio = Length / radius
            return 2 * converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Length").attrib["Value"]) / converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("FineRatio").attrib["Value"])

    def nb_moteurs(self, indice):  # Détermine si le composant correspond à un moteur ou 2 (présence de symétrie)
        sym = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Sym").find("Sym_Planar_Flag").attrib["Value"])  # 0 : aucune symétrie. 2 : symétrie selon le plan XZ
        if sym >= 1:
            return 2
        else:
            return 1

    def length_moteur(self, indice):  # Détermine la longueur d'un moteur
        TypeName = self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text
        if TypeName == "Fuselage":
            return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Length").attrib["Value"])
        elif TypeName == "Stack":
            length = 0
            for i in range(1, len(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec"))):  # Boucle pour les composants avec des longueurs d'une section à une autre et non globale.
                delta = converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("ParmContainer").find("XSec").find("XDelta").attrib["Value"])
                if delta > 0:
                    length += delta
            return length
        elif TypeName == "Custom":
            return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Chord").attrib["Value"])
        elif TypeName == "Duct":
            return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Chord").attrib["Value"])
        elif TypeName == "Ellipsoid":
            return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("A_Radius").attrib["Value"])
        elif TypeName == "Pod":
            return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Length").attrib["Value"])


if __name__ == "__main__":
    pass
