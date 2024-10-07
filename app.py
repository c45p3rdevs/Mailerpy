from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import smtplib
from email.mime.text import MIMEText
import re



app = Flask(__name__)
app.secret_key = "supersecretkey"

# Conexión a la base de datos MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sis_report"
)
cursor = conn.cursor()

# Función para validar correos electrónicos
def validar_correos(correos):
    patron_correo = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    correos_invalidos = [correo for correo in correos if not re.match(patron_correo, correo.strip())]
    return correos_invalidos

# Función para enviar correos electrónicos
def enviar_correo(asunto, mensaje, destinatarios):
    try:
        remitente = "oscar.imrandaolmos@gmail.com"
        password = "kmzz hyxw ydzn yhtx"

        
        msg = MIMEText(mensaje,  'html')
        msg['Subject'] = asunto
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remitente, password)
            server.sendmail(remitente, destinatarios, msg.as_string())
            msg = MIMEText(mensaje, 'html')
           
            
        
        flash(f"Correo enviado exitosamente a: {', '.join(destinatarios)}.", "success")
        return True
    except Exception as e:
        flash(f"Error al enviar correo: {e}", "error")
        return False

# Ruta para la página principal
@app.route('/')
def index():
    cursor.execute('SELECT * FROM reportes')
    reportes = cursor.fetchall()
    return render_template('index.html', reportes=reportes)

# Ruta para agregar un nuevo reporte
@app.route('/agregar_reporte', methods=['POST'])
def agregar_reporte():
    titulo = request.form['titulo']
    correos = request.form['correos']

    correos_lista = correos.split(',')
    correos_invalidos = validar_correos(correos_lista)
    
    if correos_invalidos:
        flash(f"Los siguientes correos son inválidos: {', '.join(correos_invalidos)}.", "error")
        return redirect(url_for('index'))

    # Insertar reporte en la tabla 'reportes' con la lista de correos
    cursor.execute('INSERT INTO reportes (titulo, estatus, correos) VALUES (%s, %s, %s)', (titulo, 'Pendiente', correos))
    conn.commit()
   
    mensaje = f"Gracias por enviar su reporte <strong>{titulo}</strong>. Le confirmamos que hemos recibido su solicitud y será atendida a la brevedad posible. Nuestro equipo ya está trabajando para resolver el asunto y le mantendremos informado(a) sobre cualquier actualización importante.<br> <br> Atentamente <br> Oscar Miranda Olmos<br> Direccion General del Sistema Penitenciario <br> <br> <img src='https://seguridad.guanajuato.gob.mx/wp-content/uploads/2021/05/logo-dgsp.jpg' "
    enviar_correo("Nuevo Reporte Generado", mensaje, correos_lista)

    flash("Reporte agregado y correos enviados.", "success")
    return redirect(url_for('index'))

# Ruta para cambiar el estatus del reporte
@app.route('/cambiar_estatus', methods=['POST'])
def cambiar_estatus():
    reporte_id = request.form['id']
    titulo = request.form.get('titulo')
    
    
    # Obtener el estatus actual y los correos desde la tabla 'reportes'
    cursor.execute('SELECT titulo, estatus, correos FROM reportes WHERE id=%s', (reporte_id,))
    titulo, estatus_actual, correos = cursor.fetchone()
    
    if correos is None:
        correos = ""

    # Cambiar el estatus
    nuevo_estatus = "Atendido" if estatus_actual == "Pendiente" else "Finalizado"
    cursor.execute('UPDATE reportes SET estatus=%s WHERE id=%s', (nuevo_estatus, reporte_id))
    conn.commit()

    if correos:
        mensaje = f"El estatus de su reporte generado <strong>{titulo}</strong>, con el ID <strong>{reporte_id}</strong> ha cambiado a <strong>{nuevo_estatus}</strong> Si tiene alguna otra consulta o necesita más información, no dude en ponerse en contacto con nosotros respondiendo a este correo.<br> Atentamente <br> Oscar Miranda Olmos<br> Direccion General del Sistema Penitenciario <br> <br> <img src='https://seguridad.guanajuato.gob.mx/wp-content/uploads/2021/05/logo-dgsp.jpg'"
        correos_lista = correos.split(",")
        enviar_correo("Cambio el Estatus de su Reporte", mensaje, correos_lista)

    flash(f"Estatus del reporte <strong>{titulo}</strong> actualizado a <strong>{nuevo_estatus}</strong>.", "success")
    return redirect(url_for('index'))

# Ruta para eliminar un reporte
@app.route('/eliminar_reporte/<int:reporte_id>', methods=['POST'])
def eliminar_reporte(reporte_id):
    cursor.execute('DELETE FROM reportes WHERE id = %s', (reporte_id,))
    conn.commit()
    
    flash("Reporte eliminado exitosamente.", "success")
    return redirect(url_for('index'))

# Ruta para editar un reporte (obtener datos)
@app.route('/editar_reporte/<int:reporte_id>', methods=['GET'])
def editar_reporte(reporte_id):
    cursor.execute('SELECT * FROM reportes WHERE id=%s', (reporte_id,))
    reporte = cursor.fetchone()
    return render_template('editar_reporte.html', reporte=reporte)

# Ruta para guardar los cambios en un reporte
@app.route('/guardar_reporte', methods=['POST'])
def guardar_reporte():
    reporte_id = request.form['id']
    titulo = request.form['titulo']
    correos = request.form['correos']
    
    correos_lista = correos.split(',')
    correos_invalidos = validar_correos(correos_lista)

    if correos_invalidos:
        flash(f"Correos inválidos: {', '.join(correos_invalidos)}.", "error")
        return redirect(url_for('editar_reporte', reporte_id=reporte_id))
    
    cursor.execute('UPDATE reportes SET titulo=%s, correos=%s WHERE id=%s', (titulo, correos, reporte_id))
    conn.commit()

    flash("Reporte actualizado exitosamente.", "success")
    return redirect(url_for('index'))

# Iniciar el servidor
if __name__ == '__main__':
    app.run(debug=True)