import time
from app.state import PREDICTION_PROGRESS

class Progress_tracker:
    def __init__(self, process_tracked, total_steps):
        self.key = process_tracked

        PREDICTION_PROGRESS[self.key] = {
            'current_step': 0,
            'total_steps': total_steps,
            'current_message': 'Iniciando...',
            'step_messages': [],
            'is_complete': False,
            'start_time': time.time(),
            'current_substep': 0,
            'total_substeps': 0
        }

    def update_progress(self, step, message, is_substep=False, substep_total=0):
        p = PREDICTION_PROGRESS[self.key]

        if is_substep:
            p['current_substep'] += 1
            p['total_substeps'] = substep_total
        else:
            p['current_step'] = step
            p['current_message'] = message
            p['current_substep'] = 0
            p['total_substeps'] = 0

        p['step_messages'].append({
            'timestamp': time.time(),
            'message': message
        })

    def complete_progress(self):
        PREDICTION_PROGRESS[self.key]['is_complete'] = True
