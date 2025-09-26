(function (window) {
    const headers = new Set();
    let observer = null;

    function ensureTooltip(btn, label) {
        if (!label) {
            return;
        }
        if (!btn.getAttribute('title')) {
            btn.setAttribute('title', label);
        }
        if (!btn.hasAttribute('data-bs-toggle')) {
            btn.setAttribute('data-bs-toggle', 'tooltip');
            if (!btn.hasAttribute('data-bs-placement')) {
                btn.setAttribute('data-bs-placement', 'top');
            }
        }
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            bootstrap.Tooltip.getInstance(btn) || new bootstrap.Tooltip(btn);
        }
    }

    function refreshHeader(header) {
        if (!header) {
            return;
        }
        const buttons = header.querySelectorAll('.panel-header-actions .btn:not(.action-btn)');
        buttons.forEach(btn => {
            const iconEl = btn.querySelector('i');
            const labelSpan = btn.querySelector('span');
            if (!iconEl || !labelSpan) {
                return;
            }

            btn.classList.remove('collapsed-label');

            if (!btn.dataset.fullLabel) {
                const text = labelSpan.textContent.trim();
                if (text) {
                    btn.dataset.fullLabel = text;
                }
            }

            const needsCollapse = btn.scrollWidth > (btn.clientWidth + 1);
            if (needsCollapse) {
                btn.classList.add('collapsed-label');
                ensureTooltip(btn, btn.dataset.fullLabel || labelSpan.textContent.trim());
            }
        });
    }

    function refreshAll() {
        headers.forEach(header => refreshHeader(header));
    }

    function init() {
        const pageHeaders = document.querySelectorAll('.payees-page .panel-header');
        pageHeaders.forEach(header => {
            if (headers.has(header)) {
                return;
            }
            headers.add(header);
            refreshHeader(header);
        });

        if (typeof ResizeObserver !== 'undefined') {
            if (!observer) {
                observer = new ResizeObserver(entries => {
                    window.requestAnimationFrame(() => {
                        entries.forEach(entry => refreshHeader(entry.target));
                    });
                });
            }
            headers.forEach(header => observer.observe(header));
        }

        window.addEventListener('resize', () => window.requestAnimationFrame(refreshAll));
    }

    window.PanelHeaderLabelManager = {
        init,
        refresh: refreshAll,
    };
})(window);
