# PsychroLib (version 2.0.0) (https://github.com/psychrometrics/psychrolib)
# Copyright (c) 2018 D. Thevenard and D. Meyer for the current library implementation
# Copyright (c) 2017 ASHRAE Handbook — Fundamentals for ASHRAE equations and coefficients
# Licensed under the MIT License.

""" psychrolib.py

Contains functions for calculating thermodynamic properties of gas-vapor mixtures
and standard atmosphere suitable for most engineering, physical and meteorological
applications.

Most of the functions are an implementation of the formulae found in the
2017 ASHRAE Handbook - Fundamentals, in both International System (SI),
and Imperial (IP) units. Please refer to the information included in
each function for their respective reference.

Example
    >>> import psychrolib
    >>> # Set the unit system, for example to SI (can be either 'SI' or 'IP')
    >>> psychrolib.SetUnitSystem('SI')
    >>> # Calculate the dew point temperature for a dry bulb temperature of 25 C, a relative humidity of 80%, at an atmospheric pressure of 101325 Pa
    >>> TDewPoint = psychrolib.GetTDewPointFromRelHum(25.0, 0.80)
    >>> print(TDewPoint)
    21.309397163661785

Copyright
    - For the current library implementation
        Copyright (c) 2018 D. Thevenard and D. Meyer.
    - For equations and coefficients published ASHRAE Handbook — Fundamentals, Chapter 1
        Copyright (c) 2017 ASHRAE Handbook — Fundamentals (https://www.ashrae.org)

License
    MIT (https://github.com/psychrometrics/psychrolib/LICENSE.txt)

Note from the Authors
    We have made every effort to ensure that the code is adequate, however, we make no
    representation with respect to its accuracy. Use at your own risk. Should you notice
    an error, or if you have a suggestion, please notify us through GitHub at
    https://github.com/psychrometrics/psychrolib/issues.


"""


import math
from enum import Enum, auto


#######################################################################################################
# Global constants
#######################################################################################################

R_DA_IP =  53.350
"""float: Universal gas constant for dry air (IP version)

    Units:
        ft lb_Force lb_DryAir⁻¹ R⁻¹

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

"""

R_DA_SI = 287.042
"""float: Universal gas constant for dry air (SI version)

    Units:
        J kg_DryAir⁻¹ K⁻¹

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

"""


#######################################################################################################
# Helper functions
#######################################################################################################

# Unit system to use.
class UnitSystem(Enum):
    IP = auto()
    SI = auto()

IP = UnitSystem.IP
SI = UnitSystem.SI

__UNITS = None

__TOL = 1.0
# Tolerance.

def SetUnitSystem(Units: UnitSystem) -> None:
    """
    This function sets the system of units to use (SI or IP).

    Args:
        Units: string indicating the system of units chosen (SI or IP)

    Notes:
        This function *HAS TO BE CALLED* before the library can be used

    """
    global __UNITS
    global __TOL

    if not isinstance(Units, UnitSystem):
        raise ValueError("The system of units has to be either SI or IP.")

    __UNITS = Units

    # Define tolerance on temperature calculations
    # The tolerance is the same in IP and SI
    if Units == IP:
        __TOL = 0.001 * 9 / 5
    else:
        __TOL = 0.001

def GetUnitSystem() -> UnitSystem:
    return __UNITS

def isIP() -> bool:
    if __UNITS == IP:
        return True
    elif __UNITS == SI:
        return False
    else:
        raise ValueError('The system of units has not been defined.')


#######################################################################################################
# Conversions between dew point, wet bulb, and relative humidity
#######################################################################################################

def GetTRankineFromTFahrenheit(TFahrenheit: float) -> float:
    """
    Utility function to convert temperature to degree Rankine (°R)
    given temperature in degree Fahrenheit (°F).

    Args:
        TRankine: Temperature in degree Fahrenheit (°F)

    Returns:
        Temperature in degree Rankine (°R)

    Notes:
        Exact conversion.

    """
    # Zero degree Fahrenheit (°F) expressed as degree Rankine (°R)
    ZERO_FAHRENHEIT_AS_RANKINE = 459.67

    TRankine = TFahrenheit + ZERO_FAHRENHEIT_AS_RANKINE
    return TRankine

