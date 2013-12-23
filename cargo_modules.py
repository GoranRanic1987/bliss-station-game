

from generic_module import BasicModule
from equipment import CBM, SolarPanel, DOCK_EQUIPMENT
from clutter import Clutter

import math
import numpy as np

                                      
class DragonCargoModule(BasicModule):
    """ Modeled after SpaceX's Dragon capsule.  Mostly empty space for cargo. """
    def __init__(self):   
        BasicModule.__init__(self) 
        self.size = np.array([ 6.1 , 3.7 , 3.7 ])
        self.interior_space = 10 #m^3
        self.stowage.capacity=14
        self.composition = {'Composite' : 4200}
        self.max_payload = 6620
        self.accept_wastes = True
        
        new_nodes={ self.node('store0'): np.array([ 0 , 0 , 0 ]),
                    self.node('CBM0') : np.array([ 0.95, 0 , 0 ])}
                    
        # merging n dicts with a generator comprehension
        self.nodes = dict(i for iterator in (self.nodes, new_nodes) for i in iterator.iteritems())                    
                    
        self.paths.add_nodes_from([f for f in self.nodes.keys() if not f in self.paths.nodes()])
        self.add_edge(self.node('CBM0'),self.node('store0'))  
        
        self.equipment['CBM0']= [ np.array([ 1 , 0 , 0 ]), np.array([0 , 0]), 'CBM', CBM().install(self)]

        self.equipment['Solars0']= [ np.array([ 0 , 1 , 0 ]), np.array([ math.pi , 0]), 'SOLAR', SolarPanel().install(self)]
        self.equipment['Solars1']= [ np.array([ 0 , -1 , 0 ]), np.array([ -math.pi , 0]), 'SOLAR', SolarPanel().install(self)]
        
        self.equipment['Solars0'][3].capacity=1
        self.equipment['Solars0'][3].in_vaccuum=True
        self.equipment['Solars1'][3].capacity=1
        self.equipment['Solars1'][3].in_vaccuum=True
        
    def setup_simple_resupply(self):
        self.stowage.add(Clutter('Food', 90.5 )) #one person-year of food
        self.stowage.add(Clutter('Water',466.4 )) #six person-months of water
        self.stowage.add(Clutter('Oxygen Candles', 30 )) #ten person-months of reserve O2.  One candle = .1 kg

                
        
