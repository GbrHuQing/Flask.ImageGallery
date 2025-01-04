const API_BASE_URL = 'http://localhost:5000/api';

class FormValidator {
    static validateUsername(username) {
        const regex = /^[a-zA-Z0-9_]{4,20}$/;
        return regex.test(username);
    }

    static validatePassword(password) {
        return password.length >= 6 && password.length <= 20;
    }

    static validateConfirmPassword(password, confirmPassword) {
        return password === confirmPassword;
    }
}

class NotificationManager {
    static show(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification-${type}`;
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

class ApiService {
    static async request(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            return await response.json();
        } catch (error) {
            console.error('API请求错误:', error);
            throw new Error('网络请求失败');
        }
    }

    static async login(username, password) {
        return await this.request('/login', { username, password });
    }

    static async register(username, password) {
        return await this.request('/register', { username, password });
    }
}

// 表单切换逻辑
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.form').forEach(form => form.classList.remove('active'));
        
        button.classList.add('active');
        document.getElementById(`${button.dataset.form}Form`).classList.add('active');
    });
});

// 登录表单处理
document.querySelector('#loginForm form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        if (!FormValidator.validateUsername(username)) {
            throw new Error('用户名格式不正确');
        }

        const response = await ApiService.login(username, password);
        if (response.success) {
            NotificationManager.show('登录成功', 'success');
            // 登录成功后跳转到图片预览页面
            window.location.href = '/gallery.html';
        } else {
            NotificationManager.show(response.message, 'error');
        }
    } catch (error) {
        NotificationManager.show(error.message, 'error');
    }
});

// 注册表单处理
document.querySelector('#registerForm form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    try {
        if (!FormValidator.validateUsername(username)) {
            throw new Error('用户名必须是4-20位字母、数字或下划线');
        }

        if (!FormValidator.validatePassword(password)) {
            throw new Error('密码长度必须在6-20位之间');
        }

        if (!FormValidator.validateConfirmPassword(password, confirmPassword)) {
            throw new Error('两次输入的密码不一致');
        }

        const response = await ApiService.register(username, password);
        if (response.success) {
            NotificationManager.show('注册成功', 'success');
            // 注册成功后自动切换到登录表单
            document.querySelector('[data-form="login"]').click();
        } else {
            NotificationManager.show(response.message, 'error');
        }
    } catch (error) {
        NotificationManager.show(error.message, 'error');
    }
}); 