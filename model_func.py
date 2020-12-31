#!/usr/bin/env python3
import os
from pathlib import Path
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '/')

def getparamssdict(p = None):
    if p is None:
        p = {}
    p_defaults = {'GAMMA': 1, 'BETA': 0.95, 'ETA': 2, 'ALPHA': 0.3, 'RHO_A': 0.95, 'Abar': 1, 'DELTA': 0.1}
    for param in p_defaults:
        if param not in p:
            p[param] = p_defaults[param]

    return(p)


def getss(p):
    p['Rp'] = 1/p['BETA']
    p['rk'] = p['Rp'] - 1 + p['DELTA']
    p['Am1'] = p['Abar']
    k = (p['ALPHA'] * p['Am1'] / p['rk'])**(1/(1-p['ALPHA']))
    p['W'] = (1 - p['ALPHA']) * p['Am1'] * k**p['ALPHA']
    y = p['Am1'] * k**p['ALPHA']
    c = y - p['DELTA'] * k
    p['L'] = (c**(-p['GAMMA']) * p['W']) **(1/(p['ETA'] + p['GAMMA']))
    p['C'] = c * p['L']
    p['K'] = k * p['L']
    p['Y'] = y * p['L']

    return(p)


def getinputdict(p = None, loglineareqs = True):
    inputdict = {}

    inputdict['paramssdict'] = getparamssdict(p)
    inputdict['states'] = ['Am1', 'K']
    inputdict['controls'] = ['C', 'L', 'Rp', 'rk', 'W', 'Y']
    inputdict['shocks'] = ['epsilon_A']

    # equations:{{{
    inputdict['equations'] = []

    # household
    if loglineareqs is True:
        inputdict['equations'].append('-GAMMA * C = Rp - GAMMA * C_p')
    else:
        inputdict['equations'].append('C^(-GAMMA) = BETA*Rp*C_p^(-GAMMA)')
    if loglineareqs is True:
        inputdict['equations'].append('-GAMMA * C = rk_ss / (rk_ss + 1 - DELTA) * rk_p - GAMMA * C_p')
    else:
        inputdict['equations'].append('C^(-GAMMA) = BETA*(rk_p + 1 - DELTA)*C_p^(-GAMMA)')
    if loglineareqs is True:
        inputdict['equations'].append('W - GAMMA * C = ETA * L')
    else:
        inputdict['equations'].append('W*C^(-GAMMA) = L^(ETA)')

    # firms
    if loglineareqs is True:
        inputdict['equations'].append('rk = Am1_p + (ALPHA - 1) * K + (1 - ALPHA) * L')
    else:
        inputdict['equations'].append('rk = ALPHA * Am1_p * K^(ALPHA - 1) * L^(1 - ALPHA)')
    if loglineareqs is True:
        inputdict['equations'].append('W = Am1_p + ALPHA * K - ALPHA * L')
    else:
        inputdict['equations'].append('W = (1 - ALPHA)*Am1_p*K^(ALPHA)*L^(-ALPHA)')
    if loglineareqs is True:
        inputdict['equations'].append('Y = Am1_p + ALPHA * K + (1 - ALPHA) * L')
    else:
        inputdict['equations'].append('Y = Am1_p*K^ALPHA*L^(1 - ALPHA)')

    # exogenous process
    if loglineareqs is True:
        inputdict['equations'].append('Am1_p = RHO_A * Am1 + epsilon_A')
    else:
        inputdict['equations'].append('log(Am1_p) = RHO_A*log(Am1) + (1 - RHO_A) * log(Abar) + epsilon_A')

    # resource
    if loglineareqs is True:
        inputdict['equations'].append('C_ss * C + K_ss * K_p = Y_ss * Y + (1 - DELTA) * K_ss * K')
    else:
        inputdict['equations'].append('C + K_p = Y + (1 - DELTA) * K')
        
    # not necessary equations
    # real interest rate for comparison
    if loglineareqs is True:
        inputdict['equations'].append('-GAMMA * C = Rp - GAMMA * C_p')
    else:
        inputdict['equations'].append('C^(-GAMMA) = BETA*Rp*C_p^(-GAMMA)')
    # equations:}}}

    # add steady state
    getss(inputdict['paramssdict'])

    if loglineareqs is True:
        inputdict['loglineareqs'] = True
    else:
        inputdict['logvars'] = inputdict['states'] + inputdict['controls']
    inputdict['irfshocks'] = ['epsilon_A', 'K']

    # save stuff
    inputdict['savefolder'] = __projectdir__ / Path('temp/')

    return(inputdict)


def check():
    inputdict_loglin = getinputdict(loglineareqs = True)
    inputdict_log = getinputdict(loglineareqs = False)
    sys.path.append(str(__projectdir__ / Path('submodules/dsge-perturbation/')))
    from dsgediff_func import checksame_inputdict
    checksame_inputdict(inputdict_loglin, inputdict_log)
    

def dsgefull():
    inputdict = getinputdict()
    sys.path.append(str(__projectdir__ / Path('submodules/dsge-perturbation/')))
    from dsge_bkdiscrete_func import discretelineardsgefull
    discretelineardsgefull(inputdict)


# Run:{{{1
check()
dsgefull()
