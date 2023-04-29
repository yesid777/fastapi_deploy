# Body: trabajar como cuerpo datos, Path: validar parametros tipo ruta, Query tipo query
# Request y HTTPException son para seguridad de rutas.
from fastapi import FastAPI, Body, Path, Query, Request, HTTPException, Depends

#fastapi.security (para seguridad en la pagina)
from fastapi.security import HTTPBearer
#Trabajar con HTML desde FastAPI - trabajar con JSON
from fastapi.responses import HTMLResponse, JSONResponse
#BaseModel permite trabajar con Objetos, Field: validaciones(rengos)
from pydantic import BaseModel, Field
#Pasar los datos optenidos de la DB a formato JSON
from fastapi.encoders import jsonable_encoder

from typing import Optional, List
#Importar archivo que genera el TOKEN
from jwt_config import dame_token, valida_token
# importamos del archivo base de datos, las funciones a usar
from config.base_de_datos import sesion, motor, base
# importamos del archivo ventas, las funciones a usar
from modelos.ventas import Ventas as VentasModelo


#uvicorn main:app (carga la aplicacion)
#uvicorn main:app --reload (Carga el app y cambios automaticamente)
#uvicorn main:app --reload --port xxxx (para cambiar el puerto de ejecucion del servidor)
#uvicorn main:app --reload --port xxxx --host 0.0.0.0 (para que cualquier equipo en la red pueda ver la aplicacion)
#pip install pyjwt (para usar tokens en FastAPI)
#pip install sqlalchemy (Manejador de bases de datos SQL)
#python pip install --update pip (actualizar PIP)


# crea instancia de FastApi
app = FastAPI()
app.title = "Aplicacion de Ventas"#titulo de la aplicacion
app.version = '1.0.1'
#crea la base de datos, en la ruta de la carpeta
base.metadata.create_all(bind=motor)

#DATOS


#Creamos el MODELO
class Usuario(BaseModel):
    correo: str
    clave: str

class Ventas(BaseModel):
    #id: Optional[int]=None
    #Validar que sea entero y que va de 0 a 20
    #id: int = Field(ge=0, le=20)
    id: Optional[int]=None
    fecha: str
    
    #Valida qu el nombre de la tienda tenga minimo 4 y max 10 caracteres
    tienda: str = Field(min_length=4, max_length=10)
    importe: float
    
    #Esqueema de ejemplo para mostrar al momento de crear una venta
    class Config:
        schema_extra ={
            "example":{
                "id":0,
                "fecha":"01/04/23",
                "tienda":"Tienda##",
                "importe": 123.45
            }
        }

#PORTADOR TOKEN
class Portador(HTTPBearer):
    
    async def __call__(self, request:Request):
        autorizacion = await super().__call__(request)
        dato = valida_token(autorizacion.credentials)
        if dato['correo'] != 'correo@gmail.com':
            raise HTTPException(status_code=403, detail='No Autorizado')
            

# Crear Punto de Entrada o EndPoint
@app.get('/',tags=['Inicio'])#cambio de etiqueta en Docuemntacion
def mensajes():
    return HTMLResponse('<h2>Titulo HTML desde Fast API</h2>')

#dependencies = [Depends(Portador) proteje la ruta
@app.get('/ventas',tags=['Ventas'],response_model = List[Ventas],status_code=200,dependencies=[Depends(Portador())])
def dame_ventas() -> List[Ventas]:
    db = sesion()
    resultado = db.query(VentasModelo).all()
    return JSONResponse(content=jsonable_encoder(resultado), status_code = 200)#devuelve datos en tipo JSON

#Usando Parametros tipo Ruta BUSCAR POR ID
@app.get('/ventas/{id}',tags=['Ventas'], response_model = Ventas, status_code = 200)
#Validamos que el parametro sea mayor a uno o igual a 1000 (Path)
def dame_ventas(id:int = Path(ge=1,le=1000)) -> Ventas:
    db = sesion()
    # buscara en la base los datos fitrando pot el id y trael el primer resultado
    resultado = db.query(VentasModelo).filter(VentasModelo.id == id).first()
    if not resultado:
        return JSONResponse(content={'mensaje':'No se encontro el identificador'}, status_code = 404)
    
    return JSONResponse(content=jsonable_encoder(resultado), status_code = 200)

#Usando Parametros tipo Query BUSCRA POR NOMBRE DE TIENDA
@app.get('/ventas/',tags=['Ventas'], response_model = List[Ventas])
#Validamos que el parametro sea de 4 a 20 caracteres (Query)
def dame_ventas_por_tienda(tienda:str = Query(min_length=4,max_length=20))-> Ventas:
    
    db = sesion()
    # buscara en la base los datos fitrando pot el id y trael el primer resultado
    resultado = db.query(VentasModelo).filter(VentasModelo.tienda == tienda).first()
    if not resultado:
        return JSONResponse(content={'mensaje':'No se encontro el la Tienda'}, status_code = 404)
    
    return JSONResponse(content=jsonable_encoder(resultado), status_code = 201)
    
    
# Post para enviar informacion al API CREAR VENTA
@app.post('/ventas',tags=['Ventas'], response_model = dict, status_code = 201)
def crea_venta(venta:Ventas) -> dict:
    # Iniciar sesion en la DB
    Session = sesion()
    db = Session

    # Extraemos atributos para paso como parametros
    nueva_venta = VentasModelo(**venta.dict())
    #añadir a la DB y hacemos commit para actualizar datos
    db.add(nueva_venta)
    db.commit()
    
    return JSONResponse(content={'mensaje':'Venta registrada con Exito'}, status_code = 200)

#PUT Actualizar Datos
@app.put('/ventas/{id}',tags=['Ventas'], response_model = dict, status_code = 200)
def actualizar_venta(id:int, venta:Ventas) -> dict:
    db=sesion()
    resultado = db.query(VentasModelo).filter(VentasModelo.id == id).first()
    if not resultado:
        return JSONResponse(content={'mensaje':'No se encontro el identificador'}, status_code = 404)
    
    resultado.fecha = venta.fecha
    resultado.tienda = venta.tienda
    resultado.importe = venta.importe
    db.commit() #ejecuta la consulta en la BD 
    
    return JSONResponse(content={'mensaje':'Venta Actualizada con Exito'}, status_code = 200)

# Delete eliminar elementos
@app.delete('/ventas/{id}',tags=['Ventas'], response_model = dict, status_code = 200)
def borra_ventas(id:int) -> dict:
    db = sesion()
    resultado = db.query(VentasModelo).filter(VentasModelo.id == id).first()
    if not resultado:
        return JSONResponse(content={'mensaje':'No se encuentra el id a Borrar, Validar'}, status_code = 404)
    db.delete(resultado)
    db.commit()
    return JSONResponse(content={'mensaje':'Venta Eliminada con Exito'}, status_code = 200)

#Creamos la rutra para Login
@app.post('/login',tags=['autenticacion'])
def login(usuario:Usuario):
    if usuario.correo == 'correo@gmail.com' and usuario.clave == '1234':
        # Obtenemos el token de la funcion dandole el diccionario de usuario
        token:str=dame_token(usuario.dict())
        return JSONResponse(content=token, status_code=200)
    else:
        return JSONResponse(content={'mensaje':'Validar usuario o Clave'}, status_code=404)
    