def GetTKelvinFromTCelsius(TCelsius: float) -> float:
    """
    Utility function to convert temperature to Kelvin (K)
    given temperature in degree Celsius (°C).

    Args:
        TCelsius: Temperature in degree Celsius (°C)

    Returns:
        Temperature in Kelvin (K)

    Notes:
        Exact conversion.

    """
    # Zero degree Celsius (°C) expressed as Kelvin (K)
    ZERO_CELSIUS_AS_KELVIN = 273.15

    TKelvin = TCelsius + ZERO_CELSIUS_AS_KELVIN
    return TKelvin


#######################################################################################################
# Conversions between dew point, wet bulb, and relative humidity
#######################################################################################################

def GetTWetBulbFromTDewPoint(TDryBulb: float, TDewPoint: float, Pressure: float) -> float:
    """
    Return wet-bulb temperature given dry-bulb temperature, dew-point temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TDewPoint : Dew-point temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Wet-bulb temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if TDewPoint > TDryBulb:
        raise ValueError("Dew point temperature is above dry bulb temperature")

    HumRatio = GetHumRatioFromTDewPoint(TDewPoint, Pressure)
    TWetBulb = GetTWetBulbFromHumRatio(TDryBulb, HumRatio, Pressure)
    return TWetBulb

def GetTWetBulbFromRelHum(TDryBulb: float, RelHum: float, Pressure: float) -> float:
    """
    Return wet-bulb temperature given dry-bulb temperature, relative humidity, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        RelHum : Relative humidity in range [0, 1]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Wet-bulb temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if RelHum < 0 or RelHum > 1:
        raise ValueError("Relative humidity is outside range [0, 1]")

    HumRatio = GetHumRatioFromRelHum(TDryBulb, RelHum, Pressure)
    TWetBulb = GetTWetBulbFromHumRatio(TDryBulb, HumRatio, Pressure)
    return TWetBulb

def GetRelHumFromTDewPoint(TDryBulb: float, TDewPoint: float) -> float:
    """
    Return relative humidity given dry-bulb temperature and dew-point temperature.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TDewPoint : Dew-point temperature in °F [IP] or °C [SI]

    Returns:
        Relative humidity in range [0, 1]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 22

    """
    if TDewPoint > TDryBulb:
        raise ValueError("Dew point temperature is above dry bulb temperature")

    VapPres = GetSatVapPres(TDewPoint)
    SatVapPres = GetSatVapPres(TDryBulb)
    RelHum = VapPres / SatVapPres
    return RelHum

def GetRelHumFromTWetBulb(TDryBulb: float, TWetBulb: float, Pressure: float) -> float:
    """
    Return relative humidity given dry-bulb temperature, wet bulb temperature and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TWetBulb : Wet-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Relative humidity in range [0, 1]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if TWetBulb > TDryBulb:
        raise ValueError("Wet bulb temperature is above dry bulb temperature")

    HumRatio = GetHumRatioFromTWetBulb(TDryBulb, TWetBulb, Pressure)
    RelHum =  GetRelHumFromHumRatio(TDryBulb, HumRatio, Pressure)
    return RelHum

def GetTDewPointFromRelHum(TDryBulb: float, RelHum: float) -> float:
    """
    Return dew-point temperature given dry-bulb temperature and relative humidity.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        RelHum: Relative humidity in range [0, 1]

    Returns:
        Dew-point temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if RelHum < 0 or RelHum > 1:
        raise ValueError("Relative humidity is outside range [0, 1]")

    VapPres = GetVapPresFromRelHum(TDryBulb, RelHum)
    TDewPoint = GetTDewPointFromVapPres(TDryBulb, VapPres)
    return TDewPoint

