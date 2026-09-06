"""
نموذج الطلب المُحسّن - مع GPS + التحقق + المدفوعات
"""
from datetime import datetime
import random
import string
import secrets


class Order:
    """فئة الطلب المُحسّنة"""
    
    # حالات الطلب
    STATUS_RECEIVED = 'received'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_ARRIVED = 'arrived'              # ✅ جديد: وصل للعنوان
    STATUS_VERIFYING = 'verifying'          # ✅ جديد: انتظار كود التحقق
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    
    # طرق الدفع
    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_ONLINE = 'online'
    
    # حالات الدفع
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    
    def __init__(self, customer_name, customer_phone, customer_address, 
                 customer_location, items, total, payment_method='cash'):
        self.order_id = self._generate_order_id()
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_address = customer_address
        self.customer_location = customer_location  # ✅ موقع GPS للعميل
        self.items = items
        self.total = total
        
        # ✅ معلومات الدفع
        self.payment_method = payment_method
        self.payment_status = self.PAYMENT_STATUS_PENDING
        self.payment_transaction_id = None
        
        # عمولة المنصة والسائق
        self.platform_commission = total * 0.10  # 10% للمنصة
        self.delivery_fee = 200  # رسوم التوصيل
        self.driver_commission = self.delivery_fee * 0.80  # 80% للسائق
        self.restaurant_amount = total - self.platform_commission
        
        self.status = self.STATUS_RECEIVED
        self.driver_id = None
        self.driver_name = None
        self.driver_phone = None
        self.driver_location = None
        
        # ✅ كود التحقق (OTP)
        self.verification_code = self._generate_verification_code()
        self.is_verified = False
        
        self.restaurant_location = {'lat': 36.7538, 'lng': 3.0588}
        self.created_at = datetime.now()
        self.delivered_at = None
        self.estimated_time = 30
        
        # ✅ تتبع المسار
        self.route_history = []  # سجل حركة السائق
        
        self.timeline = [
            {
                'status': self.STATUS_RECEIVED,
                'timestamp': datetime.now().isoformat(),
                'message': 'تم استلام طلبك'
            }
        ]
    
    def _generate_order_id(self):
        """توليد رقم طلب"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f'ORD-{timestamp}-{random_str}'
    
    def _generate_verification_code(self):
        """توليد كود تحقق من 4 أرقام"""
        return ''.join(random.choices(string.digits, k=4))
    
    def update_status(self, new_status, message=None):
        """تحديث حالة الطلب"""
        self.status = new_status
        
        if message is None:
            status_messages = {
                self.STATUS_PREPARING: 'جاري تحضير طلبك',
                self.STATUS_READY: 'طلبك جاهز للتوصيل',
                self.STATUS_PICKED_UP: 'السائق استلم طلبك',
                self.STATUS_IN_TRANSIT: 'طلبك في الطريق إليك',
                self.STATUS_ARRIVED: 'السائق وصل! تحقق من الكود',
                self.STATUS_VERIFYING: 'جاري التحقق من الكود',
                self.STATUS_DELIVERED: 'تم توصيل طلبك بنجاح',
                self.STATUS_CANCELLED: 'تم إلغاء الطلب'
            }
            message = status_messages.get(new_status, 'تحديث حالة الطلب')
        
        self.timeline.append({
            'status': new_status,
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
    
    def assign_driver(self, driver_id, driver_name, driver_phone):
        """تعيين سائق"""
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.driver_phone = driver_phone
        self.timeline.append({
            'status': 'driver_assigned',
            'timestamp': datetime.now().isoformat(),
            'message': f'تم تعيين السائق: {driver_name}'
        })
    
    def update_driver_location(self, lat, lng):
        """تحديث موقع السائق + حفظ المسار"""
        self.driver_location = {'lat': lat, 'lng': lng}
        
        # حفظ في سجل المسار
        self.route_history.append({
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.now().isoformat()
        })
    
    def verify_code(self, entered_code):
        """التحقق من الكود"""
        if entered_code == self.verification_code:
            self.is_verified = True
            self.status = self.STATUS_DELIVERED
            self.delivered_at = datetime.now()
            
            # ✅ تحديث حالة الدفع إذا كان كاش
            if self.payment_method == self.PAYMENT_CASH:
                self.payment_status = self.PAYMENT_STATUS_PAID
            
            self.update_status(self.STATUS_DELIVERED, 'تم التوصيل بنجاح')
            return True
        return False
    
    def process_payment(self, transaction_id=None):
        """معالجة الدفع"""
        if self.payment_method == self.PAYMENT_CASH:
            # الدفع نقداً عند التوصيل
            self.payment_status = self.PAYMENT_STATUS_PAID
            self.payment_transaction_id = f"CASH-{self.order_id}"
        else:
            # الدفع الإلكتروني
            self.payment_status = self.PAYMENT_STATUS_PAID
            self.payment_transaction_id = transaction_id
        
        return True
    
    def calculate_payouts(self):
        """حساب توزيع الأموال"""
        return {
            'total_order': self.total,
            'delivery_fee': self.delivery_fee,
            'grand_total': self.total + self.delivery_fee,
            
            # التوزيع:
            'restaurant_gets': self.restaurant_amount,
            'driver_gets': self.driver_commission,
            'platform_gets': self.platform_commission + (self.delivery_fee - self.driver_commission),
            
            # التفاصيل:
            'breakdown': {
                'platform_commission': f"{self.platform_commission:.2f} دج (10% من الطلب)",
                'driver_delivery': f"{self.driver_commission:.2f} دج (80% من رسوم التوصيل)",
                'platform_delivery': f"{self.delivery_fee - self.driver_commission:.2f} دج (20% من رسوم التوصيل)"
            }
        }
    
    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'customer_location': self.customer_location,
            'items': self.items,
            'total': self.total,
            'delivery_fee': self.delivery_fee,
            'grand_total': self.total + self.delivery_fee,
            
            # الدفع
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'payment_transaction_id': self.payment_transaction_id,
            
            'status': self.status,
            'driver_id': self.driver_id,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'driver_location': self.driver_location,
            
            # التحقق
            'verification_code': self.verification_code if not self.is_verified else None,
            'is_verified': self.is_verified,
            
            'restaurant_location': self.restaurant_location,
            'estimated_time': self.estimated_time,
            'created_at': self.created_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'timeline': self.timeline,
            'route_history': self.route_history,
            
            # الحسابات المالية
            'payouts': self.calculate_payouts()
        }


class OrderStore:
    """مخزن الطلبات"""
    
    def __init__(self):
        self.orders = {}
    
    def create_order(self, customer_name, customer_phone, customer_address, 
                     customer_location, items, total, payment_method='cash'):
        """إنشاء طلب جديد"""
        order = Order(customer_name, customer_phone, customer_address, 
                     customer_location, items, total, payment_method)
        self.orders[order.order_id] = order
        return order
    
    def get_order(self, order_id):
        """الحصول على طلب"""
        return self.orders.get(order_id)
    
    def get_all_orders(self):
        """الحصول على كل الطلبات"""
        return list(self.orders.values())
    
    def get_active_orders(self):
        """الطلبات النشطة"""
        return [
            order for order in self.orders.values()
            if order.status not in [Order.STATUS_DELIVERED, Order.STATUS_CANCELLED]
        ]
    
    def get_driver_orders(self, driver_id):
        """طلبات سائق معين"""
        return [
            order for order in self.orders.values()
            if order.driver_id == driver_id and order.status != Order.STATUS_DELIVERED
        ]
    
    def verify_order(self, order_id, verification_code):
        """التحقق من كود الطلب"""
        order = self.get_order(order_id)
        if order:
            return order.verify_code(verification_code)
        return False


# مثيل عام
order_store = OrderStore()