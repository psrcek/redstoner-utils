# TODO: Add cg/ac/msg support

import os
import mysqlhack
import org.bukkit as bukkit
from org.bukkit import *
from helpers import *

# Version number and requirements

alias_version = "2.1.0"
helpers_versions = ["1.1.0", "2.0.0"]
enabled = False
error_msg = colorify("&cUnspecified error")
commands_per_page = 5
global_aliases = {"./":"/"}
data = {}
use_mysql = True

# Permissions:

# Grants full access immediately
permission_ALL = "utils.alias.*"
# Access to the command to display the help screen
permission_BASE = "utils.alias"
# Make replacements only when the user has this permission
permission_USE = "utils.alias.use"
# Modify aliases
permission_MODIFY = "utils.alias.modify"
permission_MODIFY_OTHERS = "utils.alias.modify.others"
# List aliases
permission_LIST = "utils.alias.list"
permission_LIST_OTHERS = "utils.alias.list.others"
# Set alias amounts/length limits, e.g. utils.alias.amount.420
permission_AMOUNT = "utils.alias.amount."
permission_LENGTH = "utils.alias.length."
# See when the plugin was disabled due to version errors
permission_INFO = "utils.alias.info"
permission_FINFO = "utils.alias.finfo"

########
# CODE #
########

def safe_open_json(uuid):
    if not os.path.exists("plugins/redstoner-utils.py.dir/files/aliases"):
        os.makedirs("plugins/redstoner-utils.py.dir/files/aliases")
    value = open_json_file("aliases/" + uuid)
    if value is None:
        value = dict(global_aliases)
        save_json_file("aliases/" + uuid, value)
    return value


@hook.command("alias",
              usage="/<command> <add, remove, list, help> [...]",
              desc="Allows aliasing of words")
def on_alias_command(sender, cmd, label, args):
    if not is_player(sender):
        msg(sender, "&cThe console cannot use aliases!")
        return True
    try:
        args = array_to_list(args)
        if not enabled:
            disabled_fallback(sender)
            return True
        if not hasPerm(sender, permission_BASE):
            plugin_header(recipient=sender, name="Alias")
            noperm(sender)
            return True
        return subcommands[args[0].lower()](sender, args[1:])
    except:
        return subcommands["help"](sender, "1")


def help(sender, args):
    commands = [colorify("&e/alias help [page]")]
    if hasPerm(sender, permission_LIST):
        commands += [colorify("&e/alias list &7- Lists all your aliases")]
    if hasPerm(sender, permission_MODIFY):
        commands += [colorify("&e/alias add <word> <alias> &7- Add an alias")]
        commands += [colorify("&e/alias remove <word> &7- Remove an alias")]
    if can_remote(sender):
        while len(commands) < commands_per_page:
            commands += [""]
        commands += [colorify("&7Following commands will be executed on <player> yet all output will be redirected to you, except when you set silent to false, then <player> will see it too.")]
    if hasPerm(sender, permission_LIST_OTHERS):
        commands += [colorify("&e/alias player <name> list [silent]")]
    if hasPerm(sender, permission_MODIFY_OTHERS):
        commands += [colorify("&e/alias player <name> add <word> <alias> [silent]")]
        commands += [colorify("&e/alias player <name> remove <word> [silent]")]
    pages = (len(commands)-1)/commands_per_page + 1
    page = 1
    if len(args) != 0:
        page = int(args[0])
    if (page > pages):
        page = pages
    if page < 1:
        page = 1
    msg(sender, colorify("&e---- &6Help &e-- &6Page &c" + str(page) + "&6/&c" + str(pages) + " &e----"))
    page -= 1
    to_display = commands[5*page:5*page+5]
    for message in to_display:
        msg(sender, message)
    if page+1 < pages:
        msg(sender, colorify("&6To display the next page, type &c/alias help " + str(page+2)))
    return True


@hook.event("player.PlayerJoinEvent", "high")
def on_join(event):
    if enabled:
        t = threading.Thread(target=load_data, args=(uid(event.getPlayer()), ))
        t.daemon = True
        t.start()
    else:
        if event.getPlayer().hasPermission(permission_FINFO):
            disabled_fallback(event.getPlayer())


@hook.event("player.AsyncPlayerChatEvent", "high")
def on_player_chat(event):
    try:
        if enabled:
            if event.isCancelled():
                return
            player = event.getPlayer() 
            if not hasPerm(player, permission_USE):
                return
            msg_limit = int(get_permission_content(player, permission_LENGTH))
            for alias, value in data[uid(player)].iteritems():
                if player.hasPermission("essentials.chat.color"):
                    event.setMessage(event.getMessage().replace(colorify(alias), colorify(value)))
                else:
                    event.setMessage(event.getMessage().replace(alias, value))
                if not player.hasPermission(permission_ALL) and len(event.getMessage()) > msg_limit:
                    event.setCancelled(True)
                    plugin_header(player, "Alias")
                    msg(player, "The message you wanted to generate would exceed the length limit limit of %d. Please make it shorter!" % msg_limit)
                    return
    except:
        error(trace())


