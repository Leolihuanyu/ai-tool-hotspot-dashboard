"""Flask路由定义

Dashboard Web界面的所有路由。
"""

import json
import os
from flask import render_template, jsonify, request
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_latest_data():
    """加载最新数据

    Returns:
        包含ai_tools, trending_topics, pain_points, opportunities的字典
    """
    try:
        data_path = os.path.join('data', 'latest.json')

        if not os.path.exists(data_path):
            logger.warning(f"Data file not found: {data_path}")
            return {
                'ai_tools': [],
                'trending_topics': [],
                'pain_points': [],
                'opportunities': []
            }

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {
            'ai_tools': [],
            'trending_topics': [],
            'pain_points': [],
            'opportunities': []
        }


def enrich_opportunities(opportunities, pain_points, ai_tools, trending_topics):
    """Enrichment opportunities数据，将ID引用替换为完整对象

    Args:
        opportunities: 机会列表（包含ID引用）
        pain_points: 痛点列表
        ai_tools: AI工具列表
        trending_topics: 热点话题列表

    Returns:
        Enriched opportunities列表
    """
    # 创建ID到对象的映射
    pain_points_map = {pp['id']: pp for pp in pain_points}
    tools_map = {tool['id']: tool for tool in ai_tools}
    topics_map = {topic['id']: topic for topic in trending_topics}

    enriched = []
    for opp in opportunities:
        opp_copy = opp.copy()

        # Enrichment pain_point
        pain_point_id = opp.get('pain_point_id')
        if pain_point_id and pain_point_id in pain_points_map:
            pp = pain_points_map[pain_point_id]
            opp_copy['pain_point_text'] = pp.get('original_text', '')
            opp_copy['pain_point_context'] = pp.get('context_title', '')
            opp_copy['pain_point_keywords'] = pp.get('extracted_keywords', [])
            opp_copy['pain_point_confidence'] = pp.get('confidence_score', 0.0)
        else:
            # 如果找不到pain_point，设置默认值
            opp_copy['pain_point_text'] = '未找到关联的痛点数据'
            opp_copy['pain_point_context'] = ''
            opp_copy['pain_point_keywords'] = []
            opp_copy['pain_point_confidence'] = 0.0

        # Enrichment related_tools（假设opportunity模型中有这个字段）
        related_tool_ids = opp.get('related_tools', [])
        opp_copy['related_tools'] = [
            tools_map[tool_id] for tool_id in related_tool_ids
            if tool_id in tools_map
        ]

        # Enrichment related_topics
        related_topic_ids = opp.get('related_topics', [])
        opp_copy['related_topics'] = [
            topics_map[topic_id] for topic_id in related_topic_ids
            if topic_id in topics_map
        ]

        enriched.append(opp_copy)

    return enriched


def register_routes(app):
    """注册Flask路由

    Args:
        app: Flask应用实例
    """

    @app.route('/')
    def index():
        """首页"""
        try:
            data = load_latest_data()

            stats = {
                'ai_tools_count': len(data.get('ai_tools', [])),
                'trending_topics_count': len(data.get('trending_topics', [])),
                'opportunities_count': len(data.get('opportunities', []))
            }

            return render_template('index.html', stats=stats)

        except Exception as e:
            logger.error(f"Error in index route: {e}")
            return render_template('error.html', error=str(e)), 500

    @app.route('/tools')
    def tools():
        """AI工具榜页面"""
        try:
            data = load_latest_data()
            tools_list = data.get('ai_tools', [])

            # 分页和过滤参数
            source_filter = request.args.get('source', None)
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 30))

            # 来源过滤
            if source_filter:
                tools_list = [t for t in tools_list if t.get('source') == source_filter]

            # 按时间排序(最新优先)
            tools_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            # 分页
            total = len(tools_list)
            start = (page - 1) * per_page
            end = start + per_page
            tools_page = tools_list[start:end]

            # 分页器所需信息
            all_sources = list(set(t.get('source') for t in data.get('ai_tools', [])))

            return render_template(
                'tools.html',
                tools=tools_page,
                total=total,
                page=page,
                per_page=per_page,
                sources=all_sources,
                current_source=source_filter
            )

        except Exception as e:
            logger.error(f"Error in tools route: {e}")
            return render_template('error.html', error=str(e)), 500

    @app.route('/trends')
    def trends():
        """热点榜页面"""
        try:
            data = load_latest_data()
            topics_list = data.get('trending_topics', [])

            # 分页和过滤参数
            source_filter = request.args.get('source', None)
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 30))

            # 来源过滤
            if source_filter:
                topics_list = [t for t in topics_list if t.get('source') == source_filter]

            # 按热度排序
            topics_list.sort(key=lambda x: x.get('heat_score', 0), reverse=True)

            # 分页
            total = len(topics_list)
            start = (page - 1) * per_page
            end = start + per_page
            topics_page = topics_list[start:end]

            # 分页器所需信息
            all_sources = list(set(t.get('source') for t in data.get('trending_topics', [])))

            return render_template(
                'trends.html',
                topics=topics_page,
                total=total,
                page=page,
                per_page=per_page,
                sources=all_sources,
                current_source=source_filter
            )

        except Exception as e:
            logger.error(f"Error in trends route: {e}")
            return render_template('error.html', error=str(e)), 500

    @app.route('/opportunities')
    def opportunities():
        """机会榜页面"""
        try:
            data = load_latest_data()

            # Enrichment opportunities数据
            enriched_opps = enrich_opportunities(
                opportunities=data.get('opportunities', []),
                pain_points=data.get('pain_points', []),
                ai_tools=data.get('ai_tools', []),
                trending_topics=data.get('trending_topics', [])
            )

            # 按opportunity_score排序，选择Top 10
            enriched_opps.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
            top_opportunities = enriched_opps[:10]

            return render_template(
                'opportunities.html',
                opportunities=top_opportunities
            )

        except Exception as e:
            logger.error(f"Error in opportunities route: {e}", exc_info=True)
            return render_template('error.html', error=str(e)), 500

    @app.route('/api/v1/tools')
    def api_tools():
        """API: 返回AI工具列表"""
        try:
            data = load_latest_data()
            tools_list = data.get('ai_tools', [])

            return jsonify({
                'success': True,
                'count': len(tools_list),
                'data': tools_list
            })

        except Exception as e:
            logger.error(f"Error in API tools route: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/health')
    def health():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'service': 'ai-tool-hotspot-dashboard'
        })

    logger.info("路由注册完成")
