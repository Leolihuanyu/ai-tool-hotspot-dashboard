/**
 * 机会榜页面交互逻辑
 * 实现展开/收起功能和动画效果
 */

/**
 * 切换章节展开/收起状态
 * @param {HTMLElement} button - 点击的按钮元素
 * @param {string} sectionId - 要切换的章节ID
 */
function toggleSection(button, sectionId) {
    const section = document.getElementById(sectionId);
    const icon = button.querySelector('.expand-icon');

    if (section.classList.contains('collapsed')) {
        // 展开
        section.classList.remove('collapsed');
        section.classList.add('expanded');
        icon.textContent = '▼';
        button.querySelector('span:not(.expand-icon)').textContent = ' 收起';
    } else {
        // 收起
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        icon.textContent = '▶';
        // 根据section ID判断原始文本
        if (sectionId.startsWith('mvp-')) {
            button.querySelector('span:not(.expand-icon)').textContent = ' 展开查看详情';
        } else if (sectionId.startsWith('related-')) {
            button.querySelector('span:not(.expand-icon)').textContent = ' 展开查看';
        } else if (sectionId.startsWith('scores-')) {
            button.querySelector('span:not(.expand-icon)').textContent = ' 展开查看';
        }
    }
}

/**
 * 初始化页面时的设置
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('机会榜页面已加载');

    // 为所有机会卡片添加悬停效果
    const cards = document.querySelectorAll('.opportunity-card');
    cards.forEach((card, index) => {
        // 添加动画延迟
        card.style.animationDelay = `${index * 0.1}s`;

        // 悬停时轻微放大
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '';
        });
    });

    // 添加平滑滚动
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // 初始化评分条动画
    animateScoreBars();
});

/**
 * 为评分条添加动画效果
 */
function animateScoreBars() {
    const scoreFills = document.querySelectorAll('.score-fill');
    scoreFills.forEach((fill, index) => {
        const targetWidth = fill.style.width;
        fill.style.width = '0%';
        setTimeout(() => {
            fill.style.transition = 'width 1s ease-out';
            fill.style.width = targetWidth;
        }, index * 50);
    });
}

/**
 * 全部展开所有机会的详情
 */
function expandAll() {
    const buttons = document.querySelectorAll('.expand-btn');
    buttons.forEach(button => {
        const section = button.nextElementSibling;
        if (section && section.classList.contains('collapsed')) {
            button.click();
        }
    });
}

/**
 * 全部收起所有机会的详情
 */
function collapseAll() {
    const buttons = document.querySelectorAll('.expand-btn');
    buttons.forEach(button => {
        const section = button.nextElementSibling;
        if (section && section.classList.contains('expanded')) {
            button.click();
        }
    });
}

// 导出函数供全局使用
window.toggleSection = toggleSection;
window.expandAll = expandAll;
window.collapseAll = collapseAll;
