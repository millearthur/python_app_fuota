#DO DEBUG PRINT ?
debug = 0


class device_list():
    
    def __init__(self) : 
        self.device_list = {
            '0080000004006aa0' : {
                "device_name"   : 'NodeTest',
                "application_name" : 'LoraAppTest',
            }
        }
    
    #dev_eui should be in stored state ie: str of hex
    #data should be a dic of attribute/value of device
    def update_device_list(self,dev_eui,data):
        
        if debug == 1 : 
            print("-> Before : ", end="")
            print(self.device_list)
        if dev_eui in self.device_list : 
            self.device_list[dev_eui].update(data)
        else :
            self.device_list.update({
            dev_eui : data
            })
        if debug == 1 : 
            print("-> After : ", end="")
            print(self.device_list)
            
    def get_device_list(self):
        return self.device_list