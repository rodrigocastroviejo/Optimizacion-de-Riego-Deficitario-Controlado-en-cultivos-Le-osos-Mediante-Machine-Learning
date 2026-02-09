$(document).ready(function() {

    
    $('#predictionForm').submit(function(e) {
        e.preventDefault(); // Evitar que la página se recargue
        const currentVal = $('#horizon_days').val();
        localStorage.setItem('prediction_horizon', currentVal);
    });

    // Confirmar inicio
    $('#startPredictionBtn').click(function() {
        startTraining();
    });
    


    function startTraining() {

         // Deshabilitar botón
        $('#startPredictionBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Iniciando...');
        

        const horizonValue = $('#horizon_days').val();
        const formData = new FormData();
        
        formData.append('prediction_days', horizonValue);
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
                    $('#startPredictionBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Predicción');
                }
            },
            error: function(xhr) {
                showError(xhr.responseJSON?.error || 'Error de conexión');
                $('#startPredictionBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>Iniciar Predicción');
            }
        });
    }
    
    function showError(message) {
        $('#errorMessage').text(message);
        const modal = new bootstrap.Modal(document.getElementById('errorModal'));
        modal.show();
    }
    
});