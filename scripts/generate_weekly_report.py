#!/usr/bin/env python3
"""
周报自动生成和多平台发布脚本
每周五生成深度分析周报并发布到多个平台
"""

import os
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter
import markdown
from jinja2 import Template

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/weekly_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self):
        self.data_dir = Path("data")
        self.archive_dir = self.data_dir / "archive"
        self.output_dir = Path("reports/weekly")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_week_dates(self) -> Tuple[datetime, datetime]:
        """获取本周的开始和结束日期"""
        today = datetime.now()
        # 获取本周一
        monday = today - timedelta(days=today.weekday())
        # 获取本周日
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def aggregate_weekly_data(self) -> Dict:
        """聚合一周的数据"""
        monday, sunday = self.get_week_dates()
        logger.info(f"聚合数据范围: {monday.strftime('%Y-%m-%d')} 到 {sunday.strftime('%Y-%m-%d')}")

        weekly_data = {
            'opportunities': [],
            'tools': [],
            'trends': [],
            'sources': Counter(),
            'categories': Counter(),
            'dates': []
        }

        # 遍历本周每一天的数据
        current_date = monday
        while current_date <= sunday and current_date <= datetime.now():
            date_str = current_date.strftime('%Y%m%d')
            file_path = self.archive_dir / f"{date_str}.json"

            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)

                        # 聚合机会
                        weekly_data['opportunities'].extend(
                            daily_data.get('opportunities', [])
                        )

                        # 聚合工具
                        weekly_data['tools'].extend(
                            daily_data.get('tools', [])
                        )

                        # 聚合趋势
                        weekly_data['trends'].extend(
                            daily_data.get('trends', [])
                        )

                        # 统计数据源
                        for item in daily_data.get('opportunities', []):
                            source = item.get('source', 'unknown')
                            weekly_data['sources'][source] += 1

                        # 统计类别
                        for item in daily_data.get('opportunities', []):
                            category = item.get('category', 'other')
                            weekly_data['categories'][category] += 1

                        weekly_data['dates'].append(date_str)
                        logger.info(f"已加载 {date_str} 的数据")

                except Exception as e:
                    logger.error(f"加载 {file_path} 失败: {e}")

            current_date += timedelta(days=1)

        logger.info(f"共聚合了 {len(weekly_data['dates'])} 天的数据")
        logger.info(f"机会数: {len(weekly_data['opportunities'])}")
        logger.info(f"工具数: {len(weekly_data['tools'])}")
        logger.info(f"趋势数: {len(weekly_data['trends'])}")

        return weekly_data

    def deduplicate_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """去重并排序机会"""
        seen = set()
        unique_opportunities = []

        for opp in opportunities:
            # 使用标题作为唯一标识
            title = opp.get('title', '')
            if title and title not in seen:
                seen.add(title)
                unique_opportunities.append(opp)

        # 按评分排序
        unique_opportunities.sort(
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        return unique_opportunities

    def analyze_trends(self, weekly_data: Dict) -> Dict:
        """分析周趋势"""
        analysis = {
            'top_categories': weekly_data['categories'].most_common(5),
            'top_sources': weekly_data['sources'].most_common(5),
            'total_opportunities': len(weekly_data['opportunities']),
            'unique_opportunities': len(
                self.deduplicate_opportunities(weekly_data['opportunities'])
            ),
            'avg_daily_opportunities': len(weekly_data['opportunities']) / max(len(weekly_data['dates']), 1),
            'growth_rate': self._calculate_growth_rate(weekly_data)
        }

        # 分析热门关键词
        keywords = Counter()
        for opp in weekly_data['opportunities']:
            title = opp.get('title', '').lower()
            for word in title.split():
                if len(word) > 3:  # 忽略短词
                    keywords[word] += 1

        analysis['hot_keywords'] = keywords.most_common(10)

        return analysis

    def _calculate_growth_rate(self, weekly_data: Dict) -> float:
        """计算增长率（与上周对比）"""
        # 这里简化处理，实际应该对比上周数据
        return 0.0

    def generate_report_content(self, weekly_data: Dict, analysis: Dict) -> Dict:
        """生成周报内容"""
        monday, sunday = self.get_week_dates()
        week_number = monday.isocalendar()[1]  # 获取周数

        # 去重并获取Top 10机会
        unique_opportunities = self.deduplicate_opportunities(
            weekly_data['opportunities']
        )[:10]

        report = {
            'title': f"AI工具机会周报 #{week_number}",
            'subtitle': f"{monday.strftime('%Y年%m月%d日')} - {sunday.strftime('%Y年%m月%d日')}",
            'week_number': week_number,
            'date_range': {
                'start': monday.strftime('%Y-%m-%d'),
                'end': sunday.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_opportunities': analysis['total_opportunities'],
                'unique_opportunities': analysis['unique_opportunities'],
                'avg_daily': round(analysis['avg_daily_opportunities'], 1),
                'data_days': len(weekly_data['dates'])
            },
            'top_opportunities': unique_opportunities,
            'category_analysis': analysis['top_categories'],
            'source_analysis': analysis['top_sources'],
            'hot_keywords': analysis['hot_keywords'],
            'generated_at': datetime.now().isoformat()
        }

        return report

    def format_markdown_report(self, report: Dict) -> str:
        """格式化Markdown报告"""
        template = """# {{ title }}

> {{ subtitle }}
>
> 📊 本周共分析 **{{ summary.total_opportunities }}** 个机会，精选出 **{{ summary.unique_opportunities }}** 个独特机会
>
> 📈 平均每日新增 **{{ summary.avg_daily }}** 个机会

---

## 📌 本周Top 10产品机会

{% for opp in top_opportunities %}
### {{ loop.index }}. {{ opp.title }}

**类别**: {{ opp.category | default('其他', true) }} | **来源**: {{ opp.source | default('未知', true) }}

**痛点描述**:
{{ opp.description | default('暂无描述', true) }}

**为什么值得做**:
- 痛点清晰度: {{ '⭐' * opp.clarity_score | default(3, true) }}
- MVP开发速度: {{ '⭐' * opp.mvp_speed | default(3, true) }}
- 变现潜力: {{ '⭐' * opp.monetization_potential | default(3, true) }}

**MVP建议**:
{{ opp.mvp_suggestion | default('使用现有AI工具快速搭建原型，验证市场需求', true) }}

---
{% endfor %}

## 📊 数据分析

### 机会类别分布
{% for category, count in category_analysis %}
- **{{ category }}**: {{ count }} 个 ({{ (count / summary.total_opportunities * 100) | round(1) }}%)
{% endfor %}

### 数据源贡献
{% for source, count in source_analysis %}
- **{{ source }}**: {{ count }} 个
{% endfor %}

### 热门关键词
{% for keyword, count in hot_keywords[:5] %}
`{{ keyword }}` ({{ count }}) {% endfor %}

---

## 💡 本周洞察

基于本周数据分析，我们发现：

1. **{{ category_analysis[0][0] }}** 类别的机会最多，占比 {{ (category_analysis[0][1] / summary.total_opportunities * 100) | round(1) }}%，说明这个领域存在较多未满足的需求

2. 热门关键词显示，**{{ hot_keywords[0][0] }}** 和 **{{ hot_keywords[1][0] }}** 是当前最受关注的技术方向

3. 来自 **{{ source_analysis[0][0] }}** 的数据质量最高，贡献了 {{ source_analysis[0][1] }} 个有价值的机会

## 🎯 下周预告

我们将继续追踪以下趋势：
- AI Agent工具的爆发式增长
- 垂直领域AI应用的机会
- 开源AI工具的商业化路径

---

## 📮 订阅完整数据

想要获取每日Top 10机会推送？

👉 [访问Dashboard](https://your-domain.vercel.app)
👉 [申请邀请码](https://your-domain.vercel.app/invite)

---

*本报告由 AI Tool Hotspot 自动生成*
*生成时间: {{ generated_at }}*
"""

        # 使用Jinja2渲染模板
        return Template(template).render(**report)

    def format_json_report(self, report: Dict) -> str:
        """格式化JSON报告（用于API）"""
        return json.dumps(report, ensure_ascii=False, indent=2)

    def save_report(self, report: Dict, markdown_content: str) -> Tuple[Path, Path]:
        """保存报告文件"""
        week_number = report['week_number']
        date_str = datetime.now().strftime('%Y%m%d')

        # 保存Markdown版本
        md_file = self.output_dir / f"weekly_report_{date_str}_w{week_number}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        logger.info(f"Markdown报告已保存: {md_file}")

        # 保存JSON版本
        json_file = self.output_dir / f"weekly_report_{date_str}_w{week_number}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON报告已保存: {json_file}")

        return md_file, json_file

    def generate(self) -> Dict:
        """生成周报"""
        logger.info("="*50)
        logger.info("开始生成周报")

        # 1. 聚合数据
        weekly_data = self.aggregate_weekly_data()

        if not weekly_data['opportunities']:
            logger.warning("本周没有机会数据")
            return None

        # 2. 分析趋势
        analysis = self.analyze_trends(weekly_data)

        # 3. 生成报告内容
        report = self.generate_report_content(weekly_data, analysis)

        # 4. 格式化报告
        markdown_content = self.format_markdown_report(report)

        # 5. 保存报告
        md_file, json_file = self.save_report(report, markdown_content)

        logger.info("周报生成完成")

        return {
            'report': report,
            'markdown': markdown_content,
            'files': {
                'markdown': str(md_file),
                'json': str(json_file)
            }
        }


