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
    writeConfigFile('screens.cfg', False)

    # Generates speakers config
    writeConfigFile('speakers.cfg', False)

    # Generates modes config
    writeConfigFile('modes.cfg', False)

    print('\nConfig saved to ' + path)

# Prints a nice header
def printHeader(title):
    print('\n' + title + '\n---')

# Helps user build monitors config file
def getMonitors():
    input('Press Enter when all displays are connected')
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
        print()
    return cfgLines

functions = {'screens.cfg': getMonitors,
                'speakers.cfg': getSinks,
                'modes.cfg': makeModes}

headers = {'screens.cfg': '# Name:port (via xrandr)',
                'speakers.cfg': '# Name:sink (via pactl list short sinks)',
                'modes.cfg': '# Mode Name:List,of,screens:Audio Sink:Options,other option'}

# Creates a config file
def writeConfigFile(name, append):
    outType = 'w+'
    if append:
        outType = 'a'
    file = open(join(path, name), outType)
    if not append:
        file.write(headers[name])
    out = functions[name]()
    file.write(out)
    file.close()

#
# Objects
#

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

#
# Command Functions
#

# Sets the display mode
def set_cmd():
    modeNm = sys.argv[2]
    mode = Mode("None:none:none:none")

    # Finds the matching mode object
    for m in modes:
        if m.name.upper() == modeNm.upper():
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

# Enables only the given screen
def screen_cmd():
    screen = sys.argv[2]
    found = False
    for s in screens:
        if s.name.upper() == screen.upper():
            runCommand("xrandr --output " + s.port + " --auto")
            runCommand("xrandr --output " + s.port + " --primary")
            found = True
            break;
    if found:
        for s in screens:
            if s.name.upper() != screen.upper():
                runCommand("xrandr --output " + s.port + " --off")
    else:    
        print('Screen', screen, 'not found!')

# Enables only the given sink
def audio_cmd():
    sink = sys.argv[2]
    for s in sinks:
        if s.name.upper() == sink.upper():
            runCommand("pacmd set-default-sink " + s.port)
            return
    print('Sink', sink, 'not found!')

# List all options for a given object type
def list_cmd():
    obj = sys.argv[2]
    if obj == 'screens':
        printHeader('Available Screens')
        for s in screens:
            print(s.name + ' on ' + s.port)
    elif obj == 'sinks':
        printHeader('Available Audio Sinks')
        for s in sinks:
            print(s.name + ' on ' + s.port)
    elif obj == 'modes':
        printHeader('Available Modes')
        for m in modes:
            print(m.name)
            print('\tScreens:\t' + ','.join(m.screens))
            print('\tAudio Sink:\t' + m.sink)
            print('\tOptions:\t' + ','.join(m.options))
    else:
        print('Invalid object "' + obj + '". Please choose from screens, (audio) sinks, and modes.')

# Allows the user to rerun setup of a config file
def reset_cmd():
    obj = sys.argv[2]
    if obj == 'screens':
        writeConfigFile('screens.cfg', False)
    elif obj == 'sinks':
        writeConfigFile('speakers.cfg', False)
    elif obj == 'modes':
        writeConfigFile('modes.cfg', False)
    elif obj == 'all':
        init()
    else:
        print('Invalid object "' + obj + '". Please choose from screens, (audio) sinks, and modes.')

# Allows the user to continue adding new modes
def add_cmd():
    obj = sys.argv[2]
    if obj == 'modes':
        writeConfigFile('modes.cfg', True)
    else:
        print('Invalid object "' + obj + '". Please choose from modes.')

# Displays help options
def help_cmd():
    print("Commands: \nset [mode] \nscreen [screen] \naudio [speaker] \ninit \nlist [screens/sinks/modes] \nreset [screens/sinks/modes/all] \nadd [modes]")

#
# Command Execution
#

# Gets the command
command = 'no command given'
if len(sys.argv) > 1:
    command = sys.argv[1]

commands = {'set': set_cmd,
            'screen': screen_cmd,
            'audio': audio_cmd,
            'list': list_cmd,
            'init': init,
            'reset': reset_cmd,
            'add': add_cmd,
            'help': help_cmd}

# Runs the command or prints an error
if command in commands:
    commands[command]()
else:
    print('Invalid command "' + command + '".')
    help_cmd()
