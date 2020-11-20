from trapy import *

conn = listen('10.0.0.2:8080')
conn_acc = accept(conn)