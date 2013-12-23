from tasks import Task, TaskTracker
from needs import Need, need_from_task
from equipment import EquipmentSearch, Storage
from clutter import Stowage
from pathing import PathingWidget
import uuid
import numpy as np


class Actor(object):
    def __init__(self,name='Place Holder'):
        self.my_tasks = TaskTracker()
        self.id = str(uuid.uuid4())  
        self.name = name
        self.needs = dict()
        self.needs['Idle Curiosity']=Need('Idle Curiosity', self, 100, 0, 0, self.new_idle_task, None)
        self.task = None #currently active task
        self.action = None #placeholder for graphical animation or tweening or w/e
        self.task_abandon_value = 5 #if a task's importance outweighs the current task by this much, we drop and switch
        self.location = None
        self.station = None
        self.inventory = Stowage(0.5)
        self.path=None
        self.xyz = np.array([ 0, 0, 0 ])
        self.orientation = np.array([ 0, 0, 0 ])
        self.speed = 1.0 #meter per second travel time, "A leisurely float"
        
    def new_idle_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Idle Curiosity']), owner = self, timeout = 1500, task_duration = 150, severity='IGNORABLE', fetch_location_method=self.station.random_location)
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
            self.task.target, self.task.location = self.task.fetch_location() #Grab location
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
       
        
class Robot(Actor):
    def __init__(self, name='Wally'):
        super(Robot, self).__init__(name)
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
        t=Task(''.join(['Satisfy Charge']), owner = self, timeout=timeout, task_duration = 600, severity=severity, fetch_location_method=EquipmentSearch('Battery',self.station).search)
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
                    