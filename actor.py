from tasks import Task, TaskTracker
from needs import Need, need_from_task
from equipment import Storage
from clutter import Stowage
from pathing import PathingWidget
import uuid
import numpy as np
from util import separate_node
import util, logging
from filtering import EquipmentFilter

class Actor(object):
    def __init__(self,name='Place Holder',station=None, logger=None):
        self.my_tasks = TaskTracker()
        self.id = str(uuid.uuid4())  
        self.name = name
        self.logger = logging.getLogger(logger.name + '.' + self.name) if logger else util.generic_logger
        self.needs = dict()
        self.needs['Idle Curiosity']=Need('Idle Curiosity', self, 100, 0, 0, self.new_idle_task, None)
        self.task = None #currently active task
        self.action = None #placeholder for graphical animation or tweening or w/e
        self.task_abandon_value = 5 #if a task's importance outweighs the current task by this much, we drop and switch
        self.location = None
        self.station = station
        self.inventory = Stowage(0.5)
        self.path=None
        self.held=None
        self.xyz = np.array([ 0, 0, 0 ])
        self.orientation = np.array([ 0, 0, 0 ])
        self.speed = 1.0 #meter per second travel time, "A leisurely float"
        
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_actor.tif"
        self.refresh_image()
     
    def refresh_image(self):
        self.img = util.load_image(self.imgfile)
    
    def draw(self,window):
        zoom=util.ZOOM
        l= self.path.current_coords if (self.path and not self.path.completed) else self.station.loc_to_xyz( self.location )
        self.img.blit(zoom*l[0], zoom*l[1], 0)        
        
    def drop(self):
        pass #TODO drop held item        
        
    def new_idle_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Idle Curiosity']), owner = self, timeout = None, task_duration = 150, severity='IGNORABLE', fetch_location_method=self.station.random_location,logger=self.logger)
        return t     
        
    def update(self,dt):
        self.my_tasks.update(dt)
        for n in self.needs.values():
            n.update(dt)
            
        self.inventory.update(dt)
        
        if self.task and self.task.task_ended():            
            self.task=None
        
        #'grab new task'                
        _curr_value = -5 if not self.task else self.task.task_value()
        _new_task = self.my_tasks.fetch_open_task() if not self.station else max(self.my_tasks.fetch_open_task(), self.station.tasks.fetch_open_task())
        #print "TASK VALUES", self.my_tasks.fetch_open_task()
        if _new_task and _new_task.task_value() > _curr_value + self.task_abandon_value:            
            if self.task: self.task.drop()
            self.task = _new_task
            self.task.assign(self)
        
        #'work on task'
        if not self.task: return
        if not self.task.location: 
            self.task.target, self.task.location, d = self.task.fetch_location() #Grab location
            #print self.task.name, self.task.target, self.task.location
            if not self.task.location: 
                self.task.drop()
                self.task=None
                return
        if self.location == self.task.location: 
            #work on task
            #print "Check", self.task.name
            self.task.do_work(dt)
            #print [[c.name, c.volume] for c in self.inventory.contents]
        else:
            if self.task.location and not self.task.location == self.location: 
                #go to location 
                if self.path and not self.path.completed:
                    self.path.traverse_step(dt*self.speed)
                else:
                    #print self.task.name, self.task.target, self.task.location
                    new_path = PathingWidget(self,self.station.paths,self.location, self.task.location, self.xyz)
                    if not new_path.valid: assert False, "ERROR: some kind of pathing error!"
                    self.path = new_path
                    self.path.traverse_step(dt*self.speed)
                    
    def transfer_node(self, new_loc ):
        '''moving to new node, exchange air flow'''
        my_mod = self.station.get_module_from_loc( self.location )
        new_mod = self.station.get_module_from_loc( new_loc )
        my_mod.atmo.mix( new_mod.atmo, 1.0 )             
       
    def summarize_needs(self, ret_string=False):
        if ret_string:
            out = 'Needs'
            for n in self.needs.keys():
                #print n, self.needs[n].current_severity()
                out = ''.join([out,'; ',n,'-',self.needs[n].current_severity()])
            return out #what a huge PITA
        return [[n, self.needs[n].current_severity()] for n in self.needs.keys()]
        
    def log_status(self):
        #TODO log task
        #self.logger.info(self.summarize_needs(True))
        self.logger.info(self.task.name if self.task else "Task: idling")        
       
        
class Robot(Actor):
    def __init__(self, name='Wally',station=None, logger=None):
        super(Robot, self).__init__(name,station,logger)
        self.needs['Charge']=Need('Charge', self, 12, 12/86400.0, 12/600.0, self.new_charge_task, self.drained)
        self.needs['Charge'].amt = 12
        self.activity_state = 'IDLE'
        
    def drained(self):
        #TODO add "someone recharge the damned robot" task
        self.activity_state = 'SHUTDOWN'    
        if self.task: self.task.drop()
        
    def update(self, dt):
        if self.activity_state == 'SHUTDOWN': return
        Actor.update(self,dt)   
        
    def new_charge_task(self,timeout,severity):
        #TODO replace with charge sequence, maybe
        t=Task(''.join(['Satisfy Charge']), owner = self, timeout=timeout, task_duration = 600, severity=severity, fetch_location_method=Searcher(EquipmentFilter( target='Battery' ), self.station ).search,logger=self.logger)
        return t     
                                        
    def task_work_report(self,task,dt):
        if not task: return
        need = need_from_task(task.name)
        
        if need == 'Charge':
            available = 0 if not hasattr(task.target, 'charge') else max(task.target.charge,0)
            used=self.needs['Charge'].supply( available, dt )
            task.target.charge -= used
            
            
if __name__ == "__main__":
    from time import sleep    
    robby = Robot('Robby')            

    for i in range(1,300):
        robby.update(0.5)
        print None if not robby.task else robby.task.name
        sleep(0.5)
                    
