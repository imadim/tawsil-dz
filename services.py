"""Services for SMS, Payment, Firebase, Image Upload"""
import os
import requests
from PIL import Image
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import Config
import hashlib
import json


# ============================================
# IMAGE UPLOAD SERVICE
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_image(file, folder='general'):
    """Save and resize image, return URLs"""
    if not file or not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    # Create folders
    upload_path = os.path.join(Config.UPLOAD_FOLDER, folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save original
    filepath = os.path.join(upload_path, filename)
    file.save(filepath)
    
    try:
        # Create thumbnail
        img = Image.open(filepath)
        img.thumbnail(Config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumbnail_name = f"thumb_{filename}"
        thumbnail_path = os.path.join(upload_path, thumbnail_name)
        img.save(thumbnail_path, quality=85, optimize=True)
        
        # Create medium size
        img = Image.open(filepath)
        img.thumbnail(Config.MEDIUM_SIZE, Image.Resampling.LANCZOS)
        medium_name = f"medium_{filename}"
        medium_path = os.path.join(upload_path, medium_name)
        img.save(medium_path, quality=85, optimize=True)
        
        return {
            'original': f'/static/uploads/{folder}/{filename}',
            'medium': f'/static/uploads/{folder}/{medium_name}',
            'thumbnail': f'/static/uploads/{folder}/{thumbnail_name}'
        }
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return {
            'original': f'/static/uploads/{folder}/{filename}',
            'medium': f'/static/uploads/{folder}/{filename}',
            'thumbnail': f'/static/uploads/{folder}/{filename}'
        }


# ============================================
# SMS SERVICE (Disabled by default)
# ============================================

def send_sms(phone, message):
    """Send SMS - DISABLED for testing"""
    # Check if SMS is enabled
    if not Config.SMS_ENABLED:
        print(f"📱 SMS (DISABLED): To {phone}: {message}")
        return True  # Return success for testing
    
    try:
        response = requests.post(
            Config.SMS_API_URL,
            json={
                'api_key': Config.SMS_API_KEY,
                'sender': Config.SMS_SENDER,
                'to': phone,
                'message': message
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ SMS sent to {phone}")
            return True
        else:
            print(f"❌ SMS failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False


def send_verification_sms(user):
    """Send verification code via SMS"""
    code = user.generate_sms_code()
    message = f"كود التحقق ديالك في توصيل DZ: {code}\nالكود صالح لمدة 10 دقايق"
    
    # For testing: just print the code
    print(f"\n{'='*50}")
    print(f"📱 SMS VERIFICATION CODE for {user.phone}")
    print(f"{'='*50}")
    print(f"   CODE: {code}")
    print(f"{'='*50}\n")
    
    return send_sms(user.phone, message)


# ============================================
# PAYMENT SERVICE (Enhanced for Algeria)
# ============================================

class PaymentService:
    
    @staticmethod
    def validate_card_number(card_number):
        """Validate card number using Luhn algorithm"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if not card_number.isdigit():
            return False
        
        if len(card_number) != 16:
            return False
        
        # Luhn algorithm
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        return luhn_checksum(card_number) == 0
    
    @staticmethod
    def get_card_type(card_number):
        """Detect card type (CIB, Edahabia, Visa, etc.)"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        # Algerian CIB cards typically start with specific BINs
        if card_number.startswith('9272'):
            return 'cib'
        # Edahabia cards
        elif card_number.startswith('9275'):
            return 'edahabia'
        # Visa
        elif card_number.startswith('4'):
            return 'visa'
        # Mastercard
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'mastercard'
        else:
            return 'unknown'
    
    @staticmethod
    def process_card_payment(order, card_details):
        """Process card payment (unified method)"""
        try:
            # Validate card number
            if not PaymentService.validate_card_number(card_details['card_number']):
                return False, "رقم البطاقة غير صحيح"
            
            # Get card type
            card_type = PaymentService.get_card_type(card_details['card_number'])
            
            # Route to appropriate processor
            if card_type == 'cib':
                return PaymentService.process_cib_payment(order, card_details)
            elif card_type == 'edahabia':
                return PaymentService.process_edahabia_payment(order, card_details)
            else:
                return PaymentService.process_international_card(order, card_details)
                
        except Exception as e:
            print(f"❌ Card payment error: {e}")
            return False, f"خطأ في الدفع: {str(e)}"
    
    @staticmethod
    def process_cib_payment(order, card_details):
        """Process CIB payment"""
        if not Config.PAYMENT_ENABLED:
            print(f"💳 CIB Payment (MOCK): {order.final_amount} DZD for order {order.order_number}")
            # Simulate success for testing
            transaction_id = f"CIB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order.id}"
            order.payment_status = 'paid'
            order.payment_method = 'cib_card'
            order.payment_transaction_id = transaction_id
            
            # Log payment details (for testing)
            print(f"\n{'='*50}")
            print(f"💳 CIB PAYMENT DETAILS")
            print(f"{'='*50}")
            print(f"   Order: {order.order_number}")
            print(f"   Amount: {order.final_amount} DZD")
            print(f"   Card: {card_details['card_number'][-4:]}")
            print(f"   Transaction: {transaction_id}")
            print(f"{'='*50}\n")
            
            return True, transaction_id
        
        try:
            # Real CIB payment API integration
            response = requests.post(
                Config.CIB_PAYMENT_URL,
                json={
                    'merchant_id': Config.CIB_MERCHANT_ID,
                    'api_key': Config.CIB_API_KEY,
                    'amount': int(order.final_amount * 100),  # Convert to cents
                    'currency': 'DZD',
                    'order_id': order.order_number,
                    'card_number': card_details['card_number'],
                    'card_expiry_month': card_details['expiry_month'],
                    'card_expiry_year': card_details['expiry_year'],
                    'card_cvv': card_details['cvv'],
                    'cardholder_name': card_details.get('cardholder_name', ''),
                },
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') == 'success' or data.get('approved'):
                transaction_id = data.get('transaction_id') or data.get('reference')
                order.payment_status = 'paid'
                order.payment_method = 'cib_card'
                order.payment_transaction_id = transaction_id
                return True, transaction_id
            else:
                error_msg = data.get('error') or data.get('message', 'فشل الدفع')
                return False, error_msg
                
        except requests.Timeout:
            return False, "انتهت مهلة الاتصال بالبنك"
        except Exception as e:
            print(f"❌ CIB Payment error: {e}")
            return False, f"خطأ في الدفع: {str(e)}"
    
    @staticmethod
    def process_edahabia_payment(order, card_details):
        """Process Edahabia payment"""
        if not Config.PAYMENT_ENABLED:
            print(f"💳 Edahabia Payment (MOCK): {order.final_amount} DZD for order {order.order_number}")
            transaction_id = f"EDAH_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order.id}"
            order.payment_status = 'paid'
            order.payment_method = 'edahabia'
            order.payment_transaction_id = transaction_id
            
            print(f"\n{'='*50}")
            print(f"💳 EDAHABIA PAYMENT DETAILS")
            print(f"{'='*50}")
            print(f"   Order: {order.order_number}")
            print(f"   Amount: {order.final_amount} DZD")
            print(f"   Card: ****{card_details['card_number'][-4:]}")
            print(f"   Transaction: {transaction_id}")
            print(f"{'='*50}\n")
            
            return True, transaction_id
        
        try:
            # Real Edahabia payment API
            response = requests.post(
                Config.EDAHABIA_PAYMENT_URL,
                json={
                    'merchant_id': Config.EDAHABIA_MERCHANT_ID,
                    'api_key': Config.EDAHABIA_API_KEY,
                    'amount': int(order.final_amount),
                    'currency': 'DZD',
                    'order_reference': order.order_number,
                    'card_number': card_details['card_number'],
                    'card_pin': card_details.get('pin', ''),  # Edahabia uses PIN
                },
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') == 'success':
                transaction_id = data.get('transaction_id')
                order.payment_status = 'paid'
                order.payment_method = 'edahabia'
                order.payment_transaction_id = transaction_id
                return True, transaction_id
            else:
                return False, data.get('error', 'فشل الدفع')
                
        except Exception as e:
            print(f"❌ Edahabia Payment error: {e}")
            return False, str(e)
    
    @staticmethod
    def process_international_card(order, card_details):
        """Process international cards (Visa, Mastercard)"""
        if not Config.PAYMENT_ENABLED:
            print(f"💳 International Card Payment (MOCK): {order.final_amount} DZD")
            transaction_id = f"INTL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order.id}"
            order.payment_status = 'paid'
            order.payment_method = 'international_card'
            order.payment_transaction_id = transaction_id
            return True, transaction_id
        
        # Use international payment gateway (Stripe, PayPal, etc.)
        return False, "البطاقات الدولية غير مدعومة حالياً"
    
    @staticmethod
    def verify_payment(transaction_id):
        """Verify payment status"""
        if not Config.PAYMENT_ENABLED:
            return True, "Payment verified (MOCK)"
        
        # Verify with payment gateway
        try:
            # Check CIB
            response = requests.get(
                f"{Config.CIB_PAYMENT_URL}/verify/{transaction_id}",
                headers={'Authorization': f'Bearer {Config.CIB_API_KEY}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'success', data.get('message')
                
        except Exception as e:
            print(f"❌ Payment verification error: {e}")
        
        return False, "فشل التحقق من الدفع"


# ============================================
# FIREBASE PUSH NOTIFICATIONS
# ============================================

class FirebaseService:
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase"""
        if not Config.FIREBASE_ENABLED:
            print("🔥 Firebase: DISABLED (Testing Mode)")
            cls._initialized = False
            return
        
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            if not cls._initialized and os.path.exists(Config.FIREBASE_CREDENTIALS):
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                print("✅ Firebase initialized")
        except Exception as e:
            print(f"⚠️ Firebase init error: {e}")
            cls._initialized = False
    
    @staticmethod
    def send_push_notification(user, title, body, data=None):
        """Send push notification"""
        if not Config.FIREBASE_ENABLED:
            print(f"\n{'='*50}")
            print(f"🔔 PUSH NOTIFICATION (MOCK)")
            print(f"{'='*50}")
            print(f"   To: {user.username}")
            print(f"   Title: {title}")
            print(f"   Body: {body}")
            if data:
                print(f"   Data: {json.dumps(data, ensure_ascii=False)}")
            print(f"{'='*50}\n")
            return True
        
        if not user.fcm_token:
            print(f"⚠️ User {user.username} has no FCM token")
            return False
        
        try:
            from firebase_admin import messaging
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=user.fcm_token
            )
            
            response = messaging.send(message)
            print(f"✅ Push sent to {user.username}: {response}")
            return True
            
        except Exception as e:
            print(f"❌ Push notification error: {e}")
            return False
    
    @staticmethod
    def send_order_notification(order, title, body):
        """Send notification about order"""
        from models import db, Notification
        
        # Send push to customer
        FirebaseService.send_push_notification(
            order.customer,
            title,
            body,
            data={
                'type': 'order_update',
                'order_id': str(order.id),
                'order_number': order.order_number,
                'status': order.status
            }
        )
        
        # Create in-app notification
        notif = Notification(
            user_id=order.customer_id,
            title=title,
            message=body,
            order_id=order.id,
            is_pushed=True
        )
        db.session.add(notif)
        db.session.commit()


# ============================================
# RATING SERVICE
# ============================================

class RatingService:
    
    @staticmethod
    def add_restaurant_review(order, ratings, comment):
        """Add restaurant review and update rating"""
        from models import db, RestaurantReview, Restaurant
        
        # Calculate overall rating
        overall = (ratings['food'] + ratings['service'] + ratings['delivery_time']) / 3
        
        review = RestaurantReview(
            order_id=order.id,
            customer_id=order.customer_id,
            restaurant_id=order.restaurant_id,
            food_rating=ratings['food'],
            service_rating=ratings['service'],
            delivery_time_rating=ratings['delivery_time'],
            overall_rating=round(overall),
            comment=comment
        )
        
        db.session.add(review)
        
        # Update restaurant rating
        restaurant = Restaurant.query.get(order.restaurant_id)
        
        # Calculate new average
        all_reviews = RestaurantReview.query.filter_by(restaurant_id=restaurant.id).all()
        if all_reviews:
            avg_rating = sum(r.overall_rating for r in all_reviews) / len(all_reviews)
            restaurant.rating = round(avg_rating, 1)
        
        db.session.commit()
        
        return review
    
    @staticmethod
    def add_driver_review(order, ratings, comment):
        """Add driver review and update rating"""
        from models import db, DriverReview, User
        
        # Calculate overall rating
        overall = (ratings['professionalism'] + ratings['speed'] + ratings['communication']) / 3
        
        review = DriverReview(
            order_id=order.id,
            customer_id=order.customer_id,
            driver_id=order.driver_id,
            professionalism_rating=ratings['professionalism'],
            speed_rating=ratings['speed'],
            communication_rating=ratings['communication'],
            overall_rating=round(overall),
            comment=comment
        )
        
        db.session.add(review)
        
        # Update driver rating
        driver = User.query.get(order.driver_id)
        
        # Calculate new average
        all_reviews = DriverReview.query.filter_by(driver_id=driver.id).all()
        if all_reviews:
            avg_rating = sum(r.overall_rating for r in all_reviews) / len(all_reviews)
            # Assuming you have these fields in User model for drivers
            if hasattr(driver, 'driver_rating'):
                driver.driver_rating = round(avg_rating, 1)
        
        db.session.commit()
        
        return review


# ============================================
# UTILITY FUNCTIONS
# ============================================

def mask_card_number(card_number):
    """Mask card number for display"""
    card_number = card_number.replace(' ', '').replace('-', '')
    return f"****-****-****-{card_number[-4:]}"


def format_card_expiry(expiry):
    """Format card expiry date"""
    if '/' in expiry:
        return expiry
    if len(expiry) == 4:
        return f"{expiry[:2]}/{expiry[2:]}"
    return expiry