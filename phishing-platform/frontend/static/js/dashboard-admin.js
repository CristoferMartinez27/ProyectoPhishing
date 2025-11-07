const API_URL = 'https://proyectophishing-production.up.railway.app/';
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

// Mostrar info del usuario y configurar permisos
document.getElementById('userInfo').textContent = `👤 ${usuario.nombre_completo}`;
document.getElementById('rolUsuario').textContent = usuario.rol === 'administrador' ? 'Administrador' : 'Analista';

// Configurar interfaz según rol
function configurarPermisosPorRol() {
    const esAdmin = usuario.rol === 'administrador';
    
    // Mostrar/ocultar menús según rol
    if (esAdmin) {
    document.getElementById('menu-usuarios').style.display = 'block';
    document.getElementById('menu-clientes').style.display = 'block';
    document.getElementById('menu-bitacora').style.display = 'block';  // ← AGREGAR
    document.getElementById('card-usuarios').style.display = 'block';
} else {
    document.getElementById('menu-usuarios').style.display = 'none';
    document.getElementById('menu-clientes').style.display = 'none';
    document.getElementById('menu-bitacora').style.display = 'none';  // ← AGREGAR
    document.getElementById('card-usuarios').style.display = 'none';
}
    
    return esAdmin;
}

// Ejecutar al cargar
const esAdmin = configurarPermisosPorRol();


// Cerrar sesión
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('usuario');
    window.location.href = 'login.html';
}

