$(document).ready(function() {
    // Variables globales
    let selectedFile = null;
    let selectedModels = ['sarima', 'var'];
    
    // Inicializar
    loadDataFiles();
    loadSystemInfo();
    updateSummary();
    
    // Slider para test size
    $('#test_size_slider').on('input', function() {
        const value = $(this).val();
        $('#test_size').val(value);
        $('#testSizeValue').text(value + ' días');
        updateDoughnutChart(value);
        updateSummary();
    });
    
    $('#test_size').on('input', function() {
        const value = $(this).val();
        $('#test_size_slider').val(value);
        $('#testSizeValue').text(value + ' días');
        updateDoughnutChart(value);
        updateSummary();
    });
    
    // Slider para var_maxlags
    $('#var_maxlags_slider').on('input', function() {
        $('#var_maxlags').val($(this).val());
    });
    
    $('#var_maxlags').on('input', function() {
        $('#var_maxlags_slider').val($(this).val());
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
        updateSummary();
    });
    
    // Botones de selección de modelos
    $('#selectAllModels').click(function() {
        $('.model-checkbox').prop('checked', true).trigger('change');
    });
    
    $('#deselectAllModels').click(function() {
        $('.model-checkbox').prop('checked', false).trigger('change');
    });
    
    // Toggle parámetros avanzados
    $('#toggleAdvancedParams').click(function() {
        $('#advancedParams').slideToggle();
        $(this).find('i').toggleClass('fa-cogs fa-eye-slash');
        $(this).find('span').text($('#advancedParams').is(':visible') ? 'Ocultar' : 'Mostrar');
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
                    
                    // Seleccionar el primer archivo por defecto
                    if (response.files.length > 0) {
                        selectedFile = response.files[0].name;
                        $(`.file-card[data-filename="${selectedFile}"]`).addClass('selected');
                    }
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
            const isRecommended = file.rows > 365; // Más de 1 año de datos
            
            html += `
                <div class="col-md-6">
                    <div class="card file-card h-100" data-filename="${file.name}">
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
        // Cargar información del sistema (modelos existentes, etc.)
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
        
        // Cargar historial de entrenamientos
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
    
    function updateDoughnutChart(testSize) {
        const trainPercent = 100 - (testSize / 365 * 100);
        const chart = $('.doughnut-chart');
        chart.css('background', `conic-gradient(#4e54c8 ${trainPercent}%, #ffc107 ${trainPercent}%)`);
    }
    
    function updateSelectedModelsCount() {
        const count = selectedModels.length;
        $('#selectedModelsCount').text(count);
        
        // Actualizar tiempo estimado basado en modelos seleccionados
        updateEstimatedTime();
    }
    
    function updateEstimatedTime() {
        let baseTime = 2; // minutos base
        let modelTime = 0;
        
        selectedModels.forEach(model => {
            switch(model) {
                case 'sarima': modelTime += 3; break;
                case 'sarimax': modelTime += 5; break;
                case 'var': modelTime += 4; break;
                case 'lstm': modelTime += 10; break;
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
        $('#test_size').val(180);
        $('#test_size_slider').val(180);
        $('#testSizeValue').text('180 días');
        
        // Resetear modelos
        selectedModels = ['sarima', 'var'];
        $('.model-checkbox').prop('checked', false);
        $('#model_sarima, #model_var').prop('checked', true).trigger('change');
        
        // Resetear parámetros avanzados
        $('#sarima_p').val(1);
        $('#sarima_d').val(1);
        $('#sarima_q').val(1);
        $('#sarima_P').val(1);
        $('#sarima_D').val(1);
        $('#sarima_Q').val(1);
        $('#sarima_s').val(30);
        $('#var_maxlags').val(15);
        $('#var_maxlags_slider').val(15);
        
        // Resetear archivo seleccionado
        $('.file-card').removeClass('selected');
        if ($('.file-card').length > 0) {
            selectedFile = $('.file-card:first').data('filename');
            $('.file-card:first').addClass('selected');
        }
        
        updateDoughnutChart(180);
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
        
        if (selectedModels.includes('sarima') || selectedModels.includes('sarimax')) {
            summaryHtml += `
                <li><strong>Parámetros SARIMA:</strong> (${$('#sarima_p').val()},${$('#sarima_d').val()},${$('#sarima_q').val()}) × (${$('#sarima_P').val()},${$('#sarima_D').val()},${$('#sarima_Q').val()},${$('#sarima_s').val()})</li>
            `;
        }
        
        if (selectedModels.includes('var')) {
            summaryHtml += `<li><strong>VAR lags:</strong> ${$('#var_maxlags').val()}</li>`;
        }
        
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
        formData.append('test_size', $('#test_size').val());
        
        // Añadir modelos seleccionados
        selectedModels.forEach(model => {
            formData.append('models', model);
        });
        
        // Añadir parámetros SARIMA
        formData.append('sarima_p', $('#sarima_p').val());
        formData.append('sarima_d', $('#sarima_d').val());
        formData.append('sarima_q', $('#sarima_q').val());
        formData.append('sarima_P', $('#sarima_P').val());
        formData.append('sarima_D', $('#sarima_D').val());
        formData.append('sarima_Q', $('#sarima_Q').val());
        formData.append('sarima_s', $('#sarima_s').val());
        formData.append('var_maxlags', $('#var_maxlags').val());
        
        // Redirigir a la página de progreso
        window.location.href = window.TRAINING_PROGRESS_URL;

        // Enviar solicitud
        $.ajax({
            url: window.TRAINING_PROCESS_URL,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    console.log("✅ Entrenamiento exitoso!")
                } else {
                    showError(response.error || 'Error al iniciar el entrenamiento');
                    $('#startTrainingBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Entrenamiento');
                }
            },
            error: function(xhr) {
                showError(xhr.responseJSON?.error || 'Error de conexión');
                $('#startTrainingBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Entrenamiento');
            }
        });
    }
    
    function showError(message) {
        $('#errorMessage').text(message);
        const modal = new bootstrap.Modal(document.getElementById('errorModal'));
        modal.show();
    }
    
    // Inicializar valores
    updateDoughnutChart(180);
    $('.model-select-card[data-model="sarima"], .model-select-card[data-model="var"]').addClass('selected');
});