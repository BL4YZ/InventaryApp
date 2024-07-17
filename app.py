from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventario.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo_barra = db.Column(db.String(100), unique=True, nullable=False)
    precio_costo = db.Column(db.Float, nullable=False)
    precio_venta = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    def margen_bruto(self):
        return self.precio_venta - self.precio_costo

    def margen_neto(self):
        return (self.margen_bruto() / self.precio_costo) * 100

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship('Producto', backref=db.backref('ventas', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/productos', methods=['GET'])
@login_required
def get_productos():
    productos = Producto.query.all()
    productos_list = [{
        'id': p.id,
        'nombre': p.nombre,
        'codigo_barra': p.codigo_barra,
        'precio_costo': p.precio_costo,
        'precio_venta': p.precio_venta,
        'stock': p.stock,
        'margen_bruto': p.margen_bruto(),
        'margen_neto': p.margen_neto()
    } for p in productos]
    return jsonify(productos_list)

@app.route('/productos', methods=['POST'])
@login_required
def add_producto():
    data = request.json
    nuevo_producto = Producto(
        nombre=data['nombre'], 
        codigo_barra=data['codigo_barra'],
        precio_costo=data['precio_costo'],
        precio_venta=data['precio_venta'],
        stock=data['stock']
    )
    db.session.add(nuevo_producto)
    db.session.commit()
    return jsonify({'message': 'Producto agregado'}), 201

@app.route('/productos/<int:id>', methods=['DELETE'])
@login_required
def delete_producto(id):
    producto = Producto.query.get(id)
    if producto:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado'}), 200
    else:
        return jsonify({'message': 'Producto no encontrado'}), 404

@app.route('/productos/<int:id>', methods=['PUT'])
@login_required
def update_producto(id):
    producto = Producto.query.get(id)
    if producto:
        data = request.json
        producto.nombre = data['nombre']
        producto.codigo_barra = data['codigo_barra']
        producto.precio_costo = data['precio_costo']
        producto.precio_venta = data['precio_venta']
        producto.stock = data['stock']
        db.session.commit()
        return jsonify({'message': 'Producto actualizado'}), 200
    else:
        return jsonify({'message': 'Producto no encontrado'}), 404

@app.route('/ventas', methods=['POST'])
@login_required
def add_venta():
    data = request.json
    producto = Producto.query.filter_by(codigo_barra=data['codigo_barra']).first()
    if not producto:
        return jsonify({'message': 'Producto no encontrado'}), 404

    if producto.stock < data['cantidad']:
        return jsonify({'message': 'Stock insuficiente'}), 400

    nueva_venta = Venta(
        producto_id=producto.id,
        cantidad=data['cantidad']
    )

    producto.stock -= data['cantidad']

    db.session.add(nueva_venta)
    db.session.commit()
    return jsonify({'message': 'Venta registrada y stock actualizado'}), 201

@app.route('/reporte', methods=['GET'])
@login_required
def generar_reporte():
    mes_actual = datetime.utcnow().month
    ventas = Venta.query.filter(db.extract('month', Venta.fecha) == mes_actual).all()
    reporte = []
    total_ventas = 0
    total_ganancias = 0

    for v in ventas:
        producto = Producto.query.get(v.producto_id)
        total_venta = v.cantidad * producto.precio_venta
        ganancia = v.cantidad * producto.margen_bruto()
        total_ventas += total_venta
        total_ganancias += ganancia
        reporte.append({
            'id': v.id,
            'producto_nombre': producto.nombre,
            'cantidad': v.cantidad,
            'fecha': v.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'total_venta': total_venta,
            'ganancia': ganancia
        })

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    text = "Reporte de Ventas del Mes"
    text_width = c.stringWidth(text, "Helvetica", 12)
    c.drawString((width - text_width) / 2, 750, text)

    text = f"Total Ventas: {total_ventas}"
    text_width = c.stringWidth(text, "Helvetica", 12)
    c.drawString((width - text_width) / 2, 730, text)

    text = f"Total Ganancias: {total_ganancias}"
    text_width = c.stringWidth(text, "Helvetica", 12)
    c.drawString((width - text_width) / 2, 710, text)

    y = 690
    for r in reporte:
        text = (f"Producto: {r['producto_nombre']} - Cantidad: {r['cantidad']} - "
                f"Fecha: {r['fecha']} - Total Venta: {r['total_venta']}")
        text_width = c.stringWidth(text, "Helvetica", 10)
        c.drawString(72, y, text)
        y -= 20

    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='reporte.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)