def hasPerm(player, permission):
    return (player.hasPermission(permission)) or (player.hasPermission(permission_ALL))


def disabled_fallback(receiver):
    if not hasPerm(receiver, permission_INFO):
        msg(receiver, colorify("&cUnknown command. Use &e/help&c, &e/plugins &cor ask a mod."))
    else:
        msg(receiver, colorify("&cPlugin alias v" + alias_version + " has experienced an &eEMERGENCY SHUTDOWN:"))
        msg(receiver, error_msg)
        msg(receiver, colorify("&cPlease contact a dev/admin (especially pep :P) about this to take a look at it."))


def can_remote(player):
    return hasPerm(player, permission_LIST_OTHERS) or hasPerm(player, permission_MODIFY_OTHERS)


def add(sender, args):
    plugin_header(sender, "Alias")
    uuid = uid(sender)
    args = [args[0]] + [" ".join(args[1:])]
    if (args[0] not in data[uuid]) and is_alias_limit_reached(sender, sender):
        return True
    if not add_alias_data(uuid, str(args[0]), args[1]):
        msg(sender, colorify("&c") + "Could not add this alias because it would cause some sequences to be replaced multiple times", usecolor = False)
        return True
    msg(sender, colorify("&7Alias: ") + args[0] + colorify("&7 -> " + args[1] + colorify("&7 was succesfully created!")), usecolor=sender.hasPermission("essentials.chat.color"))
    return True


def radd(sender, args):
    plugin_header(sender, "Alias")
    args = args[0:2] + [" ".join(args[2:len(args)-1])] + [args[len(args)-1]]
    if is_player(sender):
        sender_name = colorify(sender.getDisplayName())
    else:
        sender_name = colorify("&6Console")
    target = server.getPlayer(args[0])
    if target == None:
        msg(sender, "&cThat player is not online")
        return True
    uuid = uid(target)
    if args[3].lower() == "false":
        plugin_header(target, "Alias")
        msg(target, "&cPlayer " + sender_name + " &cis creating an alias for you!")
    elif args[3].lower() != "true":
        args[2] += " " + args[3]
    if (args[1] not in data[uuid]) and is_alias_limit_reached(target, sender, args[3].lower() == "false"):
        return True
    if len(args) == 3:
        args += ["true"]
    if not add_alias_data(uuid, str(args[1]), str(args[2])):
        message = colorify("&c") + "Could not add this alias because it would cause some sequences to be replaced multiple times"
        msg(sender, message)
        if args[3].lower() == "false":
            msg(target, message)
        return True
    msg(sender, colorify("&7Alias: ") + args[1] + colorify("&7 -> " + args[2] + colorify("&7 was succesfully created!")), usecolor=target.hasPermission("essentials.chat.color"))
    if args[3].lower() == "false":
        msg(target, colorify("&7Alias: ") + args[1] + colorify("&7 -> " + args[2] + colorify("&7 was succesfully created!")), usecolor=target.hasPermission("essentials.chat.color"))
    return True


def is_alias_limit_reached(player, recipient, not_silent = False):
    if player.hasPermission(permission_ALL):
        return False
    alias_limit = int(get_permission_content(player, permission_AMOUNT))
    if len(data[uid(player)]) >= alias_limit:
        message = ("&cYour limit of %d has been reached" if player is recipient else "&cThe limit of %d has been reached for that player") % alias_limit
        msg(recipient, message)
        if not_silent:
            msg(player, message)
        return True
    return False


def add_alias_data(puuid, aliased, new_alias):
    prior = data[puuid]

    # prevent 2 -> 3 if there is 1 -> 2
    if aliased not in prior:
        for alias in prior.values():
            if aliased in alias:
                return False

    # prevent 1 -> 2 if there is 2 -> 3
    for sequence in prior:
        if sequence in new_alias:
            return False

    prior[aliased] = new_alias
    save_data(puuid)
    return True


def remove(sender, args):
    plugin_header(sender, "Alias")
    try:
        msg(sender, colorify("&7Successfully removed alias ") + args[0] + colorify(" &7-> ") + data[uid(sender)].pop(args[0]) + colorify("&7!"), usecolor=sender.hasPermission("essentials.chat.color"))
        save_data(uid(sender))
    except:
        msg(sender, colorify("&cCould not remove alias ") + args[0] + colorify(", it does not exist."), usecolor=sender.hasPermission("essentials.chat.color"))
    return True


