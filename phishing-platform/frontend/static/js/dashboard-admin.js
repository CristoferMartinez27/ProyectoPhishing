const API_URL = 'http://localhost:8000';
let token = localStorage.getItem('access_token');
let usuario = JSON.parse(localStorage.getItem('usuario'));

// Verificar autenticación
if (!token || !usuario) {
    window.location.href = 'login.html';
}

// Mostrar info del usuario
document.getElementById('userInfo').textContent = `👤 ${usuario.nombre_completo}`;

// Headers para peticiones
const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

// Cerrar sesión
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('usuario');
    window.location.href = 'login.html';
}

// Cambiar sección
function showSection(section) {
    document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    if (section === 'dashboard') {
        cargarEstadisticas()
        document.getElementById('dashboardSection').style.display = 'block';
        cargarEstadisticas();
    } else if (section === 'usuarios') {
        document.getElementById('usuariosSection').style.display = 'block';
        cargarUsuarios();
    } else if (section === 'clientes') {
        document.getElementById('clientesSection').style.display = 'block';
        cargarClientes();
    } else if (section === 'sitios') {
        document.getElementById('sitiosSection').style.display = 'block';
        cargarSitios();  // ← VERIFICA QUE ESTA LÍNEA EXISTA
    }
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        // Contar usuarios
        const usuariosResponse = await fetch(`${API_URL}/api/usuarios/`, { headers });
        const usuarios = await usuariosResponse.json();
        document.getElementById('totalUsuarios').textContent = usuarios.length;
        
        // Contar clientes activos
        const clientesResponse = await fetch(`${API_URL}/api/clientes/`, { headers });
        const clientes = await clientesResponse.json();
        document.getElementById('totalClientes').textContent = clientes.filter(c => c.activo).length;
        
        // Contar sitios reportados
        const sitiosResponse = await fetch(`${API_URL}/api/sitios/`, { headers });
        const sitios = await sitiosResponse.json();
        document.getElementById('totalSitios').textContent = sitios.length;
        document.getElementById('totalPendientes').textContent = 
            sitios.filter(s => s.estado === 'pendiente').length;
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}


// ========== GESTIÓN DE USUARIOS (COMPLETO CON EDITAR) ==========

