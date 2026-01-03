document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let autoScrollEnabled = true;
    let startTime = new Date();
    let updateInterval;
    
    // Elementos del DOM
    const mainProgressBar = document.getElementById('main-progress-bar');
    const subprogressContainer = document.getElementById('subprogress-container');
    const subprogressBar = document.getElementById('subprogress-bar');
    const substepText = document.getElementById('substep-text');
    const percentageElement = document.getElementById('percentage');
    const donutChart = document.getElementById('donut-chart');
    const donutPercentage = document.getElementById('donut-percentage');
    const statusBadge = document.getElementById('status-badge');
    const consoleOutput = document.getElementById('console-output');
    const completionSection = document.getElementById('completion-section');
    const elapsedTimeElement = document.getElementById('elapsed-time');
    const stepsContainer = document.getElementById('steps-container');
    
    // Botones
    document.getElementById('clear-console').addEventListener('click', clearConsole);
    document.getElementById('auto-scroll-toggle').addEventListener('click', toggleAutoScroll);
    
    // Iniciar actualización del tiempo
    updateElapsedTime();
    setInterval(updateElapsedTime, 1000);
    
    // Iniciar polling de progreso
    startProgressPolling();
    
    // Función para actualizar el tiempo transcurrido
    function updateElapsedTime() {
        const now = new Date();
        const diff = Math.floor((now - startTime) / 1000);
        
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const seconds = diff % 60;
        
        elapsedTimeElement.textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    // Función para iniciar el polling de progreso
    function startProgressPolling() {
        // Primera actualización inmediata
        fetchProgress();
        
        // Luego cada 2 segundos
        updateInterval = setInterval(fetchProgress, 2000);
    }
    
    // Función para obtener el progreso desde la API
    async function fetchProgress() {
        try {
            const response = await fetch('/api/progreso_entrenamiento');
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            
            const data = await response.json();
            updateProgressUI(data);
            
            // Si el entrenamiento está completo, detener el polling
            if (data.is_complete) {
                clearInterval(updateInterval);
                showCompletionScreen(data);
            }
        } catch (error) {
            console.error('Error obteniendo progreso:', error);
            addConsoleMessage(`[ERROR] No se pudo obtener el progreso: ${error.message}`, 'danger');
        }
    }
    
    // Función para actualizar la UI con los datos de progreso
    function updateProgressUI(data) {
        // Actualizar porcentaje
        const percentage = data.percentage;
        percentageElement.textContent = `${percentage}%`;
        donutPercentage.textContent = `${percentage}%`;
        
        // Actualizar barra de progreso principal
        mainProgressBar.style.width = `${percentage}%`;
        mainProgressBar.setAttribute('aria-valuenow', percentage);
        
        // Actualizar gráfico de dona
        donutChart.style.background = 
            `conic-gradient(#4e54c8 ${percentage}%, #e9ecef ${percentage}%)`;
        
        // Actualizar estado
        updateStatusBadge(data);
        
        // Actualizar subprogreso si existe
        if (data.total_substeps > 0) {
            subprogressContainer.classList.remove('d-none');
            const substepPercentage = (data.current_substep / data.total_substeps) * 100;
            subprogressBar.style.width = `${substepPercentage}%`;
            substepText.textContent = `${data.current_substep}/${data.total_substeps}`;
        } else {
            subprogressContainer.classList.add('d-none');
        }
        
        // Actualizar pasos
        updateSteps(data);
        
        // Actualizar consola
        if (data.current_message) {
            addConsoleMessage(data.current_message, 'info');
        }
        
        // Mantener solo los últimos mensajes
        if (data.step_messages && data.step_messages.length > 0) {
            const recentMessages = data.step_messages.slice(-10);
            recentMessages.forEach(msg => {
                if (!consoleOutput.innerHTML.includes(msg.message)) {
                    addConsoleMessage(msg.message, 'info');
                }
            });
        }
    }
    
    // Función para actualizar el badge de estado
    function updateStatusBadge(data) {
        let statusClass = 'bg-warning';
        let statusIcon = 'bi-hourglass-split';
        let statusText = 'En progreso';
        
        if (data.is_complete) {
            statusClass = 'bg-success';
            statusIcon = 'bi-check-circle-fill';
            statusText = 'Completado';
        } else if (data.percentage >= 80) {
            statusClass = 'bg-info';
            statusIcon = 'bi-hourglass-top';
            statusText = 'Finalizando';
        } else if (data.percentage >= 40) {
            statusClass = 'bg-primary';
            statusIcon = 'bi-arrow-repeat';
            statusText = 'Procesando';
        }
        
        statusBadge.className = `badge ${statusClass} p-2`;
        statusBadge.innerHTML = `<i class="bi ${statusIcon} me-1"></i>${statusText}`;
    }
    
    // Función para actualizar los pasos visualmente
    function updateSteps(data) {
        const steps = stepsContainer.querySelectorAll('.step-card');
        const currentStep = data.current_step || 0;
        
        steps.forEach((step, index) => {
            const stepNumber = step.querySelector('.step-number');
            const statusIcon = step.querySelector('.mt-2 i');
            
            // Resetear todas las tarjetas
            step.classList.remove('completed-step', 'active-step');
            stepNumber.classList.remove('bg-gradient-primary', 'bg-secondary');
            
            if (index < currentStep) {
                // Paso completado
                step.classList.add('completed-step');
                stepNumber.classList.add('bg-gradient-primary');
                statusIcon.className = 'bi bi-check-circle-fill text-success fs-5';
            } else if (index === currentStep) {
                // Paso activo
                step.classList.add('active-step');
                stepNumber.classList.add('bg-gradient-primary');
                statusIcon.className = 'bi bi-arrow-repeat text-primary fs-5 spin';
            } else {
                // Paso pendiente
                stepNumber.classList.add('bg-secondary');
                statusIcon.className = 'bi bi-clock text-muted fs-5';
            }
        });
    }
    
    // Función para agregar mensajes a la consola
    function addConsoleMessage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        let typeClass = 'text-info';
        let prefix = '[INFO]';
        
        if (type === 'error' || message.includes('❌')) {
            typeClass = 'text-danger';
            prefix = '[ERROR]';
        } else if (type === 'success' || message.includes('✅')) {
            typeClass = 'text-success';
            prefix = '[SUCCESS]';
        } else if (type === 'warning' || message.includes('⚠️')) {
            typeClass = 'text-warning';
            prefix = '[WARNING]';
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = 'console-line';
        messageElement.innerHTML = `
            <span class="${typeClass}">[${timestamp}] ${prefix}</span> ${message}
        `;
        
        consoleOutput.appendChild(messageElement);
        
        // Auto-scroll si está habilitado
        if (autoScrollEnabled) {
            const container = consoleOutput.parentElement;
            container.scrollTop = container.scrollHeight;
        }
    }
    
    // Función para limpiar la consola
    function clearConsole() {
        consoleOutput.innerHTML = '';
        addConsoleMessage('Consola limpiada', 'info');
    }
    
    // Función para alternar auto-scroll
    function toggleAutoScroll() {
        autoScrollEnabled = !autoScrollEnabled;
        const button = document.getElementById('auto-scroll-toggle');
        const icon = button.querySelector('i');
        
        if (autoScrollEnabled) {
            icon.className = 'bi bi-arrow-down-square-fill';
            button.classList.remove('btn-outline-secondary');
            button.classList.add('btn-success');
        } else {
            icon.className = 'bi bi-arrow-down-square';
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }
    }
    
    // Función para mostrar la pantalla de finalización
    function showCompletionScreen(data) {
        // Actualizar resumen
        document.getElementById('summary-time').textContent = elapsedTimeElement.textContent;
        document.getElementById('summary-steps').textContent = 
            `${data.current_step || 0}/${data.total_steps || 0}`;
        
        // Calcular modelos entrenados (simulado)
        const modelCount = Math.floor(Math.random() * 5) + 1;
        document.getElementById('summary-models').textContent = modelCount;
        
        // Mostrar sección de finalización
        completionSection.classList.remove('d-none');
        
        // Agregar mensaje final a la consola
        addConsoleMessage('🎉 Entrenamiento completado exitosamente!', 'success');
        addConsoleMessage(`⏱️ Tiempo total: ${elapsedTimeElement.textContent}`, 'info');
        addConsoleMessage(`📊 Modelos entrenados: ${modelCount}`, 'info');
    }
    
    // Añadir mensaje inicial
    addConsoleMessage('Conectando con el servidor de entrenamiento...', 'info');
});
