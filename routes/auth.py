@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'customer')
        wilaya = request.form.get('wilaya', 'Alger')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('هذا الإيميل مستعمل', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            phone=phone,
            role=role,
            wilaya=wilaya,
            commune=request.form.get('commune', '')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # If role is restaurant, create restaurant profile
        if role == 'restaurant':
            restaurant_name_ar = request.form.get('restaurant_name_ar')
            restaurant_name_en = request.form.get('restaurant_name_en', restaurant_name_ar)
            description_ar = request.form.get('description_ar')
            restaurant_address = request.form.get('restaurant_address')
            restaurant_wilaya = request.form.get('restaurant_wilaya')
            commune = request.form.get('commune')
            restaurant_phone = request.form.get('restaurant_phone')
            latitude = request.form.get('latitude', 36.7538)
            longitude = request.form.get('longitude', 3.0588)
            
            # Validate required restaurant fields
            if not all([restaurant_name_ar, description_ar, restaurant_address, 
                       restaurant_wilaya, commune, restaurant_phone]):
                flash('يرجى ملء جميع الحقول المطلوبة للمطعم', 'danger')
                db.session.rollback()
                return redirect(url_for('register'))
            
            # Handle image upload
            image_url = None
            if 'restaurant_image' in request.files:
                file = request.files['restaurant_image']
                if file and file.filename:
                    from werkzeug.utils import secure_filename
                    import uuid
                    
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join(current_dir, 'static', 'images', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    filepath = os.path.join(upload_dir, unique_filename)
                    file.save(filepath)
                    image_url = f"/static/images/uploads/{unique_filename}"
            
            # Create restaurant
            restaurant = Restaurant(
                user_id=user.id,
                name=restaurant_name_en,
                name_ar=restaurant_name_ar,
                description_ar=description_ar,
                address=restaurant_address,
                wilaya=restaurant_wilaya,
                commune=commune,
                phone=restaurant_phone,
                latitude=float(latitude),
                longitude=float(longitude),
                is_open=True,
                rating=0.0
            )
            
            db.session.add(restaurant)
        
        # Commit everything
        db.session.commit()
        
        flash('تسجيلك تم بنجاح! أدخّل ', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', wilayas=WILAYAS)