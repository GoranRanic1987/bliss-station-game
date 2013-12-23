
#miscellaneous stuff related to the loose objects one might find floating around the station

common_densities =   {  'Food' : 714.33,
                        'Water' : 1000.0,
                        'Oxygen Candles' : 2420.0 }
                        
common_qualities = {    'Water' : {'Contaminants' : 0.0, 'Salt': 0.0, 'pH' : 7.0 }, #distilled water
                        'Food' : {'Freshness': 1.0, 'Contaminants' : 0.0, 'Perishable': 0.00002, 'Nutrient': [1.0, 1.0, 1.0, 1.0, 1.0], 'Flavor': [0.5, 0.5, 0.5, 0.5, 0.5] } #Bland but very nutritious and long-lasting space food
                   }                        

gather_rate = 0.001 #m^3/s - rate of grabbing a handful of something and putting it somewhere else

def equals(type1,type2):
    if not type1 and not type2: return True
    if not type1 or not type2: return False
    if type1 == 'Any' or type2 == 'Any': return True
    if type1 == type2: return True
    return False    
    
class Clutter(object):    
    def __init__(self, name='Trash', mass=0.1, density=0.1, quality=None):    
        self.name = name
        self.mass = mass
        self.density = common_densities[self.name] if self.name in common_densities.keys() else density
        self.quality = quality if quality else common_qualities[self.name] if self.name in common_qualities.keys() else None
        
    def get_volume(self): return self.mass/self.density
    volume = property(get_volume, None, None, "Clutter volume" )  
    
    def split(self,amt):
        if amt < 0: assert False, 'Requested to split a negative amount. Denied.'
        curr_amt = min(amt, self.mass)   
        self.mass -= curr_amt
        return Clutter(self.name, curr_amt, self.density)
        
    def merge(self, other):
        if not isinstance(other, Clutter): assert False, 'Requested merge a nonClutter object. Denied.'
        if not equals(self.name,other.name): return False
        self.mass += other.mass
        return True
        
    
class Stowage(object):
    def __init__(self, capacity=1):    
        self.capacity=capacity
        self.contents=[]
                        
    def find_resource(self, check = lambda x: True):
        stuff=[]
        stuff.extend( [ v for v in self.contents if check( v ) ] )
        if stuff:
            return stuff[0]
        return None
        
    def update(self, dt):
        for c in self.contents:
            if c.mass == 0:
                self.contents.remove(c)
        
    def remove (self, target, amt):
        if amt <= 0: return None
        out=[]
        cum_amt=0
        for v in self.contents:
            if equals(target, v.name):
                bite = v.split(amt-cum_amt)
                out.append(bite)
                cum_amt += bite.mass
                if v.mass <= 0: self.contents.remove(v) 
            if cum_amt >= amt: break
        return out
                
    def add (self, stuff=None):
        #if not ( isinstance(stuff,Clutter) or isinstance(stuff,Equipment)): return False
        if not stuff: return True
        if stuff.volume > self.free_space: return False
        if stuff in self.contents: return False
        if isinstance(stuff, Clutter): 
            for v in self.contents:
                if isinstance(v,Clutter) and v.merge(stuff): 
                    return True
        self.contents.append(stuff)
        return True
        
    def get_free_space(self): 
        used_space=0
        for i in self.contents:
            used_space += i.volume
        return self.capacity - used_space        
    free_space = property(get_free_space, None, None, "Available storage space" )                  
        
    
class JanitorMon(object):
    def __init__(self,target='All'):    
        self.target=target
        
    def task_work_report(self,task,dt):
        if task.name.startswith('Pick Up'):
            #print gather_rate, dt, task.target.density, task.assigned_to.inventory.free_space
            remove_amt = min(gather_rate*dt*task.target.density,task.assigned_to.inventory.free_space*task.target.density)
            if remove_amt <= 0: return
            #clut_type = task.name.split('Pick Up')[1].strip()            
            obj = task.target.split(remove_amt)
            task.assigned_to.inventory.add(obj)
            
class ClutterFilter(object):
    def __init__(self,target='All'):    
        self.target=target                
            
    def compare(self,obj):
        if not isinstance(obj,Clutter): return False
        if self.target=='Potable Water': 
            if obj.name == 'Water' and 'Contaminants' in obj.quality and 'Salt' in obj.quality:
                return obj.quality['Contaminants'] <= 0.1 and obj.quality['Salt'] <= 0.1
        elif self.target=='Edible Food': 
            if obj.name == 'Food' and 'Contaminants' in obj.quality:
                return obj.quality['Contaminants'] <= 0.05
        return equals(self.target, obj.name)