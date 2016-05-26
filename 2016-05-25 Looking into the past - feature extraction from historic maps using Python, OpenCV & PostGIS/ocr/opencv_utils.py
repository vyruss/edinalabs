import os
import csv

key_codes = {1048603:"ESC",
             1048624:"0",
             1048625:"1",
             1048626:"2",
             1048627:"3",
             1048628:"4",
             1048629:"5",
             1048630:"6",
             1048631:"7",
             1048632:"8",
             1048633:"9",
             1048673:"a",
             1048674:"b",
             1048675:"c",
             1048676:"d",
             1048677:"e",
             1048678:"f",
             1048679:"g",
             1048680:"h",
             1048681:"i",
             1048682:"j",
             1048683:"k",
             1048684:"l",
             1048685:"m",
             1048686:"n",
             1048687:"o",
             1048688:"p",
             1048689:"q",
             1048690:"r",
             1048691:"s",
             1048692:"t",
             1048693:"u",
             1048694:"v",
             1048695:"w",
             1048696:"x",
             1048697:"y",
             1048698:"z"
}


def get_key_from_cv_keycode(keycode):
    key_pressed = None
    if keycode in key_codes:
        key_pressed = key_codes[keycode]

    return key_pressed


class ResponseLookup:
    def __init__(self):
        self.exists = False
        lut_fn = "/home/james/Desktop/response_lookup.csv"
        if os.path.exists(lut_fn):
            self.exists = True
            self.response_codes = {}
            with open(lut_fn, "r") as inpf:
                my_reader = csv.reader(inpf)
                for r in my_reader:
                    response = r[0]
                    code = int(r[1])
                    self.response_codes[code] = response

    def get_response_from_code(self, code):
        response = None
        if self.exists:
            if code in self.response_codes:
                response = self.response_codes[code]

        return response
