#!/bin/bash
# DNS 记录检查脚本
# 用于验证 jereo.co.jp 的 SendGrid 域名认证记录是否生效

echo "========================================"
echo "DNS 记录生效检查 - jereo.co.jp"
echo "========================================"
echo ""

DOMAIN="jereo.co.jp"
ALL_PASS=true

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_cname() {
    local subdomain=$1
    local expected=$2

    echo -n "检查 ${subdomain}.${DOMAIN} (CNAME)... "

    result=$(dig +short ${subdomain}.${DOMAIN} CNAME)

    if [ -z "$result" ]; then
        echo -e "${RED}✗ 未生效${NC}"
        echo "  预期值: ${expected}"
        ALL_PASS=false
    elif [[ "$result" == *"$expected"* ]]; then
        echo -e "${GREEN}✓ 已生效${NC}"
        echo "  返回值: ${result}"
    else
        echo -e "${YELLOW}⚠ 值不匹配${NC}"
        echo "  预期值: ${expected}"
        echo "  实际值: ${result}"
        ALL_PASS=false
    fi
    echo ""
}

check_txt() {
    local subdomain=$1
    local expected=$2

    echo -n "检查 ${subdomain}.${DOMAIN} (TXT)... "

    result=$(dig +short ${subdomain}.${DOMAIN} TXT)

    if [ -z "$result" ]; then
        echo -e "${RED}✗ 未生效${NC}"
        echo "  预期值: ${expected}"
        ALL_PASS=false
    elif [[ "$result" == *"$expected"* ]]; then
        echo -e "${GREEN}✓ 已生效${NC}"
        echo "  返回值: ${result}"
    else
        echo -e "${YELLOW}⚠ 值不匹配${NC}"
        echo "  预期值: ${expected}"
        echo "  实际值: ${result}"
        ALL_PASS=false
    fi
    echo ""
}

check_txt_root() {
    local expected=$1

    echo -n "检查 ${DOMAIN} (TXT - SPF)... "

    result=$(dig +short ${DOMAIN} TXT | grep "v=spf1")

    if [ -z "$result" ]; then
        echo -e "${RED}✗ 未找到 SPF 记录${NC}"
        echo "  预期值: ${expected}"
        ALL_PASS=false
    elif [[ "$result" == *"$expected"* ]]; then
        echo -e "${GREEN}✓ 已生效${NC}"
        echo "  返回值: ${result}"
    else
        echo -e "${YELLOW}⚠ SPF 记录存在但未包含 SendGrid${NC}"
        echo "  预期包含: ${expected}"
        echo "  实际值: ${result}"
        ALL_PASS=false
    fi
    echo ""
}

# 开始检查
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. DKIM 签名记录（必需）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_cname "s1._domainkey" "s1.domainkey.u57085830.wl081.sendgrid.net"
check_cname "s2._domainkey" "s2.domainkey.u57085830.wl081.sendgrid.net"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 链接品牌化记录（推荐）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_cname "url7359" "sendgrid.net"
check_cname "57085830" "sendgrid.net"
check_cname "em7660" "u57085830.wl081.sendgrid.net"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. SPF 记录（必需）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_txt_root "include:sendgrid.net"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. DMARC 记录（强烈推荐）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_txt "_dmarc" "v=DMARC1"

# 总结
echo ""
echo "========================================"
if [ "$ALL_PASS" = true ]; then
    echo -e "${GREEN}✓ 所有 DNS 记录已生效！${NC}"
    echo ""
    echo "下一步："
    echo "1. 返回 SendGrid Dashboard"
    echo "2. 点击 'Verify' 按钮验证域名"
    echo "3. 验证成功后，更新 Render 环境变量"
else
    echo -e "${RED}✗ 部分 DNS 记录未生效或配置错误${NC}"
    echo ""
    echo "建议："
    echo "1. 等待更长时间（DNS 生效可能需要 30 分钟）"
    echo "2. 检查 muumuu domain 设置是否正确"
    echo "3. 确认记录已保存"
fi
echo "========================================"
