import numpy as np


# MASS ESTIMATION


# Cabin
def cabin_mass(n_pax, design_range):
    m_furnishing = (0.063 * n_pax ** 2 + 9.76 * n_pax)  # Furnishings mass
    m_op_item = max(160., 5.2 * (n_pax * design_range * 1e-6))  # Operator items mass
    return m_furnishing + m_op_item


# Fuselage
def fuselage_mass(length, hw):  # hw = [height,wight]
    surface = length * np.sqrt(hw[0] * hw[1])
    return 5.80 * (np.pi * surface) ** 1.2  # Statistical regression versus fuselage built surface


# Wing
def wing_mass(liste, mtow, mzfw, cz_max_ld=1.2):  # liste = (span, area, aspect_ratio, sweep, root_toc, kink_toc, tip_toc)
    span, aspect_ratio, area, sweep, root_toc, kink_toc, tip_toc = liste
    A = 32 * area ** 1.1
    B = 4. * span ** 2 * np.sqrt(mtow * mzfw)
    C = 1.1e-6 * (1. + 2. * aspect_ratio) / (1. + aspect_ratio)
    D = (0.6 * root_toc + 0.3 * kink_toc + 0.1 * tip_toc) * (area / span)
    E = np.cos(sweep) ** 2
    F = 1200. * max(0., cz_max_ld - 1.8) ** 1.5
    return A + (B * C) / (D * E) + F  # Shevell formula + high lift device regression


# Horizontal tail
def horz_mass(area):
    return 22. * area


# Vertical tail
def vert_mass(area):
    if area is None:
        return 0
    return 25. * area


# Nacelle
def engines_mass(n_engine, engine_slst):
    engine_mass = (1250. + 0.021 * engine_slst)
    pylon_mass = (0.0031 * engine_slst)
    return (engine_mass + pylon_mass) * n_engine


# Landing gears
def lg_mass(mtow, mlw):
    return 0.015 * mtow ** 1.03 + 0.012 * mlw


# System
def system_mass(mtow):
    return 0.545 * mtow ** 0.8  # global mass of all systems


# AERO ESTIMATION

def cxf_c(mach, frm, re, ael, nwa, wing_ref):
    # cxf pour un composant
    fac = (1. + 0.144 * mach ** 2) ** 0.65
    # From fundamentals of aircraft and airship design, Leland M. Nicolai and Grant E. Carichner, volume 1-Aircraft design, p.64
    return frm * 0.455 * (nwa / wing_ref) / (fac * np.log10(re * ael) ** 2.58)


def fd_cx_lod(fuselage, nacelles, spe_wing, horz_area, vert_area, wing_ref, altp, cruise_mach, mach=0.82, cz=0.5):  # pamb : pression ambiante, tamb, température ambiante
    # fuselage = [length, width], nacelles = [(length, diameter),...], spe_wing = [span, aspect_ratio, area, root_c, mac], altp : pression d'altitude

    length, width = fuselage
    span, aspect_ratio, wing_area, root_c, mac = spe_wing  # mean aerodynamic chord
    pamb, tamb, g = atmosphere_g(altp)

    # Form & friction drag
    # -----------------------------------------------------------------------------------------------------------
    r, gam, cp, cv = gas_data()
    re = reynolds_number(pamb, tamb, mach)

    fuselage_frm = 1.05
    fuselage_ael = length
    fuselage_nwa = 2.70 * length * width

    cxf = cxf_c(mach, fuselage_frm, re, fuselage_ael, fuselage_nwa, wing_area)
    total_wet_area = fuselage_nwa + 2 * (wing_area - width * root_c)

    nacelles_frm = 1.15

    for i in range(len(nacelles)):
        knac = np.pi * nacelles[i][0] * nacelles[i][1]
        nwa = knac * (1.48 - 0.0076 * knac)
        ael = nacelles[i][0]
        cxf += cxf_c(mach, nacelles_frm, re, ael, nwa, wing_area)
        total_wet_area += nwa

    frm = 1.4
    wing_nwa = wing_area - width * root_c
    horz_nwa = 1.63 * horz_area
    vert_nwa = 2.0 * vert_area

    total_wet_area += wing_nwa + horz_nwa + vert_nwa

    ael = mac  # aero length

    if ael > 0:
        # Drag model is based on flat plane friction drag
        cxf += cxf_c(mach, frm, re, ael, wing_nwa, wing_ref)
        cxf += cxf_c(mach, frm, re, ael, horz_nwa, wing_ref)
        cxf += cxf_c(mach, frm, re, ael, vert_nwa, wing_ref)
    else:
        # Drag model is based on drag area, in that case nwa is frontal area
        cxf += frm * (wing_nwa / wing_ref)
        cxf += frm * (horz_nwa / wing_ref)
        cxf += frm * (vert_nwa / wing_ref)

    # Parasitic drag (seals, antennas, sensors, ...)
    # -----------------------------------------------------------------------------------------------------------
    knwa = total_wet_area / 1000.

    kp = (0.0247 * knwa - 0.11) * knwa + 0.166  # Parasitic drag factor

    cx_par = cxf * kp

    # Fuselage tail cone drag
    # -----------------------------------------------------------------------------------------------------------
    cx_tap = 0.0020

    # Total zero lift drag
    # -----------------------------------------------------------------------------------------------------------
    cx0 = cxf + cx_par + cx_tap

    # Induced drag
    # -----------------------------------------------------------------------------------------------------------
    ki_wing = (1.05 + (width / span) ** 2) / (np.pi * aspect_ratio)  # ???????????????????
    cxi = ki_wing * cz ** 2  # Induced drag

    # Compressibility drag
    # -----------------------------------------------------------------------------------------------------------
    # Freely inspired from Korn equation
    cz_design = 0.5
    mach_div = cruise_mach + (0.03 + 0.1 * (cz_design - cz))

    if 0.55 < mach:
        cxc = 0.0025 * np.exp(40. * (mach - mach_div))
    else:
        cxc = 0.

    # Sum up
    # -----------------------------------------------------------------------------------------------------------
    cx = cx0 + cxi + cxc
    lod = cz / cx
    fd = (gam / 2.) * pamb * mach ** 2 * wing_area * cx

    return fd, cx, lod