class MultiPlatformPublisher:
    """多平台发布器"""

    def __init__(self, report_data: Dict):
        self.report = report_data['report']
        self.markdown = report_data['markdown']

    def publish_to_medium(self) -> bool:
        """发布到Medium"""
        # TODO: 实现Medium API集成
        logger.info("发布到Medium（待实现）")
        return True

    def publish_to_zhihu(self) -> bool:
        """发布到知乎"""
        # TODO: 实现知乎API集成
        logger.info("发布到知乎（待实现）")
        return True

    def publish_twitter_thread(self) -> bool:
        """发布Twitter线程"""
        # 将周报拆分成多条推文
        thread_content = self._split_to_twitter_thread()

        # TODO: 调用Twitter API发布线程
        logger.info(f"准备发布{len(thread_content)}条推文的线程")
        return True

    def _split_to_twitter_thread(self) -> List[str]:
        """将周报拆分成Twitter线程"""
        tweets = []

        # 第一条：标题和概览
        tweets.append(
            f"🚀 {self.report['title']}\n\n"
            f"本周精选 {self.report['summary']['unique_opportunities']} 个AI工具机会\n"
            f"平均每日新增 {self.report['summary']['avg_daily']} 个\n\n"
            f"Top 3 机会如下👇"
        )

        # 添加Top 3机会
        for i, opp in enumerate(self.report['top_opportunities'][:3], 1):
            tweet = (
                f"{i}/10\n\n"
                f"🎯 {opp['title']}\n"
                f"类别: {opp.get('category', '其他')}\n"
                f"💡 {opp.get('description', '')[:100]}..."
            )
            tweets.append(tweet)

        # 最后一条：链接和CTA
        tweets.append(
            f"📊 完整周报已发布\n\n"
            f"查看全部10个机会 + 详细分析\n"
            f"👉 https://your-domain.vercel.app/weekly\n\n"
            f"#AITools #周报 #独立开发者"
        )

        return tweets

    def update_website(self) -> bool:
        """更新网站周报页面"""
        # 将最新周报复制到公开目录
        public_dir = Path("frontend/public/reports")
        public_dir.mkdir(parents=True, exist_ok=True)

        latest_report = public_dir / "latest_weekly.json"
        with open(latest_report, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)

        logger.info(f"网站周报已更新: {latest_report}")
        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='生成并发布周报')
    parser.add_argument(
        '--generate-only',
        action='store_true',
        help='仅生成报告，不发布'
    )
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['medium', 'zhihu', 'twitter', 'website'],
        default=['website', 'twitter'],
        help='选择发布平台'
    )

    args = parser.parse_args()

    try:
        # 生成周报
        generator = WeeklyReportGenerator()
        report_data = generator.generate()

        if not report_data:
            logger.error("周报生成失败")
            sys.exit(1)

        if args.generate_only:
            logger.info("仅生成模式，跳过发布")
            return

        # 发布到各平台
        publisher = MultiPlatformPublisher(report_data)

        for platform in args.platforms:
            logger.info(f"发布到 {platform}")
            if platform == 'medium':
                publisher.publish_to_medium()
            elif platform == 'zhihu':
                publisher.publish_to_zhihu()
            elif platform == 'twitter':
                publisher.publish_twitter_thread()
            elif platform == 'website':
                publisher.update_website()

        logger.info("所有平台发布完成")

    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()