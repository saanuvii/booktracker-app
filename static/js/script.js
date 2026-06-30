document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const icon = themeToggle ? themeToggle.querySelector('i') : null;

    if (themeToggle) {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        htmlElement.setAttribute('data-bs-theme', savedTheme);
        updateThemeIcon(savedTheme);

        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            window.dispatchEvent(new Event('themeChanged'));
        });

        function updateThemeIcon(theme) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun text-warning'; 
                themeToggle.classList.replace('text-dark', 'text-light');
            } else {
                icon.className = 'fas fa-moon text-primary'; 
                themeToggle.classList.replace('text-light', 'text-dark');
            }
        }
    }

    // 2. Show/Hide "Pages Read"
    const statusSelect = document.getElementById('bookStatus');
    const currentPageDiv = document.getElementById('currentPageDiv');
    if (statusSelect && currentPageDiv) {
        statusSelect.addEventListener('change', (e) => {
            if (e.target.value === 'Currently Reading') {
                currentPageDiv.style.display = 'block';
            } else {
                currentPageDiv.style.display = 'none';
            }
        });
    }

    // 3. Favorites Toggle
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    favoriteButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const bookId = btn.getAttribute('data-id');
            const favIcon = btn.querySelector('i');
            try {
                const response = await fetch(`/toggle_favorite/${bookId}`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    if (data.favorite) {
                        favIcon.classList.remove('far', 'text-white');
                        favIcon.classList.add('fas', 'text-danger');
                        favIcon.style.transform = 'scale(1.2)';
                        setTimeout(() => favIcon.style.transform = 'scale(1)', 200);
                    } else {
                        favIcon.classList.remove('fas', 'text-danger');
                        favIcon.classList.add('far', 'text-white');
                    }
                }
            } catch (error) { console.error('Error toggling favorite:', error); }
        });
    });

    // 4. Form Validation
    const forms = document.querySelectorAll('.needs-validation')
    Array.from(forms).forEach(form => {
      form.addEventListener('submit', event => {
        if (!form.checkValidity()) {
          event.preventDefault(); event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false)
    });

    // 5. API Auto-Fill
    const autoFillBtn = document.getElementById('autoFillBtn');
    const autoFillQuery = document.getElementById('autoFillQuery');
    const autoFillStatus = document.getElementById('autoFillStatus');

    if (autoFillBtn && autoFillQuery) {
        autoFillBtn.addEventListener('click', async () => {
            const query = autoFillQuery.value.trim();
            if (!query) {
                autoFillStatus.innerHTML = '<span class="text-warning"><i class="fas fa-exclamation-triangle"></i> Please enter a search term.</span>';
                return;
            }
            autoFillBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
            autoFillBtn.disabled = true;
            autoFillStatus.innerHTML = 'Searching Open Library...';

            try {
                const response = await fetch('/api/fetch_book', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const result = await response.json();
                if (result.success) {
                    document.querySelector('input[name="title"]').value = result.data.title;
                    document.querySelector('input[name="author"]').value = result.data.author;
                    document.querySelector('input[name="total_pages"]').value = result.data.total_pages;
                    document.querySelector('input[name="genre"]').value = result.data.genre;
                    document.querySelector('input[name="cover_image"]').value = result.data.cover_image;
                    autoFillStatus.innerHTML = '<span class="text-success"><i class="fas fa-check-circle"></i> Details found!</span>';
                } else {
                    autoFillStatus.innerHTML = `<span class="text-danger"><i class="fas fa-times-circle"></i> ${result.error}</span>`;
                }
            } catch (error) {
                autoFillStatus.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> Network error.</span>';
            } finally {
                autoFillBtn.innerHTML = '<i class="fas fa-search"></i> Fetch Details';
                autoFillBtn.disabled = false;
            }
        });

        autoFillQuery.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); autoFillBtn.click(); }
        });
    }

    // 6. Genre Chart
    const chartCanvas = document.getElementById('genreChart');
    if (chartCanvas && typeof chartLabels !== 'undefined' && chartLabels.length > 0) {
        const getTextColor = () => document.documentElement.getAttribute('data-bs-theme') === 'light' ? '#2e2836' : '#f5f3ff';
        const genreChart = new Chart(chartCanvas, {
            type: 'doughnut',
            data: {
                labels: chartLabels,
                datasets: [{
                    data: chartValues,
                    backgroundColor: ['#8b5cf6', '#10b981', '#0ea5e9', '#f97316', '#ec4899'],
                    borderWidth: 0, hoverOffset: 4
                }]
            },
            options: { plugins: { legend: { position: 'right', labels: { color: getTextColor() } } }, cutout: '65%' }
        });
        window.addEventListener('themeChanged', () => {
            genreChart.options.plugins.legend.labels.color = getTextColor();
            genreChart.update();
        });
    }

    // 7. Floating Timer
    const togglePanelBtn = document.getElementById('toggleTimerPanel');
    const timerPanel = document.getElementById('timerPanel');
    const display = document.getElementById('stopwatchDisplay');
    const startBtn = document.getElementById('startTimerBtn');
    const pauseBtn = document.getElementById('pauseTimerBtn');
    const resetBtn = document.getElementById('resetTimerBtn');
    let timerInterval = null, secondsElapsed = 0;

    if (togglePanelBtn) {
        togglePanelBtn.addEventListener('click', () => {
            if (timerPanel.style.display === 'none') {
                timerPanel.style.display = 'block';
                setTimeout(() => { timerPanel.style.opacity = '1'; timerPanel.style.transform = 'translateY(0)'; }, 10);
            } else {
                timerPanel.style.opacity = '0';
                timerPanel.style.transform = 'translateY(20px)';
                setTimeout(() => { timerPanel.style.display = 'none'; }, 300);
            }
        });
    }

    function updateDisplay() {
        const hrs = String(Math.floor(secondsElapsed / 3600)).padStart(2, '0');
        const mins = String(Math.floor((secondsElapsed % 3600) / 60)).padStart(2, '0');
        const secs = String(secondsElapsed % 60).padStart(2, '0');
        display.textContent = `${hrs}:${mins}:${secs}`;
    }

    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (!timerInterval) {
                timerInterval = setInterval(() => { secondsElapsed++; updateDisplay(); }, 1000);
                startBtn.style.display = 'none'; pauseBtn.style.display = 'block';
                togglePanelBtn.querySelector('i').classList.add('fa-spin');
            }
        });
        pauseBtn.addEventListener('click', () => {
            clearInterval(timerInterval); timerInterval = null;
            pauseBtn.style.display = 'none'; startBtn.style.display = 'block';
            togglePanelBtn.querySelector('i').classList.remove('fa-spin');
        });
        resetBtn.addEventListener('click', () => {
            clearInterval(timerInterval); timerInterval = null; secondsElapsed = 0; updateDisplay();
            pauseBtn.style.display = 'none'; startBtn.style.display = 'block';
            togglePanelBtn.querySelector('i').classList.remove('fa-spin');
        });
    }

    // 8. Random Book Generator
    const triggerRandomBtn = document.getElementById('triggerRandomBtn');
    if (triggerRandomBtn) {
        triggerRandomBtn.addEventListener('click', async () => {
            const loadingState = document.getElementById('randomLoadingState');
            const resultState = document.getElementById('randomResultState');
            
            loadingState.style.display = 'block';
            resultState.style.display = 'none';

            try {
                const response = await fetch('/api/random_book');
                const data = await response.json();

                setTimeout(() => {
                    loadingState.style.display = 'none';
                    if (data.success) {
                        document.getElementById('randomTitle').textContent = data.book.title;
                        document.getElementById('randomAuthor').textContent = data.book.author;
                        document.getElementById('randomViewBtn').href = `/book/${data.book.id}`;
                        
                        const coverImg = document.getElementById('randomCover');
                        const placeholder = document.getElementById('randomCoverPlaceholder');
                        
                        if (data.book.cover_image) {
                            coverImg.src = data.book.cover_image;
                            coverImg.style.display = 'block';
                            placeholder.style.display = 'none';
                        } else {
                            coverImg.style.display = 'none';
                            placeholder.style.display = 'block';
                        }
                        resultState.style.display = 'block';
                    } else {
                        document.getElementById('randomTitle').textContent = "No Books Found!";
                        document.getElementById('randomAuthor').textContent = data.error;
                        document.getElementById('randomViewBtn').style.display = 'none';
                        resultState.style.display = 'block';
                    }
                }, 1500); 
            } catch (error) { console.error("Error fetching random book:", error); }
        });
    }

    // --- 9. Interactive Star Rating UI ---
    const starContainers = document.querySelectorAll('.star-rating');
    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.rating-star');
        const hiddenInput = container.nextElementSibling;

        // Function to color stars up to a certain value
        const updateStars = (val) => {
            stars.forEach(s => {
                if (parseInt(s.dataset.value) <= val) {
                    s.classList.remove('far');
                    s.classList.add('fas');
                } else {
                    s.classList.remove('fas');
                    s.classList.add('far');
                }
            });
        };

        // Hover events
        stars.forEach(star => {
            star.addEventListener('mouseover', function() {
                updateStars(this.dataset.value);
            });

            star.addEventListener('mouseout', function() {
                updateStars(hiddenInput.value); // Revert to saved value when mouse leaves
            });

            star.addEventListener('click', function() {
                hiddenInput.value = this.dataset.value; // Save to hidden input
                updateStars(this.dataset.value);
            });
        });
    });
});

function confirmDelete() { return confirm("Are you sure you want to delete this book? This action cannot be undone."); }