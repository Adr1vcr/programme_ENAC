import jaro


def converti(x):  # Converti les chaines de caractères qui correspondent à des valeurs en écriture exponentielle en nombre relatif
    nb = float(x[:6])
    exp = ""
    for i in range(len(x) - 1, 0, -1):
        exp = x[i] + exp
        if x[i] == "-" or x[i] == "+":
            break
    return nb * (10 ** int(exp))


def score_jaro(c1, c2, limite):
    score = jaro.jaro_metric(c1.lower(), c2.lower())
    return score > limite


if __name__ == "__main__":
    print(converti("2.500000000000000000e-01"))
