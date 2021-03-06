#pylint: disable = F0401
"""
A plugin that automatically tiles (stacks) blocks inside a selected region in configurable directions.
"""
import org.bukkit.event.block.BlockPlaceEvent as BlockPlaceEvent
import org.bukkit.event.block.BlockBreakEvent as BlockBreakEvent
import org.bukkit.event.player.PlayerInteractEvent as PlayerInteractEvent
import thread
from time import sleep
from helpers import *

tilehelpers = open_json_file("tilehelpers", [])

dirmap = {
    #    [x, y, z]
    "n": [0, 0, -1],
    "e": [+1, 0, 0],
    "s": [0, 0, +1],
    "w": [-1, 0, 0],
    "u": [0, +1, 0],
    "d": [0, -1, 0]
}

# FIXME: disallow multiple regions by single person.
# FIXME: could lead to two regions updating each other forever -> server freezes


@hook.event("block.BlockPlaceEvent", "low")
def on_place_block(event):
    if not event.isCancelled():
        player = event.getPlayer()
        block  = event.getBlockPlaced()
        for th in tilehelpers:
            area = th.get("area")
            if th.get("owner") == uid(player) and str(block.getWorld().getUID()) == th.get("world") and block.getX() in range(area[0][0], area[0][1]+1) and block.getY() in range(area[1][0], area[1][1]+1) and block.getZ() in range(area[2][0], area[2][1]+1) and event.canBuild():

                # stack block in directions
                for direction in th.get("directions"):
                    directions = dirmap[direction]
                    size       = [
                        1 + abs(area[0][1] - area[0][0]),
                        1 + abs(area[1][1] - area[1][0]),
                        1 + abs(area[2][1] - area[2][0])
                    ]
                    against = event.getBlockAgainst()

                    newblock = block.getWorld().getBlockAt(
                        block.getX() + size[0] * directions[0],
                        block.getY() + size[1] * directions[1],
                        block.getZ() + size[2] * directions[2]
                    )

                    newagainst = against.getWorld().getBlockAt(
                        against.getX() + size[0] * directions[0],
                        against.getY() + size[1] * directions[1],
                        against.getZ() + size[2] * directions[2]
                    )
                    newstate = newblock.getState()
                    newstate.setType(block.getType())
                    newstate.setData(block.getState().getData())

                    event = BlockPlaceEvent(newstate.getBlock(), newblock.getState(), newagainst, event.getItemInHand(), player, event.canBuild())
                    server.getPluginManager().callEvent(event)
                    if not event.isCancelled():
                        newblock.setType(block.getType())
                        newblock.setData(block.getData())


@hook.event("block.BlockBreakEvent", "low")
def on_break_block(event):
    if not event.isCancelled():
        player = event.getPlayer()
        block  = event.getBlock()
        for th in tilehelpers:
            area = th.get("area")
            if th.get("owner") == uid(player) and str(block.getWorld().getUID()) == th.get("world") and block.getX() in range(area[0][0], area[0][1]+1) and block.getY() in range(area[1][0], area[1][1]+1) and block.getZ() in range(area[2][0], area[2][1]+1):

                # stack block in directions
                for direction in th.get("directions"):
                    directions = dirmap[direction]
                    size       = [
                        1 + abs(area[0][1] - area[0][0]),
                        1 + abs(area[1][1] - area[1][0]),
                        1 + abs(area[2][1] - area[2][0])
                    ]

                    newblock = block.getWorld().getBlockAt(
                        block.getX() + size[0] * directions[0],
                        block.getY() + size[1] * directions[1],
                        block.getZ() + size[2] * directions[2]
                    )

                    event = BlockBreakEvent(newblock, player)
                    server.getPluginManager().callEvent(event)
                    if not event.isCancelled():
                        newblock.setTypeId(0)


@hook.event("player.PlayerInteractEvent", "low")
def on_block_interact(event):
    action = event.getAction()
    if not event.isCancelled() and str(action) == "RIGHT_CLICK_BLOCK":
        player = event.getPlayer()
        block  = event.getClickedBlock()
        for th in tilehelpers:
            area = th.get("area")
            if th.get("owner") == uid(player) and str(block.getWorld().getUID()) == th.get("world") and block.getX() in range(area[0][0], area[0][1]+1) and block.getY() in range(area[1][0], area[1][1]+1) and block.getZ() in range(area[2][0], area[2][1]+1):

                # stack block in directions
                for direction in th.get("directions"):
                    directions = dirmap[direction]
                    size       = [
                        1 + abs(area[0][1] - area[0][0]),
                        1 + abs(area[1][1] - area[1][0]),
                        1 + abs(area[2][1] - area[2][0])
                    ]

                    newblock = block.getWorld().getBlockAt(
                        block.getX() + size[0] * directions[0],
                        block.getY() + size[1] * directions[1],
                        block.getZ() + size[2] * directions[2]
                    )

                    event = PlayerInteractEvent(event.getPlayer(), action, event.getItem(), newblock, event.getBlockFace())
                    server.getPluginManager().callEvent(event)
                    if not event.isCancelled():
                        # FIXME: do not use bukkit API calls outside main thread
                        thread.start_new_thread(update_block, (block, newblock))


def update_block(block, newblock):
    try: # we're in a thread, the universe may hace collapsed in another thread
        sleep(0.2)
        newblock.setType(block.getType())
        newblock.setData(block.getData())
    except Exception, e:
        error("Failed to update %s block in %s at %s,%s,%s: '%s'" % (str(block.getType()), block.getWorld().getName(), block.getX(), block.getY(), block.getZ(), e))