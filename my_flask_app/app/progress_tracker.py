import datetime
from flask import session

# ====================
# FUNCIONES DE PROGRESO
# ====================

def init_prediction_progress(total_steps=6):
    """Inicializar el progreso de la predicción en la sesión"""
    session['prediction_progress'] = {
        'current_step': 0,
        'total_steps': total_steps,
        'current_message': 'Iniciando predicción...',
        'step_messages': [],
        'is_complete': False,
        'start_time': datetime.now(),
        'current_substep': 0,
        'total_substeps': 0
    }
    session.modified = True

def update_progress(step, message, is_substep=False, substep_total=0):
    """Actualizar el progreso en la sesión"""
    if 'prediction_progress' not in session:
        init_prediction_progress()
    
    progress = session['prediction_progress']
    
    if is_substep:
        progress['current_substep'] += 1
        if substep_total > 0:
            progress['total_substeps'] = substep_total
    else:
        progress['current_step'] = step
        progress['current_message'] = message
    
    progress['step_messages'].append({
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': message
    })
    
    # Mantener solo los últimos 50 mensajes
    if len(progress['step_messages']) > 50:
        progress['step_messages'] = progress['step_messages'][-50:]
    
    session['prediction_progress'] = progress
    session.modified = True

def complete_progress():
    """Marcar la predicción como completa"""
    if 'prediction_progress' in session:
        progress = session['prediction_progress']
        progress['is_complete'] = True
        progress['elapsed_time'] = datetime.now() - progress['start_time']
        session['prediction_progress'] = progress
        session.modified = True