// Cambiar sección
// Cambiar sección
function showSection(section) {
    // Validar permisos
    if (!esAdmin && (section === 'usuarios' || section === 'clientes')) {
        alert('⛔ No tienes permisos para acceder a esta sección');
        return;
    }
    
    document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    if (section === 'dashboard') {
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
        cargarSitios();
    } else if (section === 'whitelist') {
        document.getElementById('whitelistSection').style.display = 'block';
        cargarWhitelist();
    } else if (section === 'takedown') {
        document.getElementById('takedownSection').style.display = 'block';
        cargarTakedowns();
    }else if (section === 'bitacora') {
        document.getElementById('bitacoraSection').style.display = 'block';
        cargarBitacora();
        cargarFiltrosBitacora();
    }if (esAdmin || !esAdmin) {  // Mostrar gráficos para todos
    cargarGraficos();
}
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        // Solo cargar usuarios si es admin
        if (esAdmin) {
            const usuariosResponse = await fetch(`${API_URL}/api/usuarios/`, { headers });
            const usuarios = await usuariosResponse.json();
            document.getElementById('totalUsuarios').textContent = usuarios.length;
        }
        
        // Cargar clientes para todos (fuera del if)
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
            ${esAdmin ? `
                <button class="btn btn-sm btn-warning me-1" onclick="editarUsuario(${u.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="eliminarUsuario(${u.id})">Eliminar</button>
            ` : '<em class="text-muted">Sin permisos</em>'}
        </td>
    </tr>
`).join('');
    } catch (error) {
        console.error('Error cargando usuarios:', error);
    }
}

// Modal crear usuario (nuevo)
async function showModalUsuario() {
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
    
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
            ${esAdmin ? `
                <button class="btn btn-sm btn-warning me-1" onclick="editarCliente(${c.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="eliminarCliente(${c.id})">Eliminar</button>
            ` : '<em class="text-muted">Solo lectura</em>'}
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
    document.getElementById('tituloModalCliente').textContent = 'Crear Nuevo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
    new bootstrap.Modal(document.getElementById('modalCliente')).show();
}

// Editar cliente
async function editarCliente(id) {
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
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
    if (!esAdmin) {
        alert('⛔ No tienes permisos para esta acción');
        return;
    }
    
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
                        ${s.es_malicioso ? `<button class="btn btn-sm btn-warning me-1" onclick="generarTakedown(${s.id})">Takedown</button>` : ''}
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
            cargarEstadisticas();
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
    if (!confirm('¿Desea validar este sitio con las APIs externas?\n\nNota: El proceso puede tardar hasta 20 segundos.')) return;
    
    // Mostrar mensaje de carga
    alert('⏳ Validando sitio...\n\nEsto puede tardar hasta 20 segundos.\nPor favor espere.');
    
    try {
        const response = await fetch(`${API_URL}/api/sitios/${id}/validar`, {
            method: 'POST',
            headers
        });
        
        if (response.ok) {
            const result = await response.json();
            
            let mensaje = `✅ Validación completada\n\n`;
            mensaje += `URL: ${result.url}\n`;
            if (result.ip) mensaje += `IP: ${result.ip}\n`;
            mensaje += `Estado: ${result.estado.toUpperCase()}\n`;
            mensaje += `¿Es malicioso?: ${result.es_malicioso ? 'SÍ' : 'NO'}\n`;
            mensaje += `Detecciones: ${result.detecciones}\n\n`;
            mensaje += `Resultados detallados:\n`;
            mensaje += `${'='.repeat(50)}\n`;
            
            result.validaciones.forEach(v => {
                mensaje += `\n${v.servicio}:\n`;
                if (v.error) {
                    mensaje += `  ❌ Error: ${v.error}\n`;
                } else {
                    mensaje += `  • Malicioso: ${v.malicioso ? 'SÍ ⚠️' : 'NO ✅'}\n`;
                    if (v.detecciones !== undefined) {
                        mensaje += `  • Detecciones: ${v.detecciones}/${v.total_escaneos}\n`;
                    }
                    if (v.score !== undefined) {
                        mensaje += `  • Score de abuso: ${v.score}%\n`;
                    }
                    if (v.reportes !== undefined) {
                        mensaje += `  • Reportes: ${v.reportes}\n`;
                    }
                    if (v.amenazas_detectadas !== undefined) {
                        mensaje += `  • Amenazas: ${v.amenazas_detectadas}\n`;
                    }
                    if (v.tipos_amenaza && v.tipos_amenaza.length > 0) {
                        mensaje += `  • Tipos: ${v.tipos_amenaza.join(', ')}\n`;
                    }
                }
            });
            
            alert(mensaje);
            cargarSitios();
        } else {
            const error = await response.json();
            alert('❌ Error: ' + error.detail);
        }
    } catch (error) {
        alert('❌ Error al validar sitio');
        console.error(error);
    }
}

// ========== GESTIÓN DE WHITELIST ==========

// Cargar whitelist
async function cargarWhitelist() {
    try {
        const response = await fetch(`${API_URL}/api/whitelist/`, { headers });
        const whitelist = await response.json();
        
        const tbody = document.getElementById('tablaWhitelist');
        if (whitelist.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay URLs en la whitelist</td></tr>';
            return;
        }
        
        tbody.innerHTML = whitelist.map(w => `
            <tr>
                <td>${w.id}</td>
                <td><span class="badge bg-info">${w.cliente_nombre}</span></td>
                <td><code>${w.url}</code></td>
                <td>${w.descripcion || '<em class="text-muted">Sin descripción</em>'}</td>
                <td>${new Date(w.fecha_agregado).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-warning me-1" onclick="editarWhitelist(${w.id})">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarWhitelist(${w.id})">Eliminar</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando whitelist:', error);
    }
}

// Modal agregar whitelist
async function showModalWhitelist() {
    document.getElementById('tituloModalWhitelist').textContent = 'Agregar URL a Whitelist';
    document.getElementById('formWhitelist').reset();
    document.getElementById('whitelistId').value = '';
    
    // Cargar clientes activos
    const response = await fetch(`${API_URL}/api/clientes/`, { headers });
    const clientes = await response.json();
    
    const select = document.getElementById('whitelistCliente');
    select.innerHTML = '<option value="">Seleccione el cliente...</option>' +
        clientes.filter(c => c.activo).map(c => 
            `<option value="${c.id}">${c.nombre} (${c.dominio_legitimo})</option>`
        ).join('');
    
    new bootstrap.Modal(document.getElementById('modalWhitelist')).show();
}

