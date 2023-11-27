import numpy as np

# MASS ESTIMATION

# Cabin
self.m_furnishing = (0.063 * self.n_pax ** 2 + 9.76 * self.n_pax)  # Furnishings mass
self.m_op_item = max(160., 5.2 * (self.n_pax * self.airplane.design_range * 1e-6))  # Operator items mass
self.mass = self.m_furnishing + self.m_op_item

# Fuselage
surface = self.length * np.sqrt(self.width * self.height)
self.mass = 5.80 * (np.pi * surface) ** 1.2  # Statistical regression versus fuselage built surface

# Wing
A = 32 * self.area ** 1.1
B = 4. * self.span ** 2 * np.sqrt(mass.mtow * mass.mzfw)
C = 1.1e-6 * (1. + 2. * self.aspect_ratio) / (1. + self.aspect_ratio)
D = (0.6 * self.root_toc + 0.3 * self.kink_toc + 0.1 * self.tip_toc) * (self.area / self.span)
E = np.cos(self.sweep25) ** 2
F = 1200. * max(0., cz_max_ld - 1.8) ** 1.5

self.mass = (A + (B * C) / (D * E) + F)  # Shevell formula + high lift device regression

# Horizontal tail
self.mass = 22. * self.area

# Vertical tail
self.mass = 25. * self.area

# Nacelle
self.engine_mass = (1250. + 0.021 * self.engine_slst)
self.pylon_mass = (0.0031 * self.engine_slst)
self.mass = (self.engine_mass + self.pylon_mass) * self.n_engine

# Landing gears
self.mass = (0.015 * mass.mtow ** 1.03 + 0.012 * mass.mlw)

# System
self.mass = 0.545 * mass.mtow ** 0.8  # global mass of all systems

# AERO ESTIMATION

# Fuselage
self.wet_area = 2.70 * self.length * self.width
self.aero_length = self.length
self.form_factor = 1.05  # Form factor for drag calculation

# Wing
self.wet_area = 2 * (self.area - fuselage.width * self.root_c)
self.aero_length = self.mac
self.form_factor = 1.4

# Horizontal tail
self.wet_area = 1.63 * self.area
self.aero_length = self.mac
self.form_factor = 1.4

# Vertical tail
self.wet_area = 2.0 * self.area
self.aero_length = self.mac
self.form_factor = 1.4

# Nacelle
knac = np.pi * self.diameter * self.length
self.wet_area = knac * (1.48 - 0.0076 * knac)  # statistical regression, all engines
self.aero_length = self.length
self.form_factor = 1.15

# Landing gears
self.wet_area = 0.
self.aero_length = 1.
self.form_factor = 0.

# System
self.wet_area = 0.
self.aero_length = 1.
self.form_factor = 0.


