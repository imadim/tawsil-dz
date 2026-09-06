// Real-time tracking utilities
class OrderTracker {
    constructor(orderId, mapElementId) {
        this.orderId = orderId;
        this.mapElement = document.getElementById(mapElementId);
        this.socket = io();
        this.markers = {};
        this.initSocket();
    }
    
    initSocket() {
        this.socket.on('connect', () => {
            this.socket.emit('join_order', { order_id: this.orderId });
        });
        
        this.socket.on('driver_location', (data) => {
            this.updateDriverLocation(data.lat, data.lng);
        });
        
        this.socket.on('order_update', (data) => {
            this.updateOrderStatus(data.status);
        });
    }
    
    updateDriverLocation(lat, lng) {
        if (this.markers.driver) {
            this.markers.driver.setPosition({ lat, lng });
        }
        console.log(`Driver location updated: ${lat}, ${lng}`);
    }
    
    updateOrderStatus(status) {
        console.log(`Order status updated: ${status}`);
        const statusBadge = document.getElementById('orderStatus');
        if (statusBadge) {
            statusBadge.textContent = status;
        }
    }
}

// Export for use in other files
window.OrderTracker = OrderTracker;