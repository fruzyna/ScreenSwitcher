import subprocess
import sys
from os.path import isfile, join, splitext

def runCommand(bashCmd):
    print("Running command: " + bashCmd)
    process = subprocess.Popen(bashCmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

class Mode(object):
    name = ""
    screens = []
    sink = ""
    options = []
    def __init__(self, str):
        parts = str.split(':')
        self.name = parts[0]
        self.screens = parts[1].split(',')
        self.sink = parts[2]
        self.options = parts[3].split(',')

class Screen(object):
    name = ""
    port = ""
    def __init__(self, str):
        parts = str.split(':')
        self.name = parts[0]
        self.port = parts[1]

class Sink(object):
    name = ""
    port = ""
    def __init__(self, str):
        parts = str.split(':')
        self.name = parts[0]
        self.port = parts[1]

modesFile = open("modes.cfg", 'r').read().split('\n')
modes = [Mode(l) for l in modesFile if ":" in l and l[0] is not '#']

screensFile = open("screens.cfg", 'r').read().split('\n')
screens = [Screen(l) for l in screensFile if ":" in l and l[0] is not '#']

speakersFile = open("speakers.cfg", 'r').read().split('\n')
sinks = [Sink(l) for l in speakersFile if ":" in l and l[0] is not '#']

# match up
for m in modes:
    ports = []
    for s in m.screens:
        for p in screens:
            if s == p.name:
                ports.append(p.port)
    m.screens = ports
    for s in sinks:
        if s.name == m.sink:
            m.sink = s.port

command = sys.argv[1]

if command == "set":
    modeNm = sys.argv[2]
    mode = Mode("None:none:none:none")
    for m in modes:
        if m.name == modeNm:
            mode = m
    if mode.name != "None":
        for screen in screens:
            if screen.port in mode.screens:
                runCommand("xrandr --output " + screen.port + " --auto")
                order = mode.screens.index(screen.port)
                if order == 0:
                    runCommand("xrandr --output " + screen.port + " --primary")
                else:
                    runCommand("xrandr --output " + screen.port + " --right-of " + mode.screens[order - 1])
            else:
                runCommand("xrandr --output " + screen.port + " --off")

        runCommand("pacmd set-default-sink " + mode.sink)

        if "bigpic" in mode.options:
            runCommand("steam -start steam://open/bigpicture")
        if "steam" in mode.options:
            runCommand("steam")
    else:
        print("No mode \"" + modeNm + "\" exists!")
elif command == "screen":
    screen = sys.argv[2]
    for s in screens:
        if s.name == screen:
            runCommand("xrandr --output " + s.port + " --auto")
            runCommand("xrandr --output " + s.port + " --primary")
        else:
            runCommand("xrandr --output " + s.port + " --off")
elif command == "audio":
    sink = sys.argv[2]
    for s in sinks:
        if s.name == sink:
            runCommand("pacmd set-default-sink " + s.port)
elif command == "help":
    print("Commands: \nset [mode] \nscreen [screen] \naudio [speaker]")
else:
    print("No command \"" + command + "\" exists")