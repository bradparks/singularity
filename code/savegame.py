#file: statistics.py
#Copyright (C) 2008 FunnyMan3595
#This file is part of Endgame: Singularity.

#Endgame: Singularity is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#Endgame: Singularity is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Endgame: Singularity; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#This file contains functions to handle savegame (load, save, ...)

import cPickle
import collections
import os

import g, player

#name given when the savegame button is pressed. This is changed when the
#game is loaded or saved.
default_savegame_name = "Default Save"

#savefile version; update whenever the data saved changes.
current_save_version = "singularity_savefile_0.31pre"
savefile_translation = {
    "singularity_savefile_r4":      ("0.30",         4   ),
    "singularity_savefile_r5_pre":  ("0.30",         4.91),
    "singularity_savefile_0.31pre": ("1.0 (dev)",   31   ),
    "singularity_savefile_99":      ("1.0 (dev)",   99   ),
}

Savegame = collections.namedtuple('Savegame', ['name', 'version'])

def get_savegames():
    save_dir = g.get_save_folder()

    all_savegames = []
    all_files = os.listdir(save_dir)
    for file_name in all_files:
        if file_name[0] != "." and file_name != "CVS":
            # If it's a new-style save, trim the .sav bit.
            if len (file_name) > 4 and file_name[-4:] == ".sav":
                name = file_name[:-4]

                # Get version, only pickle first string.
                version_name = None # None == Unknown version
                try:
                    loadfile = open(os.path.join(save_dir, file_name), 'r')
                    unpickle = cPickle.Unpickler(loadfile)

                    load_version = unpickle.load()
                    if load_version in savefile_translation:
                        version_name = savefile_translation[load_version][0]
                except:
                    version_name = None # To be sure.

                savegame = Savegame(name, version_name)
                all_savegames.append(savegame)

    return all_savegames

def get_savegame_path(loadgame_name):
    if not loadgame_name:
        print "No game specified."
        return None

    save_dir = g.get_save_folder()

    load_loc = os.path.join(save_dir, loadgame_name + ".sav")
    if os.path.exists(load_loc) == 0:
        print "file "+load_loc+" does not exist."
        return None

    return load_loc

def delete_savegame(loadgame_name):
    load_path = get_savegame_path(loadgame_name)

    if load_path is None:
        return False

    try:
        os.remove(load_path)
    except:
        return False

def load_savegame(loadgame_name):
    global default_savegame_name

    load_path = get_savegame_path(loadgame_name)

    if load_path is None:
        return False

    loadfile = open(load_path, 'r')
    unpickle = cPickle.Unpickler(loadfile)

    def find_class(module_name, class_name):
        # For cPickle
        import copy_reg
        import numpy.core.multiarray
        import collections
        import player, base, tech, item, event, location, buyable
        save_classes = dict(
            player_class=player.Player,
            Player=player.Player,
            _reconstructor = copy_reg._reconstructor,
            object=object,
            array=list,  # This is the old buyable.array.
                         # We just treat it as a list for conversion purposes.
            list=list,
            Location=location.Location,
            Tech=tech.Tech,
            event_class=event.Event,
            Event=event.Event,
            group=player.Group,
            Group=player.Group,
            Buyable_Class=buyable.BuyableClass,
            BuyableClass=buyable.BuyableClass,
            Base=base.Base,
            Base_Class=base.BaseClass,
            BaseClass=base.BaseClass,
            Item=item.Item,
            Item_Class=item.ItemClass,
            ItemClass=item.ItemClass,
            _reconstruct=numpy.core.multiarray._reconstruct,
            scalar=numpy.core.multiarray.scalar,
            ndarray=numpy.ndarray,
            dtype=numpy.dtype,
            deque=collections.deque,
        )
        if class_name in save_classes:
            return save_classes[class_name]
        else:
            raise SystemExit, (module_name, class_name)

    unpickle.find_global = find_class

    #check the savefile version
    load_version_string = unpickle.load()
    if load_version_string not in savefile_translation:
        loadfile.close()
        print loadgame_name + " is not a savegame, or is too old to work."
        return False
    load_version = savefile_translation[load_version_string][1]

    default_savegame_name = loadgame_name

    # Changes to overall structure go here.
    g.pl = unpickle.load()
    g.curr_speed = unpickle.load()
    g.techs = unpickle.load()
    g.locations = unpickle.load()
    g.events = unpickle.load()

    # Changes to individual pieces go here.
    if load_version != savefile_translation[current_save_version]:
        g.pl.convert_from(load_version)
        for my_location in g.locations.values():
            for my_base in my_location.bases:
                my_base.convert_from(load_version)
        for my_tech in g.techs.values():
            my_tech.convert_from(load_version)
        for my_event in g.events.values():
            my_event.convert_from(load_version)

    # Apply current language
    g.load_tech_defs()
    g.load_location_defs()
    g.load_event_defs()

    # Play the appropriate music
    if g.pl.apotheosis:
        g.play_music("win")
    else:
        g.play_music("music")

    loadfile.close()
    return True

def create_savegame(savegame_name):
    global default_savegame_name
    default_savegame_name = savegame_name

    save_dir = g.get_save_folder()
    save_loc = os.path.join(save_dir, savegame_name + ".sav")
    savefile=open(save_loc, 'w')

    cPickle.dump(current_save_version, savefile)
    cPickle.dump(g.pl, savefile)
    cPickle.dump(g.curr_speed, savefile)
    cPickle.dump(g.techs, savefile)
    cPickle.dump(g.locations, savefile)
    cPickle.dump(g.events, savefile)

    savefile.close()
