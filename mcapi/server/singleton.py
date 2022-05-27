class OutputChannel():
    def __init__(self):
        self.ready = False
    
    def check_status(self):
        if 'output_channel' in dir(self):
            return True
        else:
            return False
    
    def add_output_channel(self, output_channel):
        self.output_channel = output_channel

    def post(self, cmd):
        if hasattr(self, 'output_channel') and callable(self.output_channel):
            return self.output_channel(cmd)
        else:
            raise NoOutputChannelProvided(f'ServerInstance did not received a correct output channel. Add it with add_output_channel')
 
singleton = OutputChannel()

class NoOutputChannelProvided(Exception):
    pass