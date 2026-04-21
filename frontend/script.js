const API_BASE = 'http://127.0.0.1:5000/api';

// Helper function to make authenticated requests
async function apiFetch(endpoint, options = {}) {
    options.credentials = 'include';
    if (options.body && !options.headers) {
        options.headers = { 'Content-Type': 'application/json' };
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    return response;
}

// Check auth on page load (unless we are on the login page)
async function checkAuth() {
    const isLoginPage = window.location.pathname.endsWith('login.html');
    try {
        const res = await apiFetch('/check_auth');
        if (res.status === 401 && !isLoginPage) {
            window.location.href = 'login.html';
        } else if (res.status === 200 && isLoginPage) {
            window.location.href = 'index.html';
        }
    } catch (e) {
        console.error("Auth check failed", e);
    }
}

// Handle Logout
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await apiFetch('/logout', { method: 'POST' });
        window.location.href = 'login.html';
    });
}

// -----------------------------------------
// Page Specific Logic
// -----------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();

    // LOGIN PAGE
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await apiFetch('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.success) {
                window.location.href = 'index.html';
            } else {
                const flashContainer = document.getElementById('flash-container');
                const flashError = document.getElementById('flash-error');
                flashContainer.style.display = 'block';
                flashError.textContent = data.message || 'Login failed';
            }
        });
    }

    // DASHBOARD PAGE
    const statActive = document.getElementById('stat-active');
    if (statActive) {
        const res = await apiFetch('/dashboard');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stat-active').textContent = data.stats.active;
            document.getElementById('stat-permanent').textContent = data.stats.permanent;
            document.getElementById('stat-temporary').textContent = data.stats.temporary;
            document.getElementById('stat-separated').textContent = data.stats.separated;

            const tbody = document.getElementById('activities-table-body');
            tbody.innerHTML = '';
            data.activities.forEach(log => {
                tbody.innerHTML += `
                    <tr>
                        <td>${log.id}</td>
                        <td>${log.activity}</td>
                        <td>${log.employee}</td>
                        <td>${log.date}</td>
                    </tr>
                `;
            });
        }
    }

    // EMPLOYEES PAGE
    const employeesTableBody = document.getElementById('employees-table-body');
    if (employeesTableBody) {
        const loadEmployees = async (search = '') => {
            const res = await apiFetch(`/employees?search=${encodeURIComponent(search)}`);
            if (res.ok) {
                const data = await res.json();
                employeesTableBody.innerHTML = '';
                data.employees.forEach(emp => {
                    employeesTableBody.innerHTML += `
                        <tr>
                            <td>${emp.id}</td>
                            <td>${emp.last_name}</td>
                            <td>${emp.first_name}</td>
                            <td>
                                <span class="status-${emp.status.toLowerCase()}">${emp.status}</span>
                            </td>
                            <td>
                                <button class="btn-action btn-delete" onclick="deleteEmployee(${emp.id})">Delete</button>
                            </td>
                        </tr>
                    `;
                });
            }
        };

        // Expose delete to window so inline onclick works
        window.deleteEmployee = async (id) => {
            if (confirm("Are you sure you want to delete this employee?")) {
                await apiFetch(`/delete/${id}`, { method: 'DELETE' });
                loadEmployees();
            }
        };

        loadEmployees();

        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    loadEmployees(e.target.value);
                }
            });
        }
    }

    // ADD EMPLOYEE PAGE
    const addEmployeeForm = document.getElementById('addEmployeeForm');
    if (addEmployeeForm) {
        addEmployeeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const first_name = document.getElementById('first_name').value;
            const last_name = document.getElementById('last_name').value;
            const status = document.getElementById('status').value;
            
            const res = await apiFetch('/add', {
                method: 'POST',
                body: JSON.stringify({ first_name, last_name, status })
            });
            
            if (res.ok) {
                window.location.href = 'employees.html';
            }
        });
    }
});
