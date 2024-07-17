from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    codigo_barra = db.Column(db.String(13), unique=True, nullable=False)
    precio_costo = db.Column(db.Float, nullable=False)
    precio_venta = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

    def margen_bruto(self):
        return self.precio_venta - self.precio_costo

    def margen_neto(self):
        return (self.precio_venta - self.precio_costo) / self.precio_venta * 100