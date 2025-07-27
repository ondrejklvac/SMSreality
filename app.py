from flask import Flask, render_template, url_for, flash, redirect, request, abort, session, jsonify, current_app
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os

from config import Config
from forms import (
    LoginForm, RegistrationForm, UpdateAccountForm,
    CheckoutForm, ProductForm, CategoryForm, ShippingForm
)
from models import (
    db, User, Product, Order,
    OrderItem, Cart, CartItem, Shipping
)

# —— TADY VYTVOŘTE A NAKONFIGURUJTE Flask a rozšíření ——
app = Flask(__name__)
app.config.from_object(Config)

# Nastavte UPLOAD_FOLDER až **po** vytvoření app
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Inicializujte DB a další rozšíření
db.init_app(app)
login_manager = LoginManager(app)
# … případně CSRFProtect(app), atd. …

# —— Následují vaše routy atd. ——

app = Flask(__name__)
app.config.from_object(Config)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # max 2 MB

# použijeme jedinou instanci SQLAlchemy z models.py
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Pro přístup k této stránce se musíte přihlásit.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    # v rámci kontextu aplikace vytvoříme tabulky
    app.before_request_funcs[None].remove(create_tables)
    db.create_all()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = Product.query.filter_by(is_active=True).paginate(page=page, per_page=per_page)
    products = pagination.items
    return render_template('index.html', products=products, pagination=pagination)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            password=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_password_set=True
        )
        db.session.add(user)
        db.session.commit()
        flash('Váš účet byl úspěšně vytvořen! Nyní se můžete přihlásit.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrace', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            flash('Uživatel s tímto e-mailem neexistuje.', 'danger')
            return render_template('login.html', title='Přihlášení', form=form)

        # >>> dočasně vypnuto, abychom mohli vždy spustit check_password_hash
        # if not user.is_password_set:
        #     session['user_email'] = user.email
        #     return redirect(url_for('set_password'))

        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Přihlášení bylo úspěšné!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Nesprávné heslo.', 'danger')

    return render_template('login.html', title='Přihlášení', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name  = form.last_name.data
        current_user.email      = form.email.data
        db.session.commit()
        flash('Váš profil byl aktualizován!', 'success')
        return redirect(url_for('profile'))
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data  = current_user.last_name
        form.email.data      = current_user.email
    return render_template('profile.html', title='Profil', form=form)

@app.route('/cart')
@login_required
def cart():
    # 1) Načteme nebo vytvoříme košík uživatele
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        # pokud uživatel zatím nemá košík, vytvoříme prázdný
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    # 2) Položky a součet
    cart_items = cart.items
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # 3) Metody dopravy
    shipping_methods = Shipping.query.all()
    # vybraná metoda (můžete nechat None, pokud ještě nevybráno)
    selected_shipping_method = session.get(
        'shipping_method',
        shipping_methods[0].id if shipping_methods else None
    )

    # 4) Základní adresa a poznámka (pokud je uložena v session)
    shipping_address = session.get('shipping_address', current_user.address)
    note             = session.get('note', '')

    return render_template(
        'cart.html',
        cart_items               = cart_items,
        total_price              = total_price,
        shipping_methods         = shipping_methods,
        selected_shipping_method = selected_shipping_method,
        shipping_address         = shipping_address,
        note                     = note
    )

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
    else:
        cart_id = session.get('cart_id')
        if cart_id:
            cart = Cart.query.get(cart_id)
        else:
            cart = Cart()
            db.session.add(cart)
            db.session.commit()
            session['cart_id'] = cart.id

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    db.session.commit()
    flash(f'{product.name} byl přidán do košíku!', 'success')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Položka byla odstraněna z košíku.', 'success')
    return redirect(url_for('cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            item_id  = int(key.split('_')[1])
            quantity = int(value)
            cart_item = CartItem.query.get(item_id)
            if cart_item:
                cart_item.quantity = quantity
    db.session.commit()
    flash('Košík byl aktualizován.', 'success')
    return redirect(url_for('cart'))

@app.route('/apply_credits', methods=['POST'])
@login_required
def apply_credits():
    # spočítáme původní cenu
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    total = sum(ci.product.price * ci.quantity for ci in cart.items)
    # kolik kreditů lze uplatnit
    to_apply = min(current_user.credits, total)
    # uložíme do session, aby to stále zůstalo
    session['applied_credits'] = to_apply
    flash(f'Uplatněno {to_apply} kreditů, cena se snížila o {to_apply} Kč.', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # načteme košík
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = cart.items if cart else []
    subtotal = sum(item.product.price * item.quantity for item in cart_items)

    # načteme dopravce
    shipping_methods = Shipping.query.all()
    selected_id = session.get('shipping_method',
                              shipping_methods[0].id if shipping_methods else None)
    chosen_shipping = Shipping.query.get(selected_id) if selected_id else None
    shipping_cost = chosen_shipping.price if chosen_shipping else 0

    # session-held hodnoty
    shipping_address = session.get('shipping_address', current_user.address)
    note             = session.get('note', '')
    applied_credits  = session.get('applied_credits', 0)

    # POST = buď uplatnit kredity, nebo potvrdit objednávku
    if request.method == 'POST':
        # uložíme vždy aktuální volby dopravy/ adresy/ poznámky
        session['shipping_method']  = int(request.form.get('shipping_method', selected_id))
        session['shipping_address'] = request.form.get('shipping_address', shipping_address)
        session['note']             = request.form.get('note', note)

        # 1) Uplatnit kredity?
        if 'apply_credits' in request.form:
            max_app = min(current_user.credits, subtotal + shipping_cost)
            session['applied_credits'] = max_app
            return redirect(url_for('checkout'))

        # 2) Potvrdit objednávku?
        if 'confirm_order' in request.form:
            # odečteme kredity z uživatele
            current_user.credits -= applied_credits
            # vytvoříme objednávku
            order = Order(
                user_id          = current_user.id,
                shipping_id      = selected_id,
                shipping_address = session['shipping_address'],
                total_price      = subtotal + shipping_cost,
                credits_used     = applied_credits,
                final_price      = subtotal + shipping_cost - applied_credits,
                note             = session.get('note',''),
                status           = 'new'
            )
            db.session.add(order)
            db.session.flush()
            # položky
            for item in cart_items:
                db.session.add(OrderItem(
                    order_id   = order.id,
                    product_id = item.product_id,
                    quantity   = item.quantity,
                    price      = item.product.price
                ))
            # vyprázdnit košík
            CartItem.query.filter_by(cart_id=cart.id).delete()
            db.session.commit()
            session.pop('applied_credits', None)
            flash('Objednávka byla úspěšně dokončena.', 'success')
            return redirect(url_for('index'))

    # výpočet celkové dlužné částky
    total_due = subtotal + shipping_cost - applied_credits

    return render_template(
        'checkout.html',
        cart_items       = cart_items,
        subtotal         = subtotal,
        shipping_methods = shipping_methods,
        chosen_shipping  = chosen_shipping,
        shipping_address = shipping_address,
        note             = note,
        applied_credits  = applied_credits,
        total_due        = total_due
    )

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def orders():
    page       = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=10)
    return render_template('orders.html', orders=pagination.items, pagination=pagination)
def order_history():
    # Načteme všechny objednávky přihlášeného uživatele
    orders = Order.query \
        .filter_by(user_id=current_user.id) \
        .order_by(Order.created_at.desc()) \
        .all()
    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('order_detail.html', order=order)

# — Admin routes —

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin/dashboard.html')

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        abort(403)
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

from werkzeug.utils import secure_filename

@app.route('/admin/product/new', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        abort(403)

    form = ProductForm()
    if request.method == 'POST':
        name        = request.form.get('name')
        description = request.form.get('description')
        price       = request.form.get('price')
        is_active   = 'is_active' in request.form

        # Validace vstupů
        if not name or not description or not price:
            flash('Název, popis a cena jsou povinné.', 'danger')
            return redirect(url_for('admin_products'))
        try:
            price = int(price)
        except ValueError:
            flash('Cena musí být číslo.', 'danger')
            return redirect(url_for('admin_products'))

        # Zpracování obrázku
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            # 1) Ujistíme se, že uploads složka existuje
            upload_folder = os.path.join(
                current_app.root_path, 'static', 'uploads'
            )
            os.makedirs(upload_folder, exist_ok=True)

            # 2) Bezpečné jméno a uložení
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(upload_folder, filename)
            image_file.save(save_path)
            image_filename = filename

        # Vytvoření produktu
        new_product = Product(
            name           = name,
            description    = description,
            price          = price,
            image_filename = image_filename,
            is_active      = is_active,
        )
        db.session.add(new_product)
        db.session.commit()

        flash('Produkt byl úspěšně přidán.', 'success')
        return redirect(url_for('admin_products'))

    # pokud GET, vykreslíme formulář
    return render_template('admin/product_new.html', form=form)

@app.route('/admin/product/<int:product_id>/edit', methods=['POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        abort(403)

    product = Product.query.get_or_404(product_id)
    # aktualizace polí
    product.name        = request.form['name']
    product.price       = int(request.form['price'])
    product.description = request.form['description']
    product.is_active   = 'is_active' in request.form

    # obrázek pokud byl nahrán
    image = request.files.get('image')
    if image and image.filename:
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        fn = secure_filename(image.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], fn)
        image.save(path)
        product.image_filename = fn

    # specifikace
    keys   = request.form.getlist('spec_keys[]')
    values = request.form.getlist('spec_values[]')
    product.specifications = {k: v for k, v in zip(keys, values) if k and v}

    db.session.commit()
    flash('Produkt byl upraven.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        abort(403)
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Produkt byl úspěšně odstraněn!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        abort(403)
    page       = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=20)
    return render_template('admin/orders.html', orders=pagination.items, pagination=pagination)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        abort(403)
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    if not current_user.is_admin:
        abort(403)
    order  = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    if status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = status
        db.session.commit()
        flash('Status objednávky byl aktualizován!', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/order/<int:order_id>/add_note', methods=['POST'])
@login_required
def admin_add_order_note(order_id):
    # jen admin může ukládat poznámky
    if not current_user.is_admin:
        abort(403)

    order = Order.query.get_or_404(order_id)
    # očekáváme <textarea name="admin_note"> v šabloně
    note = request.form.get('admin_note', '').strip()
    order.admin_note = note
    db.session.commit()

    flash('Interní poznámka byla uložena.', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/shipping', methods=['GET', 'POST'])
@login_required
def admin_shipping():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        # 1) Přidání nové metody
        if 'add' in request.form:
            name   = request.form['name']
            price  = int(request.form['price'])
            active = 'active' in request.form
            new = Shipping(name=name, price=price, active=active)
            db.session.add(new)
            db.session.commit()
            flash('Způsob dopravy přidán.', 'success')

        # 2) Úprava existující
        elif 'edit_id' in request.form:
            method = Shipping.query.get_or_404(int(request.form['edit_id']))
            method.name   = request.form['name']
            method.price  = int(request.form['price'])
            method.active = 'active' in request.form
            db.session.commit()
            flash('Způsob dopravy upraven.', 'success')

        # 3) Smazání
        elif 'delete_id' in request.form:
            method = Shipping.query.get_or_404(int(request.form['delete_id']))
            db.session.delete(method)
            db.session.commit()
            flash('Způsob dopravy smazán.', 'success')

        return redirect(url_for('admin_shipping'))

    # GET: načtení a vykreslení seznamu
    shipping_methods = Shipping.query.all()
    return render_template('admin/shipping.html', shipping_methods=shipping_methods)


@app.route('/admin/shipping/<int:shipping_id>/edit', methods=['POST'])
@login_required
def admin_edit_shipping(shipping_id):
    if not current_user.is_admin:
        abort(403)

    method = Shipping.query.get_or_404(shipping_id)
    method.name   = request.form.get('name', method.name)
    method.price  = int(request.form.get('price', method.price))
    method.active = 'active' in request.form
    db.session.commit()
    flash('Způsob dopravy upraven.', 'success')
    return redirect(url_for('admin_shipping'))


@app.route('/admin/shipping/<int:shipping_id>/delete', methods=['POST'])
@login_required
def admin_delete_shipping(shipping_id):
    if not current_user.is_admin:
        abort(403)

    method = Shipping.query.get_or_404(shipping_id)
    db.session.delete(method)
    db.session.commit()
    flash('Způsob dopravy byl úspěšně odstraněn!', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    form = RegistrationForm()
    return render_template('admin/users.html', users=users, form=form)

@app.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    # základní údaje
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name  = request.form.get('last_name',  user.last_name)
    user.email      = request.form.get('email',      user.email)
    user.address    = request.form.get('address',    user.address)
    # změna admin práv (s výjimkou sebe sama)
    if current_user.id != user.id:
        user.is_admin = 'is_admin' in request.form
    # změna hesla
    new_password = request.form.get('new_password', '').strip()
    if new_password:
        user.password = generate_password_hash(new_password)
        user.is_password_set = True

    db.session.commit()
    flash('Uživatel byl úspěšně upraven.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/credits', methods=['POST'])
@login_required
def admin_update_credits(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    try:
        amount = int(request.form.get('amount', 0))
        if action == "add":
            user.credits += amount
        elif action == "subtract":
            user.credits = max(user.credits - amount, 0)
        elif action == "set":
            user.credits = amount
        else:
            raise ValueError
        db.session.commit()
        flash(f'Kredity uživatele {user.email} aktualizovány.', 'success')
    except ValueError:
        flash('Neplatná hodnota kreditů.', 'danger')

    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    # Zabraň smazání sebe sama
    if user_id == current_user.id:
        flash('Nemůžete smazat sami sebe.', 'danger')
        return redirect(url_for('admin_users'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Uživatel {user.email} byl odstraněn.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/new', methods=['POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        abort(403)

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(
            first_name      = form.first_name.data,
            last_name       = form.last_name.data,
            email           = form.email.data,
            password        = hashed,
            is_admin        = bool(request.form.get('is_admin')),
            is_password_set = True,
            credits         = int(request.form.get('credits', 0)),
            address         = request.form.get('address', '')
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Uživatel {user.email} byl přidán.', 'success')
    else:
        errors = "; ".join(f"{fld}: {','.join(errs)}" for fld, errs in form.errors.items())
        flash(f'Chyba při přidávání uživatele: {errors}', 'danger')

    return redirect(url_for('admin_users'))



if __name__ == '__main__':
    # zajistí vytvoření nové tabulky shipping_method, pokud ještě neexistuje
    with app.app_context():
        db.create_all()
    app.run(debug=True)
