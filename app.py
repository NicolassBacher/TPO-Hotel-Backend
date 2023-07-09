# IMPORTAR HERRAMIENTAS
from flask import Flask, request, jsonify

# Se usa en una api rest, permite conectar desde el frontend a una api.
from flask_cors import CORS

# Los siguientes módulos ayudan al manejo de la base de datos.
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.ext.declarative import declarative_base

from datetime import date, datetime as dt
import pandas as pd
from json import dumps


# Crear la app
app = Flask(__name__)

# Usar Cors para dar acceso a las rutas(ebdpoint) desde frontend
CORS(app)

# CONFIGURACIÓN A LA BASE DE DATOS DESDE app
#  (SE LE INFORMA A LA APP DONDE UBICAR LA BASE DE DATOS)
                                                    # //username:password@url/nombre de la base de datos
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:@localhost/proyecto2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False 

# COMUNICAR LA APP CON SQLALCHEMY
db = SQLAlchemy(app)

# PERMITIR LA TRANSFORMACIÓN DE DATOS
ma = Marshmallow(app)


# ESTRUCTURA DE LA TABLA producto A PARTIR DE LA CLASE
class Reserva(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    checkin = db.Column(db.Date)
    checkout = db.Column(db.Date)
    habitacion = db.Column(db.String(50))
    precio = db.Column(db.Integer)
    nombre = db.Column(db.String(50))
    apellido = db.Column(db.String(50))
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(50))
    comentario = db.Column(db.String(500))


    def __init__(self,checkin,checkout,habitacion,precio,nombre, apellido,telefono,email,comentario):
        self.checkin = checkin
        self.checkout = checkout
        self.habitacion = habitacion
        self.precio = precio
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.email = email
        self.comentario = comentario

    #Metodo que devuelve un diccionario
    def serialize(self):
        return {
            "id": self.id,
            "checkin": self.checkin,
            "checkout": self.checkout,
            "habitacion": self.habitacion,
            "precio": self.precio,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "telefono": self.telefono,
            "email": self.email,
            "comentario": self.comentario
        }

# CÓDIGO PARA CREAR LAS TABLAS DEFINIDAS EN LAS CLASES
with app.app_context():
    db.create_all()

# CREAR UNA CLASE  ProductoSchema, DONDE SE DEFINEN LOS CAMPOS DE LA TABLA
class ReservaSchema(ma.Schema):
    class Meta:
        fields=('id','checkin','checkout', 'habitacion', 'precio','nombre', 'apellido','telefono', 'email', 'comentario')


# DIFERENCIAR CUANDO SE TRANSFORME UN DATO O UNA LISTA DE DATOS
reserva_schema = ReservaSchema()
reservas_schema = ReservaSchema(many=True)




# CREAR LAS RUTAS PARA: productos
# '/reservas' ENDPOINT PARA MOSTRAR SI EXISTE DISPONIBILIDAD DE LA HABITACION EN LAS FECHAS SELECCIONADAS EN LA BASE DE DATOS: POST
# '/reservas' ENDPOINT PARA RECIBIR DATOS (RESERVA): POST
# '/reservas/<id>' ENDPOINT PARA MOSTRAR UNA RESERVA POR ID: GET
# '/reservas/<id>' ENDPOINT PARA BORRAR UNA RESERVA POR ID: DELETE
# '/reservas/<id>' ENDPOINT PARA MODIFICAR UNA RESERVA POR ID: PUT

#Ruta para consultar si existe disponibilidad
@app.route("/consultas", methods=['POST'])
def consultar_disponibilidad():

    ingreso = request.json['ingreso']
    salida = request.json['salida']
    habit = request.json['habit']

    respuesta = {
        'disponibilidad' : False,
        'ingreso' : ingreso,
        'salida' : salida,
        'cantidad_noches' : 0,
        'habit' : habit,
        'precio' : 0,
        'error' : False,
        'msj' : ''    
    }
    
    try:
        #Convierto los argumentos en formato de fecha
        ingreso = dt.date(dt.strptime(ingreso, '%Y-%m-%d'))
        salida = dt.date(dt.strptime(salida, '%Y-%m-%d'))

        #chequeo que las fechas solicitadas sean mayores al dia actual y que la fecha de salida sea mayor al igreso
        if (ingreso < date.today()) | (salida <= ingreso):
            respuesta['error'] = True
            respuesta['msj'] = "La fecha ingresada no es correcta"
            return dumps(respuesta)
    except:
        #si existe un error en las la conversion de fechas, envio msj que la fechas son incorrectas
        respuesta['error'] = True
        respuesta['msj'] = 'Debe seleccionar una fecha correcta'
        return dumps(respuesta)
    
    # Creo un dataframe de pandas para manipular los datos de reserva
    # df = pd.read_sql_query(
    #     sql = db.select(Reserva),
    #     con = 'mysql+pymysql://root:@localhost/proyecto2' 
    # )

    #Covierto los datos de la base de datos en un diccionario
    all_reservas = Reserva.query.all()
    all_reservas = list(map(lambda x: x.serialize(), all_reservas))
    #print(all_reservas)

    #convierto el diccionario en un dataFrame de pandas
    df = pd.DataFrame(all_reservas)
    
    #Filtro por la habitacion solicitada y por reservas de fechas mayores al dia de hoy
    df = (df[(df['habitacion']==habit) & (df['checkout'] > date.today())])

    #chequeo de disponibilidad en la habitacion seleccionada
    #si sale por verdadero no hay disponibilidad, cargo disponibilidad = false y msj de que no hay disponibilidad
    for i,o in zip(df.checkin, df.checkout):
        if (ingreso >= i) & (ingreso < o):
            respuesta['disponibilidad'] = False
            respuesta['msj'] = f'No disponemos de lugar para la habitacion {habit} en las fechas seleccionadas, vuelva a intentarlo con otras fechas o habitacion'
            return dumps(respuesta)
        
        elif (salida > i) & (salida <= o):
            respuesta['disponibilidad'] = False
            respuesta['msj'] = f'No disponemos de lugar para la habitacion {habit} en las fechas seleccionadas, vuelva a intentarlo con otras fechas o habitacion'
            return dumps(respuesta)
        
        elif (i >= ingreso) & (i < salida):
            respuesta['disponibilidad'] = False
            respuesta['msj'] = f'No disponemos de lugar para la habitacion {habit} en las fechas seleccionadas, vuelva a intentarlo con otras fechas o habitacion'
            return dumps(respuesta)
        
        elif (o > ingreso) & (o <= salida):
            respuesta['disponibilidad'] = False
            respuesta['msj'] = f'No disponemos de lugar para la habitacion {habit} en las fechas seleccionadas, vuelva a intentarlo con otras fechas o habitacion'
            return dumps(respuesta)

    #calculo la cantidad de noches y multiplico por el precio dependiendo de la habitacion
    catidad_noches = (salida - ingreso).days
    precio = 0
    if habit == 'sencilla':
        precio = catidad_noches*40000
    elif habit == 'doble':
        precio = catidad_noches*44000
    elif habit == 'jr_suite':
        precio = catidad_noches*46000
    elif habit == 'deluxe':
        precio = catidad_noches*50000

    #si se llega hasta aca, existe disponibilidad y esta todo ok
    #envio disponibilidad = True, precio, cantidad de noches y msj de disponibilidad
    respuesta['disponibilidad']=True
    respuesta['precio'] = precio
    respuesta['cantidad_noches'] = catidad_noches
    respuesta['msj'] = f'La habitacion {habit} se encuentra disponible, por favor complete el siguiente formulario para concretar su reserva'
    return dumps(respuesta)
        