// Cargar usuarios
async function cargarUsuarios() {
    try {
        const response = await fetch(`${API_URL}/api/usuarios/`, { headers });
        const usuarios = await response.json();
        
        const tbody = document.getElementById('tablaUsuarios');
        tbody.innerHTML = usuarios.map(u => `
            <tr>
                <td>${u.id}</td>
                <td>${u.nombre_completo}</td>
                <td>${u.nombre_usuario}</td>
                <td>${u.correo}</td>
                <td><span class="badge bg-primary">${u.rol_nombre}</span></td>
                <td>${u.activo ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-danger">Inactivo</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-warning me-1" onclick="editarUsuario(${u.id})">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarUsuario(${u.id})">Eliminar</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando usuarios:', error);
    }
}

// Modal crear usuario (nuevo)
async function showModalUsuario() {
    document.getElementById('tituloModalUsuario').textContent = 'Crear Nuevo Usuario';
    document.getElementById('formUsuario').reset();
    document.getElementById('usuarioId').value = '';
    document.getElementById('nombreUsuario').readOnly = false;
    document.getElementById('contrasena').required = true;
    document.getElementById('helperContrasena').textContent = 'Requerido';
    
    // Cargar roles
    const response = await fetch(`${API_URL}/api/usuarios/roles`, { headers });
    const roles = await response.json();
    
    const select = document.getElementById('rolId');
    select.innerHTML = '<option value="">Seleccione...</option>' +
        roles.map(r => `<option value="${r.id}">${r.nombre}</option>`).join('');
    
    new bootstrap.Modal(document.getElementById('modalUsuario')).show();
}

// Editar usuario
async function editarUsuario(id) {
    try {
        const response = await fetch(`${API_URL}/api/usuarios/`, { headers });
        const usuarios = await response.json();
        const usuario = usuarios.find(u => u.id === id);
        
        if (!usuario) {
            alert('Usuario no encontrado');
            return;
        }
        
        // Cambiar título
        document.getElementById('tituloModalUsuario').textContent = 'Editar Usuario';
        
        // Llenar formulario
        document.getElementById('usuarioId').value = usuario.id;
        document.getElementById('nombreCompleto').value = usuario.nombre_completo;
        document.getElementById('correo').value = usuario.correo;
        document.getElementById('nombreUsuario').value = usuario.nombre_usuario;
        document.getElementById('nombreUsuario').readOnly = true; // No se puede cambiar el username
        document.getElementById('contrasena').value = '';
        document.getElementById('contrasena').required = false;
        document.getElementById('helperContrasena').textContent = 'Dejar vacío para no cambiar';
        document.getElementById('estadoUsuario').value = usuario.activo.toString();
        
        // Cargar roles y seleccionar el actual
        const rolesResponse = await fetch(`${API_URL}/api/usuarios/roles`, { headers });
        const roles = await rolesResponse.json();
        const select = document.getElementById('rolId');
        select.innerHTML = roles.map(r => 
            `<option value="${r.id}" ${r.nombre === usuario.rol_nombre ? 'selected' : ''}>${r.nombre}</option>`
        ).join('');
        
        new bootstrap.Modal(document.getElementById('modalUsuario')).show();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar datos del usuario');
    }
}

// Guardar usuario (crear o actualizar)
async function guardarUsuario() {
    const usuarioId = document.getElementById('usuarioId').value;
    const esEdicion = usuarioId !== '';
    
    const data = {
        nombre_completo: document.getElementById('nombreCompleto').value,
        correo: document.getElementById('correo').value,
        rol_id: parseInt(document.getElementById('rolId').value),
        activo: document.getElementById('estadoUsuario').value === 'true'
    };
    
    if (!esEdicion) {
        data.nombre_usuario = document.getElementById('nombreUsuario').value;
        data.contrasena = document.getElementById('contrasena').value;
    }
    
    try {
        const url = esEdicion ? `${API_URL}/api/usuarios/${usuarioId}` : `${API_URL}/api/usuarios/`;
        const method = esEdicion ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(esEdicion ? 'Usuario actualizado correctamente' : 'Usuario creado correctamente');
            document.getElementById('formUsuario').reset();
            bootstrap.Modal.getInstance(document.getElementById('modalUsuario')).hide();
            cargarUsuarios();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error guardando usuario');
        console.error(error);
    }
}

// Eliminar usuario (sin cambios)
async function eliminarUsuario(id) {
    if (!confirm('¿Está seguro de eliminar este usuario?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/usuarios/${id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            alert('Usuario eliminado');
            cargarUsuarios();
        }
    } catch (error) {
        alert('Error eliminando usuario');
    }
}

// ========== GESTIÓN DE CLIENTES (COMPLETO CON EDITAR) ==========

// Cargar clientes
async function cargarClientes() {
    try {
        const response = await fetch(`${API_URL}/api/clientes/`, { headers });
        const clientes = await response.json();
        
        const tbody = document.getElementById('tablaClientes');
        if (clientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No hay clientes registrados</td></tr>';
            return;
        }
        
        tbody.innerHTML = clientes.map(c => `
            <tr>
                <td>${c.id}</td>
                <td>${c.nombre}</td>
                <td><code>${c.dominio_legitimo}</code></td>
                <td>${c.contacto_nombre || '-'}</td>
                <td>${c.contacto_correo || '-'}</td>
                <td>${c.contacto_telefono || '-'}</td>
                <td>${c.activo ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-danger">Inactivo</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-warning me-1" onclick="editarCliente(${c.id})">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarCliente(${c.id})">Eliminar</button>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('totalClientes').textContent = clientes.filter(c => c.activo).length;
    } catch (error) {
        console.error('Error cargando clientes:', error);
    }
}

// Modal crear cliente
function showModalCliente() {
    document.getElementById('tituloModalCliente').textContent = 'Crear Nuevo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
    new bootstrap.Modal(document.getElementById('modalCliente')).show();
}

// Editar cliente
async function editarCliente(id) {
    try {
        const response = await fetch(`${API_URL}/api/clientes/`, { headers });
        const clientes = await response.json();
        const cliente = clientes.find(c => c.id === id);
        
        if (!cliente) {
            alert('Cliente no encontrado');
            return;
        }
        
        document.getElementById('tituloModalCliente').textContent = 'Editar Cliente';
        document.getElementById('clienteId').value = cliente.id;
        document.getElementById('nombreCliente').value = cliente.nombre;
        document.getElementById('dominioLegitimo').value = cliente.dominio_legitimo;
        document.getElementById('contactoNombre').value = cliente.contacto_nombre || '';
        document.getElementById('contactoCorreo').value = cliente.contacto_correo || '';
        document.getElementById('contactoTelefono').value = cliente.contacto_telefono || '';
        document.getElementById('estadoCliente').value = cliente.activo.toString();
        
        new bootstrap.Modal(document.getElementById('modalCliente')).show();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar datos del cliente');
    }
}

// Guardar cliente (crear o actualizar)
async function guardarCliente() {
    const clienteId = document.getElementById('clienteId').value;
    const esEdicion = clienteId !== '';
    
    const data = {
        nombre: document.getElementById('nombreCliente').value,
        dominio_legitimo: document.getElementById('dominioLegitimo').value,
        contacto_nombre: document.getElementById('contactoNombre').value || null,
        contacto_correo: document.getElementById('contactoCorreo').value || null,
        contacto_telefono: document.getElementById('contactoTelefono').value || null,
        activo: document.getElementById('estadoCliente').value === 'true'
    };
    
    try {
        const url = esEdicion ? `${API_URL}/api/clientes/${clienteId}` : `${API_URL}/api/clientes/`;
        const method = esEdicion ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(esEdicion ? 'Cliente actualizado correctamente' : 'Cliente creado correctamente');
            document.getElementById('formCliente').reset();
            bootstrap.Modal.getInstance(document.getElementById('modalCliente')).hide();
            cargarClientes();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error guardando cliente');
        console.error(error);
    }
}

// Eliminar cliente (sin cambios)
async function eliminarCliente(id) {
    if (!confirm('¿Está seguro de eliminar este cliente? Se eliminarán también todos sus sitios asociados.')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/clientes/${id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            alert('Cliente eliminado correctamente');
            cargarClientes();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error eliminando cliente');
        console.error(error);
    }
}

// ========== GESTIÓN DE SITIOS PHISHING ==========

// Cargar sitios
async function cargarSitios() {
    try {
        const response = await fetch(`${API_URL}/api/sitios/`, { headers });
        const sitios = await response.json();
        
        const tbody = document.getElementById('tablaSitios');
        if (sitios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No hay sitios reportados</td></tr>';
            return;
        }
        
        tbody.innerHTML = sitios.map(s => {
            const estadoBadge = {
                'pendiente': 'bg-warning',
                'validado': 'bg-danger',
                'falso_positivo': 'bg-success',
                'takedown_enviado': 'bg-info',
                'sitio_caido': 'bg-secondary'
            }[s.estado] || 'bg-secondary';
            
            return `
                <tr>
                    <td>${s.id}</td>
                    <td>${s.cliente_nombre}</td>
                    <td><a href="${s.url}" target="_blank" class="text-danger">${s.url}</a></td>
                    <td><code>${s.dominio || '-'}</code></td>
                    <td><span class="badge ${estadoBadge}">${s.estado.toUpperCase()}</span></td>
                    <td>${s.usuario_reporta_nombre}</td>
                    <td>${new Date(s.fecha_reporte).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="validarSitio(${s.id})">Validar</button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarSitio(${s.id})">Eliminar</button>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Actualizar contadores
        document.getElementById('totalSitios').textContent = sitios.length;
        document.getElementById('totalPendientes').textContent = 
            sitios.filter(s => s.estado === 'pendiente').length;
    } catch (error) {
        console.error('Error cargando sitios:', error);
    }
}

// Modal reportar sitio
async function showModalReportarSitio() {
    document.getElementById('formReportarSitio').reset();
    
    // Cargar clientes activos
    const response = await fetch(`${API_URL}/api/clientes/`, { headers });
    const clientes = await response.json();
    
    const select = document.getElementById('clienteAfectado');
    select.innerHTML = '<option value="">Seleccione el cliente...</option>' +
        clientes.filter(c => c.activo).map(c => 
            `<option value="${c.id}">${c.nombre} (${c.dominio_legitimo})</option>`
        ).join('');
    
    new bootstrap.Modal(document.getElementById('modalReportarSitio')).show();
}

// Reportar sitio
async function reportarSitio() {
    const data = {
        cliente_id: parseInt(document.getElementById('clienteAfectado').value),
        url: document.getElementById('urlFraudulenta').value,
        notas: document.getElementById('notasSitio').value || null
    };
    
    if (!data.cliente_id) {
        alert('Debe seleccionar un cliente');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/sitios/`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('Sitio reportado correctamente');
            document.getElementById('formReportarSitio').reset();
            bootstrap.Modal.getInstance(document.getElementById('modalReportarSitio')).hide();
            cargarSitios();
            cargarEstadisticas(); // Actualizar dashboard
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error reportando sitio');
        console.error(error);
    }
}

// Eliminar sitio
async function eliminarSitio(id) {
    if (!confirm('¿Está seguro de eliminar este reporte?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/sitios/${id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            alert('Sitio eliminado correctamente');
            cargarSitios();
            cargarEstadisticas();
        }
    } catch (error) {
        alert('Error eliminando sitio');
        console.error(error);
    }
}
// Validar sitio con APIs
async function validarSitio(id) {
    if (!confirm('¿Desea validar este sitio con las APIs externas?\n\nNota: Se requieren API Keys configuradas.')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/sitios/${id}/validar`, {
            method: 'POST',
            headers
        });
        
        if (response.ok) {
            const result = await response.json();
            
            let mensaje = `Validación completada:\n\n`;
            mensaje += `URL: ${result.url}\n`;
            mensaje += `Estado: ${result.estado.toUpperCase()}\n`;
            mensaje += `¿Es malicioso?: ${result.es_malicioso ? 'SÍ' : 'NO'}\n\n`;
            mensaje += `Resultados por servicio:\n`;
            
            result.validaciones.forEach(v => {
                mensaje += `\n${v.servicio}:\n`;
                if (v.error) {
                    mensaje += `  - Error: ${v.error}\n`;
                } else {
                    mensaje += `  - Malicioso: ${v.malicioso ? 'SÍ' : 'NO'}\n`;
                    if (v.detecciones) mensaje += `  - Detecciones: ${v.detecciones}/${v.total_escaneos}\n`;
                    if (v.score) mensaje += `  - Score: ${v.score}%\n`;
                }
            });
            
            alert(mensaje);
            cargarSitios();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error al validar sitio');
        console.error(error);
    }
}