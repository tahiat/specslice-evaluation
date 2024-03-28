from typing import List

class ExceptionData:
    def __init__(self, exception_class: str, exception: str, stack_trace: List[str]):
        '''
        Constructor of the class
        Parameters:
            exception_class: class of the exception
            exception: which exception was raised
            strack_trace: first 5 lines of the stack trace
        '''
        self.exception_class = exception_class
        self.exception = exception
        self.stack_trace = stack_trace