#Ruta para ver todas las reservas, NO USADA POR EL MOMENTO
@app.route("/reservas", methods=['GET'])
def get_reservas():
                    # select * from producto
    all_reservas = Reserva.query.all()        
    return reservas_schema.jsonify(all_reservas)

#Ruta para guardar los datos de reserva en la db
#FALTA AGREGAR COMPROBACION DE DATOS, VERIFICAR QUE LAS FECHAS DE RESERVA, HABITACION Y PRECIO NO FUERON MANIPULADOS
@app.route("/reservas", methods=['POST'])
def create_reserva():
    """
    Entrada de datos:
    {
        "checkin": "16-8-23",
        "checkout": "17-8-23",
        "habitacion": "Doble",
        "precio": 50000,
        "nombre": "Diego",
        "apellido": "Marado",
        "telefono": 5401110101010,
        "email": "d10s@hotmail.com"
        "comentario":"asd"
}
    """
    checkin = request.json['checkin']
    checkout = request.json['checkout']
    habitacion = request.json['habitacion']
    precio = request.json['precio']
    nombre = request.json['nombre']
    apellido = request.json['apellido']
    telefono = request.json['telefono']
    email = request.json['email']
    comentario = request.json['comentario']


    new_reserva = Reserva(checkin, checkout, habitacion, precio, nombre, apellido, telefono, email, comentario)
    db.session.add(new_reserva)
    db.session.commit()
    return reserva_schema.jsonify(new_reserva)


@app.route("/reservas/<id>", methods=['GET'])
def get_reserva(id):
    reserva = Reserva.query.get(id)
    if reserva == None:
        return dumps({'id':'error'})
    print('estado', reserva)
    return reserva_schema.jsonify(reserva)


@app.route('/reservas/<id>',methods=['DELETE'])
def delete_producto(id):
    # Consultar por id, a la clase Producto.
    #  Se hace una consulta (query) para obtener (get) un registro por id
    reserva=Reserva.query.get(id)
    
    # A partir de db y la sesión establecida con la base de datos borrar 
    # el producto.
    # Se guardan lo cambios con commit
    db.session.delete(reserva)
    db.session.commit()

    return reserva_schema.jsonify(reserva)
    

@app.route('/reservas/<id>',methods=['PUT'])
def update_reserva(id):
    # Consultar por id, a la clase Producto.
    #  Se hace una consulta (query) para obtener (get) un registro por id
    reserva=Reserva.query.get(id)

    #  Recibir los datos a modificar
    checkin=request.json['checkin']
    checkout=request.json['checkout']
    habitacion=request.json['habitacion']
    precio=request.json['precio']
    nombre=request.json['nombre']
    apellido=request.json['apellido']
    telefono=request.json['email']
    email=request.json['email']
    comentario=request.json['comentario']

    # Del objeto resultante de la consulta modificar los valores  
    reserva.checkin=checkin
    reserva.checkout=checkout
    reserva.habitacion=habitacion
    reserva.precio=precio
    reserva.nombre=nombre
    reserva.apellido=apellido
    reserva.telefono=telefono
    reserva.email=email
    reserva.comentario=comentario
#  Guardar los cambios
    db.session.commit()
# Para ello, usar el objeto reserva_schema para que convierta con
# jsonify el dato recién eliminado que son objetos a JSON  
    return reserva_schema.jsonify(reserva)



# BLOQUE PRINCIPAL 
if __name__=='__main__':
    app.run(debug=True)


