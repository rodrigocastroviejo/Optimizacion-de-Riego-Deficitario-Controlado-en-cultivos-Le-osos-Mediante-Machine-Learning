from flask import session
import datetime

class Progress_tracker: 
    def __init__(self, process_tracked, total_steps):
        """Inicializar el tracker de progreso """
        self.process_tracked = process_tracked
        session[self.process_tracked] = {
            'current_step': 0,
            'total_steps': total_steps,
            'current_message': f'Iniciando {self.process_tracked}...',
            'step_messages': [],
            'is_complete': False,
            'start_time': datetime.now(),
            'current_substep': 0,
            'total_substeps': 0
        }
        session.modified = True


    def update_progress(self, step, message, is_substep=False, substep_total=0):
        """Actualizar el progreso en la sesión"""
        progress = session[self.process_tracked]

        if is_substep:
            progress['current_substep'] += 1
            if substep_total > 0:
                progress['total_substeps'] = substep_total
        else:
            progress['current_substep'] = 0
            progress['total_substeps'] = 0
            progress['current_step'] = step
            progress['current_message'] = message
        
        progress['step_messages'].append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': message
        })
        
        # Mantener solo los últimos 50 mensajes
        if len(progress['step_messages']) > 50:
            progress['step_messages'] = progress['step_messages'][-50:]
        
        session[self.process_tracked] = progress
        session.modified = True

    def complete_progress(self):
        """Marcar la predicción como completa"""

        progress = session[self.process_tracked]

        progress['is_complete'] = True
        progress['elapsed_time'] = datetime.now() - progress['start_time']

        session[self.process_tracked] = progress
        session.modified = True