def rremove(sender, args):
    plugin_header(sender, "Alias")
    target = get_player(args[0])
    if is_player(sender):
        sender_name = colorify(sender.getDisplayName())
    else:
        sender_name = colorify("&6Console")
    if args[2].lower() == "false":
        plugin_header(target, "Alias")
        msg(target, "&cPlayer " + sender_name + " &cis removing an alias for you!")
    try:
        alias = data[uid(target)].pop(args[1])
        msg(sender, colorify("&7Successfully removed alias ") + args[1] + colorify(" &7-> ") + alias + colorify("&7!"), usecolor=sender.hasPermission("essentials.chat.color"))
        if args[2].lower() == "false":
            msg(target, colorify("&7Successfully removed alias ") + args[1] + colorify(" &7-> ") + alias + colorify("&7!"), usecolor=sender.hasPermission("essentials.chat.color"))
        save_data(uid(target))
    except:
        msg(sender, colorify("&cCould not remove alias ") + args[1] + colorify(", it does not exist."), usecolor=sender.hasPermission("essentials.chat.color"))
        if args[2].lower() == "false":
            msg(target, colorify("&cCould not remove alias ") + args[1] + colorify(", it does not exist."), usecolor=sender.hasPermission("essentials.chat.color"))
    return True


def list_alias(sender, args):
    plugin_header(sender, "Alias")
    msg(sender, "&7You have a total of " + str(len(data[uid(sender)])) + " aliases:")
    for word, alias in data[str(uid(sender))].items():
        msg(sender, colorify("&7") + word + colorify("&7 -> ") + alias, usecolor=sender.hasPermission("essentials.chat.color"))
    return True


def rlist_alias(sender, args):
    plugin_header(sender, "Alias")
    target = get_player(args[0])
    if is_player(sender):
        sender_name = colorify(sender.getDisplayName())
    else:
        sender_name = colorify("&6Console")
    if len(args) == 1:
        args += ["true"]
    msg(sender, "Player " + args[0] + " has following aliases (" + str(len(data[uid(target)])) + " in total):")
    if args[1].lower() == "false":
        plugin_header(target, "Alias")
        msg(target, "&cPlayer " + sender_name + " &cis listing your aliases")
    for word, alias in data[str(uid(target))].items():
        msg(sender, colorify("&7") + word + colorify("&7 -> ") + alias, usecolor=target.hasPermission("essentials.chat.color"))
    return True


def remote(sender, args):
    try:
        return remotes[args[1].lower()](sender, [args[0]] + args[2:])
    except:
        return subcommands["help"](sender, ["2"])


def load_data(uuid):
    if use_mysql:
        try:
            t = threading.Thread(target=load_data_thread, args=(uuid,))
            t.daemon = True
            t.start()
        except:
            error(trace())
    else:
        data[uuid] = safe_open_json(uuid)

def load_data_thread(uuid):
    conn = zxJDBC.connect(mysql_database, mysql_user, mysql_pass, "com.mysql.jdbc.Driver")
    curs = conn.cursor()
    curs.execute("SELECT `alias` FROM `chatalias` WHERE `uuid` = ?;", (uuid, ))
    results = curs.fetchall()
    curs.close()
    conn.close()
    if len(results) == 0:
        value = dict(global_aliases)
    else:
        value = json_loads(results[0][0])
    data[uuid] = value


def save_data(uuid):
    if use_mysql:
        try:
            t = threading.Thread(target=save_data_thread, args=(uuid,))
            t.daemon = True
            t.start()
        except:
            error(trace())
    else:
        save_json_file("aliases/" + uuid, data[uuid])

def save_data_thread(uuid):
    conn = zxJDBC.connect(mysql_database, mysql_user, mysql_pass, "com.mysql.jdbc.Driver")
    curs = conn.cursor()
    value = json_dumps(data[uuid])
    curs.execute("INSERT INTO `chatalias` VALUES (?, ?) ON DUPLICATE KEY UPDATE `alias` = ?;", 
        (uuid, value, value))
    conn.commit()
    curs.close()
    conn.close()


# Subcommands:
subcommands = {
    "help": help,
    "?": help,
    "add": add,
    "remove": remove,
    "del": remove,
    "delete": remove,
    "player": remote,
    "remote": remote,
    "list": list_alias
}

remotes = {
    "add": radd,
    "remove": rremove,
    "del": rremove,
    "delete": rremove,
    "list": rlist_alias,
}

# OnModuleLoad

enabled = helpers_version in helpers_versions
if not enabled:
    error_msg = colorify("&6Incompatible versions detected (&chelpers.py&6)")
for player in server.getOnlinePlayers():
    if enabled:
        t = threading.Thread(target=load_data, args=(uid(player), ))
        t.daemon = True
        t.start()
    else:
        if player.hasPermission(permission_FINFO):
            disabled_fallback(player)
