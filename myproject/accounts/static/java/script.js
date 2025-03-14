// Dashboard initialization
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('dashboard')) {
        initializeDashboard();
        updateDashboardStats();
    }

    // Initialize incident form handlers
    const incidentForm = document.getElementById('incidentForm');
    if (incidentForm) {
        initializeIncidentForm();
    }

    // Initialize search functionality
    const searchInput = document.getElementById('searchIncidents');
    if (searchInput) {
        initializeSearch();
    }

    // Auto-calculate elapsed times when dates change
    const discoveryDateInput = document.querySelector('input[name="discovery_date"]');
    const incidentDateInput = document.querySelector('input[name="incident_date"]');
    const containmentDateInput = document.querySelector('input[name="containment_date"]');
    
    function calculateElapsedTime(start, end) {
        if (!start || !end) return "Not available";
        const elapsed = new Date(end) - new Date(start);
        const days = Math.floor(elapsed / (1000 * 60 * 60 * 24));
        const hours = Math.floor((elapsed % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
        return `${days} days, ${hours} hours, ${minutes} minutes`;
    }
    
    function updateElapsedTimes() {
        const discoveryDate = discoveryDateInput.value;
        const incidentDate = incidentDateInput.value;
        const containmentDate = containmentDateInput.value;
        
        // Update time to discovery
        const timeToDiscoveryElement = document.getElementById('elapsed_time_to_discovery');
        if (timeToDiscoveryElement && incidentDate && discoveryDate) {
            timeToDiscoveryElement.value = calculateElapsedTime(incidentDate, discoveryDate);
        }
        
        // Update time to restoration
        const timeToRestorationElement = document.getElementById('elapsed_time_to_restoration');
        if (timeToRestorationElement && discoveryDate && containmentDate) {
            timeToRestorationElement.value = calculateElapsedTime(discoveryDate, containmentDate);
        }
    }
    
    // Add event listeners
    if (discoveryDateInput) discoveryDateInput.addEventListener('change', updateElapsedTimes);
    if (incidentDateInput) incidentDateInput.addEventListener('change', updateElapsedTimes);
    if (containmentDateInput) containmentDateInput.addEventListener('change', updateElapsedTimes);
});

function initializeDashboard() {
    // Monthly incidents chart
    const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    new Chart(monthlyCtx, {
        type: 'line',
        data: {
            labels: getLastTwelveMonths(),
            datasets: [{
                label: 'Monthly Incidents',
                data: [12, 19, 3, 5, 2, 3, 7, 8, 9, 10, 11, 4],
                borderColor: '#007bff',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Incident types chart
    const typesCtx = document.getElementById('typesChart').getContext('2d');
    new Chart(typesCtx, {
        type: 'doughnut',
        data: {
            labels: ['Safety', 'Security', 'Environmental', 'Other'],
            datasets: [{
                data: [30, 25, 20, 25],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#ffc107',
                    '#17a2b8'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function getLastTwelveMonths() {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const result = [];
    const currentDate = new Date();
    
    for (let i = 11; i >= 0; i--) {
        const d = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
        result.push(months[d.getMonth()]);
    }
    return result;
}

function updateDashboardStats() {
    fetch('/get-dashboard-data/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalIncidents').textContent = data.total;
            document.getElementById('thisMonth').textContent = data.this_month;
            document.getElementById('thisWeek').textContent = data.this_week;
            document.getElementById('today').textContent = data.today;
        });
}

function initializeSearch() {
    const searchInput = document.getElementById('searchIncidents');
    searchInput.addEventListener('input', function(e) {
        const searchText = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#incidentTable tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchText) ? '' : 'none';
        });
    });
}

function initializeIncidentForm() {
    const form = document.getElementById('incidentForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        fetch('/report-incident/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Incident reported successfully!');
                this.reset();
            }
        });
    });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

