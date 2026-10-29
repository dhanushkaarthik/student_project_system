/**
 * Student Project Submission & Evaluation System
 * Main JavaScript utilities
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // 2. Real-time Countdown Timers
    function updateCountdowns() {
        const countdownElements = document.querySelectorAll('[data-deadline]');
        const now = new Date().getTime();

        countdownElements.forEach(el => {
            const deadlineStr = el.getAttribute('data-deadline');
            if (!deadlineStr) return;

            const deadline = new Date(deadlineStr).getTime();
            const distance = deadline - now;

            if (distance < 0) {
                el.innerHTML = '<span class="text-danger fw-semibold"><i class="bi bi-exclamation-triangle me-1"></i>Deadline Passed</span>';
                el.classList.add('countdown-expired');
                el.classList.remove('countdown-active');
            } else {
                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                let formatted = '';
                if (days > 0) formatted += `${days}d `;
                formatted += `${hours.toString().padStart(2, '0')}h ${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;

                el.innerHTML = `<span class="text-warning fw-semibold"><i class="bi bi-clock me-1"></i>${formatted}</span>`;
                el.classList.add('countdown-active');
                el.classList.remove('countdown-expired');
            }
        });
    }

    // Run countdown update immediately and tick every second
    updateCountdowns();
    setInterval(updateCountdowns, 1000);

    // 3. Client-side Table Filter
    const searchInputs = document.querySelectorAll('[data-table-filter]');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function () {
            const targetTableId = this.getAttribute('data-table-filter');
            const table = document.querySelector(targetTableId);
            if (!table) return;

            const term = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    });

    // 4. Notifications Mark as Read AJAX
    const notifReadBtns = document.querySelectorAll('.mark-read-btn');
    notifReadBtns.forEach(btn => {
        btn.addEventListener('click', async function (e) {
            e.preventDefault();
            const notifId = this.getAttribute('data-id');
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

            try {
                const res = await fetch(`/notifications/${notifId}/read`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken || ''
                    }
                });
                if (res.ok) {
                    const item = document.getElementById(`notif-item-${notifId}`);
                    if (item) {
                        item.classList.remove('unread');
                        this.remove();
                    }
                    // Update badge count
                    const badge = document.getElementById('notif-badge');
                    if (badge) {
                        let count = parseInt(badge.innerText, 10) - 1;
                        if (count <= 0) {
                            badge.remove();
                        } else {
                            badge.innerText = count;
                        }
                    }
                }
            } catch (err) {
                console.error('Error marking notification as read:', err);
            }
        });
    });

    // 5. Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