def reynolds_number(pamb, tamb, mach):
    """Reynolds number based on Sutherland viscosity model
    """
    vsnd = sound_speed(tamb)
    rho, sig = air_density(pamb, tamb)
    mu = gas_viscosity(tamb)
    re = rho * vsnd * mach / mu
    return re


def air_density(pamb, tamb):
    """Ideal gas density
    """
    r, gam, Cp, Cv = gas_data()
    rho0 = sea_level_density()
    rho = pamb / (r * tamb)
    sig = rho / rho0
    return rho, sig


def sound_speed(tamb):
    """Sound speed for ideal gas
    """
    r, gam, Cp, Cv = gas_data()
    vsnd = np.sqrt(gam * r * tamb)
    return vsnd


def gas_viscosity(tamb, gas="air"):
    """Mixed gas dynamic viscosity, Sutherland's formula
    WARNING : result will not be accurate if gas is mixing components of too different molecular weights
    """
    data = {"air": [1.715e-5, 273.15, 110.4],
            "ammonia": [0.92e-5, 273.15, 382.9],
            "argon": [2.10e-5, 273.15, 155.6],
            "benzene": [0.70e-5, 273.15, 173.1],
            "carbon_dioxide": [1.37e-5, 273.15, 253.4],
            "carbon_monoxide": [1.66e-5, 273.15, 94.0],
            "chlorine": [1.23e-5, 273.15, 273.0],
            "chloroform": [0.94e-5, 273.15, 284.2],
            "ethylene": [0.97e-5, 273.15, 163.7],
            "helium": [1.87e-5, 273.15, 69.7],
            "hydrogen": [0.84e-5, 273.15, 60.4],
            "methane": [1.03e-5, 273.15, 166.3],
            "neon": [2.98e-5, 273.15, 80.8],
            "nitrogen": [1.66e-5, 273.15, 110.9],
            "nitrous oxide": [1.37e-5, 273.15, 253.4],
            "oxygen": [1.95e-5, 273.15, 57.9],
            "steam": [0.92e-5, 273.15, 154.8],
            "sulphur_dioxide": [1.16e-5, 273.15, 482.3],
            "xenon": [2.12e-5, 273.15, 302.6]
            }  # mu0      T0      S
    # gas={"nitrogen":0.80, "oxygen":0.20}
    # mu = 0.
    # for g in list(gas.keys()):
    #     [mu0,T0,S] = data[g]
    #     mu = mu + gas[g]*(mu0*((T0+S)/(tamb+S))*(tamb/T0)**1.5)
    mu0, T0, S = data[gas]
    mu = (mu0 * ((T0 + S) / (tamb + S)) * (tamb / T0) ** 1.5)
    return mu


def gas_data(gas="air"):  # p*V = n*R*T -> p*V/n = R*T -> p*V/n*M = T*R/M -> on pose r = R/M et n*M/V = rho donc p/rho = rT
    """Gas data for a single gas
    """
    r = {"air": 287.053
         }.get(gas, "Erreur: type of gas is unknown")

    gam = {"air": 1.40
           }.get(gas, "Erreur: type of gas is unknown")

    cv = r / (gam - 1.)
    cp = gam * cv
    return r, gam, cp, cv


def sea_level_density():
    """Reference air density at sea level
    """
    rho0 = 1.225  # (kg/m3) Air density at sea level
    return rho0


def atmosphere_g(altp, disa=0.):
    """Ambiant data from pressure altitude from ground to 50 km according to Standard Atmosphere
    """
    g = 9.81
    r, gam, Cp, Cv = gas_data()

    Z = np.array([0., 11000., 20000., 32000., 47000., 50000.])
    dtodz = np.array([-0.0065, 0., 0.0010, 0.0028, 0.])
    P = np.array([101325., 0., 0., 0., 0., 0.])
    T = np.array([288.15, 0., 0., 0., 0., 0.])

    if Z[-1] < altp:
        raise Exception("atmosphere, altitude cannot exceed 50km")

    j = 0
    while Z[1 + j] <= altp:
        T[j + 1] = T[j] + dtodz[j] * (Z[j + 1] - Z[j])
        if 0. < np.abs(dtodz[j]):
            P[j + 1] = P[j] * (1. + (dtodz[j] / T[j]) * (Z[j + 1] - Z[j])) ** (-g / (r * dtodz[j]))
        else:
            P[j + 1] = P[j] * np.exp(-(g / r) * ((Z[j + 1] - Z[j]) / T[j]))
        j = j + 1

    if 0. < np.abs(dtodz[j]):
        pamb = P[j] * (1 + (dtodz[j] / T[j]) * (altp - Z[j])) ** (-g / (r * dtodz[j]))
    else:
        pamb = P[j] * np.exp(-(g / r) * ((altp - Z[j]) / T[j]))
    tamb = T[j] + dtodz[j] * (altp - Z[j]) + disa
    return pamb, tamb, g
