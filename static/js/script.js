document.addEventListener('DOMContentLoaded', function() {
    fetchProductos();

    document.getElementById('producto-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const productoId = document.getElementById('producto-id').value;
        if (productoId) {
            editarProducto(productoId);
        } else {
            agregarProducto();
        }
    });

    document.getElementById('venta-form').addEventListener('submit', function(event) {
        event.preventDefault();
        registrarVenta();
    });
});

let productos = [];

function fetchProductos() {
    fetch('/productos')
        .then(response => response.json())
        .then(data => {
            productos = data;
            renderProductos(productos);
        });
}

function renderProductos(productos) {
    const tbody = document.querySelector('#productos-table tbody');
    tbody.innerHTML = '';
    productos.forEach(producto => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${producto.nombre}</td>
            <td>${producto.codigo_barra}</td>
            <td>${producto.precio_costo}</td>
            <td>${producto.precio_venta}</td>
            <td>${producto.stock}</td>
            <td>${producto.margen_bruto}</td>
            <td>${producto.margen_neto.toFixed(2)}</td>
            <td>
                <button onclick="editarProductoForm(${producto.id})">Editar</button>
                <button onclick="eliminarProducto(${producto.id})">Eliminar</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function agregarProducto() {
    const nombre = document.getElementById('nombre').value;
    const codigo_barra = document.getElementById('codigo_barra').value;
    const precio_costo = parseFloat(document.getElementById('precio_costo').value);
    const precio_venta = parseFloat(document.getElementById('precio_venta').value);
    const stock = parseInt(document.getElementById('stock').value);

    const producto = {
        nombre,
        codigo_barra,
        precio_costo,
        precio_venta,
        stock
    };

    fetch('/productos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(producto)
    })
    .then(response => response.json())
    .then(data => {
        fetchProductos();
        document.getElementById('producto-form').reset();
        document.getElementById('producto-id').value = '';
    });
}

function editarProductoForm(id) {
    const producto = productos.find(p => p.id === id);
    document.getElementById('producto-id').value = producto.id;
    document.getElementById('nombre').value = producto.nombre;
    document.getElementById('codigo_barra').value = producto.codigo_barra;
    document.getElementById('precio_costo').value = producto.precio_costo;
    document.getElementById('precio_venta').value = producto.precio_venta;
    document.getElementById('stock').value = producto.stock;
}

function editarProducto(id) {
    const nombre = document.getElementById('nombre').value;
    const codigo_barra = document.getElementById('codigo_barra').value;
    const precio_costo = parseFloat(document.getElementById('precio_costo').value);
    const precio_venta = parseFloat(document.getElementById('precio_venta').value);
    const stock = parseInt(document.getElementById('stock').value);

    const producto = {
        nombre,
        codigo_barra,
        precio_costo,
        precio_venta,
        stock
    };

    fetch(`/productos/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(producto)
    })
    .then(response => response.json())
    .then(data => {
        fetchProductos();
        document.getElementById('producto-form').reset();
        document.getElementById('producto-id').value = '';
    });
}

function eliminarProducto(id) {
    fetch(`/productos/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        fetchProductos();
    });
}

function registrarVenta() {
    const codigoBarra = document.getElementById('venta-codigo-barra').value;
    const cantidad = parseInt(document.getElementById('cantidad').value);

    const venta = {
        codigo_barra: codigoBarra,
        cantidad
    };

    fetch('/ventas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(venta)
    })
    .then(response => response.json())
    .then(data => {
        fetchProductos();
        document.getElementById('venta-form').reset();
    });
}

function generarReporte() {
    fetch('/reporte')
        .then(response => response.json())
        .then(data => {
            const reporteOutput = document.getElementById('reporte-output');
            reporteOutput.textContent = JSON.stringify(data, null, 2);
        });
}