# pytoon by M2Sash on Github
import tqdm
import numpy as np
import base64, io, json, requests
from pytoon.JavaScript import JavaScript
from PIL import Image, ImageDraw

class Toonio:

    ERASER = 0
    PENCIL = 1
    FEATHER = 2
    MEGAERASER = 3

    def __init__(self):

        self.fps = 12
        self.frames = 1
        self.edit = None
        self.layers = [
                        {
                        "index": 0,
                        "color": 0,
                        "hidden": False,
                        "name": "Слой 1",
                        "frames": [{"lines": []}]
                        }
                        ]
                    
                    


        pass


    def LoadToon(self, _id, _v=1, _gen=True):
        response = requests.get(f"https://toonio.ru/Toons/new/{_id}.toon?v={_v}")

        NpRawData = np.frombuffer(response.content, dtype=np.int16)
        Int16Array = NpRawData.tolist()

        if not _gen:
            return Int16Array
        
        Toon = Toonio.Degenerate(Int16Array)

        self.fps = Toon["framerate"]
        if "original" in Toon:
            self.original = Toon["original"]
        else:
            self.original = None
        self.tools = Toon["tools"]
        self.layers = Toon["layers"]
        
        return Toon
    

    def LoadToonFromSave(self, _save, _gen=True):
        response = base64.b64decode(_save["saves"][0]["data"].split("base64,")[1])

        NpRawData = np.frombuffer(response, dtype=np.int16)
        Int16Array = NpRawData.tolist()

        if not _gen:
            return Int16Array
        
        Toon = Toonio.Degenerate(Int16Array)

        self.fps = Toon["framerate"]
        if Toon["original"]:
            self.original = Toon["original"]
        else:
            self.original = None
        self.tools = Toon["tools"]
        self.layers = Toon["layers"]
        
        return Toon
    

    @staticmethod
    def Degenerate(_data, _layer_colours=1):
        data = {}
        counter = 0

        def read():
            nonlocal counter
            value = _data[counter]
            counter += 1
            return value

        layer_len = read()
        frame_len = read()
        frame_rate = read()
        version = 1

        if _data[counter] == 999:
            version = _data[counter + 1]
            counter += 2

        data['framerate'] = frame_rate

        if version >= 3:
            original_len = read()
            original = ''.join(chr(read()) for _ in range(original_len))
            data['original'] = original

        data['tools'] = []

        if version >= 5:
            tool_len = read()
            data['tools'] = [None] * tool_len
            for x in range(tool_len):
                tool = {
                    'i': x,
                    't': read(),
                    'w': read()
                }

                if tool['t'] not in {Toonio.ERASER, Toonio.MEGAERASER}:
                    tool['c'] = JavaScript.RGB2HEX(read(), read(), read())

                if tool['t'] == Toonio.FEATHER:
                    tool['f'] = JavaScript.RGB2HEX(read(), read(), read())

                data['tools'][x] = tool

        data['layers'] = [None] * layer_len
        for i in range(layer_len):
            layer_data = {
                'index': i,
                'color': i % _layer_colours,
                'hidden': not read(),
                'name': "",
                'frames': []
            }

            if version >= 2:
                layer_name_len = read()
                layer_name = ''.join(chr(read()) for _ in range(layer_name_len))
                layer_data['name'] = layer_name

            layer_data['frames'] = [None] * frame_len
            for j in range(frame_len):
                frame_data = {'lines': []}

                if version >= 4 and read() == 1:
                    if layer_data['frames'] and j > 0:
                        frame_data = layer_data['frames'][j - 1]
                    layer_data['frames'][j] = frame_data
                    continue

                line_len = read()
                if line_len < 0:
                    line_len = 65536 + line_len
                frame_data['lines'] = [None] * line_len
                for x in range(line_len):
                    line = {'d': {}, 'p': []}

                    if version >= 5:
                        line['d'] = data['tools'][read()]
                    else:
                        tool = {
                            't': read(),
                            'w': read()
                        }
                        c = JavaScript.RGB2HEX(read(), read(), read())
                        f = JavaScript.RGB2HEX(read(), read(), read())

                        if tool['t'] not in {Toonio.ERASER, Toonio.MEGAERASER}:
                            tool['c'] = c

                        if tool['t'] == Toonio.FEATHER:
                            tool['f'] = f

                        line['d'] = Toonio.GetToolS(tool, data['tools'])

                    point_len = read()
                    if point_len < 0:
                        point_len = 65536 + point_len
                    line['p'] = [0] * (point_len * 2)
                    for y in range(point_len):
                        if version >= 5:
                            line['p'][y * 2] = read()
                            line['p'][y * 2 + 1] = read()
                        else:
                            pos_x = read()
                            _x = read()
                            pos_y = read()
                            _y = read()

                            line['p'][y * 2] = (_x if pos_x == 1 else -_x)
                            line['p'][y * 2 + 1] = (_y if pos_y == 1 else -_y)

                    frame_data['lines'][x] = line

                layer_data['frames'][j] = frame_data

            data['layers'][i] = layer_data

        return data
    

    def GetToolS(_tool, _tools, _push=True):
        find_tool = next((i for i, a in enumerate(_tools) 
                        if all(a.get(k) == _tool.get(k) for k in ['t', 'w', 'c', 'f'] 
                                if _tool.get(k) is not None)), -1)

        if find_tool == -1 and _push:
            new_tool = {k: _tool.get(k) for k in ['t', 'w', 'c', 'f'] if _tool.get(k) is not None}
            new_tool['i'] = len(_tools)
            _tools.append(new_tool)

            find_tool = len(_tools) - 1

        return _tools[find_tool]

    

    def DrawLine(self, _pts, _frame=1, _layer=1, _tool=1, _width=5, _color="#000000", _fill="#000000", _layername="Слой {layer}", _double=True):

        _points = []
        multiplier = 2 if _double else 1

        for Point in _pts:
            for i in range(multiplier):
                _points.append( Point[0] )
                _points.append( Point[1] )
            
        # Ensure layer exists
        while len(self.layers) < _layer:
            self.layers.append({"index": len(self.layers), "color": 0, "hidden": False, "name": _layername.replace("{layer}", str(len(self.layers)+1)), "frames": []})

        layer = self.layers[_layer - 1]

        # Ensure frame exists
        while len(layer["frames"]) < _frame:
            layer["frames"].append({"lines": []})

        frame = layer["frames"][_frame - 1]

        # Add the line
        if _tool != self.FEATHER:
            frame["lines"].append({
                "d": {
                    "t": _tool,
                    "w": _width,
                    "c": _color
                },
                "p": _points
            })
        else:
            frame["lines"].append({
                "d": {
                    "t": _tool,
                    "w": _width,
                    "c": _color,
                    "f": _fill
                },
                "p": _points
            })

    def DrawRect(self, x1, y1, x2, y2, _tool=2, **args):

        pts = [
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2],
            [x1, y1 ] # Closing the rectangle
        ]
        self.DrawLine(pts, _tool=_tool, **args)


    def Generate(self, binary=False):
        print("GEN")
        data = []
        
        def write(value):
            data.append(value)

        # Initial metadata
        write(len(self.layers))  # Number of layers
        write(len(self.layers[0]["frames"]))  # Number of frames
        write(self.fps)  # Frame rate
        write(999)  # Marker for version
        write(5)  # Version number

        # Original string if present
        if hasattr(self, 'original') and self.original:
            write(len(self.original))
            for char in self.original:
                write(ord(char))
        else:
            write(0)  # No original string

        # Tools
        tools = []
        for layer in self.layers:
            for frame in layer["frames"]:
                for line in frame["lines"]:
                    Toonio.GetToolS(line["d"], tools)

        write(len(tools))  # Number of tools
        for tool in tools:
            write(tool["t"])  # Tool type
            write(tool["w"])  # Width
            if "c" in tool:
                r, g, b = JavaScript.HEX2RGB(tool["c"])
                write(r)
                write(g)
                write(b)
            if "f" in tool:
                r, g, b = JavaScript.HEX2RGB(tool["f"])
                write(r)
                write(g)
                write(b)

        # Layers and frames
        for layer in self.layers:
            write(0 if layer["hidden"] else 1)  # Hidden flag
            write(len(layer["name"]))  # Length of layer name
            for char in layer["name"]:
                write(ord(char))

            for frame in tqdm.tqdm(layer["frames"]):
                if not frame["lines"]:  # Frame reuse optimization
                    write(1)
                    continue
                else:
                    write(0)

                write(len(frame["lines"]))  # Number of lines
                for line in frame["lines"]:
                    tool_index = Toonio.GetToolS(line["d"], tools, _push=False)["i"]
                    write(tool_index)  # Tool index

                    write(len(line["p"]) // 2)  # Number of points
                    for i in range(0, len(line["p"]), 2):
                        write(line["p"][i])     # X coordinate
                        write(line["p"][i + 1])  # Y coordinate

        if not binary: return data
        else:
            NpArray = np.array(data, dtype=np.int16)

            bites = NpArray.tobytes()

            return bites
    
    def Login(self, LoginOrSESSION, Password = None):
        if Password:
            data = requests.post("https://toonio.ru/api/v1/User.Login", data={"Username": LoginOrSESSION, "Password": Password, "remember": True})
            biscuits = data.cookies.get_dict() # Fuck you its biscuits

            if "PHPSESSID" in biscuits and "error" not in data.json():
                self.session = biscuits["PHPSESSID"]
            else:
                raise ValueError("Incorrect password")
        else:
            self.session = LoginOrSESSION

    def CreateGif(self, filename=None):
        """
        Generates an animated GIF from the Toonio object's layers and frames.
        If filename is None, returns the raw binary data of the GIF.
        :param filename: Name of the output GIF file or None to return binary data.
        :return: None if filename is provided, else binary data of the GIF.
        """

        images = []
        width, height = 1280, 720
        target_width, target_height = 640, 360  # Rescaled dimensions
        frame_duration = int(1000 / self.fps)  # Duration per frame in milliseconds

        max_frames = max(len(layer["frames"]) for layer in self.layers if not layer["hidden"])

        for frame_index in range(max_frames):
            # Create a new blank image for the current frame
            frame_image = Image.new("RGB", (width, height), "white")  # Clear previous frame
            draw = ImageDraw.Draw(frame_image)

            # Render all layers for the current frame in the correct order (bottom to top)
            for layer in reversed(self.layers):  # Reverse the order of layers
                if layer["hidden"]:
                    continue  # Skip hidden layers

                if frame_index >= len(layer["frames"]):
                    continue  # Skip if frame does not exist in the layer

                layer_frame = layer["frames"][frame_index]
                for line in layer_frame["lines"]:
                    points = line["p"]
                    tool = line["d"]

                    # Extract tool properties
                    color = tool.get("c", "#000000")
                    width = tool.get("w", 1)
                    t = tool.get("t", 1)  # Default to 1 if not specified

                    if t == 1:  # Simple line
                        for i in range(0, len(points) - 2, 2):
                            draw.line(
                                [(points[i], points[i + 1]), (points[i + 2], points[i + 3])],
                                fill=color,
                                width=width,
                            )
                    elif t == 2:  # Fill (closed polygon)
                        if len(points) >= 6:  # Minimum points for a closed polygon
                            polygon_points = [(points[i], points[i + 1]) for i in range(0, len(points), 2)]
                            draw.polygon(polygon_points, fill=color)

            # Rescale the current frame to 640x360
            frame_image = frame_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

            # Append the rendered and resized frame to the images list
            images.append(frame_image)

        if not images:
            return None  # Return None if there are no frames to render

        # Save or return raw binary data
        if filename is None:
            # Save to an in-memory bytes buffer
            gif_buffer = io.BytesIO()
            images[0].save(
                gif_buffer,
                format="GIF",
                save_all=True,
                append_images=images[1:],
                optimize=False,
                duration=frame_duration,
                loop=0,  # Infinite loop
            )
            gif_buffer.seek(0)  # Reset buffer to the beginning
            return gif_buffer.read()  # Return raw binary data
        else:
            # Save to a file
            images[0].save(
                filename,
                save_all=True,
                append_images=images[1:],
                optimize=False,
                duration=frame_duration,
                loop=0,  # Infinite loop
            )
            return None


    def Save(self, title="Draft", description="", draft=True, scrible=True, nsfw=False, dat=None):
        s = requests.Session()
        s.cookies.set("PHPSESSID", self.session)

        data= {
                "name": title, 
                "description": description, 
                "nsfw": int(nsfw), 
                "scribble": int(scrible), 
                "hidden": int(draft), 
            }
        
        if self.edit != None:
            data["edit"] = self.edit
        if not dat:
            to = self.Generate(True)
        else:
            to = dat
        print("Sending", len(to))
        resp = s.post("https://toonio.ru/Server/Save2", 
            files={
                "toon": ('toon', to, 'application/octet-stream'),
                "preview": ('preview', self.CreateGif(), 'image/gif') 
            }, 
            data=data
        )

        data = json.loads(resp.text)

        if "id" in data:
            return data["id"]
        elif "error" in data:
            raise ValueError(data["error"])
            return
        else:
            raise ValueError("An error occured")
