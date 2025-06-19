import sqlite3
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

class MaterialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет материалов - Производственная компания 'Мозаика'")
        self.root.geometry("800x600")
        
        # Подключение к базе данных
        self.conn = sqlite3.connect('materials.db')
        self.cursor = self.conn.cursor()
        
        # Создание таблиц, если их нет
        self.create_tables()
        
        # Заполнение тестовыми данными
        self.insert_test_data()
        
        # Стиль
        self.setup_style()
        
        # Создание интерфейса
        self.create_ui()
        
    def setup_style(self):
        self.root.configure(bg='#FFFFFF')
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#ABCECE')
        self.style.configure('TButton', background='#546F94', foreground='white')
        self.style.configure('TLabel', background='#FFFFFF', font=('Comic Sans MS', 10))
        
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rating REAL,
                start_date DATE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS material_types (
                type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                material_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type_id INTEGER,
                quantity_in_stock REAL NOT NULL,
                unit TEXT NOT NULL,
                package_quantity REAL NOT NULL,
                min_quantity REAL NOT NULL,
                price_per_unit REAL NOT NULL,
                supplier_id INTEGER,
                FOREIGN KEY (type_id) REFERENCES material_types(type_id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
            )
        ''')
        self.conn.commit()
    
    def insert_test_data(self):
        # Проверяем, есть ли уже данные
        self.cursor.execute("SELECT COUNT(*) FROM material_types")
        if self.cursor.fetchone()[0] == 0:
            # Добавляем тестовые данные
            self.cursor.executemany(
                "INSERT INTO material_types (name) VALUES (?)",
                [('Глина',), ('Пигменты',), ('Глазурь',)]
            )
            
            self.cursor.executemany(
                "INSERT INTO suppliers (name, rating, start_date) VALUES (?, ?, ?)",
                [
                    ('ООО "Глина и К"', 4.5, '2020-01-15'),
                    ('ИП Смирнов', 3.8, '2021-03-22'),
                    ('АО "Химические материалы"', 4.2, '2019-11-05')
                ]
            )
            
            self.cursor.executemany(
                '''INSERT INTO materials 
                (name, type_id, quantity_in_stock, unit, package_quantity, min_quantity, price_per_unit, supplier_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                [
                    ('Глина белая', 1, 1500, 'кг', 25, 1000, 50.0, 1),
                    ('Оксид железа', 2, 800, 'кг', 10, 500, 120.0, 3),
                    ('Глазурь прозрачная', 3, 200, 'л', 5, 100, 200.0, 2)
                ]
            )
            self.conn.commit()
    
    def create_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Список материалов", font=('Comic Sans MS', 14, 'bold'))
        title_label.pack(pady=10)
        
        # Фрейм для списка материалов
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=BOTH, expand=True)
        
        # Дерево для отображения материалов
        self.tree = ttk.Treeview(list_frame, columns=('type', 'name', 'quantity', 'min', 'price', 'unit', 'batch_cost'), show='headings')
        
        self.tree.heading('type', text='Тип')
        self.tree.heading('name', text='Наименование')
        self.tree.heading('quantity', text='Кол-во на складе')
        self.tree.heading('min', text='Мин. кол-во')
        self.tree.heading('price', text='Цена')
        self.tree.heading('unit', text='Ед. изм.')
        self.tree.heading('batch_cost', text='Стоимость партии')
        
        self.tree.column('type', width=100)
        self.tree.column('name', width=150)
        self.tree.column('quantity', width=100)
        self.tree.column('min', width=100)
        self.tree.column('price', width=80)
        self.tree.column('unit', width=80)
        self.tree.column('batch_cost', width=120)
        
        self.tree.pack(fill=BOTH, expand=True)
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        add_button = ttk.Button(button_frame, text="Добавить", command=self.open_add_material_window)
        add_button.pack(side=LEFT, padx=5)
        
        edit_button = ttk.Button(button_frame, text="Редактировать", command=self.open_edit_material_window)
        edit_button.pack(side=LEFT, padx=5)
        
        suppliers_button = ttk.Button(button_frame, text="Поставщики", command=self.show_suppliers)
        suppliers_button.pack(side=LEFT, padx=5)
        
        # Загрузка данных
        self.load_materials()
    
    def load_materials(self):
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем данные из БД
        self.cursor.execute('''
            SELECT m.name, mt.name, m.quantity_in_stock, m.min_quantity, 
                   m.price_per_unit, m.unit, m.package_quantity
            FROM materials m
            JOIN material_types mt ON m.type_id = mt.type_id
        ''')
        
        materials = self.cursor.fetchall()
        
        # Добавляем данные в дерево
        for material in materials:
            name, type_name, quantity, min_quantity, price, unit, package_quantity = material
            
            # Рассчитываем стоимость минимальной партии
            if quantity < min_quantity:
                needed = min_quantity - quantity
                # Округляем до ближайшего кратного package_quantity в большую сторону
                packages = int((needed + package_quantity - 1) // package_quantity)
                batch_quantity = packages * package_quantity
                batch_cost = batch_quantity * price
            else:
                batch_cost = 0.0
            
            self.tree.insert('', 'end', values=(
                type_name, name, f"{quantity} {unit}", 
                f"{min_quantity} {unit}", f"{price:.2f} р", unit, 
                f"{batch_cost:.2f} р" if batch_cost > 0 else "0.00 р"
            ))
    
    def open_add_material_window(self):
        self.add_edit_window = Toplevel(self.root)
        self.add_edit_window.title("Добавить материал")
        self.add_edit_window.geometry("400x500")
        
        self.create_material_form(self.add_edit_window, is_edit=False)
    
    def open_edit_material_window(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите материал для редактирования")
            return
        
        item = self.tree.item(selected_item[0])
        material_name = item['values'][1]
        
        # Получаем полные данные о материале из БД
        self.cursor.execute('''
            SELECT m.material_id, m.name, m.type_id, m.quantity_in_stock, m.unit, 
                   m.package_quantity, m.min_quantity, m.price_per_unit, m.supplier_id
            FROM materials m
            WHERE m.name = ?
        ''', (material_name,))
        
        material_data = self.cursor.fetchone()
        
        if not material_data:
            messagebox.showerror("Ошибка", "Материал не найден в базе данных")
            return
        
        self.add_edit_window = Toplevel(self.root)
        self.add_edit_window.title("Редактировать материал")
        self.add_edit_window.geometry("400x500")
        
        self.create_material_form(self.add_edit_window, is_edit=True, material_data=material_data)
    
    def create_material_form(self, window, is_edit, material_data=None):
        frame = ttk.Frame(window, padding="10")
        frame.pack(fill=BOTH, expand=True)
        
        # Наименование
        ttk.Label(frame, text="Наименование:").grid(row=0, column=0, sticky=W, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=0, column=1, sticky=EW, pady=5)
        
        # Тип материала (выпадающий список)
        ttk.Label(frame, text="Тип материала:").grid(row=1, column=0, sticky=W, pady=5)
        
        self.cursor.execute("SELECT type_id, name FROM material_types")
        types = self.cursor.fetchall()
        type_names = [t[1] for t in types]
        type_ids = [t[0] for t in types]
        
        type_var = StringVar()
        type_combobox = ttk.Combobox(frame, textvariable=type_var, values=type_names)
        type_combobox.grid(row=1, column=1, sticky=EW, pady=5)
        
        # Количество на складе
        ttk.Label(frame, text="Количество на складе:").grid(row=2, column=0, sticky=W, pady=5)
        quantity_entry = ttk.Entry(frame)
        quantity_entry.grid(row=2, column=1, sticky=EW, pady=5)
        
        # Единица измерения
        ttk.Label(frame, text="Единица измерения:").grid(row=3, column=0, sticky=W, pady=5)
        unit_entry = ttk.Entry(frame)
        unit_entry.grid(row=3, column=1, sticky=EW, pady=5)
        
        # Количество в упаковке
        ttk.Label(frame, text="Количество в упаковке:").grid(row=4, column=0, sticky=W, pady=5)
        package_entry = ttk.Entry(frame)
        package_entry.grid(row=4, column=1, sticky=EW, pady=5)
        
        # Минимальное количество
        ttk.Label(frame, text="Минимальное количество:").grid(row=5, column=0, sticky=W, pady=5)
        min_entry = ttk.Entry(frame)
        min_entry.grid(row=5, column=1, sticky=EW, pady=5)
        
        # Цена единицы
        ttk.Label(frame, text="Цена за единицу:").grid(row=6, column=0, sticky=W, pady=5)
        price_entry = ttk.Entry(frame)
        price_entry.grid(row=6, column=1, sticky=EW, pady=5)
        
        # Поставщик (выпадающий список)
        ttk.Label(frame, text="Поставщик:").grid(row=7, column=0, sticky=W, pady=5)
        
        self.cursor.execute("SELECT supplier_id, name FROM suppliers")
        suppliers = self.cursor.fetchall()
        supplier_names = [s[1] for s in suppliers]
        supplier_ids = [s[0] for s in suppliers]
        
        supplier_var = StringVar()
        supplier_combobox = ttk.Combobox(frame, textvariable=supplier_var, values=supplier_names)
        supplier_combobox.grid(row=7, column=1, sticky=EW, pady=5)
        
        # Если редактирование, заполняем поля
        if is_edit and material_data:
            material_id, name, type_id, quantity, unit, package_quantity, min_quantity, price_per_unit, supplier_id = material_data
            
            name_entry.insert(0, name)
            quantity_entry.insert(0, str(quantity))
            unit_entry.insert(0, unit)
            package_entry.insert(0, str(package_quantity))
            min_entry.insert(0, str(min_quantity))
            price_entry.insert(0, str(price_per_unit))
            
            # Устанавливаем тип материала
            self.cursor.execute("SELECT name FROM material_types WHERE type_id = ?", (type_id,))
            type_name = self.cursor.fetchone()[0]
            type_var.set(type_name)
            
            # Устанавливаем поставщика
            if supplier_id:
                self.cursor.execute("SELECT name FROM suppliers WHERE supplier_id = ?", (supplier_id,))
                supplier_name = self.cursor.fetchone()[0]
                supplier_var.set(supplier_name)
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)
        
        if is_edit:
            save_button = ttk.Button(button_frame, text="Сохранить", command=lambda: self.save_material(
                material_id, name_entry, type_var, type_ids, type_names, 
                quantity_entry, unit_entry, package_entry, min_entry, 
                price_entry, supplier_var, supplier_ids, supplier_names, window
            ))
        else:
            save_button = ttk.Button(button_frame, text="Добавить", command=lambda: self.save_material(
                None, name_entry, type_var, type_ids, type_names, 
                quantity_entry, unit_entry, package_entry, min_entry, 
                price_entry, supplier_var, supplier_ids, supplier_names, window
            ))
        
        save_button.pack(side=LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Отмена", command=window.destroy)
        cancel_button.pack(side=LEFT, padx=5)
    
    def save_material(self, material_id, name_entry, type_var, type_ids, type_names, 
                     quantity_entry, unit_entry, package_entry, min_entry, 
                     price_entry, supplier_var, supplier_ids, supplier_names, window):
        # Валидация данных
        try:
            name = name_entry.get().strip()
            if not name:
                raise ValueError("Введите наименование материала")
            
            type_name = type_var.get()
            if type_name not in type_names:
                raise ValueError("Выберите тип материала из списка")
            type_id = type_ids[type_names.index(type_name)]
            
            quantity = float(quantity_entry.get())
            if quantity < 0:
                raise ValueError("Количество не может быть отрицательным")
            
            unit = unit_entry.get().strip()
            if not unit:
                raise ValueError("Введите единицу измерения")
            
            package_quantity = float(package_entry.get())
            if package_quantity <= 0:
                raise ValueError("Количество в упаковке должно быть положительным")
            
            min_quantity = float(min_entry.get())
            if min_quantity < 0:
                raise ValueError("Минимальное количество не может быть отрицательным")
            
            price = float(price_entry.get())
            if price < 0:
                raise ValueError("Цена не может быть отрицательной")
            
            supplier_name = supplier_var.get()
            supplier_id = None
            if supplier_name in supplier_names:
                supplier_id = supplier_ids[supplier_names.index(supplier_name)]
            
            # Сохранение в БД
            if material_id:  # Редактирование
                self.cursor.execute('''
                    UPDATE materials 
                    SET name = ?, type_id = ?, quantity_in_stock = ?, unit = ?, 
                        package_quantity = ?, min_quantity = ?, price_per_unit = ?, supplier_id = ?
                    WHERE material_id = ?
                ''', (name, type_id, quantity, unit, package_quantity, min_quantity, price, supplier_id, material_id))
            else:  # Добавление
                self.cursor.execute('''
                    INSERT INTO materials 
                    (name, type_id, quantity_in_stock, unit, package_quantity, min_quantity, price_per_unit, supplier_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, type_id, quantity, unit, package_quantity, min_quantity, price, supplier_id))
            
            self.conn.commit()
            messagebox.showinfo("Успех", "Материал успешно сохранен")
            window.destroy()
            self.load_materials()
        
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при сохранении: {str(e)}")
    
    def show_suppliers(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите материал для просмотра поставщиков")
            return
        
        item = self.tree.item(selected_item[0])
        material_name = item['values'][1]
        
        # Получаем поставщиков для выбранного материала
        self.cursor.execute('''
            SELECT s.name, s.rating, s.start_date
            FROM suppliers s
            JOIN materials m ON s.supplier_id = m.supplier_id
            WHERE m.name = ?
        ''', (material_name,))
        
        suppliers = self.cursor.fetchall()
        
        if not suppliers:
            messagebox.showinfo("Информация", "Для этого материала нет информации о поставщиках")
            return
        
        # Создаем окно для отображения поставщиков
        suppliers_window = Toplevel(self.root)
        suppliers_window.title(f"Поставщики материала {material_name}")
        suppliers_window.geometry("600x400")
        
        frame = ttk.Frame(suppliers_window, padding="10")
        frame.pack(fill=BOTH, expand=True)
        
        # Заголовок
        ttk.Label(frame, text=f"Поставщики материала: {material_name}", font=('Comic Sans MS', 12, 'bold')).pack(pady=10)
        
        # Таблица поставщиков
        tree = ttk.Treeview(frame, columns=('name', 'rating', 'date'), show='headings')
        
        tree.heading('name', text='Наименование')
        tree.heading('rating', text='Рейтинг')
        tree.heading('date', text='Дата начала работы')
        
        tree.column('name', width=250)
        tree.column('rating', width=150)
        tree.column('date', width=150)
        
        for supplier in suppliers:
            tree.insert('', 'end', values=supplier)
        
        tree.pack(fill=BOTH, expand=True)
    
    def calculate_product_quantity(self, product_type_id, material_type_id, material_quantity, param1, param2):
        """Метод для расчета количества продукции (Модуль 4)"""
        try:
            # Проверка входных параметров
            if material_quantity <= 0 or param1 <= 0 or param2 <= 0:
                return -1
            
            # Получаем коэффициенты из БД (в реальном приложении)
            # Здесь просто примерные значения
            product_coefficient = 1.2  # Коэффициент типа продукции
            loss_percentage = 0.05     # Процент потерь (5%)
            
            # Расчет необходимого количества сырья на единицу продукции
            material_per_unit = param1 * param2 * product_coefficient
            
            # Учет потерь
            total_material_needed = material_per_unit * (1 + loss_percentage)
            
            # Расчет количества продукции
            product_quantity = int(material_quantity / total_material_needed)
            
            return product_quantity if product_quantity > 0 else 0
        
        except:
            return -1

if __name__ == "__main__":
    root = Tk()
    app = MaterialApp(root)
    root.mainloop()