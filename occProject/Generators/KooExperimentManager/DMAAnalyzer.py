import sys
import numpy as np
import os 
import json
from scipy.optimize import curve_fit

class DMAPoint:
    """Class to represent a single DMA point with frequency, temperature, storage modulus, and loss modulus."""
    def __init__(self, frequency, temperature, storageModulus, lossModulus):
        self.frequency = frequency
        self.temperature = temperature
        self.storageModulus = storageModulus
        self.lossModulus    = lossModulus
        

class DMAAnalyzer:
    """Class to manage DMA data, including points and bulk points, and perform various analyses."""
    def __init__(self, name = ""):
        """Initialize DMAData with an optional name."""
        self.name = name
        self.points = []
        self.bulkPoints = []
    
    def AddPoint(self, frequency, temperature, storageModulus, lossModulus):
        """Add a DMA point with frequency, temperature, storage modulus, and loss modulus."""
        self.points.append(DMAPoint(frequency, temperature, storageModulus, lossModulus))
    
    def AddBulkPoint(self, frequency, temperature, storageModulus, lossModulus):
        """Add a bulk DMA point with frequency, temperature, storage modulus, and loss modulus."""
        self.bulkPoints.append(DMAPoint(frequency, temperature, storageModulus, lossModulus))

    def Arrange(self, mode= "frequency"):        
        """Arrange the DMA points based on the specified mode."""
        if mode.lower() == "frequency":
            self.points = sorted(self.points, key=lambda x: x.frequency)
        elif mode.lower() == "temperature":
            self.points = sorted(self.points, key=lambda x: x.temperature)
        elif mode.lower() == "storage":
            self.points = sorted(self.points, key=lambda x: x.storageModulus)
        elif mode.lower() == "loss":
            self.points = sorted(self.points, key=lambda x: x.lossModulus)
    
    def ArrangeBulk(self, mode= "frequency"):
        """Arrange the bulk DMA points based on the specified mode."""
        if mode.lower() == "frequency":
            self.bulkPoints = sorted(self.bulkPoints, key=lambda x: x.frequency)
        elif mode.lower() == "temperature":
            self.bulkPoints = sorted(self.bulkPoints, key=lambda x: x.temperature)
        elif mode.lower() == "storage":
            self.bulkPoints = sorted(self.bulkPoints, key=lambda x: x.storageModulus)
        elif mode.lower() == "loss":
            self.bulkPoints = sorted(self.bulkPoints, key=lambda x: x.lossModulus)
    
    def GetInterpolatedPoint(self, freq):
        """Get an interpolated DMA point for a given frequency."""
        for i in range(len(self.points)-1):
            curFreq = self.points[i].frequency
            nextFreq = self.points[i+1].frequency
            if curFreq <= freq and freq <= nextFreq:
                curPoint = self.points[i]
                nextPoint = self.points[i+1]
                ratio = (freq - curFreq) / (nextFreq - curFreq)
                storage = curPoint.storageModulus * (1 - ratio) + nextPoint.storageModulus * ratio
                loss = curPoint.lossModulus * (1 - ratio) + nextPoint.lossModulus * ratio
                temperature = curPoint.temperature * (1 - ratio) + nextPoint.temperature * ratio
                return DMAPoint(freq, temperature, storage, loss)
        if self.points[0].frequency > freq:
            return DMAPoint(freq, self.points[0].temperature, self.points[0].storageModulus, self.points[0].lossModulus)
        elif self.points[-1].frequency < freq:
            return DMAPoint(freq, self.points[-1].temperature, self.points[-1].storageModulus, self.points[-1].lossModulus)
        return None
    
    def GetKeyvinVoigt(self, freq):
        """Get Kelvin-Voigt parameters for a given frequency."""
        self.Arrange("frequency")
        #interpolate
        storage = 0.0
        loss = 0.0
        point : DMAPoint = self.GetInterpolatedPoint(freq)
        if point == None:
            print("No point found for frequency : " + str(freq))
            exit(0)
        
        storage = point.storageModulus
        loss = point.lossModulus
        
        
        tandelta = loss / storage
        dampingratio = loss / (2 * storage)
        w = 2 * np.pi * freq
        beta = 2*dampingratio/w
        
        return storage, beta
    
    def GetMaxwell(self, freq):
        """Get Maxwell parameters for a given frequency."""
        self.Arrange("frequency")
        #interpolate
        storage = 0.0
        loss = 0.0
        point : DMAPoint = self.GetInterpolatedPoint(freq)
        if point == None:
            print("No point found for frequency : " + str(freq))
            exit(0)
        
        storage = point.storageModulus
        loss = point.lossModulus
        
        tandelta = loss / storage
        dampingratio = loss / (2 * storage)
        w = 2 * np.pi * freq
        alpha = dampingratio*w*2
        return storage, alpha
    
    def GetRayleigh(self, freqMin, freqMax):
        """Get Rayleigh parameters for a given frequency range."""
        self.Arrange("frequency")
        pointMin : DMAPoint = self.GetInterpolatedPoint(freqMin)
        pointMax : DMAPoint = self.GetInterpolatedPoint(freqMax)
        
        storageMin = pointMin.storageModulus
        
        dampingratioMin = pointMin.lossModulus / (2 * pointMin.storageModulus)
        dampingratioMax = pointMax.lossModulus / (2 * pointMax.storageModulus)
        
        wMin = 2 * np.pi * freqMin
        wMax = 2 * np.pi * freqMax
        
        #2 x 1 vector
        dVec = np.array([[dampingratioMin], [dampingratioMax]])
        # transpose of dVec
        #dVec = dVec.T
        #[ 1 4; 2 5]
        wMat = np.array([[1.0/(wMin*2.0), wMin/2.0], [1.0/(wMax*2.0), wMax/2.0]])
        
        #alpha, beta
        wMatInv = np.linalg.inv(wMat)
        alphaBeta = np.dot(wMatInv, dVec)
        alpha = alphaBeta[0][0]
        beta = alphaBeta[1][0]
        return storageMin, alpha, beta
    
    def losstanSimpleViscoelastic(self, w, E0, Einfty, tau):
        """Calculate the loss tangent for a simple viscoelastic model."""
        return (E0-Einfty)*w*tau / (Einfty+E0*w*w*tau*tau)     
    
    def GetSimpleViscoelastic(self, freqMin, freqTarget, freqMax):
        """Get parameters for a simple viscoelastic model based on specified frequencies."""
        freqMinPoint = self.GetInterpolatedPoint(freqMin)
        freqTargetPoint = self.GetInterpolatedPoint(freqTarget)
        freqMaxPoint = self.GetInterpolatedPoint(freqMax)
        
        storageMin = freqMinPoint.storageModulus
        lossMin = freqMinPoint.lossModulus
        storageTarget = freqTargetPoint.storageModulus
        lossTarget = freqTargetPoint.lossModulus
        storageMax = freqMaxPoint.storageModulus
        lossMax = freqMaxPoint.lossModulus
        w = []
        losstan = [] 
        w.append(2 * np.pi * freqMin)
        w.append(2 * np.pi * freqTarget)
        w.append(2 * np.pi * freqMax)
        losstan.append(lossMin / storageMin)
        losstan.append(lossTarget / storageTarget)
        losstan.append(lossMax / storageMax)
                
        E0initial = storageMin
        EinftyInitial = storageMax  
        tauinitial = 1.0 / w[1]
        initial_guess = [E0initial, EinftyInitial, tauinitial]
        params, _ = curve_fit(self.losstanSimpleViscoelastic, w, losstan, p0=initial_guess)
        
        
        # Extract the parameters
        E0, Einfty, tau = params
        
        #Einfty = storageMin * Einfty / E0 
        #E0 = storageMin
                        
        return storageMin, E0, Einfty, tau
    
    
    def prony_storage(self, w, Einfty, *Gi_taui):
        """Calculate the storage modulus for a Prony series."""
        w = np.asarray(w)
        E_storage = np.ones_like(w) * Einfty
        n_terms = len(Gi_taui) // 2
        for i in range(n_terms):
            Gi = Gi_taui[2 * i]
            taui = Gi_taui[2 * i + 1]
            E_storage += Gi * (w ** 2 * taui ** 2) / (1 + w ** 2 * taui ** 2)
        return E_storage

    def prony_loss(self, w, Einfty, *Gi_taui):
        """Calculate the loss modulus for a Prony series."""
        w = np.asarray(w)
        E_loss = np.zeros_like(w)
        n_terms = len(Gi_taui) // 2
        for i in range(n_terms):
            Gi = Gi_taui[2 * i]
            taui = Gi_taui[2 * i + 1]
            E_loss += Gi * (w * taui) / (1 + w ** 2 * taui ** 2)
        return E_loss

    def prony_tandelta(self, w, Einfty, *Gi_taui):
        """Calculate the loss tangent for a Prony series."""
        E_storage = self.prony_storage(w, Einfty, *Gi_taui)
        E_loss = self.prony_loss(w, Einfty, *Gi_taui)
        return E_loss / E_storage
    
    def GetPronySeries(self, freqs, n_terms=2):
        """Get Prony series parameters for given frequencies."""
        w = []
        E_storage = []
        E_loss = []
        for freq in freqs:
            point = self.GetInterpolatedPoint(freq)
            w.append(2 * np.pi * freq)
            E_storage.append(point.storageModulus)
            E_loss.append(point.lossModulus)
        w = np.array(w)
        E_storage = np.array(E_storage)
        E_loss = np.array(E_loss)
        
        ydata = E_loss / E_storage

        Einfty_init = min(E_storage)
        Einfty_init = max(Einfty_init, 1e-3)  # prevent zero

        Gi_total = max(E_storage) - Einfty_init
        Gi_init = Gi_total / n_terms
        Gi_init = max(Gi_init, 1e-3)

        taui_init = 1.0 / w[1] if len(w) > 1 else 1.0
        taui_init = max(taui_init, 1e-6)

        p0 = [Einfty_init]
        for _ in range(n_terms):
            p0.extend([Gi_init, taui_init])
        
        # Prepare bounds
        bounds_lower = [0.0]
        bounds_upper = [np.inf]

        for _ in range(n_terms):
            bounds_lower.extend([0.0, 1e-8])
            bounds_upper.extend([np.inf, np.inf])

        # Check feasibility
        for i, val in enumerate(p0):
            if val < bounds_lower[i] or val > bounds_upper[i]:
                print(f"Adjusting infeasible initial guess p0[{i}]={val}")
                p0[i] = max(bounds_lower[i] + 1e-6, 1e-3)

        params, _ = curve_fit(
            self.prony_tandelta,
            w,
            ydata,
            p0=p0,
            bounds=(bounds_lower, bounds_upper),
            maxfev=10000
        )
        
        Einfty = params[0]
        Gi_taui = params[1:]
        
        return Einfty, Gi_taui

    
    def GetBulkPronySeries(self, bulkData, freqs, n_terms=2, Kinf_input=None):
        """Get Prony series parameters for bulk data."""
        w = []
        K_storage = []
        K_loss = []
        for freq in freqs:
            fstr = None
            for k, v in bulkData.items():
                if abs(float(v["Freq"]) - freq) < 1e-6:
                    fstr = k
                    break
            if fstr is None:
                continue
            v = bulkData[fstr]
            w.append(2 * np.pi * freq)
            K_storage.append(v["Storage"])
            K_loss.append(v["Loss"])
        w = np.array(w)
        K_storage = np.array(K_storage)
        K_loss = np.array(K_loss)

        if len(w) == 0:
            return None, None

        # Target data for fitting
        ydata = K_loss / K_storage

        # Initial guesses
        if Kinf_input is not None:
            # Fixed Kinf mode
            Kinf = Kinf_input
            Ki_total = max(K_storage) - Kinf
            Ki_init = Ki_total / n_terms
            Ki_init = max(Ki_init, 1e-3)

            tauKi_init = 1.0 / w[1] if len(w) > 1 else 1.0
            tauKi_init = max(tauKi_init, 1e-6)

            p0_Ki_taui = []
            for _ in range(n_terms):
                p0_Ki_taui.extend([Ki_init, tauKi_init])

            bounds_lower_Ki_taui = []
            bounds_upper_Ki_taui = []
            for _ in range(n_terms):
                bounds_lower_Ki_taui.extend([0.0, 1e-8])
                bounds_upper_Ki_taui.extend([np.inf, np.inf])

            # Define function with fixed Kinf
            def bulk_tandelta_fixedK(w, *Ki_taui):
                K_storage_fit = np.ones_like(w) * Kinf
                K_loss_fit = np.zeros_like(w)
                n_terms_fit = len(Ki_taui) // 2
                for i in range(n_terms_fit):
                    Ki = Ki_taui[2 * i]
                    taui = Ki_taui[2 * i + 1]
                    K_storage_fit += Ki * (w ** 2 * taui ** 2) / (1 + w ** 2 * taui ** 2)
                    K_loss_fit += Ki * (w * taui) / (1 + w ** 2 * taui ** 2)
                return K_loss_fit / K_storage_fit

            params, _ = curve_fit(
                bulk_tandelta_fixedK,
                w,
                ydata,
                p0=p0_Ki_taui,
                bounds=(bounds_lower_Ki_taui, bounds_upper_Ki_taui),
                maxfev=10000
            )

            Ki_taui = params
            return Kinf, Ki_taui

        else:
            # Variable Kinf mode
            Kinf_init = min(K_storage)
            Kinf_init = max(Kinf_init, 1e-3)

            Ki_total = max(K_storage) - Kinf_init
            Ki_init = Ki_total / n_terms
            Ki_init = max(Ki_init, 1e-3)

            tauKi_init = 1.0 / w[1] if len(w) > 1 else 1.0
            tauKi_init = max(tauKi_init, 1e-6)

            p0 = [Kinf_init]
            for _ in range(n_terms):
                p0.extend([Ki_init, tauKi_init])

            bounds_lower = [0.0]
            bounds_upper = [np.inf]
            for _ in range(n_terms):
                bounds_lower.extend([0.0, 1e-8])
                bounds_upper.extend([np.inf, np.inf])

            def bulk_tandelta_variableK(w, Kinf, *Ki_taui):
                K_storage_fit = np.ones_like(w) * Kinf
                K_loss_fit = np.zeros_like(w)
                n_terms_fit = len(Ki_taui) // 2
                for i in range(n_terms_fit):
                    Ki = Ki_taui[2 * i]
                    taui = Ki_taui[2 * i + 1]
                    K_storage_fit += Ki * (w ** 2 * taui ** 2) / (1 + w ** 2 * taui ** 2)
                    K_loss_fit += Ki * (w * taui) / (1 + w ** 2 * taui ** 2)
                return K_loss_fit / K_storage_fit

            params, _ = curve_fit(
                bulk_tandelta_variableK,
                w,
                ydata,
                p0=p0,
                bounds=(bounds_lower, bounds_upper),
                maxfev=10000
            )

            Kinf = params[0]
            Ki_taui = params[1:]
            return Kinf, Ki_taui



    
    
    def Run(self, filePath, outPath = ""):
        """Run the DMA analysis on the specified file and write results to an output file."""
        if outPath == "":
            outPath = filePath.replace(".txt",".out")
        outfile = open(outPath, "w") 
        
        with open(filePath, "r") as f:
            data = json.load(f)            
            
            variables = data["Variables"]
            modeName = variables["Mode"]                        
            if "Nu" not in variables:
                variables["Nu"] = 0.0
            else:
                nu = variables["Nu"]
            if "BulkModulus" not in variables:
                bulkModulus = 0.0
            else:
                bulkModulus = variables["BulkModulus"]
                            
            rho = variables["Density"]
                       
            if modeName == "GeneralViscoelastic":
                shearData = data["Data"]["Shear"]
                bulkData = data["Data"]["Bulk"]
                
                for i in range(len(shearData)):
                    ithData = shearData[str(i)]
                    self.AddPoint(ithData["Freq"], ithData["Temp"], ithData["Storage"], ithData["Loss"])
                for i in range(len(bulkData)):
                    ithData = bulkData[str(i)]
                    self.AddBulkPoint(ithData["Freq"], ithData["Temp"], ithData["Storage"], ithData["Loss"])
                    
                self.Arrange("frequency")
                self.ArrangeBulk("frequency")
                outVars = []
                
                if modeName == "GeneralViscoelastic":
                    if "BulkModulus" in variables:
                        bulkModulus = variables["BulkModulus"]
                    else:
                        bulkModulus = None
                    n_terms = variables["NTerms"]
                    Einfty, Gi_taui = self.GetPronySeries([point.frequency for point in self.points], n_terms)
                    Kinf, Ki_taui = self.GetBulkPronySeries(bulkData, [point.frequency for point in self.bulkPoints], n_terms, bulkModulus)
                    print("General Viscoelastic Material Parameters are as follows")
                    print(f"Einfty: {Einfty}")
                    print(f"Kinf: {Kinf}")
                    print(f"Gi_taui: {Gi_taui}")
                    print(f"Ki_taui: {Ki_taui}")                        
                    
                    
                    A = variables["A"]
                    B = variables["B"]
                    outVars = [] 
                    outVars.append([rho, Kinf, 1.0, 0.0, 25.0, A, B])
                    outVars.append(["        "])
                    for i in range(n_terms):
                        Gi = Gi_taui[2 * i]
                        taui = Gi_taui[2 * i + 1]
                        Ki = Ki_taui[2 * i]
                        tauKi = Ki_taui[2 * i + 1]
                        outVars.append([Gi, taui, Ki, tauKi])
                    
                        
                
                    
            else:

                for i in range(len(data["Data"])):
                    ithData = data["Data"][str(i)]
                    self.AddPoint(ithData["Freq"], ithData["Temp"], ithData["Storage"], ithData["Loss"])
                self.Arrange("frequency")
                outVars = []
                outVars.append(rho)                  
                if modeName == "SimpleViscoelastic":
                    fmin = variables["Fmin"]
                    ftarget = variables["Ftarget"]
                    fmax = variables["Fmax"]
                    E, E0, Einfty, tau = self.GetSimpleViscoelastic(fmin, ftarget, fmax)
                    print("Viscoelastic Material Parameters are as follows")
                    print(f"E0: {E0}")
                    print(f"Einfty: {Einfty}")
                    print(f"tau: {tau}")                  
                    if nu == 0.0:
                        if "BulkModulus" in variables:
                            nu = (3.0*bulkModulus -E) / (6.0*bulkModulus)
                    outVars.append(E)                              
                    outVars.append(nu)             
                    outVars.append(E0)     
                    outVars.append(Einfty)
                    outVars.append(tau)
                elif modeName == "Maxwell":
                    ftarget = variables["Ftarget"]
                    E, alpha = self.GetMaxwell(ftarget)
                    print("Maxwell Material Parameters are as follows")
                    print(f"Alpha: {alpha}")
                    if nu == 0.0:
                        if "BulkModulus" in variables:
                            nu = (3.0*bulkModulus -E) / (6.0*bulkModulus)
                    outVars.append(E)
                    outVars.append(nu)
                    outVars.append(alpha)
                elif modeName == "KelvinVoigt":
                    ftarget = variables["Ftarget"]
                    E, beta = self.GetKeyvinVoigt(ftarget)
                    print("KelvinVoigt Material Parameters are as follows")
                    print(f"Beta: {beta}")
                    if nu == 0.0:
                        if "BulkModulus" in variables:
                            nu = (3.0*bulkModulus -E) / (6.0*bulkModulus)
                    outVars.append(E)
                    outVars.append(nu)
                    outVars.append(beta)
                elif modeName == "Rayleigh":
                    fmin = variables["Fmin"]
                    fmax = variables["Fmax"]
                    E, alpha, beta = self.GetRayleigh(fmin, fmax)
                    print("Rayleigh Material Parameters are as follows")
                    print(f"Alpha: {alpha}")
                    if nu == 0.0:
                        if "BulkModulus" in variables:
                            nu = (3.0*bulkModulus -E) / (6.0*bulkModulus)
                    outVars.append(E)
                    outVars.append(nu)
                    outVars.append(alpha)
                    outVars.append(beta)
            outString = self.WriteDynaKeyword(modeName, outVars)
            outfile.write(outString)    
        outfile.close()  
    
    def WriteDynaKeyword(self, modeName, variables):
        """Write the appropriate LS-DYNA keyword based on the mode and variables."""
        keyword = ""
        rho = variables[0]
        E = variables[1]
        nu = variables[2]
        if modeName == "Maxwell":            
            alpha = variables[3]
            keyword += "*MAT_ELASTIC\n"
            keyword += "$$     MID        RO         E        PR\n"
            keyword += format("MID",">10")
            keyword += format(rho,">10.3e")
            keyword += format(E,">10.3e")
            keyword += format(nu,">10.3f")
            keyword += "\n"
            keyword += "*DAMPING_PART_MASS\n"
            keyword += "$$     PID      LCID ALPHA(SF)     FLAG\n"
            keyword += format("PID",">10")
            keyword += format("0",">10")
            keyword += format(alpha,">10.3e")
            keyword += format("0", ">10")            
        elif modeName == "KelvinVoigt":
            beta = variables[3]
            keyword += "*MAT_ELASTIC\n"
            keyword += "$$     MID        RO         E        PR\n"
            keyword += format("MID",">10")
            keyword += format(rho,">10.3e")
            keyword += format(E,">10.3e")
            keyword += format(nu,">10.3e")
            keyword += "\n"
            keyword += "*DAMPING_PART_STIFFNESS\n"
            keyword += "$$     PID BETA(SF)\n"
            keyword += format("PID",">10")            
            keyword += format(beta,">10.3e")
        elif modeName == "Rayleigh":
            alpha = variables[3]
            beta = variables[4] 
            keyword += "*MAT_ELASTIC\n"
            keyword += "$$     MID        RO         E        PR\n"
            keyword += format("MID",">10")
            keyword += format(rho,">10.3e")
            keyword += format(E,">10.3e")
            keyword += format(nu,">10.3e")
            keyword += "\n"
            keyword += "*DAMPING_PART_MASS\n"
            keyword += "$$     PID      LCID ALPHA(SF)     FLAG\n"
            keyword += format("PID",">10")
            keyword += format("0",">10")
            keyword += format(alpha,">10.3e")
            keyword += format("0", ">10")
            keyword += "\n"
            keyword += "*DAMPING_PART_STIFFNESS\n"
            keyword += "$$     PID BETA(SF)\n"
            keyword += format("PID",">10")            
            keyword += format(beta,">10.3e")
        elif modeName == "SimpleViscoelastic":            
            E0 = variables[3]
            Einfty = variables[4]
            tau = variables[5]                         
            G0 = E / (2 * (1 + nu))
            Ginfty = G0 * Einfty / E0
            K = E / (3 * (1 - 2 * nu))
            keyword += "*MAT_VISCOELASTIC\n"
            keyword += "$$     MID        RO      BULK        G0        GI      BETA\n"
            keyword += format("MID",">10")
            keyword += format(rho,">10.3e") 
            keyword += format(K,">10.3e")
            keyword += format(G0,">10.3e")
            keyword += format(Ginfty,">10.3e")
            keyword += format(1.0/tau,">10.3e")
        elif modeName == "GeneralViscoelastic":            
            rho = variables[0][0] 
            Kinf = variables[0][1] 
            PCF = variables[0][2] 
            EF = variables[0][3]
            TREF = variables[0][4]
            A = variables[0][5]
            B = variables[0][6]
            keyword += "*MAT_GENERAL_VISCOELASTIC\n"
            keyword += "$$     MID        RO      BULK        PCF       EF        TRF        A         B\n"
            keyword += format("MID",">10")
            keyword += format(rho,">10.3e")
            keyword += format(Kinf,">10.3e")
            keyword += format(PCF,">10.3e")
            keyword += format(EF,">10.3e")
            keyword += format(TREF,">10.3e")
            keyword += format(A,">10.3e")
            keyword += format(B,">10.3e")
            keyword += "\n"
            keyword += "$$ Empty\n"
            keyword += variables[1][0] + "\n"
            
            for i in range(2, len(variables)):
                keyword += "$$      Gi      taui        Ki     tauKi\n"
                keyword += format(variables[i][0],">10.3e")
                keyword += format(variables[i][1],">10.3e")
                keyword += format(variables[i][2],">10.3e")
                keyword += format(variables[i][3],">10.3e")
                keyword += "\n"
            
        return keyword
            
            
        
       
if __name__ == "__main__":
    if len(sys.argv) <2:
        curDir = os.path.dirname(os.path.realpath(__file__))
        fileName = "DMAData.txt"
        fileName = "DMAData_PSA.txt"
        #fileName = "DMADataProny.txt"
        filePath = os.path.join(curDir, fileName)
        sys.argv.append(filePath)
                
    filePath = sys.argv[1]
    dmaData = DMAAnalyzer()
    dmaData.Run(filePath)
    print("DMA Analysis Completed")
    

    