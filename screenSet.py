import subprocess
import sys
from os.path import isfile, join, splitext

def runCommand(bashCmd):
    process = subprocess.Popen(bashCmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

screensFile = open("screens.cfg", 'r')
screens = screensFile.read().split('\n')
monitors = [l.split(':')[0] for l in screens if ":" in l]
ports = [l.split(':')[1] for l in screens if ":" in l]

setupsFile = open("modes.cfg", 'r')
setups = setupsFile.read().split('\n')
modes = [l.split(':')[0] for l in setups if ":" in l]
mConfig = [l.split(':')[1] for l in setups if ":" in l]
mOptions = [l.split(':')[2] for l in setups if ":" in l]

command = sys.argv[1]

if command == "set":
    mode = sys.argv[2]
    for i,m in enumerate(modes, start=0):
        if m == mode:
            mScreens = mConfig[i].split(',')
            for j,screen in enumerate(monitors, start=0):
                port = ports[j]
                if screen in mScreens:
                    runCommand("xrandr --output " + port + " --auto")
                    order = mScreens.index(screen)
                    if order == 0:
                        runCommand("xrandr --output " + port + " --primary")
                    else:
                        runCommand("xrandr --output " + port + " --right-of " + ports[monitors.index(mScreens[order - 1])])
                else:
                    runCommand("xrandr --output " + port + " --off")
            if mOptions[i] == "Steam":
                runCommand("steam -start steam://open/bigpicture")
elif command == "only":
    screen = sys.argv[2]
    for i,s in enumerate(monitors, start=0):
        if(s == screen):
            runCommand("xrandr --output " + ports[i] + " --auto")
            runCommand("xrandr --output " + ports[i] + " --primary")
        else:
            runCommand("xrandr --output " + ports[i] + " --off")