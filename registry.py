import re

API_MAPS = {
    "user-details": "<default_base>/user/details/"
}


class APIRegistryBaseParameter:
    
    mode_maps = {
        "DEV": {
            "alias": ("DEV", "DEV_LOCAL"),
            "base_params": {'default_base': 'http://127.0.0.1:8001/'}
        },
    }

    default_base_params = mode_maps['DEV']['base_params']

    
    def __init__(self, select_mode):
        self.base_params = self.default_base_params
        for k, v in self.mode_maps.items():
            if select_mode.strip().upper() in v['alias']:
                self.base_params = v['base_params']
                break
    
    
    @classmethod
    def get_key_for_alias(cls, select_mode):
        for k, v in cls.mode_maps.items():
            if select_mode.strip().upper() in v['alias']:
                return k
        
        return ''
        

class APIRegistry:
    def __init__(self, register, base_params={}) -> None:
        self.set_register(register)
        self.set_base_params(base_params)

    def get_api(self, name, params={}):
        if name not in self.register: raise ValueError(f"API not found: {name}")

        api = APIRegistry.put_params_in_api(self.register[name], params)

        remaining = re.findall(r"<[a-zA-Z0-9_]+>", api)
        if remaining:
            raise ValueError(f"required parameters {remaining} not found")

        return api

    def set_base_params(self, base_params = {}):
        if not isinstance(base_params, dict): raise ValueError("base_params type should be dict")
        self.base_params = base_params
        for k, v in self.register.items(): self.register[k] = APIRegistry.put_params_in_api(v, self.base_params)

    @staticmethod
    def put_params_in_api(api, params):
        for k, v in params.items():
            regex = f"<{k}>"
            api = str(v).join(re.split(regex, api))
        return api

    def set_register(self, register):
        if not isinstance(register, dict): raise ValueError("register type should be dict")
        self.register = register
    