class Aerodynamics(object):
    def __init__(self, airplane, hld_type, hld_conf_to, hld_conf_ld):
        self.airplane = airplane

        self.hld_type = hld_type
        self.hld_conf_to = hld_conf_to
        self.hld_conf_ld = hld_conf_ld

        self.hld_data = {0: [1.45, "Clean"],
                         1: [2.25, "Flap only, Rotation without slot"],
                         2: [2.60, "Flap only, Rotation single slot (ATR)"],
                         3: [2.80, "Flap only, Rotation double slot"],
                         4: [2.80, "Fowler Flap"],
                         5: [2.00, "Slat only"],
                         6: [2.45, "Slat + Flap rotation without slot"],
                         7: [2.70, "Slat + Flap rotation single slot"],
                         8: [2.90, "Slat + Flap rotation double slot"],
                         9: [3.00, "Slat + Fowler (A320)"],
                         10: [3.20, "Slat + Fowler + Fowler double slot (A321)"]}

    def wing_high_lift(self, hld_conf):
        """Retrieves max lift and zero aoa lift of a given (flap/slat) deflection (from 0 to 1).
            * 0 =< hld_type =< 10 : type of high lift device
            * 0 =< hld_conf =< 1  : (slat) flap deflection
        Typically:
            * hld_conf = 1 gives the :math:`C_{z,max}` for landind (`czmax_ld`)
            * hld_conf = 0.1 to 0.5 gives the :math:`C_{z,max}` for take-off(`czmax_to`)
        """
        wing = self.airplane.wing

        # Maximum lift coefficients of different airfoils, DUBS 1987
        czmax_ld = self.hld_data.get(self.hld_type, "Erreur - high_lift_, HLDtype out of range")[0]  # 9 is default if x not found

        if self.hld_type < 5:
            czmax_base = 1.45  # Flap only
        else:
            if hld_conf == 0:
                czmax_base = 1.45  # Clean
            else:
                czmax_base = 2.00  # Slat + Flap

        czmax_2d = (1. - hld_conf) * czmax_base + hld_conf * czmax_ld  # Setting effect

        if hld_conf == 0:
            cz0_2d = 0.  # Clean
        else:
            cz0_2d = czmax_2d - czmax_base  # Assumed the Lift vs AoA is just translated upward and Cz0 clean equal to zero

        # Source : http://aerodesign.stanford.edu/aircraftdesign/highlift/clmaxest.html
        czmax = czmax_2d * (1. - 0.08 * np.cos(wing.sweep25) ** 2) * np.cos(wing.sweep25) ** 0.75
        cz0 = cz0_2d

        return czmax, cz0

    def drag_force(self, pamb, tamb, mach, cz):
        """Retrieves airplane drag and L/D in current flying conditions
        """
        fuselage = self.airplane.fuselage
        wing = self.airplane.wing
        geometry = self.airplane.geometry

        gam = 1.4

        # Form & friction drag
        # -----------------------------------------------------------------------------------------------------------
        re = reynolds_number(pamb, tamb, mach)

        fac = (1. + 0.126 * mach ** 2)

        total_wet_area = 0
        cxf = 0.
        for comp in self.airplane:
            nwa = comp.wet_area
            ael = comp.aero_length
            frm = comp.form_factor
            if ael > 0.:
                # Drag model is based on flat plane friction drag
                cxf += frm * ((0.455 / fac) * (np.log(10) / np.log(re * ael)) ** 2.58) \
                       * (nwa / wing.area)
            else:
                # Drag model is based on drag area, in that case nwa is frontal area
                cxf += frm * (nwa / wing.area)
            total_wet_area += nwa

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
        ki_wing = (1.05 + (fuselage.width / wing.span) ** 2) / (np.pi * wing.aspect_ratio)
        cxi = ki_wing * cz ** 2  # Induced drag

        # Compressibility drag
        # -----------------------------------------------------------------------------------------------------------
        # Freely inspired from Korn equation
        cz_design = 0.5
        mach_div = self.airplane.cruise_mach + (0.03 + 0.1 * (cz_design - cz))

        if 0.55 < mach:
            cxc = 0.0025 * np.exp(40. * (mach - mach_div))
        else:
            cxc = 0.

        # Sum up
        # -----------------------------------------------------------------------------------------------------------
        cx = cx0 + cxi + cxc
        lod = cz / cx
        fd = (gam / 2.) * pamb * mach ** 2 * wing.area * cx

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


def gas_data(gas="air"):
    """Gas data for a single gas
    """
    r = {"air": 287.053,
         "argon": 208.,
         "carbon_dioxide": 188.9,
         "carbon_monoxide": 297.,
         "helium": 2077.,
         "hydrogen": 4124.,
         "methane": 518.3,
         "nitrogen": 296.8,
         "oxygen": 259.8,
         "propane": 189.,
         "sulphur_dioxide": 130.,
         "steam": 462.
         }.get(gas, "Erreur: type of gas is unknown")


def sea_level_density():
    """Reference air density at sea level
    """
    rho0 = 1.225  # (kg/m3) Air density at sea level
    return rho0


def atmosphere_g(altp, disa=0.):
    """Ambiant data from pressure altitude from ground to 50 km according to Standard Atmosphere
    """
    g = gravity()
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
