// Socket.IO Connection
const socket = io();

socket.on('connect', () => {
    console.log('✅ Connected to server');
});

socket.on('disconnect', () => {
    console.log('❌ Disconnected from server');
});

// Load Notifications
function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            const notifList = document.getElementById('notificationList');
            const notifCount = document.getElementById('notifCount');
            
            if (data.length === 0) {
                notifList.innerHTML = '<p class="text-center text-muted">لا توجد إشعارات</p>';
                notifCount.textContent = '0';
                notifCount.style.display = 'none';
                return;
            }
            
            const unreadCount = data.filter(n => !n.is_read).length;
            notifCount.textContent = unreadCount;
            notifCount.style.display = unreadCount > 0 ? 'inline' : 'none';
            
            let html = '';
            data.forEach(notif => {
                html += `
                    <div class="alert alert-${notif.is_read ? 'secondary' : 'primary'} mb-2" 
                         onclick="markAsRead(${notif.id})">
                        <strong>${notif.title}</strong><br>
                        <small>${notif.message}</small><br>
                        <small class="text-muted">${new Date(notif.created_at).toLocaleString('ar')}</small>
                    </div>
                `;
            });
            
            notifList.innerHTML = html;
        });
}

function markAsRead(notifId) {
    fetch(`/api/notifications/${notifId}/read`, {
        method: 'POST'
    }).then(() => loadNotifications());
}

// Notification Bell Click
document.getElementById('notificationBell')?.addEventListener('click', (e) => {
    e.preventDefault();
    loadNotifications();
    new bootstrap.Modal(document.getElementById('notificationModal')).show();
});

// Load notifications on page load
if (document.getElementById('notificationBell')) {
    loadNotifications();
    setInterval(loadNotifications, 30000); // Refresh every 30 seconds
}

// Geolocation Helper
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                }),
                error => reject(error)
            );
        } else {
            reject(new Error('Geolocation not supported'));
        }
    });
}

// Auto-fill location in forms
document.addEventListener('DOMContentLoaded', () => {
    const addressField = document.getElementById('deliveryAddress');
    if (addressField) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-outline-primary mt-2';
        btn.innerHTML = '<i class="fas fa-map-marker-alt"></i> استخدم موقعي الحالي';
        btn.onclick = () => {
            getCurrentLocation()
                .then(location => {
                    addressField.value = `Lat: ${location.lat.toFixed(6)}, Lng: ${location.lng.toFixed(6)}`;
                    alert('تم تحديد موقعك!');
                })
                .catch(error => {
                    alert('لم نتمكن من الوصول لموقعك. يرجى التأكد من السماح بالوصول للموقع.');
                });
        };
        addressField.parentElement.appendChild(btn);
    }
});