import subprocess
import sys
from os.path import isfile, join, splitext

def runCommand(bashCmd):
    print("Running command: " + bashCmd)
    process = subprocess.Popen(bashCmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

screensFile = open("screens.cfg", 'r').read().split('\n')
screenNames = [l.split(':')[0] for l in screensFile if ":" in l]
screenPorts = [l.split(':')[1] for l in screensFile if ":" in l]

speakersFile = open("speakers.cfg", 'r').read().split('\n')
speakerNames = [l.split(':')[0] for l in speakersFile if ":" in l]
speakerPorts = [l.split(':')[1] for l in speakersFile if ":" in l]

modesFile = open("modes.cfg", 'r').read().split('\n')
modeNames = [l.split(':')[0] for l in modesFile if ":" in l]
modeScreens = [l.split(':')[1] for l in modesFile if ":" in l]
modeSpeakers = [l.split(':')[2] for l in modesFile if ":" in l]
modeOps = [l.split(':')[3] for l in modesFile if ":" in l]

command = sys.argv[1]

if command == "set":
    mode = sys.argv[2]
    if mode in modeNames:
        modeNum = modeNames.index(mode)
        screens = modeScreens[modeNum].split(',')
        for screenNum,screen in enumerate(screenNames, start=0):
            port = screenPorts[screenNum]
            if screen in screens:
                runCommand("xrandr --output " + port + " --auto")
                order = screens.index(screen)
                if order == 0:
                    runCommand("xrandr --output " + port + " --primary")
                else:
                    runCommand("xrandr --output " + port + " --right-of " + screenPorts[screenNames.index(screens[order - 1])])
            else:
                runCommand("xrandr --output " + port + " --off")
        speakers = modeSpeakers[modeNum]
        for speakerNum,speaker in enumerate(speakerNames, start=0):
            jack = speakerPorts[speakerNum]
            if speaker == speakers:
                runCommand("pacmd set-default-sink " + jack)
        op = modeOps[modeNum]
        if op == "Steam":
            print("Launching Steam")
            runCommand("steam -start steam://open/bigpicture")
    else:
        print("No mode \"" + mode + "\" exists!")
elif command == "only":
    screen = sys.argv[2]
    for i,s in enumerate(monitors, start=0):
        if(s == screen):
            runCommand("xrandr --output " + ports[i] + " --auto")
            runCommand("xrandr --output " + ports[i] + " --primary")
        else:
            runCommand("xrandr --output " + ports[i] + " --off")
else:
    print("No command \"" + command + "\" exists")