// Editar whitelist
async function editarWhitelist(id) {
    try {
        const response = await fetch(`${API_URL}/api/whitelist/`, { headers });
        const whitelist = await response.json();
        const item = whitelist.find(w => w.id === id);
        
        if (!item) {
            alert('Entrada no encontrada');
            return;
        }
        
        document.getElementById('tituloModalWhitelist').textContent = 'Editar Whitelist';
        document.getElementById('whitelistId').value = item.id;
        document.getElementById('whitelistUrl').value = item.url;
        document.getElementById('whitelistDescripcion').value = item.descripcion || '';
        
        // Cargar clientes y seleccionar el actual
        const clientesResponse = await fetch(`${API_URL}/api/clientes/`, { headers });
        const clientes = await clientesResponse.json();
        const select = document.getElementById('whitelistCliente');
        select.innerHTML = clientes.filter(c => c.activo).map(c => 
            `<option value="${c.id}" ${c.id === item.cliente_id ? 'selected' : ''}>${c.nombre}</option>`
        ).join('');
        select.disabled = true;
        
        new bootstrap.Modal(document.getElementById('modalWhitelist')).show();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar datos');
    }
}

// Guardar whitelist
async function guardarWhitelist() {
    const whitelistId = document.getElementById('whitelistId').value;
    const esEdicion = whitelistId !== '';
    
    const data = {
        url: document.getElementById('whitelistUrl').value,
        descripcion: document.getElementById('whitelistDescripcion').value || null
    };
    
    if (!esEdicion) {
        data.cliente_id = parseInt(document.getElementById('whitelistCliente').value);
        if (!data.cliente_id) {
            alert('Debe seleccionar un cliente');
            return;
        }
    }
    
    try {
        const url = esEdicion ? `${API_URL}/api/whitelist/${whitelistId}` : `${API_URL}/api/whitelist/`;
        const method = esEdicion ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(esEdicion ? 'Whitelist actualizada correctamente' : 'URL agregada a whitelist correctamente');
            document.getElementById('formWhitelist').reset();
            document.getElementById('whitelistCliente').disabled = false;
            bootstrap.Modal.getInstance(document.getElementById('modalWhitelist')).hide();
            cargarWhitelist();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error guardando en whitelist');
        console.error(error);
    }
}

