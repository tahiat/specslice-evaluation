class Result:
    def __init__(self, name, status, reason):
        '''
        Constructor of the class
        Parameters:
            name (string): issue name
            status (string): PASS/FAIL
            reason (string): reason to fail
        '''
        self.name = name
        self.status = status
        self.reason = reason
        self.status = False

    def set_preservation_status(self, status):
        '''
        status True if the minimized program preserve the target behavior
        '''
        self.status = status