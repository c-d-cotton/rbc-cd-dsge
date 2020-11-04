#!/usr/bin/env python3
# PYTHON_PREAMBLE_START_STANDARD:{{{

# Christopher David Cotton (c)
# http://www.cdcotton.com

# modules needed for preamble
import importlib
import os
from pathlib import Path
import sys

# Get full real filename
__fullrealfile__ = os.path.abspath(__file__)

# Function to get git directory containing this file
def getprojectdir(filename):
    curlevel = filename
    while curlevel is not '/':
        curlevel = os.path.dirname(curlevel)
        if os.path.exists(curlevel + '/.git/'):
            return(curlevel + '/')
    return(None)

# Directory of project
__projectdir__ = Path(getprojectdir(__fullrealfile__))

# Function to call functions from files by their absolute path.
# Imports modules if they've not already been imported
# First argument is filename, second is function name, third is dictionary containing loaded modules.
modulesdict = {}
def importattr(modulefilename, func, modulesdict = modulesdict):
    # get modulefilename as string to prevent problems in <= python3.5 with pathlib -> os
    modulefilename = str(modulefilename)
    # if function in this file
    if modulefilename == __fullrealfile__:
        return(eval(func))
    else:
        # add file to moduledict if not there already
        if modulefilename not in modulesdict:
            # check filename exists
            if not os.path.isfile(modulefilename):
                raise Exception('Module not exists: ' + modulefilename + '. Function: ' + func + '. Filename called from: ' + __fullrealfile__ + '.')
            # add directory to path
            sys.path.append(os.path.dirname(modulefilename))
            # actually add module to moduledict
            modulesdict[modulefilename] = importlib.import_module(''.join(os.path.basename(modulefilename).split('.')[: -1]))

        # get the actual function from the file and return it
        return(getattr(modulesdict[modulefilename], func))

# PYTHON_PREAMBLE_END:}}}

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
    importattr(__projectdir__ / Path('submodules/dsge-perturbation/dsgediff_func.py'), 'checksame_inputdict')(inputdict_loglin, inputdict_log)
    

def dsgefull():
    inputdict = getinputdict()
    importattr(__projectdir__ / Path('submodules/dsge-perturbation/dsge_bkdiscrete_func.py'), 'discretelineardsgefull')(inputdict)


# Run:{{{1
check()
dsgefull()
