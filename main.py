__plugin_name__      = "RedstonerUtils"
__plugin_version__   = "3.0"
__plugin_mainclass__ = "foobar"

import sys
from traceback import format_exc as print_traceback

# damn pythonloader changed the PATH
sys.path += ['', '/usr/lib/python2.7', '/usr/lib/python2.7/plat-linux2', '/usr/lib/python2.7/lib-tk', '/usr/lib/python2.7/lib-old', '/usr/lib/python2.7/lib-dynload', '/usr/local/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages', '/usr/lib/pymodules/python2.7', '/usr/lib/pyshared/python2.7']

try:
    # Library that adds a bunch of re-usable methods which are used in nearly all other modules
    from helpers import *
except:
    print("[RedstonerUtils] ERROR: Failed to import helpers:")
    print(print_traceback())



@hook.enable
def on_enable():
    if "blockplacemods" in shared["modules"]:
        shared["modules"]["blockplacemods"].schedule_torch_breaker()
    if "imbusy" in shared["modules"]:
        shared["modules"]["imbusy"].replace_ess_commands()
    if "serversigns" in shared["modules"]:
        shared["modules"]["serversigns"].check_all_signs_and_force_commands()
    info("RedstonerUtils enabled!")


@hook.disable
def on_disable():
    if "reports" in shared["modules"]:
        shared["modules"]["reports"].stop_reporting()
    info("RedstonerUtils disabled!")


info("Loading RedstonerUtils...")

# Import all modules, in this order
shared["load_modules"] = [
    # Collection of tiny utilities
    "misc",
    # Adds chat for staff using /ac <text or ,<text>
    "adminchat",
    # Adds /badge, allows to give players achievements
    "badges",
    # Adds a few block placement corrections/mods
    "blockplacemods",
    # Adds /calc, toggles automatic solving of Math expressions in chat
    "calc",
    # Adds aliasing of chat words
    "chatalias",
    # For players to point friends
    "friends",
    # Plugin to locate laggy chunks. /lc <n> lists chunks with more than n entities
    "lagchunks",
    # Adds /report and /rp, Stores reports with time and location
    "reports",
    # Adds group-chat with /chatgroup and /cgt to toggle normal chat into group mode
    "chatgroups",
    # Adds /token, reads and writes from the database to generate pronouncable (and thus memorable) registration-tokens for the website
    "webtoken",
    # Adds /lol, broadcasts random funyy messages. A bit like the splash text in the menu
    "saylol",
    # Adds /signalstrength, lets you request a signal strength and an amount of items will be inserted into target container to meet that strength.
    "signalstrength",
    # Shows the owner of a skull when right-clicked
    "skullclick",
    # Adds /listen, highlights chat and plays a sound when your name was mentioned
    "mentio",
    # Adds /cycler, swaps the hotbar with inventory when player changes slot from right->left or left->right
    "cycle",
    # Adds /getmotd & /setmotd to update the motd on the fly (no reboot)
    "motd",
    # AnswerBot. Hides stupid questions from chat and tells the sender about /faq or the like
    "abot",
    # Adds '/forcefield', creates forcefield for players who want it.
    "forcefield",
    # Adds /damnspam, creates timeout for buttons/levers to mitigate button spam.
    "damnspam",
    # Adds /check, useful to lookup details about a player
    "check",
    # Adds /an, a command you can use to share thoughts/plans/news
    "adminnotes",
    # Adds busy status to players
    "imbusy",
    # Adds /imout, displays fake leave/join messages
    "imout",
    #adds snowbrawl minigame
    "snowbrawl",
    # Adds /tm [player] for a messages to be sent to this player via /msg
    "pmtoggle",
    # Replacement for LoginSecurity
    "loginsecurity",
    # Centralized Player class
    "player",
    # Servercontrol extension for telnet access to logs/AC
    #"servercontrol",
    # Script helper plugin
    "scriptutils",
    # Per-player notes
    "tag",
    # vanish toggle module - temporary fix
    #"vanishfix",
    # obisidian mining punishment plugin
    "punishments",
    # a simple replacement for the buggy essentials /vanish
    "vanish",
    # ip-tracking utility - disabled as of instability
    #"iptracker",
    #server signs for everyone
    "serversigns",
    # Makes player's names colored, sorts tab list by rank
    "nametags"
]
shared["modules"] = {}
for module in shared["load_modules"]:
    try:
        shared["modules"][module] = __import__(module)
        info("Module %s loaded." % module)
    except:
        error("Failed to import module %s:" % module)
        error(print_traceback())
