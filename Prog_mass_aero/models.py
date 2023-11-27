import numpy as np


# COEFFICIENT DRAG DUE TO LIFT MODELS

def cxi_druot(cz, width, spe_wing):
    """
Model Thierry Druot, marilib
    :param cz:
    :param width:
    :param spe_wing:
    :return:
    """
    span, aspect_ratio, sweep = spe_wing
    ki_wing = (1.05 + (width / span) ** 2) / (np.pi * aspect_ratio)  # ???????????????????
    return ki_wing * cz ** 2  # Induced drag


def cxi_basic_model(cz, spe_wing):
    """
trouvé sur internet
    :param cz:
    :param spe_wing:
    :return:
    """
    span, aspect_ratio, sweep = spe_wing
    e = 0.8  # valeur moyenne trouvée sur internet
    return cz ** 2 / (np.pi * aspect_ratio * e)


# From fundamentals of aircraft and airship design, Leland M. Nicolai and Grant E. Carichner, volume 1-Aircraft design, p.332-333
def cxi_model_1(cz, width, spe_wing):
    span, aspect_ratio, sweep = spe_wing
    e_prime = 0.98  # lecture des graphiques p.333
    e = e_prime * (1 - (width / span) ** 2)
    return cz ** 2 / (np.pi * aspect_ratio * e)


# From Aircraft design, Daniel P. Raymer, sixth edidion, p.444
def cxi_model_2(cz, spe_wing):
    span, aspect_ratio, sweep = spe_wing
    if sweep <= 30:
        e_straight = 1.78 * (1 - 0.045 * aspect_ratio ** 0.68) - 0.64
        e_sweep = 4.61 * (1 - 0.045 * aspect_ratio ** 0.68) * np.cos(sweep * np.pi / 180) ** 0.15 - 3.1
        # interpolation linéaire entre e_straight et e_sweep
        e = e_straight * (30 - sweep) / 30 + e_sweep * sweep / 30
    else:
        e_sweep = 4.61 * (1 - 0.045 * aspect_ratio ** 0.68) * np.cos(sweep * np.pi / 180) ** 0.15 - 3.1
        e = e_sweep
    return cz ** 2 / (np.pi * aspect_ratio * e)


def cxi_model_3(cz, mach, spe_wing):
    span, aspect_ratio, sweep = spe_wing
    beta = np.sqrt(1 - mach ** 2)

    # From fundamentals of aircraft and airship design, Leland M. Nicolai and Grant E. Carichner, volume 1-Aircraft design, p.46
    cz_alpha_w = 2 * np.pi * aspect_ratio / (2 + np.sqrt(4 + aspect_ratio ** 2 * beta ** 2 * (1 + (np.tan(sweep * np.pi / 180) / beta) ** 2)))

    # From Airplane design Part VI : Preliminary calculation of aerodynamic, trust and power characteristics, Dr. Jan Roskam, 2008, p.27
    R = 0.9
    cz_w = 1.05 * cz
    e = 1.1 * (cz_alpha_w / aspect_ratio) / (R * (cz_alpha_w / aspect_ratio) + np.pi * (1 - R))
    return cz_w ** 2 / (np.pi * aspect_ratio * e)


# -----------------------------------------------------------------------------------------------------------------------
# MODELS OF SKIN FRICTION DRAG COEFFICIENT OF WING (turbulent flow : re > 5*10**5)

def cxf_druot_model(mach, re, width, spe_wing):
    """
Model Thierry Druot
    :param mach:
    :param re:
    :param width:
    :param spe_wing:
    :return:
    """
    if re == 0:
        return 0
    wing_area, root_c, sweep, thickchord = spe_wing
    frm_wing = 1.4
    ael = wing_area
    nwa = wing_area - width * root_c
    fac = (1. + 0.126 * mach ** 2)
    return frm_wing * 0.455 / (fac * np.log10(re * ael) ** 2.58) * (nwa / wing_area)


# From fundamentals of aircraft and airship design, Leland M. Nicolai and Grant E. Carichner, volume 1-Aircraft design, p.52
def cxf_model_1(mach, re, width, spe_wing):
    if re == 0:
        return 0
    wing_area, root_c, sweep, thickchord = spe_wing
    nwa = wing_area - width * root_c
    ael = mach
    Cf = 0.455 / (np.log10(re * ael) ** 2.58)
    return Cf * nwa / wing_area


# From Aircraft design, Daniel P. Raymer, sixth edidion, p.417, 422, 425
def cxf_model_2(mach, re, width, spe_wing):
    if re == 0:
        return 0
    wing_area, root_c, sweep, thickchord = spe_wing
    nwa = wing_area - width * root_c
    ael = wing_area
    Cf = 0.455 / (np.log10(re * ael) ** 2.58 * (1 + 0.144 * mach ** 2) ** 0.65)
    x_c = 0.3
    FF = (1 + (0.6 / x_c) * thickchord + 100 * thickchord ** 4) * (1.34 * mach ** 0.18 * np.cos(sweep * np.pi / 180) ** 0.28)
    Q = 1
    return Cf * FF * Q * nwa / wing_area


if __name__ == "__main__":
    pass