def GetTDewPointFromTWetBulb(TDryBulb: float, TWetBulb: float, Pressure: float) -> float:
    """
    Return dew-point temperature given dry-bulb temperature, wet-bulb temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TWetBulb : Wet-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Dew-point temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if TWetBulb > TDryBulb:
        raise ValueError("Wet bulb temperature is above dry bulb temperature")

    HumRatio = GetHumRatioFromTWetBulb(TDryBulb, TWetBulb, Pressure)
    TDewPoint = GetTDewPointFromHumRatio(TDryBulb, HumRatio, Pressure)
    return TDewPoint


#######################################################################################################
# Conversions between dew point, or relative humidity and vapor pressure
#######################################################################################################

def GetVapPresFromRelHum(TDryBulb: float, RelHum: float) -> float:
    """
    Return partial pressure of water vapor as a function of relative humidity and temperature.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        RelHum : Relative humidity in range [0, 1]

    Returns:
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 12, 22

    """
    if RelHum < 0 or RelHum > 1:
        raise ValueError("Relative humidity is outside range [0, 1]")

    VapPres = RelHum * GetSatVapPres(TDryBulb)
    return VapPres

def GetRelHumFromVapPres(TDryBulb: float, VapPres: float) -> float:
    """
    Return relative humidity given dry-bulb temperature and vapor pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        VapPres: Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]

    Returns:
        Relative humidity in range [0, 1]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 12, 22

    """
    if VapPres < 0:
        raise ValueError("Partial pressure of water vapor in moist air cannot be negative")

    RelHum = VapPres / GetSatVapPres(TDryBulb)
    return RelHum

def GetTDewPointFromVapPres(TDryBulb: float, VapPres: float) -> float:
    """
    Return dew-point temperature given dry-bulb temperature and vapor pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        VapPres: Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]

    Returns:
        Dew-point temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn. 5 and 6

    Notes:
        The dew point temperature is solved by inverting the equation giving water vapor pressure
        at saturation from temperature rather than using the regressions provided
        by ASHRAE (eqn. 37 and 38) which are much less accurate and have a
        narrower range of validity.
        The Newton-Raphson (NR) method is used on the logarithm of water vapour
        pressure as a function of temperature, which is a very smooth function
        Convergence is usually achieved in 3 to 5 iterations.
        TDryBulb is not really needed here, just used for convenience.

    """
    if isIP():
        _BOUNDS = -148, 392
        _STEPSIZE = 0.01 * 9 / 5
    else:
        _BOUNDS = -100, 200
        _STEPSIZE = 0.01

    TMidPoint = (_BOUNDS[0] + _BOUNDS[1]) / 2.     # Midpoint of domain of validity

    if VapPres < GetSatVapPres(_BOUNDS[0]) or VapPres > GetSatVapPres(_BOUNDS[1]):
        raise ValueError("Partial pressure of water vapor is outside range of validity of equations")

    # First guess
    TDewPoint = TDryBulb        # Calculated value of dew point temperatures, solved for iteratively

    lnVP = math.log(VapPres)    # Partial pressure of water vapor in moist air

    while True:
        TDewPoint_iter = TDewPoint   # Value of Tdp used in NR calculation
        # Step - negative in the right part of the curve, positive in the left part
		# to avoid going past the domain of validity of eqn. 5 and 6
		# when TDewPoint_iter is close to its bounds
        if TDewPoint_iter > TMidPoint:
            StepSize = -_STEPSIZE
        else:
            StepSize = _STEPSIZE

        lnVP_iter = math.log(GetSatVapPres(TDewPoint_iter))
        # Derivative of function, calculated numerically
        d_lnVP = (math.log(GetSatVapPres(TDewPoint_iter + StepSize)) - lnVP_iter) / StepSize
        # New estimate, bounded by domain of validity of eqn. 5 and 6
        TDewPoint = TDewPoint_iter - (lnVP_iter - lnVP) / d_lnVP
        TDewPoint = max(TDewPoint, _BOUNDS[0])
        TDewPoint = min(TDewPoint, _BOUNDS[1])

        if math.fabs(TDewPoint - TDewPoint_iter) <= __TOL:
           break

    TDewPoint = min(TDewPoint, TDryBulb)
    return TDewPoint

def GetVapPresFromTDewPoint(TDewPoint: float) -> float:
    """
    Return vapor pressure given dew point temperature.

    Args:
        TDewPoint : Dew-point temperature in °F [IP] or °C [SI]

    Returns:
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 36

    """
    VapPres = GetSatVapPres(TDewPoint)
    return VapPres


#######################################################################################################
# Conversions from wet-bulb temperature, dew-point temperature, or relative humidity to humidity ratio
#######################################################################################################

def GetTWetBulbFromHumRatio(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return wet-bulb temperature given dry-bulb temperature, humidity ratio, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Wet-bulb temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 33 and 35 solved for Tstar

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio cannot be negative")

    TDewPoint = GetTDewPointFromHumRatio(TDryBulb, HumRatio, Pressure)

    # Initial guesses
    TWetBulbSup = TDryBulb
    TWetBulbInf = TDewPoint
    TWetBulb = (TWetBulbInf + TWetBulbSup) / 2

    # Bisection loop
    while (TWetBulbSup - TWetBulbInf > __TOL):

        # Compute humidity ratio at temperature Tstar
        Wstar = GetHumRatioFromTWetBulb(TDryBulb, TWetBulb, Pressure)

        # Get new bounds
        if Wstar > HumRatio:
            TWetBulbSup = TWetBulb
        else:
            TWetBulbInf = TWetBulb

        # New guess of wet bulb temperature
        TWetBulb = (TWetBulbSup + TWetBulbInf) / 2
    return TWetBulb

def GetHumRatioFromTWetBulb(TDryBulb: float, TWetBulb: float, Pressure: float) -> float:
    """
    Return humidity ratio given dry-bulb temperature, wet-bulb temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TWetBulb : Wet-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 33 and 35

    """
    if TWetBulb > TDryBulb:
        raise ValueError("Wet bulb temperature is above dry bulb temperature")

    Wsstar = GetSatHumRatio(TWetBulb, Pressure)

    if isIP():
       if TWetBulb >= 32:
           HumRatio = ((1093 - 0.556 * TWetBulb) * Wsstar - 0.240 * (TDryBulb - TWetBulb)) \
                    / (1093 + 0.444 * TDryBulb - TWetBulb)
       else:
           HumRatio = ((1220 - 0.04 * TWetBulb) * Wsstar - 0.240 * (TDryBulb - TWetBulb)) \
                    / (1220 + 0.444 * TDryBulb - 0.48*TWetBulb)
    else:
       if TWetBulb >= 0:
           HumRatio = ((2501. - 2.326 * TWetBulb) * Wsstar - 1.006 * (TDryBulb - TWetBulb)) \
                    / (2501. + 1.86 * TDryBulb - 4.186 * TWetBulb)
       else:
           HumRatio = ((2830. - 0.24 * TWetBulb) * Wsstar - 1.006 * (TDryBulb - TWetBulb)) \
                    / (2830. + 1.86 * TDryBulb - 2.1 * TWetBulb)
    return HumRatio

def GetHumRatioFromRelHum(TDryBulb: float, RelHum: float, Pressure: float) -> float:
    """
    Return humidity ratio given dry-bulb temperature, relative humidity, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        RelHum : Relative humidity in range [0, 1]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if RelHum < 0 or RelHum > 1:
        raise ValueError("Relative humidity is outside range [0, 1]")

    VapPres = GetVapPresFromRelHum(TDryBulb, RelHum)
    HumRatio = GetHumRatioFromVapPres(VapPres, Pressure)
    return HumRatio

