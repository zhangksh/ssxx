import threading
import log_config
from time import sleep


processing_tasks= {}

class task_processor:
    def __init__(self):
        self.is_processing = True
        self.thread = threading.Thread(target = self.run, daemon = True)
        self.thread.start()
    def run(self):
        print("processor started")
        while self.is_processing:
            if processing_tasks:
                task = next(iter(processing_tasks))
                log_config.logging.info(f'start task:{processing_tasks[task].detect_id}')
                print(f"start task:{processing_tasks[task].detect_id}")
                processing_tasks[task].process()
                log_config.logging.info(f'task done:{processing_tasks[task].detect_id}')
                print(f"task done:{processing_tasks[task].detect_id}")
                del processing_tasks[task]
            else:
                print("no task detected")
                sleep(5)