// Eliminar de whitelist
async function eliminarWhitelist(id) {
    if (!confirm('¿Está seguro de eliminar esta URL de la whitelist?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/whitelist/${id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            alert('URL eliminada de la whitelist correctamente');
            cargarWhitelist();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error eliminando de whitelist');
        console.error(error);
    }
}

let takedownActualId = null;
// Cargar takedowns
async function cargarTakedowns() {
    try {
        const response = await fetch(`${API_URL}/api/takedown/`, { headers });
        const takedowns = await response.json();
        
        const tbody = document.getElementById('tablaTakedown');
        if (takedowns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay solicitudes de takedown</td></tr>';
            return;
        }
        
        tbody.innerHTML = takedowns.map(t => {
            const estadoBadge = {
                'pendiente': 'bg-secondary',
                'enviado': 'bg-info',
                'confirmado': 'bg-success',
                'rechazado': 'bg-danger'
            }[t.estado] || 'bg-secondary';
            
            return `
                <tr>
                    <td>${t.id}</td>
                    <td><code>${t.sitio_url}</code></td>
                    <td>${t.cliente_nombre}</td>
                    <td>${t.destinatario}</td>
                    <td><span class="badge ${estadoBadge}">${t.estado.toUpperCase()}</span></td>
                    <td>${t.fecha_envio ? new Date(t.fecha_envio).toLocaleDateString() : '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-info me-1" onclick="verTakedown(${t.id})">Ver</button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarTakedown(${t.id})">Eliminar</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando takedowns:', error);
    }
}

// Generar takedown
// Generar takedown
async function generarTakedown(sitioId) {
    try {
        const response = await fetch(`${API_URL}/api/takedown/generar/${sitioId}`, {
            method: 'POST',
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            alert('Error: ' + error.detail);
            return;
        }

        const data = await response.json();

        // Llenar el formulario
        document.getElementById('takedownSitioId').value = sitioId;
        document.getElementById('takedownDestinatario').value = '';
        document.getElementById('takedownSugerencia').textContent = data.destinatario_sugerido;
        document.getElementById('takedownAsunto').value = data.asunto;
        document.getElementById('takedownCuerpo').value = data.cuerpo;
        
        // Mostrar lista de proveedores comunes
        const listaEmails = document.getElementById('listaEmails');
        listaEmails.innerHTML = data.emails_abuse_comunes.map(email => 
            `<li>${email}</li>`
        ).join('');
        
        // Guardar los emails comunes en un atributo data
        document.getElementById('enviarATodos').setAttribute('data-emails', JSON.stringify(data.emails_abuse_comunes));
        
        // Marcar checkbox por defecto
        document.getElementById('enviarATodos').checked = true;
        document.getElementById('listaProveedoresComunes').style.display = 'block';
        
        // Deshabilitar edición por defecto
        document.getElementById('takedownAsunto').readOnly = true;
        document.getElementById('takedownCuerpo').readOnly = true;
        
        // Mostrar modal
        new bootstrap.Modal(document.getElementById('modalGenerarTakedown')).show();
        
    } catch (error) {
        console.error('Error generando el takedown:', error);
        alert('Hubo un error al generar el takedown.');
    }
}

// Toggle envío masivo
function toggleEnvioMasivo() {
    const checkbox = document.getElementById('enviarATodos');
    const lista = document.getElementById('listaProveedoresComunes');
    
    if (checkbox.checked) {
        lista.style.display = 'block';
    } else {
        lista.style.display = 'none';
    }
}

// Habilitar edición del template
function habilitarEdicion() {
    document.getElementById('takedownAsunto').readOnly = false;
    document.getElementById('takedownCuerpo').readOnly = false;
    alert('Ahora puedes editar el asunto y el cuerpo del email');
}

// Copiar al portapapeles
function copiarAlPortapapeles() {
    const cuerpo = document.getElementById('takedownCuerpo').value;
    navigator.clipboard.writeText(cuerpo).then(() => {
        alert('✅ Email copiado al portapapeles');
    }).catch(err => {
        console.error('Error al copiar:', err);
        alert('No se pudo copiar al portapapeles');
    });
}

// Guardar takedown
async function guardarTakedown() {
    const sitioId = document.getElementById('takedownSitioId').value;
    const destinatario = document.getElementById('takedownDestinatario').value;
    const asunto = document.getElementById('takedownAsunto').value;
    const cuerpo = document.getElementById('takedownCuerpo').value;
    const enviarATodos = document.getElementById('enviarATodos').checked;
    
    if (!destinatario) {
        alert('Debe ingresar un email destinatario principal (del hosting específico)');
        return;
    }
    
    // Preparar lista de destinatarios
    let destinatarios_secundarios = [];
    
    if (enviarATodos) {
        const emailsComunes = JSON.parse(document.getElementById('enviarATodos').getAttribute('data-emails'));
        destinatarios_secundarios = emailsComunes;
    }
    
    const data = {
        sitio_id: parseInt(sitioId),
        destinatario_principal: destinatario,
        destinatarios_secundarios: destinatarios_secundarios.length > 0 ? destinatarios_secundarios : null,
        asunto: asunto,
        cuerpo: cuerpo
    };
    
    const totalDestinatarios = 1 + (destinatarios_secundarios.length || 0);
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(`✅ Solicitud de takedown guardada correctamente.\n\nSe generó para ${totalDestinatarios} destinatario(s):\n- Principal: ${destinatario}\n${destinatarios_secundarios.length > 0 ? '- Adicionales: ' + destinatarios_secundarios.length : ''}\n\nAhora puedes copiar el email y enviarlo.`);
            document.getElementById('formGenerarTakedown').reset();
            bootstrap.Modal.getInstance(document.getElementById('modalGenerarTakedown')).hide();
            cargarTakedowns();
            cargarSitios();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error guardando takedown');
        console.error(error);
    }
}

// Ver detalles de takedown
// Ver detalles de takedown
async function verTakedown(id) {
    try {
        const response = await fetch(`${API_URL}/api/takedown/`, { headers });
        const takedowns = await response.json();
        const takedown = takedowns.find(t => t.id === id);
        
        if (!takedown) {
            alert('Takedown no encontrado');
            return;
        }
        
        takedownActualId = id;
        
        // Mostrar destinatarios
        let destinatariosHTML = `<strong>Principal:</strong> ${takedown.destinatario}`;
        if (takedown.destinatarios_adicionales) {
            const cantidad = takedown.destinatarios_adicionales.split(',').length;
            destinatariosHTML += `<br><strong>CC (${cantidad} adicionales):</strong> ${takedown.destinatarios_adicionales}`;
        }
        document.getElementById('verDestinatario').innerHTML = destinatariosHTML;
        
        document.getElementById('verAsunto').textContent = takedown.asunto;
        document.getElementById('verCuerpo').textContent = takedown.cuerpo;
        
        const estadoBadge = {
            'pendiente': '<span class="badge bg-secondary">PENDIENTE</span>',
            'enviado': '<span class="badge bg-info">ENVIADO</span>',
            'confirmado': '<span class="badge bg-success">CONFIRMADO</span>',
            'rechazado': '<span class="badge bg-danger">RECHAZADO</span>'
        }[takedown.estado] || '<span class="badge bg-secondary">DESCONOCIDO</span>';
        
        document.getElementById('verEstado').innerHTML = estadoBadge;
        
        // Mostrar/ocultar botones según estado
        const btnEnviarEmail = document.getElementById('btnEnviarEmail');
        const btnEnviado = document.getElementById('btnMarcarEnviado');
        const btnConfirmado = document.getElementById('btnMarcarConfirmado');
        
        if (takedown.estado === 'pendiente') {
            btnEnviarEmail.style.display = 'inline-block';
            btnEnviado.style.display = 'inline-block';
            btnConfirmado.style.display = 'none';
        } else if (takedown.estado === 'enviado') {
            btnEnviarEmail.style.display = 'none';
            btnEnviado.style.display = 'none';
            btnConfirmado.style.display = 'inline-block';
        } else {
            btnEnviarEmail.style.display = 'none';
            btnEnviado.style.display = 'none';
            btnConfirmado.style.display = 'none';
        }
        
        if (takedown.respuesta_proveedor) {
            document.getElementById('seccionRespuesta').style.display = 'block';
            document.getElementById('verRespuesta').value = takedown.respuesta_proveedor;
        } else {
            document.getElementById('seccionRespuesta').style.display = 'none';
        }
        
        new bootstrap.Modal(document.getElementById('modalVerTakedown')).show();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar detalles del takedown');
    }
}

// Marcar como enviado
async function marcarComoEnviado() {
    if (!takedownActualId) return;
    
    if (!confirm('¿Confirma que envió el email al proveedor?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/${takedownActualId}/marcar-enviado`, {
            method: 'POST',
            headers
        });
        
        if (response.ok) {
            alert('✅ Takedown marcado como ENVIADO');
            bootstrap.Modal.getInstance(document.getElementById('modalVerTakedown')).hide();
            cargarTakedowns();
            cargarSitios();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error al actualizar takedown');
        console.error(error);
    }
}

// Marcar como confirmado
async function marcarComoConfirmado() {
    if (!takedownActualId) return;
    
    if (!confirm('¿Confirma que el proveedor eliminó el sitio fraudulento?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/${takedownActualId}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({
                estado: 'confirmado',
                respuesta_proveedor: document.getElementById('verRespuesta').value || null
            })
        });
        
        if (response.ok) {
            alert('✅ Takedown CONFIRMADO. El sitio ha sido marcado como caído.');
            bootstrap.Modal.getInstance(document.getElementById('modalVerTakedown')).hide();
            cargarTakedowns();
            cargarSitios();
            cargarEstadisticas(); // Actualizar dashboard
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error al actualizar takedown');
        console.error(error);
    }
}

// Actualizar respuesta del proveedor
async function actualizarRespuesta() {
    if (!takedownActualId) return;
    
    const respuesta = document.getElementById('verRespuesta').value;
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/${takedownActualId}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({
                estado: 'enviado', // Mantener el estado actual
                respuesta_proveedor: respuesta
            })
        });
        
        if (response.ok) {
            alert('✅ Respuesta guardada correctamente');
            cargarTakedowns();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error al guardar respuesta');
        console.error(error);
    }
}

