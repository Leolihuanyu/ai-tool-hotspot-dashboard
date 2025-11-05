"""Flask路由定义

Dashboard Web界面的所有路由。
"""

import json
import os
import time
from flask import render_template, jsonify, request
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 数据缓存（全局变量）
_cached_data = None
_cache_timestamp = 0
CACHE_TTL = 300  # 缓存有效期：5分钟（300秒）


def load_latest_data():
    """加载最新数据（优先从GitHub获取，本地文件作为fallback）

    数据获取优先级：
    1. 检查缓存（5分钟有效期）
    2. 从GitHub raw URL获取最新数据
    3. 如果GitHub失败，尝试读取本地文件
    4. 都失败则返回空数据

    Returns:
        包含ai_tools, trending_topics, pain_points, opportunities的字典
    """
    global _cached_data, _cache_timestamp

    # 1. 检查缓存是否有效
    current_time = time.time()
    if _cached_data and (current_time - _cache_timestamp < CACHE_TTL):
        logger.debug("使用缓存数据")
        return _cached_data

    # 2. 尝试从GitHub获取数据
    github_url = os.getenv(
        'GITHUB_DATA_URL',
        'https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json'
    )

    try:
        import requests
        logger.info(f"从GitHub获取数据: {github_url}")
        response = requests.get(github_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # 更新缓存
            _cached_data = data
            _cache_timestamp = current_time
            logger.info("成功从GitHub加载数据并更新缓存")
            return data
        else:
            logger.warning(f"GitHub返回非200状态码: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.warning("从GitHub获取数据超时（10秒）")
    except requests.exceptions.RequestException as e:
        logger.warning(f"从GitHub获取数据失败（网络错误）: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"GitHub数据JSON解析失败: {e}")
    except Exception as e:
        logger.error(f"从GitHub加载数据时发生未知错误: {e}")

    # 3. 尝试从本地文件加载（fallback）
    try:
        data_path = os.path.join('data', 'latest.json')
        if os.path.exists(data_path):
            logger.info(f"尝试从本地文件加载: {data_path}")
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新缓存
            _cached_data = data
            _cache_timestamp = current_time
            logger.info("成功从本地文件加载数据")
            return data
        else:
            logger.warning(f"本地数据文件不存在: {data_path}")

    except json.JSONDecodeError as e:
        logger.error(f"本地文件JSON解析失败: {e}")
    except Exception as e:
        logger.error(f"从本地文件加载数据失败: {e}")

    # 4. 所有方法都失败，返回空数据
    logger.error("所有数据源都失败，返回空数据")
    empty_data = {
        'ai_tools': [],
        'trending_topics': [],
        'pain_points': [],
        'opportunities': []
    }
    return empty_data


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
