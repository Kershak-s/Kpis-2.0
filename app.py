from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from io import BytesIO
import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cambia_esta_llave_por_una_mas_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------------------------------------
# MODELOS
# --------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    bu = db.Column(db.String(50))
    plant = db.Column(db.String(150))
    lineas_config = db.relationship('LineaConfig', backref='user', lazy=True)

class LineaPlanta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bu = db.Column(db.String(50))
    planta = db.Column(db.String(150))
    categoria = db.Column(db.String(50))
    linea = db.Column(db.String(150))
    marca = db.Column(db.String(150))
    modelo = db.Column(db.String(150))
    pesadora = db.Column(db.String(150))
    empacadora = db.Column(db.String(150))
    high_speed = db.Column(db.String(150))
    # Nuevos campos
    low_speed = db.Column(db.String(150))
    seal_checker = db.Column(db.String(150))
    dacs = db.Column(db.String(150))
    rcc = db.Column(db.String(150))
    terma_tira_semi_auto = db.Column(db.String(150))
    festo = db.Column(db.String(150))
    hanco = db.Column(db.String(150))
    guacp = db.Column(db.String(150))
    pkg_manual = db.Column(db.String(150))
    pkg_auto = db.Column(db.String(150))
    pallet_auto = db.Column(db.String(150))
    numero_da_ea = db.Column(db.String(150))
    pesadoras_mes = db.Column(db.String(150))
    guacp_mes = db.Column(db.String(150))
    estatus_revisado = db.Column(db.String(150))
    # Campo original
    asteriscos = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class LineaConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Relación para equipos
    equipos = db.relationship('Equipo', backref='linea_config', lazy=True)

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(255))
    linea_id = db.Column(db.Integer, db.ForeignKey('linea_config.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Kpi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    linea = db.Column(db.String(150))
    mes = db.Column(db.Integer)
    anio = db.Column(db.Integer)
    eficiencia_pesadora = db.Column(db.Float)
    eficiencia_empaque = db.Column(db.Float)
    eficiencia_dme = db.Column(db.Float)
    sobre_gramaje = db.Column(db.Float)
    eficiencia_guacp = db.Column(db.Float)
    mtbf = db.Column(db.Float)
    mttr = db.Column(db.Float)
    eficiencia_espera_producto = db.Column(db.Float)

class KpiComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kpi_id = db.Column(db.Integer, db.ForeignKey('kpi.id'))
    packing_efficiency = db.Column(db.Text)
    material_waste = db.Column(db.Text)
    giveaway = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

# control de fecha maxima para el mes actual
class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

#--------------------------------------------------

# --------------------------------------------------
# DATOS DE PLANTS (JSON)
# --------------------------------------------------
PLANTS = [
    {"bu": "ANDINOS",  "planta": "Funza"},
    {"bu": "ANDINOS",  "planta": "Oriente"},
    {"bu": "ANDINOS",  "planta": "Quito"},
    {"bu": "ANDINOS",  "planta": "Santa Anita"},
    {"bu": "ANDINOS",  "planta": "Santa Cruz"},
    {"bu": "CARICAM",  "planta": "Barceloneta"},
    {"bu": "CARICAM",  "planta": "Guatemala"},
    {"bu": "CARICAM",  "planta": "Santo Domingo"},
    {"bu": "PBF",      "planta": "Curitiba"},
    {"bu": "PBF",      "planta": "Itaquera"},
    {"bu": "PBF",      "planta": "ITU"},
    {"bu": "PBF",      "planta": "Recife"},
    {"bu": "PBF",      "planta": "Sete Lagoas"},
    {"bu": "PBF",      "planta": "Sorocaba"},
    {"bu": "PMF",      "planta": "Guadalajara"},
    {"bu": "PMF",      "planta": "Mexicali"},
    {"bu": "PMF",      "planta": "Obregón"},
    {"bu": "PMF",      "planta": "Saltillo"},
    {"bu": "PMF",      "planta": "Celaya"},
    {"bu": "PMF",      "planta": "Toluca"},
    {"bu": "PMF",      "planta": "Vallejo"},
    {"bu": "PMF",      "planta": "Veracruz"},
    {"bu": "SOCO",     "planta": "Cerrillos"},
    {"bu": "SOCO",     "planta": "Mar del Plata"}
]

# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------
def create_default_admin():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        hashed_password = generate_password_hash('PEPCODE', method='pbkdf2:sha256')
        admin_user = User(username='admin', password=hashed_password, is_admin=True, bu='SOCO', plant='Cerrillos')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario admin 'admin' creado con contraseña 'PEPCODE'.")



# --------------------------------------------------
# FUNCIONES PARA GESTIONAR CONFIGURACIÓN DE SISTEMA
# --------------------------------------------------
def get_deadline_day():
    """Obtiene el día límite configurado para carga de KPIs"""
    config = SystemConfig.query.filter_by(key='kpi_deadline_day').first()
    if config:
        return int(config.value)
    else:
        # Valor por defecto: día 10 de cada mes
        return 10

def check_deadline_passed():
    """Verifica si la fecha actual ya superó la fecha límite del mes actual"""
    deadline_day = get_deadline_day()
    current_date = datetime.datetime.now()
    
    # Calcular la fecha límite del mes actual
    if current_date.day > deadline_day:
        # Ya pasó la fecha límite del mes actual
        return True
    else:
        # Todavía estamos dentro del plazo
        return False

def get_deadline_formatted():
    """Devuelve la fecha límite formateada"""
    deadline_day = get_deadline_day()
    current_date = datetime.datetime.now()
    
    # Calcular la fecha límite del mes actual
    deadline_date = datetime.datetime(current_date.year, current_date.month, deadline_day)
    return deadline_date.strftime("%d/%m/%Y")

@app.route('/save_deadline_config', methods=['POST'])
def save_deadline_config():
    """Guarda la configuración del día límite para carga de KPIs"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Acceso restringido'}), 403
    
    try:
        data = request.get_json()
        deadline_day = int(data.get('deadline_day', 10))
        
        if deadline_day < 1 or deadline_day > 31:
            return jsonify({'success': False, 'error': 'El día debe estar entre 1 y 31'}), 400
        
        # Guardar en la base de datos
        config = SystemConfig.query.filter_by(key='kpi_deadline_day').first()
        if not config:
            config = SystemConfig(
                key='kpi_deadline_day',
                value=str(deadline_day),
                description='Día límite de cada mes para carga de KPIs'
            )
            db.session.add(config)
        else:
            config.value = str(deadline_day)
        
        db.session.commit()
        
        # Devolver estado actualizado
        deadline_passed = check_deadline_passed()
        deadline_formatted = get_deadline_formatted()
        
        return jsonify({
            'success': True, 
            'deadline_day': deadline_day,
            'deadline_passed': deadline_passed,
            'deadline_formatted': deadline_formatted
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --------------------------------------------------
# RUTAS PRINCIPALES (USUARIO)
# --------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin')) if user.is_admin else redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/carga-kpis')
def carga_kpis():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    current_user = User.query.get(session.get('user_id'))
    lineas_config = LineaConfig.query.filter_by(user_id=session.get('user_id')).all()
    
    # Obtener usuarios de la misma planta y BU
    plant_users = User.query.filter(
        db.func.upper(User.plant) == db.func.upper(current_user.plant),
        db.func.upper(User.bu) == db.func.upper(current_user.bu)
    ).all()
    
    plant_user_ids = [u.id for u in plant_users]
    
    # Obtener KPIs ordenados por año y mes descendente (más nuevo primero)
    # Ahora incluye KPIs de todos los usuarios de la misma planta
    kpis = Kpi.query.filter(Kpi.user_id.in_(plant_user_ids)).order_by(Kpi.anio.desc(), Kpi.mes.desc()).all()
    
    # Verificar fecha límite
    deadline_day = get_deadline_day()
    deadline_passed = check_deadline_passed()
    deadline_formatted = get_deadline_formatted()
    
    return render_template(
        'carga_kpis.html', 
        lineas_config=lineas_config, 
        kpis=kpis,
        deadline_day=deadline_day,
        deadline_passed=deadline_passed,
        deadline_formatted=deadline_formatted
    )


@app.route('/lay-out-planta')
def lay_out_planta():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    current_user = User.query.get(session.get('user_id'))
    lineas = LineaPlanta.query.filter_by(user_id=session.get('user_id')).all()
    lineas_config = LineaConfig.query.filter_by(user_id=session.get('user_id')).all()
    return render_template('lay_out_planta.html', lineas=lineas, current_bu=current_user.bu, current_plant=current_user.plant, lineas_config=lineas_config)

@app.route('/cajas')
def cajas():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('cajas.html')

@app.route('/contactos')
def contactos():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('contactos.html')

@app.route('/configuracion')
def configuracion():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    # Obtener las líneas configuradas por el usuario
    lineas = LineaConfig.query.filter_by(user_id=session.get('user_id')).all()
    return render_template('configuracion.html', lineas=lineas)

# --------------------------------------------------
# RUTAS ADMINISTRATIVAS (ADMIN)
# --------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('is_admin'):
        flash("Acceso restringido", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        bu_plant_value = request.form.get('bu_plant')
        if bu_plant_value:
            bu, plant = bu_plant_value.split('|')
        else:
            bu, plant = '', ''
        is_admin = True if request.form.get('is_admin') == 'on' else False
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("El usuario ya existe.", "danger")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, is_admin=is_admin, bu=bu, plant=plant)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuario registrado con éxito', 'success')
        return redirect(url_for('admin'))
    return render_template('register.html', plants=PLANTS)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('is_admin'):
        flash("Acceso restringido", "danger")
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        new_password = request.form['password']
        if new_password.strip():
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        bu_plant_value = request.form.get('bu_plant')
        if bu_plant_value:
            bu, plant = bu_plant_value.split('|')
            user.bu = bu
            user.plant = plant
        user.is_admin = True if request.form.get('is_admin') == 'on' else False
        db.session.commit()
        flash('Usuario actualizado con éxito', 'success')
        return redirect(url_for('admin'))
    return render_template('edit_user.html', user=user, plants=PLANTS)

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash("Acceso restringido", "danger")
        return redirect(url_for('dashboard'))
        
    # Obtener fecha actual para los filtros por defecto
    from datetime import datetime
    current_date = datetime.now()
    current_month = int(request.args.get('month', current_date.month))
    current_year = int(request.args.get('year', current_date.year))
    current_bu = request.args.get('bu', 'TODOS')
    
    print(f"DEBUG: Filtrando KPIs para BU={current_bu}, mes={current_month}, año={current_year}")
    
    # 1. Lista de usuarios
    users = User.query.all()
    
    # 2. Combinaciones únicas de BU y Planta (Lay Out)
    lay_outs_query = db.session.query(LineaPlanta.bu, LineaPlanta.planta).distinct().all()
    lay_outs = [{'bu': bu, 'plant': plant} for bu, plant in lay_outs_query]
    
    # 3. Datos para el panel de status de carga
    plants_status = {
        'total': len(lay_outs),
        'loaded': 0,
        'not_loaded': 0,
        'details': []
    }
    
    # 4. KPIs por planta para el mes y año seleccionados
    kpis_by_plant = []
    
    # Obtener TODOS los KPIs para el mes y año actual (para depuración)
    all_kpis_debug = Kpi.query.filter_by(mes=current_month, anio=current_year).all()
    print(f"DEBUG: Total de KPIs encontrados para {current_month}/{current_year}: {len(all_kpis_debug)}")
    for kpi in all_kpis_debug:
        kpi_user = User.query.get(kpi.user_id)
        user_info = f"{kpi_user.username} (BU: {kpi_user.bu}, Planta: {kpi_user.plant})" if kpi_user else "Usuario desconocido"
        print(f"DEBUG: KPI ID: {kpi.id}, Línea: {kpi.linea}, Usuario: {user_info}")
    
    # Lista todas las plantas (filtradas por BU si corresponde)
    filtered_lay_outs = lay_outs
    if current_bu != 'TODOS':
        print(f"DEBUG: Filtrando plantas para BU={current_bu}")
        filtered_lay_outs = [layout for layout in lay_outs if layout['bu'].upper() == current_bu.upper()]

    # Procesar cada planta
    for lay_out in filtered_lay_outs:
        bu = lay_out['bu'].strip() if lay_out['bu'] else ""
        plant = lay_out['plant'].strip() if lay_out['plant'] else ""
        
        print(f"DEBUG: Procesando planta: {plant} (BU: {bu})")
        
        # Buscar usuarios asignados a esta planta
        plant_users = User.query.filter(
            db.func.upper(User.plant) == plant.upper(),
            db.func.upper(User.bu) == bu.upper()
        ).all()
        
        print(f"DEBUG: Usuarios encontrados para {plant}: {[u.username for u in plant_users]}")
        
        # Variables para almacenar información del KPI
        username = "No asignado"
        has_kpi = False
        kpi_data = None
        kpi_user_id = None
        
        # Si hay usuarios para esta planta, buscar KPIs
        if plant_users:
            user_ids = [u.id for u in plant_users]
            
            # Buscar KPIs para cualquier usuario de esta planta
            plant_kpis = Kpi.query.filter(
                Kpi.user_id.in_(user_ids),
                Kpi.mes == current_month,
                Kpi.anio == current_year
            ).all()
            
            print(f"DEBUG: KPIs encontrados para planta {plant}: {len(plant_kpis)}")
            
            if plant_kpis:
                # Tomar el primer KPI encontrado
                kpi_data = plant_kpis[0]
                has_kpi = True
                kpi_user = User.query.get(kpi_data.user_id)
                kpi_user_id = kpi_data.user_id
                username = kpi_user.username if kpi_user else "Usuario desconocido"
                print(f"DEBUG: Se usará el KPI ID: {kpi_data.id} de la línea {kpi_data.linea} cargado por {username}")
        
        # Determinar estado de carga y agregar a los datos
        if has_kpi and kpi_data:
            # Actualizar contador de plantas con datos
            plants_status['loaded'] += 1
            plants_status['details'].append({
                'bu': bu,
                'plant': plant,
                'loaded': True
            })
            
            kpi_entry = {
                'id': kpi_data.id,
                'plant': plant,
                'bu': bu,
                'username': username,
                'has_data': True,
                'user_id': kpi_user_id,
                'fecha_carga': f"{current_month}/{current_year}",
                'linea': kpi_data.linea,
                'eficiencia_pesadora': kpi_data.eficiencia_pesadora,
                'eficiencia_empaque': kpi_data.eficiencia_empaque,
                'eficiencia_dme': kpi_data.eficiencia_dme,
                'sobre_gramaje': kpi_data.sobre_gramaje,
                'eficiencia_guacp': kpi_data.eficiencia_guacp,
                'mtbf': kpi_data.mtbf,
                'mttr': kpi_data.mttr,
                'eficiencia_espera_producto': kpi_data.eficiencia_espera_producto,
                'has_comments': False  # Valor por defecto
            }
            kpis_by_plant.append(kpi_entry)
        else:
            # No hay datos para esta planta en el mes/año seleccionado
            plants_status['not_loaded'] += 1
            plants_status['details'].append({
                'bu': bu,
                'plant': plant,
                'loaded': False
            })
            
            user_id = plant_users[0].id if plant_users else None
            kpis_by_plant.append({
                'plant': plant,
                'bu': bu,
                'username': username,
                'user_id': user_id,
                'has_data': False,
                'has_comments': False  # Valor por defecto
            })
    
    # Añadir info de comentarios a los KPIs
    for k in kpis_by_plant:
        if k.get('has_data') and 'id' in k:
            # Buscar comentarios para este KPI
            comment = KpiComment.query.filter_by(kpi_id=k['id']).first()
            
            # Verificar si existe el comentario y tiene contenido real
            if comment is not None:
                has_content = False
                
                # Verificar cada campo independientemente
                if comment.packing_efficiency and comment.packing_efficiency.strip():
                    has_content = True
                elif comment.material_waste and comment.material_waste.strip():
                    has_content = True
                elif comment.giveaway and comment.giveaway.strip():
                    has_content = True
                
                k['has_comments'] = has_content
                
                # Debug para ver si hay comentarios
                if has_content:
                    print(f"DEBUG: KPI {k['id']} tiene comentarios")
                else:
                    print(f"DEBUG: KPI {k['id']} tiene registro de comentarios pero están vacíos")
            else:
                print(f"DEBUG: KPI {k['id']} no tiene comentarios")
    
    # 5. Métricas de KPI para el mes seleccionado (promedios, tendencias)
    kpi_metrics = {
        'avg_pesadora': 0,
        'avg_empaque': 0,
        'avg_dme': 0,
        'avg_gramaje': 0,
        'trend_pesadora': 0,
        'trend_empaque': 0,
        'trend_dme': 0,
        'trend_gramaje': 0
    }
    
    # Recopilamos todos los KPIs del mes y año seleccionados
    current_kpis = Kpi.query.filter_by(mes=current_month, anio=current_year).all()
    
    if current_kpis:
        # Diagnóstico
        print(f"DEBUG: KPIs totales para {current_month}/{current_year}: {len(current_kpis)}")
        
        # Calcular promedios
        kpi_metrics['avg_pesadora'] = sum(k.eficiencia_pesadora for k in current_kpis) / len(current_kpis)
        kpi_metrics['avg_empaque'] = sum(k.eficiencia_empaque for k in current_kpis) / len(current_kpis)
        kpi_metrics['avg_dme'] = sum(k.eficiencia_dme for k in current_kpis) / len(current_kpis)
        kpi_metrics['avg_gramaje'] = sum(k.sobre_gramaje for k in current_kpis) / len(current_kpis)
        
        # Calcular tendencias (comparado con el mes anterior)
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1
        
        prev_kpis = Kpi.query.filter_by(mes=prev_month, anio=prev_year).all()
        
        if prev_kpis:
            prev_avg_pesadora = sum(k.eficiencia_pesadora for k in prev_kpis) / len(prev_kpis)
            prev_avg_empaque = sum(k.eficiencia_empaque for k in prev_kpis) / len(prev_kpis)
            prev_avg_dme = sum(k.eficiencia_dme for k in prev_kpis) / len(prev_kpis)
            prev_avg_gramaje = sum(k.sobre_gramaje for k in prev_kpis) / len(prev_kpis)
            
            kpi_metrics['trend_pesadora'] = kpi_metrics['avg_pesadora'] - prev_avg_pesadora
            kpi_metrics['trend_empaque'] = kpi_metrics['avg_empaque'] - prev_avg_empaque
            kpi_metrics['trend_dme'] = kpi_metrics['avg_dme'] - prev_avg_dme
            kpi_metrics['trend_gramaje'] = kpi_metrics['avg_gramaje'] - prev_avg_gramaje
    
    # Ordenar las plantas por BU para agruparlas en la visualización
    kpis_by_plant.sort(key=lambda x: (x['bu'], x['plant']))
    plants_status['details'].sort(key=lambda x: (x['bu'], x['plant']))
    
    return render_template(
        'admin_panel.html', 
        users=users, 
        lay_outs=lay_outs, 
        plants_status=plants_status,
        kpis_by_plant=kpis_by_plant,
        kpi_metrics=kpi_metrics,
        current_month=current_month,
        current_year=current_year,
        current_bu=current_bu,
        deadline_day=get_deadline_day(),
        deadline_passed=check_deadline_passed(),
        deadline_formatted=get_deadline_formatted()
    )



#--------------------------------------------------
#RUTAS PARA GESTIONAR TABLAS BOTON VER


# Add these routes to app.py

# Agregar estas rutas a tu archivo app.py

@app.route('/get_plant_lines')
def get_plant_lines():
    """
    Obtiene todas las líneas disponibles para una planta específica
    y verifica cuáles tienen datos de KPI cargados para el mes/año seleccionado.
    """
    if not session.get('is_admin'):
        return jsonify({'error': 'Acceso restringido'}), 403
    
    plant = request.args.get('plant')
    bu = request.args.get('bu')
    month = int(request.args.get('month'))
    year = int(request.args.get('year'))
    
    if not plant or not bu:
        return jsonify({'error': 'Faltan parámetros'}), 400
    
    # Imprimir información de depuración
    print(f"DEBUG: Buscando líneas para planta={plant}, bu={bu}, month={month}, year={year}")
    
    # 1. Obtener usuarios asignados a esta planta
    # Normalizar búsqueda - ignorar mayúsculas/minúsculas y espacios
    plant_norm = plant.strip().upper()
    bu_norm = bu.strip().upper()
    
    users = User.query.filter(
        db.func.upper(User.plant) == plant_norm,
        db.func.upper(User.bu) == bu_norm
    ).all()
    
    print(f"DEBUG: Usuarios encontrados: {[u.username for u in users]}")
    
    # Conjunto para almacenar todas las líneas únicas
    all_lines = set()
    
    # 2. Obtener líneas desde LineaConfig para cada usuario
    if users:
        for user in users:
            lines = LineaConfig.query.filter_by(user_id=user.id).all()
            for line in lines:
                all_lines.add(line.nombre)
            print(f"DEBUG: Líneas para usuario {user.username}: {[l.nombre for l in lines]}")
    
    # 3. Buscar líneas desde LineaPlanta si hay pocas o ninguna desde usuarios
    lineas_planta = db.session.query(LineaPlanta).filter(
        db.func.upper(LineaPlanta.planta) == plant_norm,
        db.func.upper(LineaPlanta.bu) == bu_norm
    ).all()
    
    print(f"DEBUG: LineaPlanta registros encontrados: {len(lineas_planta)}")
    
    for lp in lineas_planta:
        if lp.linea and lp.linea.strip():
            all_lines.add(lp.linea.strip().upper())
    
    # 4. Si aún no hay suficientes líneas, usar líneas genéricas
    if len(all_lines) < 2:
        print("DEBUG: Usando líneas genéricas")
        default_lines = ['LÍNEA 1', 'LÍNEA 2', 'LÍNEA 3', 'LÍNEA 4', 'LÍNEA 5']
        for line in default_lines:
            all_lines.add(line)
    
    # Preparar información de todas las líneas obtenidas
    result = []
    
    # Buscar TODOS los KPIs para esta planta/BU/mes/año
    all_kpis = []
    user_ids = [u.id for u in users]
    if user_ids:
        all_kpis = Kpi.query.filter(
            Kpi.user_id.in_(user_ids),
            Kpi.mes == month,
            Kpi.anio == year
        ).all()
    
    print(f"DEBUG: Total KPIs encontrados: {len(all_kpis)}")
    for kpi in all_kpis:
        print(f"DEBUG: KPI encontrado - línea: '{kpi.linea}', usuario: {kpi.user_id}, ID: {kpi.id}")
    
    # Procesar cada línea
    for line_name in sorted(all_lines):
        line_name_upper = line_name.strip().upper()
        line_data = {
            'nombre': line_name,
            'has_data': False,
            'kpi_id': None
        }
        
        # Verificar si hay KPI para esta línea (comparando siempre en mayúsculas)
        for kpi in all_kpis:
            kpi_linea = kpi.linea.strip().upper() if kpi.linea else ""
            if kpi_linea == line_name_upper:
                line_data['has_data'] = True
                line_data['kpi_id'] = kpi.id
                print(f"DEBUG: Línea '{line_name}' tiene datos (KPI ID: {kpi.id})")
                break
        
        result.append(line_data)
    
    print(f"DEBUG: Total de líneas encontradas: {len(result)}")
    print(f"DEBUG: Líneas con datos: {sum(1 for line in result if line['has_data'])}")
    
    return jsonify(result)


@app.route('/get_kpi_details/<int:kpi_id>')
def get_kpi_details(kpi_id):
    """
    Obtiene los detalles específicos de un KPI por su ID.
    """
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Acceso restringido'}), 403
    
    kpi = Kpi.query.get(kpi_id)
    if not kpi:
        return jsonify({'success': False, 'error': 'KPI no encontrado'}), 404
    
    # Devolver información detallada del KPI
    return jsonify({
        'success': True,
        'kpi': {
            'id': kpi.id,
            'linea': kpi.linea,
            'mes': kpi.mes,
            'anio': kpi.anio,
            'eficiencia_pesadora': kpi.eficiencia_pesadora,
            'eficiencia_empaque': kpi.eficiencia_empaque,
            'eficiencia_dme': kpi.eficiencia_dme,
            'sobre_gramaje': kpi.sobre_gramaje,
            'eficiencia_guacp': kpi.eficiencia_guacp,
            'mtbf': kpi.mtbf,
            'mttr': kpi.mttr,
            'eficiencia_espera_producto': kpi.eficiencia_espera_producto
        }
    })
#--------------------------------------------------

# --------------------------------------------------
# RUTAS PARA CONFIGURAR LAS LÍNEAS DE EQUIPOS (Configuración)
# --------------------------------------------------
@app.route('/config_lineas')
def config_lineas():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    lineas = LineaConfig.query.filter_by(user_id=session.get('user_id')).all()
    return render_template('config_lineas.html', lineas=lineas)

@app.route('/guardar_linea_config', methods=['POST'])
def guardar_linea_config():
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify({'success': False, 'error': 'No se proporcionó nombre'})
    nueva_linea = LineaConfig(nombre=data.get('nombre').upper(), user_id=session.get('user_id'))
    db.session.add(nueva_linea)
    db.session.commit()
    return jsonify({'success': True, 'id': nueva_linea.id})

@app.route('/actualizar_linea_config/<int:linea_id>', methods=['PUT'])
def actualizar_linea_config(linea_id):
    data = request.get_json()
    linea = LineaConfig.query.get(linea_id)
    if not linea:
        return jsonify({'success': False, 'error': 'Línea no encontrada'})
    linea.nombre = data.get('nombre').upper()
    db.session.commit()
    return jsonify({'success': True, 'id': linea.id})

@app.route('/borrar_linea_config/<int:linea_id>', methods=['DELETE'])
def borrar_linea_config(linea_id):
    linea = LineaConfig.query.get(linea_id)
    if linea:
        db.session.delete(linea)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Línea no encontrada'})

# --------------------------------------------------
# ENDPOINTS PARA GESTIONAR EQUIPOS POR LÍNEA (Configuración)
# --------------------------------------------------
@app.route('/config_equipos/<int:linea_id>')
def config_equipos(linea_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    linea = LineaConfig.query.get_or_404(linea_id)
    equipos = linea.equipos
    return render_template('config_equipos.html', linea=linea, equipos=equipos)

@app.route('/guardar_equipo', methods=['POST'])
def guardar_equipo():
    data = request.get_json()
    if not data or not data.get('nombre') or not data.get('linea_id'):
        return jsonify({'success': False, 'error': 'Datos incompletos'})
    nuevo_equipo = Equipo(
        nombre=data.get('nombre'),
        descripcion=data.get('descripcion', ''),
        linea_id=data.get('linea_id'),
        user_id=session.get('user_id')
    )
    db.session.add(nuevo_equipo)
    db.session.commit()
    return jsonify({'success': True, 'id': nuevo_equipo.id})

@app.route('/actualizar_equipo/<int:equipo_id>', methods=['PUT'])
def actualizar_equipo(equipo_id):
    data = request.get_json()
    equipo = Equipo.query.get(equipo_id)
    if not equipo:
        return jsonify({'success': False, 'error': 'Equipo no encontrado'})
    equipo.nombre = data.get('nombre')
    equipo.descripcion = data.get('descripcion', '')
    db.session.commit()
    return jsonify({'success': True, 'id': equipo.id})

@app.route('/borrar_equipo/<int:equipo_id>', methods=['DELETE'])
def borrar_equipo(equipo_id):
    equipo = Equipo.query.get(equipo_id)
    if equipo:
        db.session.delete(equipo)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Equipo no encontrado'})

# --------------------------------------------------
# ENDPOINTS PARA KPI
# --------------------------------------------------
@app.route('/guardar_kpi', methods=['POST'])
def guardar_kpi():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    # Verificar fecha límite
    deadline_passed = check_deadline_passed()
    
    user_id = session.get('user_id')
    current_user = User.query.get(user_id)
    linea = data.get('linea').upper()
    mes = int(data.get('mes'))
    anio = int(data.get('anio'))
    
    print(f"DEBUG: Guardando KPI para usuario ID {user_id}, línea {linea}, mes {mes}, año {anio}")
    print(f"DEBUG: Usuario {current_user.username}, BU: {current_user.bu}, Planta: {current_user.plant}")
    
    # Verificar si los datos son para el mes actual
    current_date = datetime.datetime.now()
    is_current_month = (mes == current_date.month and anio == current_date.year)
    
    # Si es el mes actual y pasó la fecha límite, BLOQUEAR la carga
    if is_current_month and deadline_passed:
        # Verificar si el usuario es administrador (los administradores pueden cargar en cualquier momento)
        if not session.get('is_admin'):
            return jsonify({
                'success': False, 
                'deadline_passed': True,
                'error': f"La fecha límite para cargar datos del mes actual ha pasado ({get_deadline_formatted()}). Contacte al administrador si necesita cargar datos fuera de plazo."
            })
    
    # Verificar si ya existe un KPI para esta línea/mes/año
    existing = Kpi.query.filter_by(user_id=user_id, linea=linea, mes=mes, anio=anio).first()
    
    # También verificar si otros usuarios de la misma planta ya cargaron este KPI
    if not existing and current_user.bu and current_user.plant:
        # Buscar otros usuarios de la misma planta
        same_plant_users = User.query.filter(
            User.id != user_id,
            db.func.upper(User.bu) == db.func.upper(current_user.bu),
            db.func.upper(User.plant) == db.func.upper(current_user.plant)
        ).all()
        
        if same_plant_users:
            print(f"DEBUG: Encontrados {len(same_plant_users)} usuarios adicionales en la misma planta")
            user_ids = [u.id for u in same_plant_users]
            
            # Verificar si alguno de estos usuarios ya cargó un KPI para esta línea/mes/año
            other_existing = Kpi.query.filter(
                Kpi.user_id.in_(user_ids),
                db.func.upper(Kpi.linea) == linea,
                Kpi.mes == mes,
                Kpi.anio == anio
            ).first()
            
            if other_existing:
                other_user = User.query.get(other_existing.user_id)
                return jsonify({
                    'success': False, 
                    'exists': True, 
                    'message': f"Ya existe un registro para {mes}/{anio} en la línea {linea}, cargado por el usuario {other_user.username}."
                })
    
    if existing:
        return jsonify({
            'success': False, 
            'exists': True, 
            'message': f"Ya existe un registro para {mes}/{anio} en la línea {linea}."
        })
    
    # Preparar mensaje de advertencia si aplica
    warning_message = None
    if is_current_month and deadline_passed and session.get('is_admin'):
        warning_message = f"¡Atención! La fecha límite para cargar datos del mes actual ha pasado ({get_deadline_formatted()}). Se han guardado los datos con permisos de administrador."
    
    # Crear nuevo KPI
    new_kpi = Kpi(
        user_id=user_id,
        linea=linea,
        mes=mes,
        anio=anio,
        eficiencia_pesadora=float(data.get('eficiencia_pesadora')),
        eficiencia_empaque=float(data.get('eficiencia_empaque')),
        eficiencia_dme=float(data.get('eficiencia_dme')),
        sobre_gramaje=float(data.get('sobre_gramaje')),
        eficiencia_guacp=float(data.get('eficiencia_guacp')),
        mtbf=float(data.get('mtbf')),
        mttr=float(data.get('mttr')),
        eficiencia_espera_producto=float(data.get('eficiencia_espera_producto'))
    )
    
    db.session.add(new_kpi)
    db.session.commit()
    
    print(f"DEBUG: KPI guardado exitosamente con ID {new_kpi.id}")
    
    return jsonify({
        'success': True, 
        'id': new_kpi.id,
        'warning': warning_message
    })
        
@app.route('/actualizar_kpi/<int:kpi_id>', methods=['PUT'])
def actualizar_kpi(kpi_id):
    data = request.get_json()
    kpi = Kpi.query.get(kpi_id)
    if not kpi:
        return jsonify({'success': False, 'error': 'KPI no encontrado'})
    if 'linea' in data:
        kpi.linea = data.get('linea').upper()
    if 'mes' in data:
        kpi.mes = int(data.get('mes'))
    if 'anio' in data:
        kpi.anio = int(data.get('anio'))
    if 'eficiencia_pesadora' in data:
        kpi.eficiencia_pesadora = float(data.get('eficiencia_pesadora'))
    if 'eficiencia_empaque' in data:
        kpi.eficiencia_empaque = float(data.get('eficiencia_empaque'))
    if 'eficiencia_dme' in data:
        kpi.eficiencia_dme = float(data.get('eficiencia_dme'))
    if 'sobre_gramaje' in data:
        kpi.sobre_gramaje = float(data.get('sobre_gramaje'))
    if 'eficiencia_guacp' in data:
        kpi.eficiencia_guacp = float(data.get('eficiencia_guacp'))
    if 'mtbf' in data:
        kpi.mtbf = float(data.get('mtbf'))
    if 'mttr' in data:
        kpi.mttr = float(data.get('mttr'))
    if 'eficiencia_espera_producto' in data:
        kpi.eficiencia_espera_producto = float(data.get('eficiencia_espera_producto'))
    db.session.commit()
    return jsonify({'success': True, 'id': kpi.id})

@app.route('/borrar_kpi/<int:kpi_id>', methods=['DELETE'])
def borrar_kpi(kpi_id):
    kpi = Kpi.query.get(kpi_id)
    if kpi:
        db.session.delete(kpi)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'KPI no encontrado'})

@app.route('/get_kpis')
def get_kpis():
    user_id_param = request.args.get('user_id')
    
    # Si se solicita específicamente para un usuario (desde panel admin)
    if user_id_param and session.get('is_admin'):
        try:
            user_id = int(user_id_param)
            user = User.query.get(user_id)
        except ValueError:
            return jsonify({"error": "ID de usuario inválido"}), 400
    else:
        # Usuario actual
        user_id = session.get('user_id')
        user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Obtener todos los usuarios de la misma planta y BU
    plant_users = User.query.filter(
        db.func.upper(User.plant) == db.func.upper(user.plant),
        db.func.upper(User.bu) == db.func.upper(user.bu)
    ).all()
    
    plant_user_ids = [u.id for u in plant_users]
    
    # Obtener todos los KPIs de todos los usuarios de la misma planta
    kpis = Kpi.query.filter(Kpi.user_id.in_(plant_user_ids)).all()
    
    data = {}
    for kpi in kpis:
        anio = kpi.anio
        if anio not in data:
            data[anio] = {}
        
        # Si ya existe un KPI para este mes, solo lo reemplazamos si es del usuario actual
        # o si no hay KPI actual para este mes
        if kpi.mes not in data[anio] or kpi.user_id == user_id:
            data[anio][kpi.mes] = {
                'id': kpi.id,
                'linea': kpi.linea,
                'eficiencia_pesadora': kpi.eficiencia_pesadora,
                'eficiencia_empaque': kpi.eficiencia_empaque,
                'eficiencia_dme': kpi.eficiencia_dme,
                'sobre_gramaje': kpi.sobre_gramaje,
                'eficiencia_guacp': kpi.eficiencia_guacp,
                'mtbf': kpi.mtbf,
                'mttr': kpi.mttr,
                'eficiencia_espera_producto': kpi.eficiencia_espera_producto,
                'user_id': kpi.user_id  # Añadimos esta información para referencia
            }
    
    return jsonify(data)

# --------------------------------------------------
# ENDPOINTS PARA CONSULTA DE DATOS DE USUARIO (ADMIN)
# --------------------------------------------------
@app.route('/consulta_usuario', methods=['GET', 'POST'])
def consulta_usuario():
    if not session.get('is_admin'):
        flash("Acceso restringido", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        selected_user_id = request.form.get('user_id')
        return redirect(url_for('consulta_usuario', user_id=selected_user_id))
    else:
        user_id = request.args.get('user_id')
        users = User.query.all()
        return render_template('consulta_usuario.html', users=users, user_id=user_id)

@app.route('/get_users')
def get_users():
    users = User.query.all()
    data = []
    for u in users:
        data.append({
            'id': u.id,
            'username': u.username,
            'bu': u.bu,
            'plant': u.plant,
            'is_admin': u.is_admin
        })
    return jsonify(data)

@app.route('/get_lay_outs')
def get_lay_outs():
    lay_outs = db.session.query(LineaPlanta.bu, LineaPlanta.planta).distinct().all()
    data = [{'bu': bu, 'plant': planta} for bu, planta in lay_outs]
    return jsonify(data)

@app.route('/get_last_kpis')
def get_last_kpis():
    users = User.query.all()
    data = []
    for u in users:
        kpi = Kpi.query.filter_by(user_id=u.id).order_by(Kpi.anio.desc(), Kpi.mes.desc()).first()
        if kpi:
            data.append({
                'username': u.username,
                'linea': kpi.linea,
                'mes': kpi.mes,
                'anio': kpi.anio,
                'eficiencia_pesadora': kpi.eficiencia_pesadora,
                'eficiencia_empaque': kpi.eficiencia_empaque,
                'eficiencia_dme': kpi.eficiencia_dme,
                'sobre_gramaje': kpi.sobre_gramaje,
                'eficiencia_guacp': kpi.eficiencia_guacp,
                'mtbf': kpi.mtbf,
                'mttr': kpi.mttr,
                'eficiencia_espera_producto': kpi.eficiencia_espera_producto
            })
    return jsonify(data)

# --------------------------------------------------
# ENDPOINTS PARA DESCARGAR/CARGAR PLANTILLA KPI
# --------------------------------------------------
@app.route('/download_template_kpi')
def download_template_kpi():
    columns = ["Línea", "Mes", "Año", "Eficiencia Pesadora", "Eficiencia Empaque",
               "Eficiencia DME", "Sobre Grameaje", "Eficiencia GUACP", "MTBF", "MTTR",
               "Eficiencia en Espera de Producto"]
    df = pd.DataFrame(columns=columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="KPI")
    output.seek(0)
    return (output.read(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename="plantilla_kpi.xlsx"'
    })

@app.route('/upload_template_kpi', methods=['POST'])
def upload_template_kpi():
    if 'file' not in request.files:
        flash('No se envió ningún archivo.', 'danger')
        return redirect(url_for('carga_kpis'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('carga_kpis'))
    
    try:
        df = pd.read_excel(file)
    except Exception as e:
        flash('Error al leer el archivo: ' + str(e), 'danger')
        return redirect(url_for('carga_kpis'))
    
    required_columns = [
        "Línea", "Mes", "Año", "Eficiencia Pesadora", "Eficiencia Empaque",
        "Eficiencia DME", "Sobre Grameaje", "Eficiencia GUACP", "MTBF", "MTTR",
        "Eficiencia en Espera de Producto"
    ]
    for col in required_columns:
        if col not in df.columns:
            flash(f'La columna "{col}" no se encuentra en el archivo.', 'danger')
            return redirect(url_for('carga_kpis'))
    
    errors = []
    user_id = session.get('user_id')
    user_lines = [lc.nombre for lc in LineaConfig.query.filter_by(user_id=user_id).all()]
    
    for idx, row in df.iterrows():
        fila = idx + 2  # +2 para considerar el encabezado y que Excel comienza en 1
        try:
            mes = int(row["Mes"])
            if mes < 1 or mes > 12:
                errors.append(f"Fila {fila}: El Mes debe estar entre 1 y 12.")
        except:
            errors.append(f"Fila {fila}: El Mes debe ser numérico.")
        
        try:
            anio = int(row["Año"])
        except:
            errors.append(f"Fila {fila}: El Año debe ser numérico.")
        
        for col in ["Eficiencia Pesadora", "Eficiencia Empaque", "Eficiencia DME",
                    "Sobre Grameaje", "Eficiencia GUACP", "Eficiencia en Espera de Producto"]:
            try:
                val = float(row[col])
                if val < 0 or val > 100:
                    errors.append(f"Fila {fila}: {col} debe estar entre 0 y 100.")
            except:
                errors.append(f"Fila {fila}: {col} debe ser numérico.")
        
        linea = str(row["Línea"]).upper()
        df.at[idx, "Línea"] = linea
        if linea not in user_lines:
            errors.append(f"Fila {fila}: La Línea '{linea}' no está configurada para este usuario.")
    
    if errors:
        errors_to_show = errors[:10]
        if len(errors) > 10:
            errors_to_show.append("... y más errores.")
        flash("Errores en el archivo: " + " | ".join(errors_to_show), 'danger')
        return redirect(url_for('carga_kpis'))
    
    for idx, row in df.iterrows():
        linea = row["Línea"]
        mes = int(row["Mes"])
        anio = int(row["Año"])
        existing = Kpi.query.filter_by(user_id=user_id, linea=linea, mes=mes, anio=anio).first()
        
        if existing:
            existing.eficiencia_pesadora = float(row["Eficiencia Pesadora"])
            existing.eficiencia_empaque = float(row["Eficiencia Empaque"])
            existing.eficiencia_dme = float(row["Eficiencia DME"])
            existing.sobre_gramaje = float(row["Sobre Grameaje"])
            existing.eficiencia_guacp = float(row["Eficiencia GUACP"])
            existing.mtbf = float(row["MTBF"])
            existing.mttr = float(row["MTTR"])
            existing.eficiencia_espera_producto = float(row["Eficiencia en Espera de Producto"])
        else:
            new_kpi = Kpi(
                user_id=user_id,
                linea=linea,
                mes=mes,
                anio=anio,
                eficiencia_pesadora=float(row["Eficiencia Pesadora"]),
                eficiencia_empaque=float(row["Eficiencia Empaque"]),
                eficiencia_dme=float(row["Eficiencia DME"]),
                sobre_gramaje=float(row["Sobre Grameaje"]),
                eficiencia_guacp=float(row["Eficiencia GUACP"]),
                mtbf=float(row["MTBF"]),
                mttr=float(row["MTTR"]),
                eficiencia_espera_producto=float(row["Eficiencia en Espera de Producto"])
            )
            db.session.add(new_kpi)
    
    db.session.commit()
    flash("Datos cargados exitosamente.", "success")
    return redirect(url_for('carga_kpis'))

# --------------------------------------------------
# ENDPOINTS PARA LÍNEA DE PLANTA (USAR PARA LAY OUT)
# --------------------------------------------------
@app.route('/guardar_linea_planta', methods=['POST'])
def guardar_linea_planta():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    nueva_linea = LineaPlanta(
         bu = data.get('bu').upper(),
         planta = data.get('planta').upper(),
         categoria = data.get('categoria'),
         linea = data.get('linea'),
         marca = data.get('marca'),
         modelo = data.get('modelo'),
         pesadora = data.get('pesadora'),
         empacadora = data.get('empacadora'),
         high_speed = data.get('high_speed'),
         # Nuevos campos
         low_speed = data.get('low_speed', ''),
         seal_checker = data.get('seal_checker', ''),
         dacs = data.get('dacs', ''),
         rcc = data.get('rcc', ''),
         terma_tira_semi_auto = data.get('terma_tira_semi_auto', ''),
         festo = data.get('festo', ''),
         hanco = data.get('hanco', ''),
         guacp = data.get('guacp', ''),
         pkg_manual = data.get('pkg_manual', ''),
         pkg_auto = data.get('pkg_auto', ''),
         pallet_auto = data.get('pallet_auto', ''),
         numero_da_ea = data.get('numero_da_ea', ''),
         pesadoras_mes = data.get('pesadoras_mes', ''),
         guacp_mes = data.get('guacp_mes', ''),
         estatus_revisado = data.get('estatus_revisado', ''),
         # Campo original
         asteriscos = data.get('asteriscos', '*****'),
         user_id = session.get('user_id')
    )
    db.session.add(nueva_linea)
    db.session.commit()
    return jsonify({'success': True, 'id': nueva_linea.id})

# Esta versión es la primera que aparece y debes mantenerla
@app.route('/actualizar_linea_planta/<int:linea_id>', methods=['PUT'])
def actualizar_linea_planta(linea_id):
    data = request.get_json()
    linea = LineaPlanta.query.get(linea_id)
    if not linea:
        return jsonify({'success': False, 'error': 'Línea no encontrada'})
    linea.bu = data.get('bu')
    linea.planta = data.get('planta')
    linea.categoria = data.get('categoria')
    linea.linea = data.get('linea')
    linea.marca = data.get('marca')
    linea.modelo = data.get('modelo')
    linea.pesadora = data.get('pesadora')
    linea.empacadora = data.get('empacadora')
    linea.high_speed = data.get('high_speed')
    # Nuevos campos
    linea.low_speed = data.get('low_speed', '')
    linea.seal_checker = data.get('seal_checker', '')
    linea.dacs = data.get('dacs', '')
    linea.rcc = data.get('rcc', '')
    linea.terma_tira_semi_auto = data.get('terma_tira_semi_auto', '')
    linea.festo = data.get('festo', '')
    linea.hanco = data.get('hanco', '')
    linea.guacp = data.get('guacp', '')
    linea.pkg_manual = data.get('pkg_manual', '')
    linea.pkg_auto = data.get('pkg_auto', '')
    linea.pallet_auto = data.get('pallet_auto', '')
    linea.numero_da_ea = data.get('numero_da_ea', '')
    linea.pesadoras_mes = data.get('pesadoras_mes', '')
    linea.guacp_mes = data.get('guacp_mes', '')
    linea.estatus_revisado = data.get('estatus_revisado', '')
    # Campo original
    linea.asteriscos = data.get('asteriscos', '*****')
    db.session.commit()
    return jsonify({'success': True, 'id': linea.id})

# ELIMINA ESTE SEGUNDO BLOQUE DUPLICADO
# @app.route('/actualizar_linea_planta/<int:linea_id>', methods=['PUT'])
# def actualizar_linea_planta(linea_id):
#     data = request.get_json()
#     linea = LineaPlanta.query.get(linea_id)
#     if not linea:
#         return jsonify({'success': False, 'error': 'Línea no encontrada'})
#     ...

@app.route('/borrar_linea_planta/<int:linea_id>', methods=['DELETE'])
def borrar_linea_planta(linea_id):
    linea = LineaPlanta.query.get(linea_id)
    if linea:
        db.session.delete(linea)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Línea no encontrada'})

@app.route('/get_lay_out_info')
def get_lay_out_info():
    try:
        bu = request.args.get('bu')
        plant = request.args.get('plant')
        if not bu or not plant:
            return jsonify({'error': 'Faltan parámetros'}), 400

        # Estandarizamos a mayúsculas
        bu = bu.upper()
        plant = plant.upper()

        # Filtrar por usuario (si no es admin, usa el de la sesión)
        if session.get('is_admin'):
            records = LineaPlanta.query.filter(
                db.func.upper(LineaPlanta.bu) == bu,
                db.func.upper(LineaPlanta.planta) == plant
            ).all()
        else:
            records = LineaPlanta.query.filter(
                db.func.upper(LineaPlanta.bu) == bu,
                db.func.upper(LineaPlanta.planta) == plant,
                LineaPlanta.user_id == session.get('user_id')
            ).all()

        print("Parámetros:", bu, plant)
        print("Registros encontrados:", len(records))
        data = []
        for r in records:
            # No usamos r.user directamente
            # En su lugar, buscamos el usuario por ID
            user_info = "Desconocido"
            if r.user_id:
                user = User.query.get(r.user_id)
                if user:
                    user_info = user.username
            
            data.append({
                'user': user_info,
                'categoria': r.categoria or "",
                'linea': r.linea or "",
                'marca': r.marca or "",
                'modelo': r.modelo or "",
                'pesadora': r.pesadora or "",
                'empacadora': r.empacadora or "",
                'high_speed': r.high_speed or "",
                # Nuevos campos
                'low_speed': r.low_speed or "",
                'seal_checker': r.seal_checker or "",
                'dacs': r.dacs or "",
                'rcc': r.rcc or "",
                'terma_tira_semi_auto': r.terma_tira_semi_auto or "",
                'festo': r.festo or "",
                'hanco': r.hanco or "",
                'guacp': r.guacp or "",
                'pkg_manual': r.pkg_manual or "",
                'pkg_auto': r.pkg_auto or "",
                'pallet_auto': r.pallet_auto or "",
                'numero_da_ea': r.numero_da_ea or "",
                'pesadoras_mes': r.pesadoras_mes or "",
                'guacp_mes': r.guacp_mes or "",
                'estatus_revisado': r.estatus_revisado or "",
                # Campo original
                'asteriscos': r.asteriscos or ""
            })
        return jsonify(data)
    except Exception as e:
        # Captura cualquier excepción y devuelve un JSON con el error
        import traceback
        print("ERROR en get_lay_out_info:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': 'Error interno: ' + str(e)}), 500
    
    ##########************************#####
### Rutas para comentarios de KPI
@app.route('/get_kpi_comments/<int:kpi_id>')
def get_kpi_comments(kpi_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Acceso restringido'}), 403
    
    comments = KpiComment.query.filter_by(kpi_id=kpi_id).first()
    if not comments:
        return jsonify({'success': True, 'comments': {}})
    
    return jsonify({
        'success': True,
        'comments': {
            'packing_efficiency': comments.packing_efficiency,
            'material_waste': comments.material_waste,
            'giveaway': comments.giveaway,
        }
    })

@app.route('/save_kpi_comments', methods=['POST'])
def save_kpi_comments():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Acceso restringido'}), 403
    
    data = request.get_json()
    kpi_id = data.get('kpi_id')
    user_id = data.get('user_id')
    month = int(data.get('month'))
    year = int(data.get('year'))
    
    # Si el KPI no existe pero tenemos user_id, month, year, intentar buscar
    if kpi_id == '0' and user_id:
        kpi = Kpi.query.filter_by(
            user_id=user_id,
            mes=month,
            anio=year
        ).first()
        
        if kpi:
            kpi_id = kpi.id
    
    # Si aún no hay KPI, devolver error
    if kpi_id == '0':
        return jsonify({'success': False, 'error': 'No se encontró KPI asociado'}), 400
    
    # Buscar comentario existente o crear uno nuevo
    comments = KpiComment.query.filter_by(kpi_id=kpi_id).first()
    if not comments:
        comments = KpiComment(kpi_id=kpi_id)
        db.session.add(comments)
    
    # Actualizar comentarios
    comments.packing_efficiency = data.get('packing_efficiency')
    comments.material_waste = data.get('material_waste')
    comments.giveaway = data.get('giveaway')
    comments.updated_at = datetime.datetime.now()
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'kpi_id': kpi_id
    })



# formato hora 
# --------------------------------------------------
# Función para formatear horas decimales a formato HH:MM
@app.template_filter('format_hours')
def format_hours(hours):
    """Convierte horas decimales a formato HH:MM:SS"""
    if hours is None:
        return ""
    
    hours_int = int(hours)
    minutes_decimal = (hours - hours_int) * 60
    minutes = int(minutes_decimal)
    seconds = int((minutes_decimal - minutes) * 60)
    
    return f"{hours_int}:{minutes:02d}:{seconds:02d}"


@app.route('/download_kpi_report', methods=['POST'])
def download_kpi_report():
    if not session.get('is_admin'):
        flash("Acceso restringido", "danger")
        return redirect(url_for('dashboard'))
    
    data_json = request.form.get('data', '{}')
    try:
        data = json.loads(data_json)
    except Exception as e:
        flash(f"Error al procesar datos: {str(e)}", "danger")
        return redirect(url_for('admin'))
    
    year = data.get('year')
    months = data.get('months', [])  # Lista de meses seleccionados
    bu = data.get('bu', 'TODOS')
    
    # Validar parámetros
    if not year or not months:
        return jsonify({'success': False, 'error': 'Se requiere año y al menos un mes'}), 400
    
    # Convertir meses a enteros
    months = [int(m) for m in months]
    year = int(year)
    
    # Construir la consulta
    query = Kpi.query.filter(Kpi.anio == year, Kpi.mes.in_(months))
    
    # Si se especifica una BU, filtrar por usuarios de esa BU
    if bu != 'TODOS':
        # Obtener IDs de usuarios de la BU seleccionada
        user_ids = [u.id for u in User.query.filter_by(bu=bu).all()]
        if user_ids:
            query = query.filter(Kpi.user_id.in_(user_ids))
    
    # Ejecutar consulta
    kpis = query.all()
    
    # Preparar datos para Excel
    data = []
    for kpi in kpis:
        user = User.query.get(kpi.user_id)
        if not user:
            continue
            
        # Obtener comentarios
        comments_obj = KpiComment.query.filter_by(kpi_id=kpi.id).first()
        comments = ""
        if comments_obj:
            comments_parts = []
            if comments_obj.packing_efficiency:
                comments_parts.append(f"Packing Efficiency: {comments_obj.packing_efficiency}")
            if comments_obj.material_waste:
                comments_parts.append(f"Material Waste: {comments_obj.material_waste}")
            if comments_obj.giveaway:
                comments_parts.append(f"Giveaway: {comments_obj.giveaway}")
            comments = " | ".join(comments_parts)
        
        # Determinar si algún KPI está fuera de objetivo
        fuera_objetivo = []
        if kpi.eficiencia_pesadora < 85:
            fuera_objetivo.append("Eficiencia Pesadora")
        if kpi.eficiencia_empaque < 85:
            fuera_objetivo.append("Eficiencia Empaque")
        if kpi.eficiencia_dme < 85:
            fuera_objetivo.append("Eficiencia DME")
        if kpi.sobre_gramaje > 5:  # Ejemplo, ajustar según sus criterios
            fuera_objetivo.append("Sobregramaje")
        
        # Formatear fecha
        month_names = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha = f"{month_names[kpi.mes-1]} {kpi.anio}"
        
        data.append({
            'Negocios': user.bu,
            'Pais': obtener_pais(user.plant),  # Función auxiliar para mapear planta a país
            'Planta': user.plant,
            'Linea': kpi.linea,
            'Fecha': fecha,
            'Eficiencia pesadora': kpi.eficiencia_pesadora,
            'Eficiencia Tubo Empaque': kpi.eficiencia_empaque,
            'Eficiencia DME': kpi.eficiencia_dme,
            'Sobregramaje': kpi.sobre_gramaje,
            'Eficiencia Guacp': kpi.eficiencia_guacp,
            'MTBF': kpi.mtbf,
            'MTTR': kpi.mttr,
            'Comentarios sobre KPI´s': comments,
            'Fuera de objetivo': ", ".join(fuera_objetivo) if fuera_objetivo else "No"
        })
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Generar Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte KPIs")
        
        # Obtener el objeto workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets["Reporte KPIs"]
        
        # Definir formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Aplicar formato a encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Ajustar ancho de columnas
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_kpis_{timestamp}.xlsx"
    
    return (output.read(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': f'attachment; filename="{filename}"'
    })

# Función auxiliar para mapear planta a país
def obtener_pais(planta):
    # Implementar mapeo de planta a país según tus datos
    # Esta es una versión simplificada, ajustar según sea necesario
    plantas_paises = {
        'Funza': 'Colombia',
        'Oriente': 'Colombia',
        'Quito': 'Ecuador',
        'Santa Anita': 'Perú',
        'Santa Cruz': 'Bolivia',
        'Barceloneta': 'Puerto Rico',
        'Guatemala': 'Guatemala',
        'Santo Domingo': 'República Dominicana',
        'Curitiba': 'Brasil',
        'Itaquera': 'Brasil',
        'ITU': 'Brasil',
        'Recife': 'Brasil',
        'Sete Lagoas': 'Brasil',
        'Sorocaba': 'Brasil',
        'Guadalajara': 'México',
        'Mexicali': 'México',
        'Obregón': 'México',
        'Saltillo': 'México',
        'Celaya': 'México',
        'Toluca': 'México',
        'Vallejo': 'México',
        'Veracruz': 'México',
        'Cerrillos': 'Chile',
        'Mar del Plata': 'Argentina'
    }
    
    return plantas_paises.get(planta, "No especificado")

# --------------------------------------------------
# EJECUCIÓN DE LA APLICACIÓN
# --------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)
