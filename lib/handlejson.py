import os, json

class Json:
    def read(self, file):
        with open(file, 'r') as f:
            data = json.load(f)
        return data

    def write(self, file, key, value):
        data = self.read(file)
    
        if key not in data:
            data[key] = value

        else:
            if isinstance(data[key], list):
                data[key].append(value)
            else:
                data[key] = value

        with open(file, 'w') as f:
            json.dump(data, f, indent=4)