// Eliminar takedown
async function eliminarTakedown(id) {
    if (!confirm('¿Está seguro de eliminar esta solicitud de takedown?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/${id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            alert('Takedown eliminado correctamente');
            cargarTakedowns();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        alert('Error eliminando takedown');
        console.error(error);
    }
}

// Enviar email automático
async function enviarEmailTakedown() {
    if (!takedownActualId) return;
    
    if (!confirm('¿Desea enviar el email de takedown AHORA vía SMTP?\n\nSe enviará automáticamente a todos los destinatarios configurados.')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/takedown/${takedownActualId}/enviar-email`, {
            method: 'POST',
            headers
        });
        
        if (response.ok) {
            const resultado = await response.json();
            const destinatarios = resultado.destinatarios_enviados.join('\n- ');
            alert(`✅ ${resultado.mensaje}\n\nDestinatarios:\n- ${destinatarios}`);
            bootstrap.Modal.getInstance(document.getElementById('modalVerTakedown')).hide();
            cargarTakedowns();
            cargarSitios();
        } else {
            const error = await response.json();
            alert('❌ Error al enviar email:\n\n' + error.detail);
        }
    } catch (error) {
        alert('❌ Error al enviar email');
        console.error(error);
    }
}


// ========== GESTIÓN DE BITÁCORA ==========

// Cargar bitácora
async function cargarBitacora() {
    try {
        const limite = document.getElementById('limiteBitacora').value;
        const accion = document.getElementById('filtroBitacoraAccion').value;
        const usuario_id = document.getElementById('filtroBitacoraUsuario').value;
        
        let url = `${API_URL}/api/bitacora/?limite=${limite}`;
        if (accion) url += `&accion=${accion}`;
        if (usuario_id) url += `&usuario_id=${usuario_id}`;
        
        const response = await fetch(url, { headers });
        const bitacoras = await response.json();
        
        const tbody = document.getElementById('tablaBitacora');
        if (bitacoras.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay registros de bitácora</td></tr>';
            return;
        }
        
        tbody.innerHTML = bitacoras.map(b => {
            const fecha = new Date(b.fecha);
            const fechaFormateada = fecha.toLocaleDateString() + ' ' + fecha.toLocaleTimeString();
            
            const accionBadge = {
                'LOGIN': 'bg-success',
                'CREAR': 'bg-primary',
                'ACTUALIZAR': 'bg-warning',
                'ELIMINAR': 'bg-danger',
                'VALIDAR': 'bg-info',
                'ENVIAR': 'bg-secondary'
            };
            
            let badgeClass = 'bg-secondary';
            for (let key in accionBadge) {
                if (b.accion.includes(key)) {
                    badgeClass = accionBadge[key];
                    break;
                }
            }
            
            return `
                <tr>
                    <td>${b.id}</td>
                    <td><small>${fechaFormateada}</small></td>
                    <td><small>${b.usuario_nombre}</small></td>
                    <td><span class="badge ${badgeClass}">${b.accion}</span></td>
                    <td><small>${b.detalle || '-'}</small></td>
                    <td><small>${b.ip_origen || '-'}</small></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando bitácora:', error);
    }
}

// Cargar filtros de bitácora
async function cargarFiltrosBitacora() {
    try {
        // Cargar acciones
        const accionesResponse = await fetch(`${API_URL}/api/bitacora/acciones`, { headers });
        const acciones = await accionesResponse.json();
        
        const selectAccion = document.getElementById('filtroBitacoraAccion');
        selectAccion.innerHTML = '<option value="">Todas</option>' +
            acciones.map(a => `<option value="${a}">${a}</option>`).join('');
        
        // Cargar usuarios
        const usuariosResponse = await fetch(`${API_URL}/api/usuarios/`, { headers });
        const usuarios = await usuariosResponse.json();
        
        const selectUsuario = document.getElementById('filtroBitacoraUsuario');
        selectUsuario.innerHTML = '<option value="">Todos</option>' +
            usuarios.map(u => `<option value="${u.id}">${u.nombre_completo}</option>`).join('');
    } catch (error) {
        console.error('Error cargando filtros:', error);
    }
}

// Limpiar filtros
function limpiarFiltrosBitacora() {
    document.getElementById('filtroBitacoraAccion').value = '';
    document.getElementById('filtroBitacoraUsuario').value = '';
    document.getElementById('limiteBitacora').value = '100';
    cargarBitacora();
}

// Ver estadísticas de bitácora
async function cargarEstadisticasBitacora() {
    try {
        const response = await fetch(`${API_URL}/api/bitacora/estadisticas`, { headers });
        const stats = await response.json();
        
        let mensaje = `📊 ESTADÍSTICAS DE BITÁCORA\n\n`;
        mensaje += `Total de registros: ${stats.total_registros}\n`;
        mensaje += `Últimas 24h: ${stats.registros_24h}\n\n`;
        
        mensaje += `Acciones más frecuentes:\n`;
        mensaje += `${'-'.repeat(40)}\n`;
        stats.acciones_frecuentes.forEach(a => {
            mensaje += `${a.accion}: ${a.cantidad}\n`;
        });
        
        mensaje += `\nUsuarios más activos:\n`;
        mensaje += `${'-'.repeat(40)}\n`;
        stats.usuarios_activos.forEach(u => {
            mensaje += `${u.nombre}: ${u.acciones} acciones\n`;
        });
        
        alert(mensaje);
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar estadísticas');
    }
}


// ========== GRÁFICOS Y ESTADÍSTICAS ==========

let chartEstadosSitios, chartActividadSemanal, chartTopClientes, chartTakedowns;

async function cargarGraficos() {
    try {
        const response = await fetch(`${API_URL}/api/sitios/estadisticas`, { headers });
        const stats = await response.json();
        
        // Destruir gráficos existentes antes de crear nuevos
        if (chartEstadosSitios) chartEstadosSitios.destroy();
        if (chartActividadSemanal) chartActividadSemanal.destroy();
        if (chartTopClientes) chartTopClientes.destroy();
        if (chartTakedowns) chartTakedowns.destroy();
        
        // Gráfico de sitios por estado
        crearGraficoEstadosSitios(stats.sitios_por_estado);
        
        // Gráfico de actividad semanal
        crearGraficoActividadSemanal(stats.actividad_semanal);
        
        // Gráfico top clientes
        crearGraficoTopClientes(stats.top_clientes);
        
        // Gráfico takedowns
        crearGraficoTakedowns(stats.takedowns_estados);
        
    } catch (error) {
        console.error('Error cargando gráficos:', error);
    }
}

function crearGraficoEstadosSitios(data) {
    const ctx = document.getElementById('chartEstadosSitios');
    if (!ctx) return;
    
    const estados = {
        'pendiente': { label: 'Pendientes', color: '#ffc107' },
        'validado': { label: 'Validados', color: '#dc3545' },
        'falso_positivo': { label: 'Falsos Positivos', color: '#28a745' },
        'takedown_enviado': { label: 'Takedown Enviado', color: '#17a2b8' },
        'sitio_caido': { label: 'Sitio Caído', color: '#6c757d' }
    };
    
    const labels = [];
    const valores = [];
    const colores = [];
    
    for (let estado in estados) {
        if (data[estado]) {
            labels.push(estados[estado].label);
            valores.push(data[estado]);
            colores.push(estados[estado].color);
        }
    }
    
    chartEstadosSitios = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: colores
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function crearGraficoActividadSemanal(data) {
    const ctx = document.getElementById('chartActividadSemanal');
    if (!ctx) return;
    
    // Ordenar por fecha
    data.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
    
    const labels = data.map(d => {
        const fecha = new Date(d.fecha);
        return fecha.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
    });
    const valores = data.map(d => d.cantidad);
    
    chartActividadSemanal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sitios Reportados',
                data: valores,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function crearGraficoTopClientes(data) {
    const ctx = document.getElementById('chartTopClientes');
    if (!ctx) return;
    
    const labels = data.map(c => c.nombre);
    const valores = data.map(c => c.cantidad);
    
    chartTopClientes = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sitios Reportados',
                data: valores,
                backgroundColor: [
                    '#dc3545',
                    '#fd7e14',
                    '#ffc107',
                    '#20c997',
                    '#17a2b8'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function crearGraficoTakedowns(data) {
    const ctx = document.getElementById('chartTakedowns');
    if (!ctx) return;
    
    const estados = {
        'pendiente': { label: 'Pendientes', color: '#6c757d' },
        'enviado': { label: 'Enviados', color: '#17a2b8' },
        'confirmado': { label: 'Confirmados', color: '#28a745' },
        'rechazado': { label: 'Rechazados', color: '#dc3545' }
    };
    
    const labels = [];
    const valores = [];
    const colores = [];
    
    for (let estado in estados) {
        if (data[estado]) {
            labels.push(estados[estado].label);
            valores.push(data[estado]);
            colores.push(estados[estado].color);
        }
    }
    
    chartTakedowns = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: colores
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ========== EXPORTAR CSV ==========

// Modal exportar CSV
async function showModalExportarCSV() {
    document.getElementById('formExportarCSV').reset();
    document.getElementById('infoExportacion').style.display = 'none';
    document.getElementById('btnDescargarCSV').disabled = true;
    
    // Cargar clientes
    const response = await fetch(`${API_URL}/api/clientes/`, { headers });
    const clientes = await response.json();
    
    const select = document.getElementById('clienteExportar');
    select.innerHTML = '<option value="">Seleccione un cliente...</option>' +
        clientes.filter(c => c.activo).map(c => 
            `<option value="${c.id}" data-nombre="${c.nombre}" data-dominio="${c.dominio_legitimo}">${c.nombre} (${c.dominio_legitimo})</option>`
        ).join('');
    
    // Evento change para mostrar información
    select.onchange = async function() {
        const clienteId = this.value;
        if (!clienteId) {
            document.getElementById('infoExportacion').style.display = 'none';
            document.getElementById('btnDescargarCSV').disabled = true;
            return;
        }
        
        const selectedOption = this.options[this.selectedIndex];
        const clienteNombre = selectedOption.getAttribute('data-nombre');
        const clienteDominio = selectedOption.getAttribute('data-dominio');
        
        // Obtener cantidad de sitios del cliente
        try {
            const sitiosResponse = await fetch(`${API_URL}/api/sitios/`, { headers });
            const sitios = await sitiosResponse.json();
            const sitiosCliente = sitios.filter(s => s.cliente_id == clienteId);
            
            document.getElementById('infoClienteNombre').textContent = clienteNombre;
            document.getElementById('infoClienteDominio').textContent = clienteDominio;
            document.getElementById('infoTotalSitios').textContent = sitiosCliente.length;
            
            if (sitiosCliente.length > 0) {
                document.getElementById('infoExportacion').style.display = 'block';
                document.getElementById('btnDescargarCSV').disabled = false;
            } else {
                document.getElementById('infoExportacion').style.display = 'none';
                document.getElementById('btnDescargarCSV').disabled = true;
                alert('⚠️ Este cliente no tiene sitios reportados para exportar');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al verificar sitios del cliente');
        }
    };
    
    new bootstrap.Modal(document.getElementById('modalExportarCSV')).show();
}

// Descargar CSV
async function descargarCSV() {
    const clienteId = document.getElementById('clienteExportar').value;
    
    if (!clienteId) {
        alert('Debe seleccionar un cliente');
        return;
    }
    
    try {
        // Hacer petición para descargar
        const response = await fetch(`${API_URL}/api/sitios/exportar-csv/${clienteId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert('Error: ' + error.detail);
            return;
        }
        
        // Obtener el blob y crear enlace de descarga
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Obtener nombre del archivo del header
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'reporte_sitios.csv';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        alert('Reporte CSV descargado correctamente');
        bootstrap.Modal.getInstance(document.getElementById('modalExportarCSV')).hide();
        
    } catch (error) {
        console.error('Error descargando CSV:', error);
        alert('Error al descargar el archivo CSV');
    }
}