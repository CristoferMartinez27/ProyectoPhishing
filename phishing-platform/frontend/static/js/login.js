const API_URL = 'https://proyectophishing-production.up.railway.app';

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const alertBox = document.getElementById('alertBox');

    // Deshabilitar botón y mostrar spinner
    loginBtn.disabled = true;
    btnText.classList.add('d-none');
    btnSpinner.classList.remove('d-none');
    alertBox.innerHTML = '';

    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombre_usuario: username,
                contrasena: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Guardar token y datos de usuario
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('usuario', JSON.stringify(data.usuario));

            // Mostrar éxito
            alertBox.innerHTML = `
                <div class="alert alert-success" role="alert">
                    ✅ Bienvenido, ${data.usuario.nombre_completo}
                </div>
            `;

            // Redirigir según rol
            setTimeout(() => {
                if (data.usuario.rol === 'administrador') {
                    window.location.href = 'dashboard-admin.html';
                } else {
                    window.location.href = 'dashboard-admin.html'; // En este caso, ambos roles van al mismo dashboard
                }
            }, 1500);

        } else {
            throw new Error(data.detail || 'Error en el login');
        }

    } catch (error) {
        alertBox.innerHTML = `
            <div class="alert alert-danger" role="alert">
                ❌ ${error.message}
            </div>
        `;
    } finally {
        loginBtn.disabled = false;
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
    }
});