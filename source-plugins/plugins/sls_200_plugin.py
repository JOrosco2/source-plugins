from plugin_system.base_device import SourceInterface
from dataclasses import dataclass
import pyvisa

plugin_info = {
    "name":"SLS-200",
    "type":"source",
    "class":"SLS_200"
}

@dataclass
class SourceInfo:
    module_number: int
    source_number: int
    wavelength: str
    state: int

class SLS_200(SourceInterface):
    _last_index = 0 #class variable, tracks which instruemnt was returned last

    @classmethod
    def can_connect(cls):
        rm = pyvisa.ResourceManager()
        res = rm.list_resources()
        
        while cls._last_index < len(res):
            resource = res[cls._last_index]
            cls._last_index += 1
            try:
                inst = rm.open_resource(resource)
                idn = inst.query("*IDN?")
                if "SLS" in idn:
                    return (resource, inst)
            except:
                continue

        return None #no more instruments found

        
    def __init__(self,inst):
        self.inst = inst
        self.ch = 0 #This driver probably won't use the channel, but just in case...
        self.sn = ""
        self.source_map: list[SourceInfo] = []

    #Queries the onboard modules and builds a source channel mapping
    def connect(self):
        num_mod = int(self.inst.query("MOD:NUM?"))

        #Source number is 1 indexed (module is 0 indexed)
        source_num = 1
        
        #Iterate through all setup modules and store the module_number, source_number, wavelength, and state
        for i in range(num_mod):
            self.inst.write(f"MOD{i}:INFO?")
            info = self.inst.read_raw()
            parts = str(info).split(',')

            idx = 2 #The 1st wavelength in the module always appears at index 2

            while idx < len(parts):
                self.source_map.append(
                    SourceInfo(
                        wavelength = parts[idx],
                        module_number = i,
                        source_number = source_num,
                        state = 0
                    )
                )
                source_num += 1
                idx += 3

            #Reset source_num for the next module
            source_num = 1
    
    #Translates the SourceInfo datalcass into a dict to return
    def get_source_setup(self):
        sourceMap = []
        for i in range(len(self.source_map)):
            sourceMap.append({"module":self.source_map[i].module_number,"source":self.source_map[i].source_number,"wvl":self.source_map[i].wavelength})
        return sourceMap
    
    #Gets the module and source number for the source at the given index
    def _get_mod_source_num(self,index:int):
        return self.source_map[index].module_number, self.source_map[index].source_number
    
    #Sets the state of the source for channel
    def set_source_state(self,ch:int,state:int):
        module, source_num = self._get_mod_source_num(ch)
        state_str = "DISAB" if state == 0 else "ENAB"
        
        #Write the command to the instrument
        self.inst.write(f"SOUR{module}:{state_str} {source_num}")

    #Sets the source power for the given channel
    def set_source_power(self,ch:int,pow:float):
        module, source_num = self._get_mod_source_num(ch)

        #Write the power to the instrument
        self.inst.write(f"SOUR{module}:POW{source_num} {pow}")

    #Sets the absolute source power for the given channel
    def set_source_power_abs(self,ch:int,abs_pow:float):
        module, source_num = self._get_mod_source_num(ch)

        #Write the absolute power to the instrument
        self.inst.write(f"SOUR{module}:POW{source_num}:ABS {abs_pow}")

    #Get the source power for the given channel
    def get_source_power(self,ch:int):
        module, source_num = self._get_mod_source_num(ch)
    
        #Query the power for the given channel
        try:
            result = self.inst.query(f"SOUR{module}:POW{source_num}?")
            return float(result)
        except Exception as e:
            #If a value that cannot be interpreted as float is returned then return None
            return None
            
    #Get the absolute power for the given channel
    def get_source_power_abs(self,ch:int):
        module, source_num = self._get_mod_source_num(ch)

        #Query the absolute power for the given channel
        try:
            result = self.inst.query(f"SOUR{module}:POW{source_num}:ABS?")
            return float(result)
        except Exception as e:
            #If a value that cannot be interpreted as a float is returned then return none. 
            return None
        
    #Return the unit's serial number
    def get_sn(self):
        resp = self.inst.query(f"*IDN?")
        parts = resp.split(",")
        return parts[2]
        


    


    