def GetRelHumFromHumRatio(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return relative humidity given dry-bulb temperature, humidity ratio, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Relative humidity in range [0, 1]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio cannot be negative")

    VapPres = GetVapPresFromHumRatio(HumRatio, Pressure)
    RelHum = GetRelHumFromVapPres(TDryBulb, VapPres)
    return RelHum

def GetHumRatioFromTDewPoint(TDewPoint: float, Pressure: float) -> float:
    """
    Return humidity ratio given dew-point temperature and pressure.

    Args:
        TDewPoint : Dew-point temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    VapPres = GetSatVapPres(TDewPoint)
    HumRatio = GetHumRatioFromVapPres(VapPres, Pressure)
    return HumRatio

def GetTDewPointFromHumRatio(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return dew-point temperature given dry-bulb temperature, humidity ratio, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Dew-point temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio cannot be negative")

    VapPres = GetVapPresFromHumRatio(HumRatio, Pressure)
    TDewPoint = GetTDewPointFromVapPres(TDryBulb, VapPres)
    return TDewPoint


#######################################################################################################
# Conversions between humidity ratio and vapor pressure
#######################################################################################################

def GetHumRatioFromVapPres(VapPres: float, Pressure: float) -> float:
    """
    Return humidity ratio given water vapor pressure and atmospheric pressure.

    Args:
        VapPres : Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 20

    """
    if VapPres < 0:
        raise ValueError("Partial pressure of water vapor in moist air cannot be negative")

    HumRatio = 0.621945 * VapPres / (Pressure - VapPres)
    return HumRatio

def GetVapPresFromHumRatio(HumRatio: float, Pressure: float) -> float:
    """
    Return vapor pressure given humidity ratio and pressure.

    Args:
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 20 solved for pw

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    VapPres = Pressure * HumRatio / (0.621945 + HumRatio)
    return VapPres


#######################################################################################################
# Dry Air Calculations
#######################################################################################################

def GetDryAirEnthalpy(TDryBulb: float) -> float:
    """
    Return dry-air enthalpy given dry-bulb temperature.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]

    Returns:
        Dry air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 28

    """
    if isIP():
        DryAirEnthalpy = 0.240 * TDryBulb
    else:
        DryAirEnthalpy = 1006 * TDryBulb
    return DryAirEnthalpy

def GetDryAirDensity(TDryBulb: float, Pressure: float) -> float:
    """
    Return dry-air density given dry-bulb temperature and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Dry air density in lb ft⁻³ [IP] or kg m⁻³ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    Notes:
        Eqn 14 for the perfect gas relationship for dry air.
        Eqn 1 for the universal gas constant.
        The factor 144 in IP is for the conversion of Psi = lb in⁻² to lb ft⁻².

    """
    if isIP():
        DryAirDensity = (144 * Pressure) / R_DA_IP / GetTRankineFromTFahrenheit(TDryBulb)
    else:
        DryAirDensity = Pressure / R_DA_SI / GetTKelvinFromTCelsius(TDryBulb)
    return DryAirDensity

def GetDryAirVolume(TDryBulb: float, Pressure: float) -> float:
    """
    Return dry-air volume given dry-bulb temperature and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Dry air volume in ft³ lb⁻¹ [IP] or in m³ kg⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    Notes:
        Eqn 14 for the perfect gas relationship for dry air.
        Eqn 1 for the universal gas constant.
        The factor 144 in IP is for the conversion of Psi = lb in⁻² to lb ft⁻².

    """
    if isIP():
        DryAirVolume = GetTRankineFromTFahrenheit(TDryBulb) * R_DA_IP / (144 * Pressure)
    else:
        DryAirVolume = GetTKelvinFromTCelsius(TDryBulb) * R_DA_SI / Pressure
    return DryAirVolume


#######################################################################################################
# Saturated Air Calculations
#######################################################################################################

def GetSatVapPres(TDryBulb: float) -> float:
    """
    Return saturation vapor pressure given dry-bulb temperature.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]

    Returns:
        Vapor pressure of saturated air in Psi [IP] or Pa [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1  eqn 5

    """
    if isIP():
        if (TDryBulb < -148 or TDryBulb > 392):
            raise ValueError("Dry bulb temperature must be in range [-148, 392]°F")

        T = GetTRankineFromTFahrenheit(TDryBulb)

        if (TDryBulb <= 32.):
            LnPws = (-1.0214165E+04 / T - 4.8932428 - 5.3765794E-03 * T + 1.9202377E-07 * T**2 \
                  + 3.5575832E-10 * math.pow(T, 3) - 9.0344688E-14 * math.pow(T, 4) + 4.1635019 * math.log(T))
        else:
            LnPws = -1.0440397E+04 / T - 1.1294650E+01 - 2.7022355E-02* T + 1.2890360E-05 * T**2 \
                  - 2.4780681E-09 * math.pow(T, 3) + 6.5459673 * math.log(T)
    else:
        if (TDryBulb < -100 or TDryBulb > 200):
            raise ValueError("Dry bulb temperature must be in range [-100, 200]°C")

        T = GetTKelvinFromTCelsius(TDryBulb)

        if (TDryBulb <= 0):
            LnPws = -5.6745359E+03 / T + 6.3925247 - 9.677843E-03 * T + 6.2215701E-07 * T**2 \
                  + 2.0747825E-09 * math.pow(T, 3) - 9.484024E-13 * math.pow(T, 4) + 4.1635019 * math.log(T)
        else:
            LnPws = -5.8002206E+03 / T + 1.3914993 - 4.8640239E-02 * T + 4.1764768E-05 * T**2 \
                  - 1.4452093E-08 * math.pow(T, 3) + 6.5459673 * math.log(T)

    SatVapPres = math.exp(LnPws)
    return SatVapPres

def GetSatHumRatio(TDryBulb: float, Pressure: float) -> float:
    """
    Return humidity ratio of saturated air given dry-bulb temperature and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio of saturated air in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 36, solved for W

    """
    SatVaporPres = GetSatVapPres(TDryBulb)
    SatHumRatio = 0.621945 * SatVaporPres / (Pressure - SatVaporPres)
    return SatHumRatio

def GetSatAirEnthalpy(TDryBulb: float, Pressure: float) -> float:
    """
    Return saturated air enthalpy given dry-bulb temperature and pressure.

    Args:
        TDryBulb: Dry-bulb temperature in °F [IP] or °C [SI]
        Pressure: Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Saturated air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1

    """
    SatHumRatio = GetSatHumRatio(TDryBulb, Pressure)
    SatAirEnthalpy = GetMoistAirEnthalpy(TDryBulb, SatHumRatio)
    return SatAirEnthalpy


#######################################################################################################
# Moist Air Calculations
#######################################################################################################

def GetVaporPressureDeficit(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return Vapor pressure deficit given dry-bulb temperature, humidity ratio, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Vapor pressure deficit in Psi [IP] or Pa [SI]

    Reference:
        Oke (1987) eqn 2.13a

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    RelHum = GetRelHumFromHumRatio(TDryBulb, HumRatio, Pressure)
    VaporPressureDeficit = GetSatVapPres(TDryBulb) * (1 - RelHum)
    return VaporPressureDeficit

def GetDegreeOfSaturation(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return the degree of saturation (i.e humidity ratio of the air / humidity ratio of the air at saturation
    at the same temperature and pressure) given dry-bulb temperature, humidity ratio, and atmospheric pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Degree of saturation in arbitrary unit

    Reference:
        ASHRAE Handbook - Fundamentals (2009) ch. 1 eqn 12

    Notes:
        This definition is absent from the 2017 Handbook. Using 2009 version instead.

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    SatHumRatio = GetSatHumRatio(TDryBulb, Pressure)
    DegreeOfSaturation = HumRatio / SatHumRatio
    return DegreeOfSaturation

def GetMoistAirEnthalpy(TDryBulb: float, HumRatio: float) -> float:
    """
    Return moist air enthalpy given dry-bulb temperature and humidity ratio.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]

    Returns:
        Moist air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 30

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    if isIP():
        MoistAirEnthalpy = 0.240 * TDryBulb + HumRatio * (1061 + 0.444 * TDryBulb)
    else:
        MoistAirEnthalpy = (1.006 * TDryBulb + HumRatio * (2501. + 1.86 * TDryBulb)) * 1000
    return MoistAirEnthalpy

def GetMoistAirVolume(TDryBulb: float, HumRatio: float, Pressure: float) -> float:
    """
    Return moist air specific volume given dry-bulb temperature, humidity ratio, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Specific volume of moist air in ft³ lb⁻¹ of dry air [IP] or in m³ kg⁻¹ of dry air [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 26

    Notes:
        In IP units, R_DA_IP / 144 equals 0.370486 which is the coefficient appearing in eqn 26
        The factor 144 is for the conversion of Psi = lb in⁻² to lb ft⁻².

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    if isIP():
        MoistAirVolume = R_DA_IP * GetTRankineFromTFahrenheit(TDryBulb) * (1 + 1.607858 * HumRatio) / (144 * Pressure)
    else:
        MoistAirVolume = R_DA_SI * GetTKelvinFromTCelsius(TDryBulb) * (1 + 1.607858 * HumRatio) / Pressure
    return MoistAirVolume

def GetMoistAirDensity(TDryBulb: float, HumRatio: float, Pressure:float) -> float:
    """
    Return moist air density given humidity ratio, dry bulb temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        HumRatio : Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        MoistAirDensity: Moist air density in lb ft⁻³ [IP] or kg m⁻³ [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 11

    """
    if HumRatio < 0:
        raise ValueError("Humidity ratio is negative")

    MoistAirVolume = GetMoistAirVolume(TDryBulb, HumRatio, Pressure)
    MoistAirDensity = (1 + HumRatio) / MoistAirVolume
    return MoistAirDensity


#######################################################################################################
# Standard atmosphere
#######################################################################################################

def GetStandardAtmPressure(Altitude: float) -> float:
    """
    Return standard atmosphere barometric pressure, given the elevation (altitude).

    Args:
        Altitude: Altitude in ft [IP] or m [SI]

    Returns:
        Standard atmosphere barometric pressure in Psi [IP] or Pa [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 3

    """

    if isIP():
        StandardAtmPressure = 14.696 * math.pow(1 - 6.8754e-06 * Altitude, 5.2559)
    else:
        StandardAtmPressure = 101325 * math.pow(1 - 2.25577e-05 * Altitude, 5.2559)
    return StandardAtmPressure

def GetStandardAtmTemperature(Altitude: float) -> float:
    """
    Return standard atmosphere temperature, given the elevation (altitude).

    Args:
        Altitude: Altitude in ft [IP] or m [SI]

    Returns:
        Standard atmosphere dry-bulb temperature in °F [IP] or °C [SI]

    Reference:
        ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 4

    """
    if isIP():
        StandardAtmTemperature = 59 - 0.00356620 * Altitude
    else:
        StandardAtmTemperature = 15 - 0.0065 * Altitude
    return StandardAtmTemperature

def GetSeaLevelPressure(StationPressure: float, Altitude: float, TDryBulb: float) -> float:

    """
    Return sea level pressure given dry-bulb temperature, altitude above sea level and pressure.

    Args:
        StationPressure : Observed station pressure in Psi [IP] or Pa [SI]
        Altitude: Altitude in ft [IP] or m [SI]
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]

    Returns:
        Sea level barometric pressure in Psi [IP] or Pa [SI]

    Reference:
        Hess SL, Introduction to theoretical meteorology, Holt Rinehart and Winston, NY 1959,
        ch. 6.5; Stull RB, Meteorology for scientists and engineers, 2nd edition,
        Brooks/Cole 2000, ch. 1.

    Notes:
        The standard procedure for the US is to use for TDryBulb the average
        of the current station temperature and the station temperature from 12 hours ago.

    """
    if isIP():
        # Calculate average temperature in column of air, assuming a lapse rate
        # of 3.6 °F/1000ft
        TColumn = TDryBulb + 0.0036 * Altitude / 2

        # Determine the scale height
        H = 53.351 * GetTRankineFromTFahrenheit(TColumn)
    else:
        # Calculate average temperature in column of air, assuming a lapse rate
        # of 6.5 °C/km
        TColumn = TDryBulb + 0.0065 * Altitude / 2

        # Determine the scale height
        H = 287.055 * GetTKelvinFromTCelsius(TColumn) / 9.807

    # Calculate the sea level pressure
    SeaLevelPressure = StationPressure * math.exp(Altitude / H)
    return SeaLevelPressure

def GetStationPressure(SeaLevelPressure: float, Altitude: float, TDryBulb: float) -> float:
    """
    Return station pressure from sea level pressure.

    Args:
        SeaLevelPressure : Sea level barometric pressure in Psi [IP] or Pa [SI]
        Altitude: Altitude in ft [IP] or m [SI]
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]

    Returns:
        Station pressure in Psi [IP] or Pa [SI]

    Reference:
        See 'GetSeaLevelPressure'

    Notes:
        This function is just the inverse of 'GetSeaLevelPressure'.

    """
    StationPressure = SeaLevelPressure / GetSeaLevelPressure(1, Altitude, TDryBulb)
    return StationPressure


######################################################################################################
# Functions to set all psychrometric values
#######################################################################################################

def CalcPsychrometricsFromTWetBulb(TDryBulb: float, TWetBulb: float, Pressure: float) -> tuple:
    """
    Utility function to calculate humidity ratio, dew-point temperature, relative humidity,
    vapour pressure, moist air enthalpy, moist air volume, and degree of saturation of air given
    dry-bulb temperature, wet-bulb temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TWetBulb : Wet-bulb temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Dew-point temperature in °F [IP] or °C [SI]
        Relative humidity in range [0, 1]
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]
        Moist air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]
        Specific volume of moist air in ft³ lb⁻¹ [IP] or in m³ kg⁻¹ [SI]
        Degree of saturation [unitless]

    """
    HumRatio = GetHumRatioFromTWetBulb(TDryBulb, TWetBulb, Pressure)
    TDewPoint = GetTDewPointFromHumRatio(TDryBulb, HumRatio, Pressure)
    RelHum = GetRelHumFromHumRatio(TDryBulb, HumRatio, Pressure)
    VapPres = GetVapPresFromHumRatio(HumRatio, Pressure)
    MoistAirEnthalpy = GetMoistAirEnthalpy(TDryBulb, HumRatio)
    MoistAirVolume = GetMoistAirVolume(TDryBulb, HumRatio, Pressure)
    DegreeOfSaturation = GetDegreeOfSaturation(TDryBulb, HumRatio, Pressure)
    return HumRatio, TDewPoint, RelHum, VapPres, MoistAirEnthalpy, MoistAirVolume, DegreeOfSaturation

def CalcPsychrometricsFromTDewPoint(TDryBulb: float, TDewPoint: float, Pressure: float) -> tuple:
    """
    Utility function to calculate humidity ratio, wet-bulb temperature, relative humidity,
    vapour pressure, moist air enthalpy, moist air volume, and degree of saturation of air given
    dry-bulb temperature, dew-point temperature, and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        TDewPoint : Dew-point temperature in °F [IP] or °C [SI]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Wet-bulb temperature in °F [IP] or °C [SI]
        Relative humidity in range [0, 1]
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]
        Moist air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]
        Specific volume of moist air in ft³ lb⁻¹ [IP] or in m³ kg⁻¹ [SI]
        Degree of saturation [unitless]

    """
    HumRatio = GetHumRatioFromTDewPoint(TDewPoint, Pressure)
    TWetBulb = GetTWetBulbFromHumRatio(TDryBulb, HumRatio, Pressure)
    RelHum = GetRelHumFromHumRatio(TDryBulb, HumRatio, Pressure)
    VapPres = GetVapPresFromHumRatio(HumRatio, Pressure)
    MoistAirEnthalpy = GetMoistAirEnthalpy(TDryBulb, HumRatio)
    MoistAirVolume = GetMoistAirVolume(TDryBulb, HumRatio, Pressure)
    DegreeOfSaturation = GetDegreeOfSaturation(TDryBulb, HumRatio, Pressure)
    return HumRatio, TWetBulb, RelHum, VapPres, MoistAirEnthalpy, MoistAirVolume, DegreeOfSaturation

def CalcPsychrometricsFromRelHum(TDryBulb: float, RelHum: float, Pressure: float) -> tuple:
    """
    Utility function to calculate humidity ratio, wet-bulb temperature, dew-point temperature,
    vapour pressure, moist air enthalpy, moist air volume, and degree of saturation of air given
    dry-bulb temperature, relative humidity and pressure.

    Args:
        TDryBulb : Dry-bulb temperature in °F [IP] or °C [SI]
        RelHum : Relative humidity in range [0, 1]
        Pressure : Atmospheric pressure in Psi [IP] or Pa [SI]

    Returns:
        Humidity ratio in lb_H₂O lb_Air⁻¹ [IP] or kg_H₂O kg_Air⁻¹ [SI]
        Wet-bulb temperature in °F [IP] or °C [SI]
        Dew-point temperature in °F [IP] or °C [SI].
        Partial pressure of water vapor in moist air in Psi [IP] or Pa [SI]
        Moist air enthalpy in Btu lb⁻¹ [IP] or J kg⁻¹ [SI]
        Specific volume of moist air in ft³ lb⁻¹ [IP] or in m³ kg⁻¹ [SI]
        Degree of saturation [unitless]

    """
    HumRatio = GetHumRatioFromRelHum(TDryBulb, RelHum, Pressure)
    TWetBulb = GetTWetBulbFromHumRatio(TDryBulb, HumRatio, Pressure)
    TDewPoint = GetTDewPointFromHumRatio(TDryBulb, HumRatio, Pressure)
    VapPres = GetVapPresFromHumRatio(HumRatio, Pressure)
    MoistAirEnthalpy = GetMoistAirEnthalpy(TDryBulb, HumRatio)
    MoistAirVolume = GetMoistAirVolume(TDryBulb, HumRatio, Pressure)
    DegreeOfSaturation = GetDegreeOfSaturation(TDryBulb, HumRatio, Pressure)
    return HumRatio, TWetBulb, TDewPoint, VapPres, MoistAirEnthalpy, MoistAirVolume, DegreeOfSaturation