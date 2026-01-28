import sys
import numpy as np
import os
import json
from scipy.optimize import curve_fit

class DMAPoint:
    def __init__(self, frequency, temperature, storageModulus, lossModulus):
        self.frequency = frequency
        self.temperature = temperature
        self.storageModulus = storageModulus
        self.lossModulus = lossModulus

class DMAData:
    def __init__(self, name=""):
        self.name = name
        self.points = []
    
    def AddPoint(self, frequency, temperature, storageModulus, lossModulus):
        self.points.append(DMAPoint(frequency, temperature, storageModulus, lossModulus))
    
    def Arrange(self, mode="frequency"):
        if mode.lower() == "frequency":
            self.points = sorted(self.points, key=lambda x: x.frequency)
        elif mode.lower() == "temperature":
            self.points = sorted(self.points, key=lambda x: x.temperature)
        elif mode.lower() == "storage":
            self.points = sorted(self.points, key=lambda x: x.storageModulus)
        elif mode.lower() == "loss":
            self.points = sorted(self.points, key=lambda x: x.lossModulus)
    
    def GetInterpolatedPoint(self, freq):
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
    
    def prony_storage(self, w, Einfty, *Gi_taui):
        w = np.asarray(w)
        E_storage = np.ones_like(w) * Einfty
        n_terms = len(Gi_taui) // 2
        for i in range(n_terms):
            Gi = Gi_taui[2 * i]
            taui = Gi_taui[2 * i + 1]
            E_storage += Gi * (w ** 2 * taui ** 2) / (1 + w ** 2 * taui ** 2)
        return E_storage

    def prony_loss(self, w, Einfty, *Gi_taui):
        w = np.asarray(w)
        E_loss = np.zeros_like(w)
        n_terms = len(Gi_taui) // 2
        for i in range(n_terms):
            Gi = Gi_taui[2 * i]
            taui = Gi_taui[2 * i + 1]
            E_loss += Gi * (w * taui) / (1 + w ** 2 * taui ** 2)
        return E_loss

    def prony_tandelta(self, w, Einfty, *Gi_taui):
        E_storage = self.prony_storage(w, Einfty, *Gi_taui)
        E_loss = self.prony_loss(w, Einfty, *Gi_taui)
        return E_loss / E_storage
    
    def GetPronySeries(self, freqs, n_terms=2):
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
        
        Einfty_init = E_storage[-1]
        Gi_init = (E_storage[0] - Einfty_init) / n_terms
        taui_init = 1.0 / w[1] if len(w) > 1 else 1.0
        
        p0 = [Einfty_init]
        for _ in range(n_terms):
            p0.extend([Gi_init, taui_init])
        
        params, _ = curve_fit(
            self.prony_tandelta,
            w,
            ydata,
            p0=p0,
            maxfev=10000
        )
        
        Einfty = params[0]
        Gi_taui = params[1:]
        
        return Einfty, Gi_taui

    def GetBulkPronySeries(self, bulkData, freqs, n_terms=2):
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
        
        ydata = K_loss / K_storage
        
        Kinf_init = K_storage[-1]
        Ki_init = (K_storage[0] - Kinf_init) / n_terms
        tauKi_init = 1.0 / w[1] if len(w) > 1 else 1.0
        
        def bulk_tandelta(w, Kinf, *Ki_taui):
            K_storage_fit = np.ones_like(w) * Kinf
            K_loss_fit = np.zeros_like(w)
            n_terms = len(Ki_taui) // 2
            for i in range(n_terms):
                Ki = Ki_taui[2 * i]
                taui = Ki_taui[2 * i + 1]
                K_storage_fit += Ki * (w ** 2 * taui ** 2) / (1 + w ** 2 * taui ** 2)
                K_loss_fit += Ki * (w * taui) / (1 + w ** 2 * taui ** 2)
            return K_loss_fit / K_storage_fit
        
        params, _ = curve_fit(
            bulk_tandelta,
            w,
            ydata,
            p0=[Kinf_init] + [Ki_init, tauKi_init] * n_terms,
            maxfev=10000
        )
        
        Kinf = params[0]
        Ki_taui = params[1:]
        
        return Kinf, Ki_taui
    
    def Run(self, filePath, outPath=""):
        if outPath == "":
            outPath = filePath.replace(".txt", ".out")
        outfile = open(outPath, "w")
        
        with open(filePath, "r") as f:
            data = json.load(f)
            
            variables = data["Variables"]
            modeName = variables["Mode"]
            nu = variables["Nu"]
            rho = variables["Density"]
            
            for i in range(len(data["Data"])):
                ithData = data["Data"][str(i)]
                self.AddPoint(ithData["Freq"], ithData["Temp"], ithData["Storage"], ithData["Loss"])
            self.Arrange("frequency")
            outVars = []
            outVars.append(rho)
            if modeName == "PronySeries":
                f_list = variables["Frequencies"]
                n_terms = variables.get("NTerms", 2)
                TREF = variables["TREF"]
                A = variables["A"]
                B = variables["B"]
                bulkModulus = variables.get("BulkModulus", None)
                
                Einfty, Gi_taui = self.GetPronySeries(f_list, n_terms=n_terms)
                Ginf = Einfty / (2 * (1 + nu))
                
                bulkData = data["Data"].get("Bulk", None)
                if bulkData is not None:
                    Kinf, Ki_taui = self.GetBulkPronySeries(bulkData, f_list, n_terms=n_terms)
                else:
                    if bulkModulus is not None:
                        Kinf = bulkModulus
                    else:
                        Kinf = Einfty / (3 * (1 - 2 * nu))
                    Ki_taui = []
                    for _ in range(n_terms):
                        Ki_taui.append(0.0)
                        Ki_taui.append(1.0e6)
                
                nu_calc = (3 * Kinf - 2 * Ginf) / (6 * Kinf + 2 * Ginf)
                print("Calculated Poisson's ratio from fitted Kinf and Ginf: {:.6f}".format(nu_calc))
                
                outVars.append(Einfty)
                outVars.append(nu_calc)
                outVars.append(Einfty)
                outVars.append(Gi_taui)
                outVars.append(Kinf)
                outVars.append(Ki_taui)
                outVars.append(TREF)
                outVars.append(A)
                outVars.append(B)
                
                print("Prony Series Parameters are as follows:")
                for i in range(n_terms):
                    Gi = Gi_taui[2*i]
                    taui = Gi_taui[2*i+1]
                    Ki = Ki_taui[2*i]
                    tauKi = Ki_taui[2*i+1]
                    print(f"Term {i+1}: Gi={Gi}, taui={taui}, Ki={Ki}, tauKi={tauKi}")
            
            outString = self.WriteDynaKeyword(modeName, outVars)
            outfile.write(outString)
        outfile.close()
    
    def WriteDynaKeyword(self, modeName, variables):
        keyword = ""
        rho = variables[0]
        if modeName == "PronySeries":
            Einfty = variables[2]
            Gi_taui = variables[3]
            Kinf = variables[4]
            Ki_taui = variables[5]
            TREF = variables[6]
            A = variables[7]
            B = variables[8]
            
            nu = variables[1]
            Ginf = Einfty / (2 * (1 + nu))
            
            keyword += "*MAT_VISCOELASTIC_GENERAL\n"
            keyword += "$     MID        RO       BULK      PCF         EF\n"
            keyword += format("MID", ">10")
            keyword += format(rho, ">10.3e")
            keyword += format(Kinf, ">10.3e")
            keyword += format(0.0, ">10.3e")
            keyword += format(0.0, ">10.3e")
            keyword += "\n"
            keyword += "$     TREF        A         B\n"
            keyword += format(TREF, ">10.3e")
            keyword += format(A, ">10.3e")
            keyword += format(B, ">10.3e")
            keyword += "\n"
            
            n_terms = len(Gi_taui) // 2
            keyword += "$       GI      BETAi        KI      BETAKi\n"
            for i in range(n_terms):
                Gi = Gi_taui[2 * i]
                taui = Gi_taui[2 * i + 1]
                Ki = Ki_taui[2 * i]
                tauKi = Ki_taui[2 * i + 1]
                keyword += format(Gi, ">10.3e")
                keyword += format(1.0 / taui, ">10.3e")
                keyword += format(Ki, ">10.3e")
                keyword += format(1.0 / tauKi, ">10.3e")
                keyword += "\n"
        keyword += "\n"
        return keyword

if __name__ == "__main__":
    if len(sys.argv) < 2:
        curDir = os.path.dirname(os.path.realpath(__file__))
        fileName = "DMAData.txt"
        filePath = os.path.join(curDir, fileName)
        sys.argv.append(filePath)
    filePath = sys.argv[1]
    dmaData = DMAData()
    dmaData.Run(filePath)
