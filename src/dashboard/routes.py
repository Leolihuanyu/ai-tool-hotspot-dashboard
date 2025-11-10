"""Flask API路由定义

后端API路由（前后端分离架构）。
仅提供JSON API，不包含HTML渲染。
"""

import json
import os
import time
from flask import jsonify, request
from src.utils.logger import get_logger
from src.dashboard.auth_middleware import require_auth, verify_token_from_request

logger = get_logger(__name__)

# 数据缓存（全局变量）
_cached_data = None
_cache_timestamp = 0
CACHE_TTL = 300  # 缓存有效期：5分钟（300秒）


def load_latest_data():
    """加载最新数据（优先使用本地文件，GitHub作为备份）

    数据获取优先级：
    1. 检查缓存（5分钟有效期）
    2. 读取本地文件 data/latest.json（主要数据源）
    3. 如果本地文件不存在，快速尝试从GitHub获取（2秒超时）
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

    # 2. 优先尝试从本地文件加载（Docker镜像中应该包含此文件）
    data_path = os.path.join('data', 'latest.json')

    try:
        if os.path.exists(data_path):
            file_size = os.path.getsize(data_path)
            logger.info(f"从本地文件加载数据: {data_path} ({file_size} bytes)")

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证数据不是空的
            if data and len(data.get('opportunities', [])) > 0:
                # 更新缓存
                _cached_data = data
                _cache_timestamp = current_time
                logger.info(f"✓ 成功加载本地数据: {len(data.get('ai_tools', []))} 工具, "
                           f"{len(data.get('trending_topics', []))} 热点, "
                           f"{len(data.get('opportunities', []))} 机会")
                return data
            else:
                logger.warning(f"本地文件存在但数据为空或无效")
        else:
            logger.warning(f"本地数据文件不存在: {data_path}")

    except json.JSONDecodeError as e:
        logger.error(f"本地文件JSON解析失败: {e}")
    except Exception as e:
        logger.error(f"从本地文件加载数据失败: {e}")

    # 3. 本地文件失败，快速尝试从GitHub获取（仅用于公开仓库）
    github_url = os.getenv(
        'GITHUB_DATA_URL',
        'https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json'
    )

    try:
        import requests
        logger.info(f"本地文件不可用，尝试从GitHub获取: {github_url}")
        response = requests.get(github_url, timeout=2)  # 快速失败：2秒超时

        if response.status_code == 200:
            data = response.json()
            # 更新缓存
            _cached_data = data
            _cache_timestamp = current_time
            logger.info("✓ 从GitHub加载数据成功")
            return data
        else:
            logger.warning(f"GitHub返回状态码: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.warning("从GitHub获取数据超时（2秒），可能是私有仓库或网络问题")
    except requests.exceptions.RequestException as e:
        logger.warning(f"从GitHub获取数据失败: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"GitHub数据JSON解析失败: {e}")
    except Exception as e:
        logger.warning(f"GitHub加载时出错: {e}")

    # 4. 所有方法都失败，返回空数据
    logger.error("⚠️ 所有数据源都失败，返回空数据结构")
    logger.error("提示：请确保 data/latest.json 存在于Docker镜像中")

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
    """注册Flask API路由（仅API，不包含HTML渲染）

    Args:
        app: Flask应用实例
    """

    # === 公开API路由 ===

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

    # === 认证相关路由 ===

    @app.route('/api/verify-token', methods=['POST', 'GET'])
    def api_verify_token():
        """
        API: 验证访问token的有效性

        请求参数（URL参数或JSON body）：
            token: 访问token
            email: 用户邮箱（可选）

        返回：
            {
                "success": True/False,
                "valid": True/False,
                "email": "user@example.com",
                "subscription_type": "beta/paid",
                "error": "错误信息"
            }
        """
        try:
            result = verify_token_from_request()

            return jsonify({
                "success": True,
                **result
            })

        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            return jsonify({
                "success": False,
                "valid": False,
                "error": str(e)
            }), 500

    # === 需要认证的API路由 ===

    @app.route('/api/data')
    @require_auth
    def api_data():
        """
        API: 获取完整数据（需要认证）

        返回：
            {
                "success": True,
                "user_email": "user@example.com",
                "data": {
                    "ai_tools": [...],
                    "trending_topics": [...],
                    "opportunities": [...]
                }
            }
        """
        try:
            data = load_latest_data()

            # Enrichment opportunities数据
            enriched_opps = enrich_opportunities(
                opportunities=data.get('opportunities', []),
                pain_points=data.get('pain_points', []),
                ai_tools=data.get('ai_tools', []),
                trending_topics=data.get('trending_topics', [])
            )

            return jsonify({
                "success": True,
                "user_email": request.user_email,
                "subscription_type": request.subscription_type,
                "data": {
                    "ai_tools": data.get('ai_tools', []),
                    "trending_topics": data.get('trending_topics', []),
                    "pain_points": data.get('pain_points', []),
                    "opportunities": enriched_opps
                }
            })

        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    # === 用户认证和注册API ===

    @app.route('/api/register', methods=['POST'])
    def api_register():
        """
        API: 用户注册（通过邀请码）

        请求体：
            {
                "email": "user@example.com",
                "invite_code": "BETA-XXXX-XXXX",
                "language": "zh"  # 可选：zh/en/ja
            }

        返回：
            {
                "success": True,
                "message": "注册成功",
                "token": "access_token_here"
            }
        """
        try:
            data = request.get_json()
            email = data.get('email')
            invite_code = data.get('invite_code')
            language = data.get('language', 'zh')

            # 获取timezone，如果未提供则根据language推断默认值
            timezone = data.get('timezone')
            if not timezone:
                # 根据语言推断时区
                timezone_map = {
                    'zh': 'Asia/Shanghai',
                    'ja': 'Asia/Tokyo',
                    'en': 'UTC'
                }
                timezone = timezone_map.get(language, 'UTC')

            if not email or not invite_code:
                return jsonify({
                    "success": False,
                    "error": "邮箱和邀请码不能为空"
                }), 400

            # 验证邀请码
            from src.user.invite_manager import InviteManager
            invite_manager = InviteManager()

            verify_result = invite_manager.validate_code(invite_code)
            if not verify_result.get('valid'):
                return jsonify({
                    "success": False,
                    "error": verify_result.get('error', '邀请码无效')
                }), 400

            # 创建用户
            from src.user.user_manager import UserManager
            user_manager = UserManager()

            user_result = user_manager.create_user(
                email=email,
                subscription_type='beta',
                invite_code=invite_code,
                language=language,
                timezone=timezone
            )

            if not user_result.get('success'):
                return jsonify({
                    "success": False,
                    "error": user_result.get('error', '创建用户失败')
                }), 500

            # 标记邀请码为已使用
            invite_manager.mark_invite_used(invite_code, email)

            # 生成访问token
            from src.auth.token_manager import TokenManager
            token_manager = TokenManager()
            token = token_manager.generate_token(email)

            logger.info(f"用户注册成功: {email}")

            return jsonify({
                "success": True,
                "message": "注册成功",
                "token": token,
                "email": email
            })

        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/verify-invite', methods=['POST'])
    def api_verify_invite():
        """
        API: 验证邀请码是否有效

        请求体：
            {
                "invite_code": "BETA-XXXX-XXXX"
            }

        返回：
            {
                "success": True,
                "valid": True/False,
                "message": "验证结果"
            }
        """
        try:
            data = request.get_json()
            invite_code = data.get('invite_code')

            if not invite_code:
                return jsonify({
                    "success": False,
                    "error": "邀请码不能为空"
                }), 400

            from src.user.invite_manager import InviteManager
            invite_manager = InviteManager()

            result = invite_manager.validate_code(invite_code)

            return jsonify({
                "success": True,
                "valid": result.get('valid'),
                "message": result.get('error', '邀请码有效') if not result.get('valid') else '邀请码有效'
            })

        except Exception as e:
            logger.error(f"验证邀请码失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    # === Stripe支付Webhook ===

    @app.route('/api/webhook/stripe', methods=['POST'])
    def stripe_webhook():
        """
        Stripe Webhook端点
        处理订阅生命周期事件

        处理的事件：
        - checkout.session.completed - 支付成功
        - customer.subscription.updated - 订阅更新
        - customer.subscription.deleted - 订阅取消
        - invoice.payment_failed - 支付失败
        """
        try:
            payload = request.data
            sig_header = request.headers.get('Stripe-Signature')

            if not sig_header:
                logger.warning("Webhook请求缺少Stripe-Signature头部")
                return jsonify({"error": "Missing signature"}), 400

            # 验证webhook签名并处理事件
            from src.payment.webhook_handler import StripeWebhookHandler
            handler = StripeWebhookHandler()

            event = handler.verify_signature(payload, sig_header)
            if not event:
                return jsonify({"error": "Invalid signature"}), 400

            result = handler.handle_event(event)

            if result.get('success'):
                return jsonify({"received": True, "message": result.get('message')}), 200
            else:
                return jsonify({"error": result.get('message')}), 500

        except Exception as e:
            logger.error(f"处理Stripe webhook失败: {e}")
            return jsonify({"error": str(e)}), 500

    # === Stripe支付创建 ===

    @app.route('/api/create-checkout-session', methods=['POST'])
    def create_checkout_session():
        """
        API: 创建Stripe Checkout Session

        请求体：
            {
                "email": "user@example.com",
                "plan": "monthly" | "yearly",
                "language": "zh"  # 可选
            }

        返回：
            {
                "success": True,
                "checkout_url": "https://checkout.stripe.com/..."
            }
        """
        try:
            data = request.get_json()
            email = data.get('email')
            plan = data.get('plan', 'monthly')
            language = data.get('language', 'zh')

            # 获取timezone，如果未提供则根据language推断默认值
            timezone = data.get('timezone')
            if not timezone:
                # 根据语言推断时区
                timezone_map = {
                    'zh': 'Asia/Shanghai',
                    'ja': 'Asia/Tokyo',
                    'en': 'UTC'
                }
                timezone = timezone_map.get(language, 'UTC')

            # email是可选参数，如果未提供，Stripe Checkout会自动收集
            if not email:
                logger.info("未提供email，将由Stripe Checkout收集用户邮箱")

            from src.payment.stripe_service import StripeService
            stripe_service = StripeService()

            result = stripe_service.create_checkout_session(
                email=email,
                plan=plan,
                language=language,
                timezone=timezone
            )

            if result.get('success'):
                return jsonify({
                    "success": True,
                    "url": result.get('url')
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.get('error', '创建支付会话失败')
                }), 500

        except Exception as e:
            logger.error(f"创建支付会话失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    logger.info("API路由注册完成（前后端分离架构）")
