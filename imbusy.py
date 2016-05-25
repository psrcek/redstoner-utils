# I'M BUSY! Plugin by Curs3d #
##############################
# Concept by CookieManors :D #
# http://bit.ly/1GnNPW8      #
##############################
# This plugin permits users to
# send a command that renders
# them "busy", not letting them
# to get tpa requests or direct
# messages, except from console.
# On restart, all busy data will
# be cleared.

from helpers import *
from basecommands import simplecommand
import org.bukkit.command.Command as Command
from traceback import format_exc as trace

busy_players = []


def unclear(sender):
    msg(sender, "Umm, what? Sorry, directions unclear, got head stuck in washing machine")


@hook.command("busy",
    aliases = ["focus"],
    usage = "/<command> <on|off|status>",
    description = "Sets busy mode on, you cannot recieve tpas and MSGs"
    )
def on_busy_command(sender, cmd, label, args):

    if not is_player(sender):
       msg(sender, "Sorry, Console cannot be busy")
       return True

    plugin_header(recipient = sender, name = "I'M BUSY!")

    if not sender.hasPermission("utils.busy.allowed"):
        noperm(sender)
        return True

    if len(args) == 0:
        msg(sender, "This plugin allows being busy, and when turned on you will not receive any direct messages or tpa requests.")
        msg(sender, "\nCommands:")
        msg(sender, "/busy on: turns on busy mode")
        msg(sender, "/busy off: turns off busy mode")
        msg(sender, "/busy status [player]: shows your or [player]'s current busy status.")

    elif len(args) == 1:
        if args[0] == "on":
            if sender.getName() in busy_players:
                msg(sender, "You cannot be even more focused than this without being a jedi!")
            else:
                busy_players.append(sender.getName())
                broadcast(None, "&c[&2Busy&c] &fNow busy: %s&r, don't even TRY bothering them!" % sender.getDisplayName())

        elif args[0] == "off":
            try:
                busy_players.remove(sender.getName())
                msg(sender, "Master has sent /busy command, %s&r is freeee of bothering!" % sender.getDisplayName())
            except ValueError:
                msg(sender, "You are not busy! You cannot be even less busy! Are you perhaps bored?")

        elif args[0] == "status":
            if sender.getName() in busy_players:
                msg(sender, "You are super-duper busy and concentrated right now. Think, think, think!")
            else:
                msg(sender, "You are completely unable to focus right now.")

        else:
            unclear(sender)
            return False

    elif len(args) == 2 and args[0] == "status":
        target = server.getPlayer(args[1])
        if target is None:
            msg(sender, "That player is not online, I doubt they are busy.")
        elif target.getName() in busy_players:
            msg(sender, "Yes, %s&r is busy. Shhh..." % target.getDisplayName())
        else:
            msg(sender, "No, you're good. Feel free to chat with %s&r!" % target.getDisplayName())

    else:
        unclear(sender)
        return False
    return True


@hook.event("player.PlayerQuitEvent", "lowest")
def on_player_leave(event):
    try:
        busy_players.remove(event.getPlayer().getName())
    except:
        pass


#---- Dicode for catching any bothering of busy people ----


reply_targets = {}
override_perm = "utils.imbusy.override"


def whisper(sender, target_name):
    target = server.getPlayer(target_name)

    if target is not None:
        if target is not sender and not sender.hasPermission(override_perm) and target.getName() in busy_players:
            msg(sender, "&c[&fBUSY&c] %s&r is busy!" % target.getDisplayName())
            return False

        reply_targets[sender.getName()] = target.getName()

        # allow the target to reply regardless of sender being busy
        if target.getName() in reply_targets:
            del reply_targets[target.getName()]
    return True


