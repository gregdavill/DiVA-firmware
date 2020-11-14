import math
from numpy import arange

import matplotlib.pyplot as plt


def W(x):
    a = -0.5
    if abs(x) <= 1:
        return (a+2)*abs(x)**3 - (a+3)*abs(x)**2 + 1
    if abs(x) < 2:
        return (a)*abs(x)**3 - (5*a)*abs(x)**2 + 8*a*abs(x) - 4*a
    return 0
        

def coeffs(i):
    return [W(n-i) for n in arange(-1.0,2.001,1)]

current_offset = 0.0
total_offset = 0.0
delta_offset = 1.0 - 64/75
n_phases = 75
n_taps = 4


for n in range(n_phases):
    
    skip = False
    if current_offset + (delta_offset) > 1.0:
        skip = True
        #if not ((current_offset + delta_offset) > 1.0):
    
    #print(f't={total_offset} o={current_offset}, d={delta_offset} skip={skip} n={n}', end='')

    #print('')

    c = coeffs(current_offset)
    def encode(d):
        return int(d * 2**8)
        
    for i in range(n_taps):
        v = encode(c[i])
        s = '1' if skip else '0'
        print(f'height_coeff_write({i},{n},{v},{s});')

    total_offset += delta_offset
    current_offset += delta_offset
    if current_offset >= 1.0:
        current_offset -= 1.0
    


#plt.show()


