from plugin_system.base_device import SourceInterface
from source_setup_map import SourceInfo
import pyvisa

plugin_info = {
    "name":"SLS-200",
    "type":"source",
    "class":"SLS_200"
}

class SLS_200(SourceInterface):
    @classmethod
    def can_connect(cls):
        rm = pyvisa.ResourceManager()
        res = rm.list_resources()
        for i in res:
            try:
                print(f"Trying resource: {i}")
                inst = rm.open_resource(i)
                idn = inst.query("*IDN?")
                if "SLS" in idn:
                    return (i, inst)
            except:
                continue
        return None
    
    def __init__(self,inst):
        self.inst = inst
        self.ch = 0 #This driver probably won't use the channel, but just in case...
        self.source_map: list[SourceInfo] = []

    #Queries the onboard modules and builds a source channel mapping
    def connect(self):
        num_mod = self.inst.query("MOD:NUM?")

        #Source number is 1 indexed (module is 0 indexed)
        source_num = 1
        
        #Iterate through all setup modules and store the module_number, source_number, wavelength, and state
        for i in range(num_mod):
            info = self.inst.query(f"MOD{i}:INFO?")
            parts = info.split(',')

            for wvl in parts[1:-1]:
                self.source_map.append(
                    SourceInfo(
                        wavelength = wvl,
                        module_number = i,
                        source_number = source_num,
                        state = 0
                    )
                )

                #Increment source_num for the next source
                source_num += 1

            #Reset source_num for the next module
            source_num = 1
    
    #Translates the SourceInfo datalcass into a dict to return
    def getSourceSetup(self):
        sourceMap = []
        for i in len(self.source_map):
            sourceMap.append({"module":self.source_map[i].module_number,"source":self.source_map[i].source_number,"wvl":self.source_map[i].wavelength})
        return sourceMap
    
    #Gets the module and source number for the source at the given index
    def _getModSourceNum(self,index:int):
        return self.source_map[index].module_number, self.source_map[ch].source_number
    
    #Sets the state of the source for channel
    def setSourceState(self,ch:int,state:int):
        module, source_num = self._getModSourceNum(ch)
        state_str = "DISAB" if state == 0 else "ENAB"
        
        #Write the command to the instrument
        self.inst.write(f"SOUR{module}:{state_str} {source_num}")

    #Sets the source power for the given channel
    def setSourcePower(self,ch:int,pow:float):
        module, source_num = self._getModSourceNum(ch)

        #Write the power to the instrument
        self.inst.write(f"SOUR{module}:POW{source_num} {pow}")

    #Sets the absolute source power for the given channel
    def setSourcePowerABS(self,ch:int,abs_pow:float):
        module, source_num = self._getModSourceNum(ch)

        #Write the absolute power to the instrument
        self.inst.write(f"SOUR{module}:POW{source_num}:ABS {abs_pow}")

    #Get the source power for the given channel
    def getSourcePower(self,ch:int):
        module, source_num = self._getModSourceNum(ch)
    
        #Query the power for the given channel
        try:
            result = self.inst.query(f"SOUR{module}:POW{source_num}?")
            return float(result)
        except Exception as e:
            #If a value that cannot be interpreted as float is returned then return None
            return None
            
    #Get the absolute power for the given channel
    def getSourcePowerABS(self,ch:int):
        module, source_num = self._getModSourceNum(ch)

        #Query the absolute power for the given channel
        try:
            result = self.inst.query(f"SOUR{module}:POW{source_num}:ABS?")
            return float(result)
        except Exception as e:
            #If a value that cannot be interpreted as a float is returned then return none. 
            return None


    


    