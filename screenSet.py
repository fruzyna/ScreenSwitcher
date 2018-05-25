import sys
import subprocess
from os.path import isfile, join, splitext, expanduser, exists
from os import mkdir, listdir

# Sets the config directory
path = expanduser('~/.config/Screen-Switcher')

# Runs a bash command and returns the output
def runCommand(bashCmd):
    #print("Running command: " + bashCmd)
    proc = subprocess.Popen(bashCmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return out.decode('utf-8')

# Builds a set of config files
def init():
    if not exists(path):
        mkdir(path)

    # Generates screens config
    file = open(join(path, 'screens.cfg'), 'w+')
    file.write('# Name:port (via xrandr)')
    file.write(getMonitors())
    file.close()

    # Generates speakers config
    file = open(join(path, 'speakers.cfg'), 'w+')
    file.write('# Name:sink (via pactl list short sinks)')
    file.write(getSinks())
    file.close()

    # Generates modes config
    file = open(join(path, 'modes.cfg'), 'w+')
    file.write('# Mode Name:List,of,screens:Audio Sink:Options,other option')
    file.write(makeModes())
    file.close()

    print('\nConfig saved to ' + path)

# Prints a nice header
def printHeader(title):
    print('\n' + title + '\n---')

# Helps user build monitors config file
def getMonitors():
    printHeader('Initializing Displays')
    output = runCommand('xrandr --listmonitors')
    cfgLines = ''
    for line in output.split('\n'):
        if line.count('x') > 0:
            parts = line.split()
            port = parts[-1]
            res = parts[-2].split('x')
            width = res[0].split('/')[0]
            height = res[1].split('/')[0]
            name = input('Name ' + width + 'x' + height + ' monitor on ' + port + ': ')
            cfgLines += '\n' + name + ':' + port
    return cfgLines

# Helps user build speakers config file
def getSinks():
    printHeader('Initializing Audio Sinks')
    output = runCommand('pactl list short sinks')
    cfgLines = ''
    for line in output.split('\n'):
        if line.count('alsa') > 0:
            parts = line.split()
            port = parts[1]
            name = input('Name ' + port + ': ')
            cfgLines += '\n' + name + ':' + port
    return cfgLines

# Helps user build modes config file
def makeModes():
    printHeader('Initializing Modes')
    cfgLines = ''
    while 1:
        name = input('New mode name (blank for stop): ')
        if len(name) == 0:
            break
        order = input('Order of monitors (separated by commas): ')
        sink = input('Audio Sink: ')
        options = input('Options (separated by commas): ')
        if len(options) == 0:
            options = 'none'
        cfgLines += '\n' + name + ':' + order + ':' + sink + ':' + options
    return cfgLines

# Objects
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

# Starts config file builder if config directory does not exits
if not exists(path):
    init()
    sys.exit()

# Reads and creates objects from all config files
modesFile = open(join(path, 'modes.cfg'), 'r').read().split('\n')
modes = [Mode(l) for l in modesFile if ":" in l and l[0] is not '#']

screensFile = open(join(path, 'screens.cfg'), 'r').read().split('\n')
screens = [Screen(l) for l in screensFile if ":" in l and l[0] is not '#']

speakersFile = open(join(path, 'speakers.cfg'), 'r').read().split('\n')
sinks = [Sink(l) for l in speakersFile if ":" in l and l[0] is not '#']

# Match up modes to outputs
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

# Gets the command
command = sys.argv[1]

# Executes based on command
if command == "set":
    # Sets the display mode
    modeNm = sys.argv[2]
    mode = Mode("None:none:none:none")

    # Finds the matching mode object
    for m in modes:
        if m.name == modeNm:
            mode = m

    # If the mode was found, implement it
    if mode.name != "None":
        for screen in screens:
            if screen.port in mode.screens:
                # Adds the screen if it is there
                runCommand("xrandr --output " + screen.port + " --auto")
                order = mode.screens.index(screen.port)
                
                if order == 0:
                    # The first given screen is primary
                    runCommand("xrandr --output " + screen.port + " --primary")
                else:
                    # Orders all other screens to the right of the last
                    runCommand("xrandr --output " + screen.port + " --right-of " + mode.screens[order - 1])
            else:
                # Turns the screen off it is wasn't there
                runCommand("xrandr --output " + screen.port + " --off")

        # Updates the audio sink
        runCommand("pacmd set-default-sink " + mode.sink)

        # Runs extra options
        if "bigpic" in mode.options:
            # Opens steam in big picture mode
            runCommand("steam -start steam://open/bigpicture")
        elif "steam" in mode.options:
            # Opens steam, not valid if already opening in big picture
            runCommand("steam")
    else:
        print("No mode \"" + modeNm + "\" exists!")
elif command == "screen":
    # Enables only the given screen
    screen = sys.argv[2]
    for s in screens:
        if s.name == screen:
            runCommand("xrandr --output " + s.port + " --auto")
            runCommand("xrandr --output " + s.port + " --primary")
        else:
            runCommand("xrandr --output " + s.port + " --off")
elif command == "audio":
    # Enables only the given sink
    sink = sys.argv[2]
    for s in sinks:
        if s.name == sink:
            runCommand("pacmd set-default-sink " + s.port)
elif command == "init":
    # Re-runs the initialization script
    init()
elif command == "help":
    # Displays help options
    print("Commands: \nset [mode] \nscreen [screen] \naudio [speaker] \ninit")
else:
    # Error
    print('No command "' + command + '" exists')