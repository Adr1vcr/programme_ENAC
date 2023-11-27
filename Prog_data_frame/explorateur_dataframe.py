from fonctions_dataframe import converti, score_jaro
import xml.etree.ElementTree as et
import pandas as pd
import jaro


class Explorateur:  # Classe qui contient toutes les méthodes pour le traitement et l'extraction de données des
    # fichiers .vsp3
    def __init__(self, path):
        self.vehicle = et.parse(path).getroot().find("Vehicle")  # enregistre le chemin d'accès au dossier contenant
        # toutes les informations sur la modélisation
        self.composants = [i for i in range(len(self.vehicle.findall("Geom")))]
        self.indice_fuse = 0
        self.length = 0
        self.span = 0

    def fuselage(self):  # Détermine l'indice de la balise "Geom" correspondant à celui du fuselage de l'avion
        n = 0
        length = dict()
        for i in range(len(self.vehicle.findall("Geom"))):
            Type = self.vehicle.findall("Geom")[i].find("GeomBase").find("TypeName").text
            if Type in ["Fuselage", "Pod", "TransportFuse"]:
                n += 1
                length[i] = converti(self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length").attrib["Value"])
            elif Type == "Custom":
                if not (self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length") is None):
                    n += 1
                    length[i] = converti(
                        self.vehicle.findall("Geom")[i].find("ParmContainer").find("Design").find("Length").attrib[
                            "Value"])
        if n > 0:
            s_length = pd.Series([length[key] for key in length], index=length.keys())
            self.length = s_length.max()
            self.composants.remove(int(s_length.idxmax()))
            self.indice_fuse = s_length.idxmax()
            return s_length.idxmax()
        return None

    def fuselage_diameters(self, indice):  # À partir de l'indice de la balise du fuselage, trouve certaines spécificités du fuselage
        if indice is None:
            return [None for i in range(3)]
        TypeName = self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text
        if TypeName == "Fuselage":
            l_Height = []
            l_Width = []
            l_diameter = []
            for i in range(1, len(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec"))):
                if not(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Width") is None):
                    l_Height.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Height").attrib["Value"]))
                    l_Width.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Ellipse_Width").attrib["Value"]))
                elif not(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Width") is None):
                    l_Height.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Height").attrib["Value"]))
                    l_Width.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Width").attrib["Value"]))
                elif not (self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Circle_Diameter") is None):
                    l_diameter.append(converti(self.vehicle.findall("Geom")[indice].find("FuselageGeom").find("XSecSurf").findall("XSec")[i].find("XSec").find("XSecCurve").find("ParmContainer").find("XSecCurve").find("Circle_Diameter").attrib["Value"]))
            if len(l_Height) > 0 and len(l_Width) > 0:
                return [(max(l_Height), max(l_Width)), [(l_Height[i], l_Width[i]) for i in range(len(l_Height))]]
            elif len(l_diameter) > 0:
                return [(max(l_diameter), max(l_diameter)), [l_diameter[i] for i in range(len(l_diameter))]]
        elif TypeName == "Custom" or "TransportFuse":
            Diameter = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Diameter").attrib["Value"])
            return [(Diameter, Diameter), [Diameter]]
        return [None, None]

    def wing(self):  # Détermine l'indice de la balise "Geom" correspondant à celui des ailes de l'avion
        span = dict()
        for indice in self.composants:
            if self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text == "Wing":
                span[indice] = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find(
                    "TotalSpan").attrib["Value"])
        s_span = pd.Series([span[key] for key in span], index=span.keys())
        self.composants.remove(int(s_span.idxmax()))
        self.span = s_span.max()
        return s_span.idxmax()

    def vert(self):
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
            self.composants.remove(int(s_vert.idxmax()))
            return s_vert.idxmax()
        return None

    def horz(self):
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
            self.composants.remove(int(s_horz.idxmax()))
            return s_horz.idxmax()
        return None

    def get_id(self, indice):
        if indice is None:
            return None
        return self.vehicle.findall("Geom")[indice].find("ParmContainer").find("ID").text

    def get_total_span(self, indice):
        if indice is None:
            return None
        # Prend en compte l'écart entre les ailes ("Y_Location") qui n'est pas pris en compte dans le calcul du span sur openvsp
        return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalSpan").attrib["Value"]) + 2 * converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("Y_Location").attrib["Value"])

    def get_area(self, indice):
        if indice is None:
            return None
        return converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("WingGeom").find("TotalArea").attrib["Value"])

    def get_aspect_ratio(self, indice):
        if indice is None:
            return None
        return self.get_total_span(indice) ** 2 / self.get_area(indice)

    def get_x_location(self, indice):
        if indice is None:
            return None
        # Position des ailes par rapport au fuselage
        X_loc_abs_fuse = converti(self.vehicle.findall("Geom")[self.indice_fuse].find("ParmContainer").find("XForm").find("X_Location").attrib["Value"])
        X_loc_abs_wing = converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("XForm").find("X_Location").attrib["Value"])
        return X_loc_abs_wing - X_loc_abs_fuse

    def get_twist(self, indice):
        if indice is None:
            return None
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        return converti(X_sec[0].find("ParmContainer").find("XSec").find("Twist").attrib["Value"])

    def get_sweeps(self, indice):
        if indice is None:
            return None, None, None
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        sweeps_par_sec = [converti(X_sec[i].find("ParmContainer").find("XSec").find("Sweep").attrib["Value"]) for i in range(1, len(X_sec))]
        sweep_loc = [converti(X_sec[i].find("ParmContainer").find("XSec").find("Sweep_Location").attrib["Value"]) for i in range(1, len(X_sec))]
        return pd.Series(sweeps_par_sec, index=[i + 1 for i in range(len(sweeps_par_sec))]).mean(), sweep_loc, sweeps_par_sec

    def get_dihedrals(self, indice):
        if indice is None:
            return None, None, None
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        dihedrals_par_sec = [converti(X_sec[i].find("ParmContainer").find("XSec").find("Dihedral").attrib["Value"]) for i in range(1, len(X_sec))]
        return pd.Series(dihedrals_par_sec, index=[i + 1 for i in range(len(dihedrals_par_sec))]).mean(), dihedrals_par_sec

    def get_chords(self, indice):
        if indice is None:
            return None, None, None
        X_sec = self.vehicle.findall("Geom")[indice].find("WingGeom").find("XSecSurf").findall("XSec")
        root_chord = converti(X_sec[1].find("ParmContainer").find("XSec").find("Root_Chord").attrib["Value"])
        i = 1
        # Trouve la dernière section de l'aile horz winglet s'il y en a
        while i + 1 < len(X_sec) and converti(X_sec[len(X_sec) - i].find("ParmContainer").find("XSec").find("Dihedral").attrib["Value"]) > 30:
            i += 1
        tip_chord = converti(X_sec[len(X_sec) - i].find("ParmContainer").find("XSec").find("Tip_Chord").attrib["Value"])
        taper = tip_chord / root_chord
        return root_chord, tip_chord, taper

    def get_thickchords(self, indice):
        if indice is None:
            return None, None, None
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
        return [thickchords[0], thickchords[k], thickchords[-1]]

    def names(self, verif):  # Vérifie la concordance des noms des composants avec ceux demandés
        recap = [None for i in range(len(verif))]
        for i in range(len(verif)):
            scores = pd.Series([jaro.jaro_metric(geom.find("ParmContainer").find("Name").text.lower(), verif[i]) for
                                geom in
                                self.vehicle.findall("Geom")])
            recap[i] = scores.max()
        return recap

    def name_moteur(self, liste):  # Trouve si les moteurs de l'avion ont le bon nom
        l_indice = list()
        l_engine = [("Nacelle", 0.9), ("moteurs", 0.819), ("reacteurs", 0.8), ("Duct", 0.9), ]
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
            if abs(Y_loc) < self.span//2:  # Retient que les éléments qui sont à moins d'une envergure d'aile du fuselage.
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
            return [self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Name").text for indice in moteurs_indice]
        return [None]

    def max_xsec_diameter(self, indice):
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

    def max_design_diameter(self, indice):  # Height/Width = diameter
        if not (self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Height") is None):
            return max(converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Height").attrib["Value"]),
                       converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Width").attrib["Value"]))
        elif not (self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Diameter") is None):
            return converti(self.vehicle.findall("Geom")[indice].find("CustomGeom").find("Diameter").attrib["Value"])
        else:
            return 0

    def diameter(self, indice):
        TypeName = self.vehicle.findall("Geom")[indice].find("GeomBase").find("TypeName").text
        if TypeName == "Fuselage" or TypeName == "Stack":
            return self.max_xsec_diameter(indice)
        elif TypeName == "Custom" or TypeName == "Duct":
            return self.max_design_diameter(indice)
        elif TypeName == "Ellipsoid":
            # B Radius : radius of the ellipsoid along y, C Radius : radius of ellipsoid along z
            return 2 * max(converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("B_Radius").attrib["Value"]),
                           converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("B_Radius").attrib["Value"]))
        elif TypeName == "Pod":
            # FineRatio = Length / radius
            return 2 * converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("Length").attrib["Value"]) / converti(self.vehicle.findall("Geom")[indice].find("ParmContainer").find("Design").find("FineRatio").attrib["Value"])


if __name__ == "__main__":
    e = Explorateur("../IENAC17/Avion dimensionné/Equipe 28-GROLL Jean-Baptiste_120455_assignsubmission_file_/A320.vsp3")
