from tasks import Task

need_severity_profile = {'VARIABLE' : {0.0:'HIGH', 0.2:'MODERATE', 0.5:'LOW',0.7:'IGNORABLE'}, 
                         'HUMAN_BIOLOGICAL': {0.0:'HIGH',0.1:'MODERATE',0.2:'LOW',0.3:'IGNORABLE'} }

def need_from_task(taskname):
    if taskname.startswith('Satisfy '):
        return taskname.split('Satisfy ')[1]
    else:
        return None

class Need():
    def __init__(self,name,owner,max_amt,depletion_rate,replenish_rate,on_task,on_fail,severity='VARIABLE'):
        self.name = name
        self.owner = owner
        self.amt = max_amt
        self.max_amt = max_amt
        self.depletion_rate = depletion_rate
        self.replenish_rate = replenish_rate
        self.on_task = on_task
        self.on_fail = on_fail
        self.severity = severity
        self.touched = 0
        
    def update(self,dt):
        assert(self.owner, "Need has no owner.  This should never happen.")
        if self.touched > 0: self.touched -= dt
        if self.amt < 0 and self.on_fail and self.touched <= 0:
            self.on_fail()
            return
                                
        _need_severity = self.current_severity()
        
        _need_task = None
        _need_task = self.owner.my_tasks.find_task(''.join(['Satisfy ',self.name]))
        
        #print _need_task, _need_ratio
        if _need_task: 
            _need_task.severity = _need_severity        
            #if _need_ratio > 0.95 and self.owner.task == _need_task: _need_task.flag('IGNORED')
        elif self.on_task:
            t=self.on_task(self.amt/(self.depletion_rate+0.00001),_need_severity)
            t.flag('OPEN')
            self.owner.my_tasks.add_task(t)
            
        self.amt -= dt*self.depletion_rate

    def current_severity(self):        
        if self.severity in need_severity_profile.keys():
            _need_ratio = self.amt/self.max_amt
            profile = need_severity_profile[self.severity]
            for f in sorted(profile.keys(),reverse=True):
                if _need_ratio > f:
                    return profile[f]                
        else:
            return self.severity
            
    def supply(self, available_amt, dt):
        _amt = min( available_amt, dt*self.replenish_rate, self.max_amt - self.amt )
        self.amt += _amt            
        return _amt
        
    def set_amt_to_severity(self,severity='IGNORABLE'):
        mult = 0.2 if severity=='HIGH' else 0.5 if severity=='MODERATE' else 0.7 if severity=='LOW' else 1.0
        self.amt = mult*self.max_amt
        
    def status(self):
        return [self.amt/self.max_amt, self.severity]
        
        
