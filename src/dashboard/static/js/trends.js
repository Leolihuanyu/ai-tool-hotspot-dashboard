/**
 * 热点榜JavaScript功能
 *
 * 功能:
 * - 数据源筛选
 * - 热度排序
 * - 趋势方向过滤
 */

/**
 * 根据数据源筛选热点
 * @param {string} source - 数据源名称,空字符串表示全部
 */
function filterBySource(source) {
    const currentParams = new URLSearchParams(window.location.search);

    if (source) {
        currentParams.set('source', source);
    } else {
        currentParams.delete('source');
    }

    // 重置到第一页
    currentParams.delete('page');

    window.location.href = '/trends?' + currentParams.toString();
}

/**
 * 根据趋势方向筛选
 * @param {string} direction - rising, falling, stable, 或空字符串表示全部
 */
function filterByDirection(direction) {
    const cards = document.querySelectorAll('.trend-card');

    cards.forEach(card => {
        const directionBadge = card.querySelector('.trend-badge');

        if (!direction || !directionBadge) {
            card.style.display = 'block';
            return;
        }

        const cardDirection = directionBadge.classList.contains(direction);
        card.style.display = cardDirection ? 'block' : 'none';
    });
}

/**
 * 按热度重新排序(客户端排序)
 * @param {string} order - 'desc' 或 'asc'
 */
function sortByHeat(order = 'desc') {
    const grid = document.querySelector('.trends-grid');
    const cards = Array.from(document.querySelectorAll('.trend-card'));

    cards.sort((a, b) => {
        const heatA = parseFloat(a.querySelector('.heat-score').textContent.replace('🔥 ', ''));
        const heatB = parseFloat(b.querySelector('.heat-score').textContent.replace('🔥 ', ''));

        return order === 'desc' ? heatB - heatA : heatA - heatB;
    });

    // 清空并重新添加
    grid.innerHTML = '';
    cards.forEach(card => grid.appendChild(card));
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trends page loaded');

    // 如果有趋势方向筛选按钮,绑定事件
    const directionFilter = document.getElementById('direction-filter');
    if (directionFilter) {
        directionFilter.addEventListener('change', function() {
            filterByDirection(this.value);
        });
    }

    // 如果有排序按钮,绑定事件
    const sortButton = document.getElementById('sort-heat');
    if (sortButton) {
        sortButton.addEventListener('click', function() {
            const currentOrder = this.dataset.order || 'desc';
            const newOrder = currentOrder === 'desc' ? 'asc' : 'desc';
            this.dataset.order = newOrder;
            sortByHeat(newOrder);

            // 更新按钮文本
            this.textContent = newOrder === 'desc' ? '热度 ↓' : '热度 ↑';
        });
    }
});
