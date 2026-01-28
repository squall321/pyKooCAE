import numpy as np

# Define frequency range (log scale from 10^0 to 10^6 Hz)
frequencies = np.logspace(0, 6, num=50)  # 1 Hz to 1 MHz

# Define estimated material properties
E_low = 1  # MPa (low frequency)
E_high = 10  # MPa (high frequency)
tan_delta_low = 0.5  # Loss tangent at low frequency
tan_delta_high = 0.1  # Loss tangent at high frequency

# Storage modulus (E') estimation using empirical log-based model
E_storage = E_low + (E_high - E_low) * (np.log10(frequencies) / np.log10(max(frequencies)))

# Loss modulus (E'') estimation using tan delta variation
tan_delta = tan_delta_low + (tan_delta_high - tan_delta_low) * (np.log10(frequencies) / np.log10(max(frequencies)))
E_loss = E_storage * tan_delta


with open('.\\occProject\\Generators\\KooExperimentManager\\DMAData_PSA.txt', 'w') as f:
    f.write("{\n")
    f.write("   \"Data\": {\n")
    for i in range(50):
        freq = frequencies[i]
        storage = E_storage[i]
        loss = E_loss[i]
        temp = 25.0
        f.write("       \"{0}\" : {{\n".format(i))
        f.write("           \"Freq\" : {0},\n".format(freq))
        f.write("           \"Storage\" : {0},\n".format(storage))
        f.write("           \"Loss\" : {0},\n".format(loss))
        f.write("           \"Temp\" : {0}\n".format(temp))
        f.write("       }")
        if i < 49:
            f.write(",\n")
        else:
            f.write("\n")
            
    f.write("   },\n")
    f.write("   \"Variables\": {\n")
    f.write("       \"Density\": 1300,\n")
    f.write("       \"Nu\": 0.49,\n")
    f.write("       \"Fmin\": 100,\n")
    f.write("       \"Fmax\": 10000,\n")
    f.write("       \"Ftarget\": 1000,\n")
    f.write("       \"Mode\": \"SimpleViscoelastic\"\n")
    f.write("   }\n")
    f.write("}\n")
    