class Result:
    def __init__(self, name, status, reason , prev_status = "FAIL",  prev_status_reason= ""):
        '''
        Constructor of the class
        Parameters:
            name (string): issue name
            status (string): PASS/FAIL
            reason (string): reason to fail
            preservation_status (strig):  Whether the minimized program preserves the target behavior
        '''
        self.name = name
        self.status = status
        self.reason = reason
        self.preservation_status = prev_status
        self.preservation_status_reason = prev_status_reason

    def set_preservation_status(self, status, reason):
        '''
        status True if the minimized program preserve the target behavior
        '''
        self.preservation_status = status
        self.preservation_status_reason = reason