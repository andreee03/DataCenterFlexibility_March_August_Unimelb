
C_CFM_to_m3s = 0.472/ 1000


import math
import matplotlib.pyplot as plt

data = ( 0.295, 12.6)

def UA_from_data( data):
    R_sa, CFM = data
    C = CFM*C_CFM_to_m3s*1200 
    if R_sa*C < 1:
        print('pb')
        return 
    return -C* math.log(1 - 1/(R_sa*C))

k = UA_from_data(data)
def f_model(CFM):
    C = CFM*C_CFM_to_m3s*1200   # J/K
    return 1/(C*(1 - math.exp(-k/C)))   # K/J


UA_from_data(data)
def f_calibr(CFM):
    return 0.1431 + 1.9451*CFM**(-1.0719) 



C_CFM = [i for i in range(1,140)]

fig, ax = plt.subplots()

# Plot both graphs on the same axes
plt.plot(C_CFM, [f_model(elt) for elt in C_CFM], label ="Graph model")
plt.plot(C_CFM, [f_calibr(elt) for elt in C_CFM], label ="Graph empiric")
plt.plot([36],[0.185], 'ro', markersize=10)
plt.plot([12.6], [0.295],  'ro', markersize=10)
plt.plot([28],[0.210],  'ro', markersize=10)
# Add legend and show plot
ax.legend()

# First graph
plt.show()

## BILAN LE MODEL EMPIRIQUE SUIT BIEN LES POINTS. ON LE GARDE, PAS DE UA OU DE EPSILON