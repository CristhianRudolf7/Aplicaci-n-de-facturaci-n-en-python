import sys
from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt
import datetime
from PyQt5.uic import loadUi
import sqlite3

#Es una subclase de QDialog, es una clase personalizada de dialogo para crear un interfaz grafica
class MainDialog(QDialog):
    def __init__(self):
        #Constructor, con self se puede acceder a atributos y metodos
        super(MainDialog, self).__init__()
        #Carga la interfaz "ui" y la asocia con la instancia de MainDialog (que es self).
        loadUi("pantalla principal.ui", self)

        # Conexión a la base de datos SQLite
        self.connection = sqlite3.connect("productos.db")
        self.cursor = self.connection.cursor()

        # Crear la tabla "productos" si no existe
        self.create_table()

        # Crear la tabla "categorias" si no existe
        self.create_categorias_table()

        # Insertar categorías iniciales si no existen
        self.insertar_categorias_iniciales()
        self.categorias = self.obtener_categorias()

        # Cargar datos de productos desde la base de datos
        self.actualizar_producto()
        
        # Conexiones de botones
        self.agregarproducto.clicked.connect(self.agregar_producto)
        self.agregarcategoria.clicked.connect(self.agregar_categoria)
        self.actualizarproducto.clicked.connect(self.actualizar_producto)
        self.eliminarproducto.clicked.connect(self.eliminar_producto)
        self.eliminarcategoria.clicked.connect(self.eliminar_categoria)

        self.connection_clientes = sqlite3.connect("clientes.db")
        self.cursor_clientes = self.connection_clientes.cursor()
        self.create_clientes_table()
        self.actualizar_clientes()
        self.agregarcliente.clicked.connect(self.agregar_cliente)
        self.eliminarcliente.clicked.connect(self.eliminar_cliente)
        self.actualizarcliente.clicked.connect(self.actualizar_clientes)

        self.categoriaproducto.addItems(self.categorias)
        self.categoriaproducto.currentIndexChanged.connect(self.actualizar_productos_por_categoria)
        self.agregar.clicked.connect(self.agregar_a_lista_venta)
        self.eliminar.clicked.connect(self.eliminar_fila_listaventa)
        
        self.actualizar_costo_total()

        self.connection_ventas = sqlite3.connect("ventas.db")
        self.cursor_ventas = self.connection_ventas.cursor()
        self.create_ventas_table()

        self.generarventa.clicked.connect(self.guardar_venta)
        self.eliminarventa.clicked.connect(self.eliminar_venta_seleccionada)
        self.actualizarventa.clicked.connect(self.actualizar_ventas)
        
        self.modificarcantidad.clicked.connect(self.modificar_cantidad_producto)

    def modificar_cantidad_producto(self):
        selected_rows = self.tablaproducto.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            nombre_producto = self.tablaproducto.item(row, 0).text()
            cantidad_actual = int(self.tablaproducto.item(row, 1).text())

            cantidad_nueva, ok = QInputDialog.getInt(self, "Modificar Cantidad", f"Ingrese la nueva cantidad para {nombre_producto}:", value=cantidad_actual)
            if ok:
                self.cursor.execute("UPDATE productos SET cantidad=? WHERE nombre=?", (cantidad_nueva, nombre_producto))
                self.connection.commit()
                self.actualizar_producto()
                QMessageBox.information(self, "Cantidad Actualizada", f"La cantidad de {nombre_producto} se ha actualizado correctamente a {cantidad_nueva}.")
        else:
            QMessageBox.warning(self, "Selecciona un Producto", "Por favor, selecciona un producto de la tabla para modificar su cantidad.")

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                               nombre TEXT,
                               cantidad INTEGER,
                               precio REAL,
                               categoria TEXT)''')
        self.connection.commit()

    def create_categorias_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
                               nombre TEXT PRIMARY KEY)''')
        self.connection.commit()

    def insertar_categorias_iniciales(self):
        categorias_iniciales = ["vidrio", "aluminio", "accesorio"]
        for categoria in categorias_iniciales:
            self.cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (categoria,))
        self.connection.commit()

    def agregar_producto(self):
        nombre, ok = QInputDialog.getText(self, "Agregar Producto", "Ingrese el nombre del producto:")
        if ok and nombre:
            cantidad, ok1 = QInputDialog.getInt(self, "Agregar Producto", "Ingrese la cantidad:")
            if ok1:
                precio, ok2 = QInputDialog.getDouble(self, "Agregar Producto", "Ingrese el precio unitario:")
                if ok2:
                    categorias = self.obtener_categorias()
                    categoria, ok3 = QInputDialog.getItem(self, "Agregar Producto", "Seleccione la categoría:", categorias)
                    if ok3 and categoria:
                        self.cursor.execute("INSERT INTO productos (nombre, cantidad, precio, categoria) VALUES (?, ?, ?, ?)",
                                            (nombre, cantidad, precio, categoria))
                        self.connection.commit()
                        self.actualizar_producto()

    def agregar_categoria(self):
        categoria, ok = QInputDialog.getText(self, "Agregar Categoría", "Ingrese el nombre de la categoría:")
        if ok and categoria:
            self.cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (categoria,))
            self.connection.commit()
            self.categoriaproducto.addItem(categoria)

    def obtener_categorias(self):
        self.cursor.execute("SELECT nombre FROM categorias")
        categorias = self.cursor.fetchall()
        categorias = [categoria[0] for categoria in categorias]
        return categorias
    
    def eliminar_categoria(self):
        categorias = self.obtener_categorias()
        categoria, ok = QInputDialog.getItem(self, "Eliminar Categoría", "Seleccione la categoría a eliminar:", categorias, editable=False)
        if ok and categoria:
            self.cursor.execute("DELETE FROM categorias WHERE nombre=?", (categoria,))
            self.connection.commit()
            self.actualizar_producto()
            self.cargar_categorias_venta()

    def actualizar_producto(self):
        self.tablaproducto.setRowCount(0)
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()
        for row, producto in enumerate(productos):
            self.tablaproducto.insertRow(row)
            for col, data in enumerate(producto):
                self.tablaproducto.setItem(row, col, QTableWidgetItem(str(data)))

    def eliminar_producto(self):
        selected_rows = self.tablaproducto.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            nombre = self.tablaproducto.item(row, 0).text()
            self.cursor.execute("DELETE FROM productos WHERE nombre=?", (nombre,))
            self.connection.commit()
            self.actualizar_producto()

    def create_clientes_table(self):
        self.cursor_clientes.execute('''CREATE TABLE IF NOT EXISTS clientes (
                                       apellido TEXT,
                                       nombre TEXT,
                                       dni TEXT PRIMARY KEY,
                                       compras INTEGER)''')
        self.connection_clientes.commit()

    def actualizar_clientes(self):
        self.tablacliente.setRowCount(0)
        self.cursor_clientes.execute("SELECT * FROM clientes")
        clientes = self.cursor_clientes.fetchall()
        for row, cliente in enumerate(clientes):
            self.tablacliente.insertRow(row)
            for col, data in enumerate(cliente):
                self.tablacliente.setItem(row, col, QTableWidgetItem(str(data)))

    def agregar_cliente(self):
        apellido, ok = QInputDialog.getText(self, "Agregar Cliente", "Ingrese el apellido:")
        if ok and apellido:
            nombre, ok1 = QInputDialog.getText(self, "Agregar Cliente", "Ingrese el nombre:")
            if ok1 and nombre:
                while True:  # Bucle para solicitar el DNI hasta que sea válido
                    dni, ok2 = QInputDialog.getText(self, "Agregar Cliente", "Ingrese el DNI (8 dígitos):")
                    if ok2 and dni and dni.isdigit() and len(dni) == 8:
                    # Verificar que el DNI sea un número de 8 dígitos
                        break
                    else:
                        QMessageBox.warning(self, "DNI Inválido", "El DNI ingresado es inválido. Debe tener 8 dígitos numéricos.")
                self.cursor_clientes.execute("INSERT INTO clientes (apellido, nombre, dni, compras) VALUES (?, ?, ?, ?)",
                                        (apellido, nombre, dni, 0))
                self.connection_clientes.commit()
                self.actualizar_clientes()

    def eliminar_cliente(self):
        selected_rows = self.tablacliente.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            dni = self.tablacliente.item(row, 2).text()

        # Eliminar al cliente de la tabla de clientes
            self.cursor_clientes.execute("DELETE FROM clientes WHERE dni=?", (dni,))
            self.connection_clientes.commit()

        # Eliminar las compras del cliente de la tabla de ventas
            self.cursor_ventas.execute("DELETE FROM ventas WHERE cliente=?", (dni,))
            self.connection_ventas.commit()

            self.actualizar_clientes()

    def actualizar_productos_por_categoria(self):
        categoria = self.categoriaproducto.currentText()
        self.cursor.execute("SELECT nombre FROM productos WHERE categoria=?", (categoria,))
        productos = self.cursor.fetchall()
        productos = [producto[0] for producto in productos]
        self.nombreproducto.clear()
        self.nombreproducto.addItems(productos)
        self.cargar_apellidos_clientes()

    def agregar_a_lista_venta(self):
        categoria = self.categoriaproducto.currentText()
        producto = self.nombreproducto.currentText()
        cliente = self.cliente.currentText()
        cantidad = self.cantidad.value()

        self.cursor.execute("SELECT precio FROM productos WHERE nombre=?", (producto,))
        precio_unitario = self.cursor.fetchone()[0]
        subtotal = precio_unitario * cantidad

        row_position = self.listaventa.rowCount()
        self.listaventa.insertRow(row_position)
        self.listaventa.setItem(row_position, 0, QTableWidgetItem(producto))
        self.listaventa.setItem(row_position, 1, QTableWidgetItem(str(cantidad)))
        self.listaventa.setItem(row_position, 2, QTableWidgetItem(cliente))
        self.listaventa.setItem(row_position, 3, QTableWidgetItem(str(subtotal)))

        self.actualizar_costo_total()

    def eliminar_fila_listaventa(self):
        selected_rows = self.listaventa.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            self.listaventa.removeRow(row)
            self.actualizar_costo_total()

    def actualizar_costo_total(self):
        total = 0
        for row in range(self.listaventa.rowCount()):
            subtotal = float(self.listaventa.item(row, 3).text())
            total += subtotal
        self.etiqueta_costo_total.setText(f"Costo Total: ${total:.2f}")
   
    def cargar_categorias_venta(self):
        self.categoriaproducto.clear()
        self.categoriaproducto.addItems(self.categorias)

    def cargar_apellidos_clientes(self):
        self.cursor_clientes.execute("SELECT apellido FROM clientes")
        apellidos = self.cursor_clientes.fetchall()
        apellidos = [apellido[0] for apellido in apellidos]
        self.cliente.clear()
        self.cliente.addItems(apellidos)

    def create_ventas_table(self):
        self.cursor_ventas.execute('''CREATE TABLE IF NOT EXISTS ventas (
                               cliente TEXT,
                               num_productos INTEGER,  -- Agrega la columna num_productos
                               fecha TEXT,
                               costo_total REAL,
                               productos TEXT)''')  # No olvides modificar la definición de la tabla aquí
        self.connection_ventas.commit()

    def guardar_venta(self):
        cliente = self.cliente.currentText()
        num_productos = self.listaventa.rowCount()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        costo_total = float(self.etiqueta_costo_total.text().split("$")[1])
        productos = []

        valid = True  # Variable para comprobar si todos los productos tienen suficiente cantidad

        for row in range(self.listaventa.rowCount()):
            producto = self.listaventa.item(row, 0).text()
            cantidad = int(self.listaventa.item(row, 1).text())
            self.cursor.execute("SELECT cantidad FROM productos WHERE nombre=?", (producto,))
            existing_quantity = self.cursor.fetchone()[0]
        
            if cantidad <= existing_quantity:
                productos.append(f"{producto} (Cantidad: {cantidad})")
                new_quantity = existing_quantity - cantidad
                self.cursor.execute("UPDATE productos SET cantidad=? WHERE nombre=?", (new_quantity, producto))
                self.connection.commit()
            else:
                valid = False
                QMessageBox.warning(self, "Cantidad no disponible", f"La cantidad de {producto} seleccionada ({cantidad}) es mayor que la cantidad disponible ({existing_quantity}).")

        if valid:
            productos_str = ", ".join(productos)

            self.cursor_ventas.execute("INSERT INTO ventas (cliente, num_productos, fecha, costo_total, productos) VALUES (?, ?, ?, ?, ?)",
                           (cliente, num_productos, fecha, costo_total, productos_str))
            self.connection_ventas.commit()

            self.cursor_clientes.execute("UPDATE clientes SET compras = compras + 1 WHERE apellido = ?", (cliente,))
            self.connection_clientes.commit()

            self.actualizar_ventas()
            self.limpiar_venta()

            QMessageBox.information(self, "Venta guardada", "La venta se ha guardado satisfactoriamente.")


    def actualizar_ventas(self):
        self.tablaventa.setRowCount(0)
        self.cursor_ventas.execute("SELECT * FROM ventas")
        ventas = self.cursor_ventas.fetchall()
        for row, venta in enumerate(ventas):
            self.tablaventa.insertRow(row)
            for col, data in enumerate(venta):
                self.tablaventa.setItem(row, col, QTableWidgetItem(str(data)))

    def limpiar_venta(self):
        self.cliente.setCurrentIndex(0)
        self.categoriaproducto.setCurrentIndex(0)
        self.nombreproducto.clear()
        self.cantidad.setValue(1)
        self.listaventa.setRowCount(0)
        self.etiqueta_costo_total.setText("Costo Total: $0.00")
    
    def eliminar_venta_seleccionada(self):
        selected_rows = self.tablaventa.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            cliente = self.tablaventa.item(row, 0).text()
            fecha = self.tablaventa.item(row, 2).text()

        # Eliminar la venta de la base de datos
            self.cursor_ventas.execute("DELETE FROM ventas WHERE cliente=? AND fecha=?", (cliente, fecha))
            self.connection_ventas.commit()

        # Disminuir el número de compras del cliente en la base de datos
            self.cursor_clientes.execute("UPDATE clientes SET compras = compras - 1 WHERE apellido = ?", (cliente,))
            self.connection_clientes.commit()

        # Eliminar la fila de la tabla
            self.tablaventa.removeRow(row)
    
app = QApplication(sys.argv)
window = MainDialog()
window.show()
sys.exit(app.exec_())
