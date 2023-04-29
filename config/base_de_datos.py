import os
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base #manipula tabla de base

fichero = "../datos.sqlite"

#Leemos el directorio actual del archivo de la BD
directorio = os.path.dirname(os.path.realpath(__file__))

# dirreccion de la BD uniendo la s2 variables anteriores
ruta = f"sqlite:///{os.path.join(directorio,fichero)}"

# Creamos el motor
motor = create_engine(ruta, echo=True)

# Creamos la Sesion pasandole el motor
sesion = sessionmaker(bind=motor)

# Creamos una base para manejar las tablas de la BD
base = declarative_base()
