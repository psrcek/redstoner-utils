from helpers import *
from java.util.UUID import fromString as java_uuid
from org.bukkit.util import Vector

ff_perms       = ["utils.forcefield", "utils.forcefield.ignore"]
ff_prefix      = "&8[&aFF&8]"
ff_users       = []
whitelists     = {}  # {ff_owner_id: [white, listed, ids]}
fd             = 4   # forcefield distance
speed_limiter  = 100 # the higher, the lower the forcefield sensitivity.

Xv = 1.0 / speed_limiter # used in set_velocity_away(), this is more efficient.
Xve = 5 * Xv

# /ff admin  is a future option I might implement

@hook.command("forcefield")
def on_forcefield_command(sender, args):
  if not is_player(sender) or not sender.hasPermission(ff_perms[0]):
    noperm(sender)
    return True
  sender_id = str(sender.getUniqueId())

  if not args or args[0].lower() == "toggle": #Toggle
    toggle_forcefield(sender, sender_id)

  elif args[0].lower() in ["whitelist", "wl", "wlist"]: #Whitelist commands
    if not args[1:] or args[1].lower() == "list":
      whitelist_list(sender, sender_id)
    elif args[1].lower() == "clear":
      whitelist_clear(sender, sender_id)
    elif args[1].lower() in ["add", "+"]:
      whitelist_add(sender, sender_id, True, args[2:])
    elif args[1].lower() in ["remove", "delete", "rem", "del", "-"]:
      whitelist_add(sender, sender_id, False, args[2:])
    else:
      invalid_syntax(sender)

  elif args[0].lower() in ["help", "?"]: #/forcefield help
    forcefield_help(sender)
  else:
    invalid_syntax(sender)
  return True


def whitelist_add(sender, sender_id, add, players):
  if not players:
    msg(sender, "%s &cGive space-separated playernames." % ff_prefix)
  elif add == True and sender_id not in whitelists:
    whitelists[sender_id] = []
  online_players = []
  for name in list(server.getOnlinePlayers()):
    online_players.append(str(name).lower())
  for name in players:
    online = False
    player = server.getPlayer(name) if name.lower() in online_players else server.getOfflinePlayer(name)
    if not player == None:    
      if name.lower() in online_players:
        online = True
      uid = str(player.getUniqueId())
      pname = stripcolors(player.getDisplayName())
      if add == True and uid not in whitelists[sender_id]:
        if player == sender:
          msg(sender, "%s &cYou can't whitelist yourself." % ff_prefix)
        else:
          whitelists[sender_id].append(uid)
          msg(sender, "%s &aAdded %s to your forcefield whitelist." % (ff_prefix, pname))
          if online == True:
            msg(player, "%s %s &aAdded you to his forcefield whitelist." % (ff_prefix, sender.getDisplayName()))
      elif add == False and uid in whitelists[sender_id]:
        whitelists[sender_id].remove(uid)
        msg(sender, "%s &cRemoved %s from your forcefield whitelist." % (ff_prefix, pname))
        if online == True:
          msg(player, "%s %s &cRemoved you from his forcefield whitelist." % (ff_prefix, sender.getDisplayName()))
      elif add == True:
        msg(sender, "%s &c%s &cWas already in your forcefield whitelist." % (ff_prefix, pname))
      else:
        msg(sender, "%s &c%s &cWas not in your forcefield whitelist." % (ff_prefix, pname))
    else:
      msg(sender, "%s &cplayer %s &cwas not found." % (ff_prefix, name))


def whitelist_list(sender, sender_id):
  msg(sender, "%s &aForceField Whitelist:" % ff_prefix)
  if not sender_id in whitelists or len(whitelists[sender_id]) == 0:
    msg(sender, "&c      Your whitelist has no entries.")
  else:
    c = 0
    for uid in whitelists[sender_id]:
      c+=1
      msg(sender, "&a      %s. &f%s" % (c, stripcolors(server.getPlayer(java_uuid(uid)).getDisplayName())))


def whitelist_clear(sender, sender_id):
  if len(whitelists[sender_id]) == 0:
    msg(sender, "%s &cYou had no players whitelisted." % ff_prefix)
  else:
    whitelists[sender_id] = []
    msg(sender, "%s &aForceField Whitelist cleared." % ff_prefix)


def forcefield_help(sender):
  msg(sender, "%s &a&l/ForceField Help: \n&aYou can use the forcefield to keep players on distance." % ff_prefix)
  msg(sender, "&2Commands:")
  msg(sender, "&a1. &6/ff &ohelp &a: aliases: ?")
  msg(sender, "&a2. &6/ff &o(toggle)")
  msg(sender, "&a3. &6/ff &owhitelist (list) &a: aliases: wlist, wl")
  msg(sender, "&a4. &6/ff wl &oclear")
  msg(sender, "&a5. &6/ff wl &oadd <players> &a: aliases: &o+")
  msg(sender, "&a6. &6/ff wl &oremove <players> &a: aliases: &odelete, rem, del, -")


def toggle_forcefield(sender, sender_id):
  if sender_id in ff_users:
    ff_users.remove(sender_id)
    msg(sender, "%s &aForceField toggle: &cOFF" % ff_prefix)
  else:
    ff_users.append(sender_id)
    msg(sender, "%s &aForceField toggle: &2ON" % ff_prefix)


def invalid_syntax(sender):
  msg(sender, "%s &cInvalid syntax. Use &o/ff ? &cfor info." % ff_prefix)


#--------------------------------------------------------------------------------------------------------#


@hook.event("player.PlayerMoveEvent")
def on_move(event):
  player = event.getPlayer()
  if is_creative(player):
    player_id = str(player.getUniqueId())
    if player_id in ff_users: # player has forcefield, entity should be blocked
      for entity in player.getNearbyEntities(fd, fd, fd):
        if is_player(entity) and is_creative(entity) and not entity.hasPermission(ff_perms[1]) and not (player_id in whitelists.get(str(entity.getUniqueId()), [])):
          #if not whitelists[entity_id], check in blank list e.g. False
          set_velocity_away(player, entity)

    if not player.hasPermission(ff_perms[1]): # player should be blocked, entity has forcefield
      for entity in player.getNearbyEntities(fd, fd, fd):
        entity_id = str(entity.getUniqueId())
        if is_player(entity) and is_creative(entity) and (entity_id in ff_users) and not (player_id in whitelists.get(entity_id, [])):
          #if not whitelists[entity_id], check in blank list e.g. False
          set_velocity_away(entity, player) #Other way around


def set_velocity_away(player, entity): #Moves entity away from player
  player_loc = player.getLocation()
  entity_loc = entity.getLocation()

  dx = entity_loc.getX() - player_loc.getX()
  dx = dx if not (-Xv < dx < Xv) else Xv
  vx = Xv / Xve * dx

  dy = entity_loc.getY() - player_loc.getY()
  dy = dy if not (-Xv < dy < Xv) else Xv
  vy = Xv / Xve * dy

  dz = entity_loc.getZ() - player_loc.getZ()
  dz = dz if not (-Xv < dz < Xv) else Xv
  vz = Xv / Xve * dz
  entity.setVelocity(Vector(vx, vy, vz))
  #We don't want to go above max_speed, and we dont want to divide by 0.


#--------------------------------------------------------------------------------------------------------#


@hook.event("player.PlayerQuitEvent")
def on_quit(event):
  player = event.getPlayer()
  uid    = str(player.getUniqueId())
  if uid in ff_users:
    ff_users.remove(uid)