def reply(sender):
    if sender.getName() in reply_targets:
        target = server.getPlayer(reply_targets[sender.getName()])
        if target is not None: 
            if target is not sender and not sender.hasPermission(override_perm) and target.getName() in busy_players:
                msg(sender, "&c[&fBUSY&c] %s&r is busy!" % target.getDisplayName())
                return False

            # allow the target to reply regardless of sender being busy
            if target.getName() in reply_targets:
                del reply_targets[target.getName()]
    return True


class CommandWrapper(Command):

    def __init__(self, wrapped, checker):
        Command.__init__(self, wrapped.getName())
        self.setDescription(wrapped.getDescription())
        self.setPermission(wrapped.getPermission())
        self.setUsage(wrapped.getUsage())
        self.setAliases(wrapped.getAliases())
        self.wrapped = wrapped
        self.checker = checker

    def execute(self, sender, label, args):
        info("/" + self.getLabel() + " executed by " + sender.getName())
        try:
            if self.checker(sender, args):
                return self.wrapped.execute(sender, label, args)
        except:
            error(trace())
        return True

    def tabComplete(self, sender, alias, args):
        return self.wrapped.tabComplete(sender, alias, args)

def msg_command_checker(sender, args):
    return len(args) <= 1 or whisper(sender, args[0])

def reply_command_checker(sender, args):
    return len(args) == 0 or reply(sender)

def tpa_command_checker(sender, args):
    if len(args) == 0:
        return True
    target = server.getPlayer(args[0])
    if target is not None and target is not sender and not sender.hasPermission(override_perm) and target.getName() in busy_players:
        msg(sender, "&c[&fBUSY&c] %s&r is busy!" % target.getDisplayName())
        return False
    return True

def tpahere_command_checker(sender, args):
    return tpa_command_checker(sender, args)


@hook.event("player.PlayerCommandPreprocessEvent", "monitor")
def on_player_command_preprocess(event):
    message = event.getMessage().split(" ")
    if len(message) > 1 and message[0].lower() in ("/tell", "/minecraft:tell") and not whisper(event.getPlayer(), message[1]):
        event.setCancelled(True)


@hook.enable
def replace_ess_commands():

    try:
        info("[imbusy] Wrapping ess commands")
        map_field = server.getPluginManager().getClass().getDeclaredField("commandMap")
        map_field.setAccessible(True)
        command_map = map_field.get(server.getPluginManager())

        commands_field = command_map.getClass().getDeclaredField("knownCommands")
        commands_field.setAccessible(True)
        map = commands_field.get(command_map)

        ess_msg_cmd = map.get("essentials:msg")
        ess_reply_cmd = map.get("essentials:reply")
        ess_tpa_cmd = map.get("essentials:tpa")
        ess_tpahere_cmd = map.get("essentials:tpahere")

        msg_cmd_wrapper = CommandWrapper(ess_msg_cmd, msg_command_checker)
        reply_cmd_wrapper = CommandWrapper(ess_reply_cmd, reply_command_checker)
        tpa_cmd_wrapper = CommandWrapper(ess_tpa_cmd, tpa_command_checker)
        tpahere_cmd_wrapper = CommandWrapper(ess_tpahere_cmd, tpahere_command_checker)

        iterator = map.entrySet().iterator()
        while iterator.hasNext():
            entry = iterator.next()
            value = entry.getValue()
            if value is ess_msg_cmd:
                entry.setValue(msg_cmd_wrapper)
                info("[imbusy] wrapped /" + entry.getKey())
            elif value is ess_reply_cmd:
                entry.setValue(reply_cmd_wrapper)
                info("[imbusy] wrapped /" + entry.getKey())
            elif value is ess_tpa_cmd:
                entry.setValue(tpa_cmd_wrapper)
                info("[imbusy] wrapped /" + entry.getKey())
            elif value is ess_tpahere_cmd:
                entry.setValue(tpahere_cmd_wrapper)
                info("[imbusy] wrapped /" + entry.getKey())

    except:
        error("[Imbusy] Failed to wrap essentials commands")
        error(trace())
