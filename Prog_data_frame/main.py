from hangar_vsp3 import HangarVsp3
import os
import pickle

reponse = input("Encoder ou lire une dataframe, w ou r :")

path_dossier = ""
while not os.path.isdir(path_dossier):  # Boucle while pour vérifier que le chemin d'accès est correcte et mène à un dossier
    # Pour copier le chemin d'accès d'un fichier : click droit --> "Copier en tant que chemin d'accès"
    path_dossier = input("- Pour copier le chemin d'accès d'un dossier : click droit --> Copier en tant que chemin d'accès\nChemin d'accès du dossier IENAC :")
    if path_dossier[0] == "\"":  # Pour enlever les guillements autour du chemin d'accès
        path_dossier = path_dossier[1:-1]
    if os.path.isdir(path_dossier):
        path = True
    else:
        print("--------------------------------------------\nERREUR DANS LE CHEMIN D'ACCES :\n", path_dossier)
if reponse == "w":
    # Crée ou ouvre le fichier et y code en binaire la data frame complet obtenue
    output = open(os.path.join(f"{path_dossier}/", "DataFrame.pickle"), "wb")
    pickle.dump(HangarVsp3(path_dossier).data_total(), output)
    output.close()

# Ouvre et décode le fichier ".pickle" contenant la dataframe
Input = open(os.path.join(f"{path_dossier}/", "DataFrame.pickle"), "rb")
df = pickle.load(Input)
Input.close()
