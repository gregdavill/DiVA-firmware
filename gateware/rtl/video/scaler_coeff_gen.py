import math
from numpy import arange


def W(x):
    a = -0.5
    if abs(x) <= 1:
        return (a+2)*abs(x)**3 - (a+3)*abs(x)**2 + 1
    if abs(x) < 2:
        return (a)*abs(x)**3 - (5*a)*abs(x)**2 + 8*a*abs(x) - 4*a
    return 0
        

def coeffs(i):
    return [W(n-i) for n in arange(-1.0,2.001,1)]





def generate(delta_offset, n_phases, n_taps):
    output_coeffs = []
    current_offset = 0
    total_offset = 0

    for n in range(n_phases):
        
        skip = False
        if current_offset + (delta_offset*2 + 0.0001) > 1.0:
            if not ((current_offset + delta_offset + 0.0001) > 1.0):
                skip = True

        c = coeffs(current_offset)
        def encode(d):
            return int(d * 2**8)

        for i in range(n_taps):
            v = encode(c[i]) & 0xFFFF

            if skip:
                v |= (1 << 31)

            v |= (i << 24)
            v |= (n << 16)
            

            output_coeffs += [v]

        total_offset += delta_offset
        current_offset += delta_offset
        if current_offset >= 1.0:
            current_offset -= 1.0
    
    return output_coeffs

def print_c(coeff_list, name):
    chunks = [coeff_list[x:x+16] for x in range(0, len(coeff_list), 16)]

    print(f'const uint32_t {name} [{len(coeff_list)}] = {{')
    for c in chunks:
        print('\t', end='')
        for v in c:
            print("0x{0:08x}".format(v), end=', ')
        print('')
    print(f'}};\n\n')



n_taps = 4
delta_offset = 1.0 - 64/75 # (512 > 600)
n_phases = 75



output_coeffs = generate(delta_offset, n_phases, n_taps)
print(f' // Scaler coefficients generated with the following parameters:')
print(f' // delta_offset={delta_offset}')
print(f' // n_phases={n_phases}')
print(f' // n_taps={n_taps}')
print(f'')
print_c(output_coeffs, 'scaler_coef_512_600')



delta_offset = 1.0 - 4/5 # (640 > 800)
n_phases = 5


output_coeffs = generate(delta_offset, n_phases, n_taps)
print(f' // Scaler coefficients generated with the following parameters:')
print(f' // delta_offset={delta_offset}')
print(f' // n_phases={n_phases}')
print(f' // n_taps={n_taps}')
print(f'')
print_c(output_coeffs, 'scaler_coef_640_800')




delta_offset = 1.0 - 64/75 # (640 > 750)
n_phases = 75


output_coeffs = generate(delta_offset, n_phases, n_taps)
print(f' // Scaler coefficients generated with the following parameters:')
print(f' // delta_offset={delta_offset}')
print(f' // n_phases={n_phases}')
print(f' // n_taps={n_taps}')
print(f'')
print_c(output_coeffs, 'scaler_coef_640_750')




delta_offset = 1.0 - 4/5 # (512 > 640)
n_phases = 5


output_coeffs = generate(delta_offset, n_phases, n_taps)
print(f' // Scaler coefficients generated with the following parameters:')
print(f' // delta_offset={delta_offset}')
print(f' // n_phases={n_phases}')
print(f' // n_taps={n_taps}')
print(f'')
print_c(output_coeffs, 'scaler_coef_512_640')





delta_offset = 1.0 - 640/1280 # (512 > 640)
n_phases = 5

512/720


output_coeffs = generate(delta_offset, n_phases, n_taps)
print(f' // Scaler coefficients generated with the following parameters:')
print(f' // delta_offset={delta_offset}')
print(f' // n_phases={n_phases}')
print(f' // n_taps={n_taps}')
print(f'')
print_c(output_coeffs, 'scaler_coef_512_640')



