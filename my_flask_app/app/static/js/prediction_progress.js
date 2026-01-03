$(document).ready(function() {
    // Variables globales
    let progressInterval;
    let startTime = new Date();
    let consoleMessageCount = 0;
    let isProcessing = true;
    
    // Iniciar el proceso de predicción automáticamente
    startPredictionProcess();
    
    // Función para iniciar el proceso
    function startPredictionProcess() {
        // Obtener horizon_days del formulario anterior (almacenado en localStorage)
        const horizonDays = localStorage.getItem('prediction_horizon') || 30;
        
        // Enviar solicitud para iniciar predicción
        $.ajax({
            url: window.PREDICTION_PROCESS_URL,
            type: 'POST',
            data: {
                horizon_days: horizonDays
            },
            success: function(response) {
                if (response.success) {
                    console.log("✅ Proceso iniciado correctamente");
                } else {
                    showError(response.error || 'Error al iniciar el proceso');
                }
            },
            error: function(xhr) {
                showError(xhr.responseJSON?.error || 'Error de conexión');
            }
        });
        
        // Iniciar monitoreo de progreso
        startProgressMonitoring();
    }
    
    // Función para monitorear el progreso
    function startProgressMonitoring() {
        progressInterval = setInterval(fetchProgress, 5000);
    }
    
    // Función para obtener el progreso
    function fetchProgress() {
        $.ajax({
            url: window.API_PREDICTION_PROGRESS_URL,
            type: 'GET',
            success: function(data) {
                console.log(data)
                updateUI(data);
                
                // Si el proceso está completo
                if (data.is_complete) {
                    completeProcess();
                }
            },
            error: function() {
                // Intento de reconexión
                console.log("⚠️ Error de conexión, reintentando...");
            }
        });
    }
    
    // Función para actualizar la UI
    function updateUI(progress) {

        // Actualizar barra de progreso principal
        const overallPercentage = progress.percentage;
        $('#overallPercentage').text(overallPercentage + '%');
        $('#overallProgressBar').css('width', overallPercentage + '%');
        $('#overallProgressBar .progress-text').text(overallPercentage + '%');
        
        // Actualizar paso actual
        $('#currentStep').text(progress.current_message);
               

        // Actualizar pasos individuales
        updateSteps(progress);
                

        // Actualizar consola de mensajes
        updateConsole(progress.step_messages);
                

        // Actualizar contadores
        updateCounters(progress.step_messages);

        // Actualizar tiempo transcurrido
        updateElapsedTime();


    }
    
    // Función para actualizar los pasos
    function updateSteps(progress) {
        // Resetear todos los pasos
        $('.step-card').removeClass('active-step completed-step');
        $('.step-icon i').removeClass('text-primary text-success').addClass('text-muted');
        $('.step-progress-bar').css('width', '0%');
        
        // Marcar pasos completados
        for (let i = 0; i < progress.current_step; i++) {
            const stepCard = $('#step' + i);
            stepCard.addClass('completed-step');
            stepCard.find('.step-icon i').removeClass('text-muted').addClass('text-success');
            stepCard.find('.step-progress-bar').css('width', '100%');
        }
        
        // Marcar paso actual
        if (progress.current_step < progress.total_steps) {
            const currentStepCard = $('#step' + progress.current_step);
            currentStepCard.addClass('active-step');
            currentStepCard.find('.step-icon i').removeClass('text-muted').addClass('text-primary');
            
            // Calcular progreso del paso actual
            const progress_with_substep = progress.current_substep / progress.total_substeps * 100;
            currentStepCard.find('.step-progress-bar').css('width', progress_with_substep + '%');
        }
    }
    
    // Función para actualizar la consola
    function updateConsole(messages) {
        const consoleElement = $('#messageConsole');
        const messageCount = messages.length;
        
        // Solo actualizar si hay nuevos mensajes
        if (messageCount > consoleMessageCount) {
            const newMessages = messages.slice(consoleMessageCount);
            
            newMessages.forEach(msg => {
                const line = `
                    <div class="console-line mb-1">
                        <span class="text-success">[${msg.timestamp}]</span>
                        <span class="ms-2">${formatConsoleMessage(msg.message)}</span>
                    </div>
                `;
                consoleElement.append(line);
            });
            
            // Scroll al final
            consoleElement.scrollTop(consoleElement[0].scrollHeight);
            consoleMessageCount = messageCount;
            
            // Actualizar contador
            $('#messageCount').text(messageCount + ' mensajes');
        }
    }
    
    // Función para formatear mensajes de consola
    function formatConsoleMessage(message) {
        // Colores para diferentes tipos de mensajes
        let formatted = message;
        
        if (message.includes('✅')) {
            formatted = `<span class="text-success">${message}</span>`;
        } else if (message.includes('❌')) {
            formatted = `<span class="text-danger">${message}</span>`;
        } else if (message.includes('🔍') || message.includes('📁')) {
            formatted = `<span class="text-info">${message}</span>`;
        } else if (message.includes('🎯') || message.includes('🔮')) {
            formatted = `<span class="text-warning">${message}</span>`;
        } else if (message.includes('📊') || message.includes('📈')) {
            formatted = `<span class="text-primary">${message}</span>`;
        } else if (message.includes('💧') || message.includes('💦')) {
            formatted = `<span class="text-info">${message}</span>`;
        } else if (message.includes('🎨')) {
            formatted = `<span class="text-purple">${message}</span>`;
        }
        
        return formatted;
    }
    
    // Función para actualizar contadores
    function updateCounters(messages) {
        // Extraer información de los mensajes
        let modelsLoaded = 0;
        let variablesPredicted = 0;
        let daysPredicted = 0;
        let irrigationTotal = 0;
        
        messages.forEach(msg => {
            const message = msg.message;
            
            // Contar modelos cargados
            if (message.includes('cargado exitosamente') || message.includes('cargado correctamente')) {
                modelsLoaded++;
            }
            
            // Extraer variables predichas
            if (message.includes('variables predichas')) {
                const match = message.match(/(\d+)\s+variables predichas/);
                if (match) variablesPredicted = parseInt(match[1]);
            }
            
            // Extraer días predichos
            if (message.includes('días') && message.includes('Generando predicciones para')) {
                const match = message.match(/Generando predicciones para\s+(\d+)\s+días/);
                if (match) daysPredicted = parseInt(match[1]);
            }
            
            // Extraer riego total
            if (message.includes('Riego total:')) {
                const match = message.match(/Riego total:\s+([\d\.]+)\s+mm/);
                if (match) irrigationTotal = parseFloat(match[1]);
            }
        });
        
        // Actualizar UI
        $('#modelsLoaded').text(modelsLoaded);
        $('#variablesPredicted').text(variablesPredicted);
        $('#daysPredicted').text(daysPredicted);
        $('#irrigationCalculated').text(irrigationTotal.toFixed(1));
    }
    
    // Función para actualizar tiempo transcurrido
    function updateElapsedTime() {
        const now = new Date();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        
        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        $('#elapsedTime').text(timeString);
        $('#elapsedTimeDetailed').text(`${elapsedSeconds} segundos`);
    }
    
    // Función para completar el proceso
    function completeProcess() {
        clearInterval(progressInterval);
        isProcessing = false;
        
        // Mostrar mensaje de completado
        $('#completionMessage').fadeIn();
        
        // Redirigir después de 5 segundos
        setTimeout(() => {
            window.location.href =  window.PREDICTION_RESULTS_URL;
        }, 5000);
    }
    
    // Función para mostrar error
    function showError(message) {
        clearInterval(progressInterval);
        
        $('#errorMessage').text(message);
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
    
    // Event Listeners
    $('#clearConsole').click(function() {
        $('#messageConsole').empty();
        consoleMessageCount = 0;
    });
    
    $('#refreshBtn').click(function() {
        if (isProcessing) {
            fetchProgress();
        }
    });
    
    $('#cancelBtn').click(function() {
        if (confirm('¿Estás seguro de que quieres cancelar la predicción?')) {
            clearInterval(progressInterval);
            window.location.href = window.PREDICTION_MAIN_URL;
        }
    });
    
    // Estilos CSS adicionales
    const style = document.createElement('style');
    style.textContent = `
        .step-card {
            transition: all 0.3s ease;
            border-radius: 10px;
        }
        .step-card.active-step {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #4e54c8;
        }
        .step-card.completed-step {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        .step-progress-bar {
            background: linear-gradient(90deg, #4e54c8, #8f94fb);
            transition: width 0.5s ease;
        }
        .console-line {
            border-left: 3px solid #28a745;
            padding-left: 10px;
            margin-bottom: 5px;
        }
        .text-purple {
            color: #6f42c1 !important;
        }
        .progress-text {
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
    `;
    document.head.appendChild(style);
});
