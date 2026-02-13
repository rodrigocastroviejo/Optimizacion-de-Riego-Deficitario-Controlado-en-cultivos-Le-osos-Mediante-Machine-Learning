$(document).ready(function() {
    // Variables globales
    let selectedFile = null;
    let selectedModels = ['sarima', 'var'];
    let currentFileRows = 0;

    // Inicializar
    loadDataFiles();
    loadSystemInfo();
    updateSummary();
    
    // Slider para horizonte de predicción
    $('#test_size_slider').on('input', function() {
        const value = $(this).val();
        $('#test_size').val(value);
        updateSummary();
    });
    
    $('#test_size').on('input', function() {
        const value = $(this).val();
        $('#test_size_slider').val(value);
        updateSummary();
    });
    
    
    // Selección de modelos
    $('.model-checkbox').change(function() {
        const model = $(this).val();
        const card = $(this).closest('.model-select-card');
        
        if ($(this).is(':checked')) {
            card.addClass('selected');
            if (!selectedModels.includes(model)) {
                selectedModels.push(model);
            }
        } else {
            card.removeClass('selected');
            selectedModels = selectedModels.filter(m => m !== model);
        }
        
        updateSelectedModelsCount();
        updateSummary();
        updateEstimatedTime();
    });
    
    // Selección de archivos
    $(document).on('click', '.file-card', function() {
        $('.file-card').removeClass('selected');
        $(this).addClass('selected');
        
        selectedFile = $(this).data('filename');
        
        // Extraer el número de filas desde el atributo data que insertaremos en el render
        currentFileRows = parseInt($(this).data('rows'));
        
        updateSummary();
    });
    
    // Botones de selección de modelos
    $('#selectAllModels').click(function() {
        $('.model-checkbox:not(:disabled)').prop('checked', true).trigger('change');
    });
    
    $('#deselectAllModels').click(function() {
        $('.model-checkbox').prop('checked', false).trigger('change');
    });
    
    
    // Resetear formulario
    $('#resetFormBtn').click(function() {
        if (confirm('¿Restablecer todos los valores a los predeterminados?')) {
            resetForm();
        }
    });
    
    // Envío del formulario
    $('#trainingForm').submit(function(e) {
        e.preventDefault();
        validateAndConfirm();
    });
    
    // Confirmar inicio
    $('#confirmStartBtn').click(function() {
        startTraining();
    });
    
    // Funciones auxiliares
    function loadDataFiles() {
        $.ajax({
           url: '/api/archivos_datos',
            type: 'GET',
            success: function(response) {
                if (response.files && response.files.length > 0) {
                    renderFileCards(response.files);
                    $('#availableFilesCount').text(response.files.length);
                    $('#filesCountBadge').text(response.files.length);
                    
                    // --- SE ELIMINÓ EL BLOQUE QUE SELECCIONABA EL PRIMER ARCHIVO ---
                    selectedFile = null; 
                    currentFileRows = 0;
                } else {
                    $('#dataFilesContainer').html(`
                        <div class="col-12">
                            <div class="alert alert-warning text-center">
                                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                                <h5>No hay archivos de datos</h5>
                                <p class="mb-0">Sube un archivo CSV en la sección de <a href="/upload">Subir Dataset</a></p>
                            </div>
                        </div>
                    `);
                }
            },
            error: function() {
                $('#dataFilesContainer').html(`
                    <div class="col-12">
                        <div class="alert alert-danger text-center">
                            <i class="fas fa-times-circle fa-2x mb-3"></i>
                            <h5>Error al cargar archivos</h5>
                            <p class="mb-0">No se pudieron cargar los archivos disponibles</p>
                        </div>
                    </div>
                `);
            }
        });
    }
    
    function renderFileCards(files) {
        let html = '';
        files.forEach(file => {
            const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
            const isRecommended = file.rows > 365;
            
            // Se ha eliminado el div 'selection-badge' para quitar el indicador visual superior
            html += `
                <div class="col-md-6">
                    <div class="card file-card h-100" data-filename="${file.name}" data-rows="${file.rows}">
                        <div class="card-body">
                            <div class="d-flex align-items-start">
                                <div class="bg-primary rounded-circle p-2 me-3">
                                    <i class="fas fa-file-csv text-white"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1 fw-bold">${file.name}</h6>
                                    <div class="d-flex flex-wrap gap-2 mb-2">
                                        <span class="badge bg-primary">
                                            <i class="fas fa-columns me-1"></i>${file.columns.length} cols
                                        </span>
                                        <span class="badge bg-success">
                                            <i class="fas fa-list-ol me-1"></i>${file.rows.toLocaleString()} rows
                                        </span>
                                        ${isRecommended ? '<span class="badge bg-warning">Recomendado</span>' : ''}
                                    </div>
                                    <p class="small text-muted mb-0">
                                        <i class="fas fa-calendar me-1"></i>${file.modified}<br>
                                        <i class="fas fa-hdd me-1"></i>${fileSizeMB} MB
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        $('#dataFilesContainer').html(html);
    }
    
    function loadSystemInfo() {
        $.ajax({
            url: '/api/modelos_disponibles',
            type: 'GET',
            success: function(response) {
                if (response.modelos) {
                    $('#availableModelsCount').text(response.modelos.length);
                    $('#modelsCountBadge').text(response.modelos.length);
                    $('#systemStatus').removeClass().addClass('badge bg-success').text('Listo');
                }
            }
        });
        
        $.ajax({
            url: '/api/check_trained_models', // Nuestra nueva ruta
            type: 'GET',
            success: function(response) {

                const availableModels = response.available; 
                
                // Iterar sobre cada tarjeta de modelo
                $('.model-select-card').each(function() {
                    const modelType = $(this).data('model');
                    const checkbox = $(this).find('.model-checkbox');
                    
                    if (!availableModels.includes(modelType)) {
                        // --- MODELO NO ENTRENADO ---
                        $(this).addClass('disabled');
                        checkbox.prop('checked', false).prop('disabled', true);
                        $(this).removeClass('selected');
                        
                        // Quitar de la lista de seleccionados si estaba por defecto
                        selectedModels = selectedModels.filter(m => m !== modelType);
                        
                        // Añadir aviso visual dentro de la tarjeta
                        if ($(this).find('.unavailable-badge').length === 0) {
                            $(this).find('.card-body').append(
                                '<div class="unavailable-badge"><i class="fas fa-lock me-1"></i>Requiere entrenamiento previo</div>'
                            );
                        }
                    }
                });
                
                // Actualizar contadores y resumen tras el filtrado
                updateSelectedModelsCount();
                updateSummary();
            }
    });
    
    // El resto de la función original (historial, etc.)
    loadTrainingHistory();
}
    
    function loadTrainingHistory() {
        // En una implementación real, harías una petición al servidor
        // Por ahora, mostramos un mensaje estático
        $('#trainingHistory').html(`
            <div class="text-center py-3">
                <i class="fas fa-clock fa-2x text-muted mb-3"></i>
                <p class="text-muted mb-0">No hay entrenamientos previos</p>
            </div>
        `);
    }
    
    
    function updateSelectedModelsCount() {
        const count = selectedModels.length;
        $('#selectedModelsCount').text(count);
        
        // Actualizar tiempo estimado basado en modelos seleccionados
        updateEstimatedTime();
    }
    
    function updateEstimatedTime() {
        let baseTime = 0; // minutos base
        let modelTime = 0;
        
        selectedModels.forEach(model => {
            switch(model) {
                case 'sarima': modelTime += 3; break;
                case 'sarimax': modelTime += 4; break;
                case 'var': modelTime += 1; break;
                case 'lstm': modelTime += 2; break;
            }
        });
        
        const totalTime = baseTime + modelTime;
        $('#estimatedTime').text(`${totalTime}-${totalTime + 5} min`);
    }
    
    function updateSummary() {
        const modelsText = `${selectedModels.length} modelo${selectedModels.length !== 1 ? 's' : ''}`;
        const testText = `${$('#test_size').val()} días de prueba`;
        
        $('#summaryModels').text(modelsText);
        $('#summaryTestSize').text(testText);
        $('#configSummary').html(`<strong>${modelsText}</strong> • <strong>${testText}</strong>`);
    }
    
    function resetForm() {
        // Resetear valores
        $('#test_size').val(45);
        $('#test_size_slider').val(45);
        
        // Resetear modelos
        selectedModels = ['sarima', 'var'];
        $('.model-checkbox').prop('checked', false);
        $('#model_sarima, #model_var').prop('checked', true).trigger('change');

        // Resetear archivo seleccionado
        $('.file-card').removeClass('selected');
        if ($('.file-card').length > 0) {
            selectedFile = $('.file-card:first').data('filename');
            $('.file-card:first').addClass('selected');
        }
            
        updateSummary();
        updateEstimatedTime();
    }
    
    function validateAndConfirm() {
        // Validar selección de archivo
        if (!selectedFile) {
            showError('Por favor, selecciona un archivo de datos');
            return;
        }
        
        // Validar selección de modelos
        if (selectedModels.length === 0) {
            showError('Por favor, selecciona al menos un modelo para entrenar');
            return;
        }
        
        // Mostrar resumen de confirmación
        let summaryHtml = `
            <li><strong>Archivo de datos:</strong> ${selectedFile}</li>
            <li><strong>Modelos a entrenar:</strong> ${selectedModels.map(m => m.toUpperCase()).join(', ')}</li>
            <li><strong>Tamaño de test:</strong> ${$('#test_size').val()} días</li>
        `;
        
        $('#confirmSummary').html(summaryHtml);
        
        // Mostrar modal de confirmación
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        modal.show();
    }

    
    function startTraining() {
        // Cerrar modal
        bootstrap.Modal.getInstance(document.getElementById('confirmModal')).hide();
        
        // Deshabilitar botón
        $('#startTrainingBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Iniciando...');
        
        // Preparar datos del formulario
        const formData = new FormData();
        formData.append('data_file', selectedFile);
        formData.append('horizon_days', $('#test_size').val());

        
        // Añadir modelos seleccionados
        selectedModels.forEach(model => {
            formData.append('models', model);
        });

        console.log(formData)
        
        // Redirigir a la página de progreso
        window.location.href = window.PREDICTION_PROGRESS_URL;

        // Enviar solicitud
        $.ajax({
            url: window.PREDICTION_PROCESS_URL,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    console.log("✅ Predicción exitosa!")
                } else {
                    showError(response.error || 'Error al iniciar la predicción');
                    $('#startTrainingBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Predicción');
                }
            },
            error: function(xhr) {
                showError(xhr.responseJSON?.error || 'Error de conexión');
                $('#startTrainingBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Predicción');
            }
        });
    }
    
    function showError(message) {
        $('#errorMessage').text(message);
        const modal = new bootstrap.Modal(document.getElementById('errorModal'));
        modal.show();
    }
    
    // Inicializar valores
    $('.model-select-card[data-model="sarima"], .model-select-card[data-model="var"]').addClass('selected');
});