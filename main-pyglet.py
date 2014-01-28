from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
import util
import logging
import pyglet
from pyglet.gl import *  
from pyglet import clock
                                      
if __name__ == "__main__":
    from time import sleep    

    
    #window = pyglet.window.Window(visible=False, resizable=True)

    #@window.event
    #def on_draw():
    #    background.blit_tiled(0, 0, 0, window.width, window.height)
    #    img.blit(window.width // 2, window.height // 2, 0)


    logger=logging.getLogger("Universe")
    logger.setLevel(logging.DEBUG)
    #DEBUG INFO WARNING ERROR CRITICAL
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #create formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    modA  = DestinyModule()
    modDock = UnityModule()    
    modB   = ZvezdaModule()
    modDrag = DragonCargoModule()
    modDrag.setup_simple_resupply()
           
    station = Station(modDock, 'NewbieStation', logger)
    station.berth_module(modDock,'CBM0',modA, None, True)
    station.berth_module(modDock,'CBM3',modB, None, True)    
    station.berth_module(modA,None,modDrag, None, True)
    
    '''rob = Robot('Robby')     
    rob.station = station
    station.actors[rob.id]=rob
    rob.location = modB.node('hall0')
    rob.xyz = modB.location'''
    
    ernie= Human('Bela Lugosi',station=station,logger=station.logger)
    station.actors[ernie.id] = ernie
    ernie.location = modA.node('hall0')
    ernie.xyz = modA.location
    
    ernie.needs['WasteCapacityLiquid'].amt=0.1
    ernie.needs['Food'].set_amt_to_severity('HIGH')
    ernie.nutrition = [0.5, 0.5, 0.5, 0.5, 0.5]
    #modB.equipment['Electrolyzer'][3].broken=True
    
      
    #modA.berth('CBM0', modB, 'CBM0')
    #for m in station.modules.values(): print m.short_id, m.location
    #for n in station.paths.edges(data=True): print n
    tot_time=0
    def status_update(dt):
        print
        print round(util.TIME_FACTOR*tot_time),': Human task:', None if not ernie.task else (ernie.task.name,ernie.task.location,ernie.task.severity)
        util.generic_logger.info('FPS is %f' % clock.get_fps())
        for m in station.modules.values():
            logger.debug(''.join([m.short_id,' O2:', str(m.atmo.partial_pressure('O2')), ' CO2:',str(m.atmo.partial_pressure('CO2'))]))
        ernie.log_status()
        
    def system_tick(dt):    
        station.update(dt*util.TIME_FACTOR)
        global tot_time
        tot_time += dt        
        
    clock.set_fps_limit(30)
    clock.schedule_interval(status_update,1)
    clock.schedule(system_tick)
    
    pyglet.app.run()

    
