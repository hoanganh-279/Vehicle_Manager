"""
momo.py — Module tích hợp cổng thanh toán MoMo
Dùng cho hệ thống Quản lý Bãi Xe NQT
"""

import uuid
import hmac
import hashlib
import json
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# CẤU HÌNH — đọc từ .env
# =============================================================================

MOMO_ENDPOINT    = os.getenv('MOMO_ENDPOINT',     'https://test-payment.momo.vn/v2/gateway/api/create')
MOMO_PARTNER_CODE= os.getenv('MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY  = os.getenv('MOMO_ACCESS_KEY',   '')
MOMO_SECRET_KEY  = os.getenv('MOMO_SECRET_KEY',   '')
MOMO_REDIRECT_URL= os.getenv('MOMO_REDIRECT_URL', 'http://localhost:5000/payment/result')
MOMO_IPN_URL     = os.getenv('MOMO_IPN_URL',      'http://localhost:5000/payment/result')

# =============================================================================
# HÀM TẠO CHỮ KÝ
# =============================================================================

def _build_signature(raw: str) -> str:
    """Tạo HMAC SHA256 signature từ raw string."""
    return hmac.new(
        bytes(MOMO_SECRET_KEY, 'ascii'),
        bytes(raw, 'ascii'),
        hashlib.sha256
    ).hexdigest()

# =============================================================================
# HÀM CHÍNH — TẠO THANH TOÁN MOMO
# =============================================================================

def create_momo_payment(
    order_id: str,
    amount: int,
    order_info: str = 'Thanh toán bãi xe NQT',
    request_type: str = 'captureWallet',
    extra_data: str = '',
) -> dict:
    """
    Tạo URL thanh toán MoMo.

    Args:
        order_id:     Mã đơn hàng duy nhất (thường là vehicle_id hoặc topup_id)
        amount:       Số tiền (VND, kiểu int)
        order_info:   Mô tả đơn hàng hiển thị cho khách
        request_type: 'captureWallet' (ví MoMo) hoặc 'payWithATM'
        extra_data:   Dữ liệu thêm (base64 JSON hoặc chuỗi rỗng)

    Returns:
        {
            'success': True/False,
            'pay_url': 'https://...',   # URL chuyển hướng khách hàng
            'order_id': '...',
            'message': '...'
        }
    """
    request_id = str(uuid.uuid4())
    amount_str = str(amount)

    # Chuỗi ký theo đúng thứ tự alphabet của MoMo
    raw_signature = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={amount_str}"
        f"&extraData={extra_data}"
        f"&ipnUrl={MOMO_IPN_URL}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={MOMO_PARTNER_CODE}"
        f"&redirectUrl={MOMO_REDIRECT_URL}"
        f"&requestId={request_id}"
        f"&requestType={request_type}"
    )

    signature = _build_signature(raw_signature)

    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'partnerName': 'Bãi Xe NQT',
        'storeId':     'NQTParkingStore',
        'requestId':   request_id,
        'amount':      amount_str,
        'orderId':     order_id,
        'orderInfo':   order_info,
        'redirectUrl': MOMO_REDIRECT_URL,
        'ipnUrl':      MOMO_IPN_URL,
        'lang':        'vi',
        'extraData':   extra_data,
        'requestType': request_type,
        'signature':   signature,
    }

    logger.info(f"[MoMo] Tạo thanh toán | order_id={order_id} | amount={amount}")

    try:
        response = requests.post(
            MOMO_ENDPOINT,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        if result.get('resultCode') == 0:
            logger.info(f"[MoMo] Thành công | order_id={order_id} | payUrl={result.get('payUrl','')[:60]}")
            return {
                'success': True,
                'pay_url': result.get('payUrl', ''),
                'order_id': order_id,
                'request_id': request_id,
                'message': result.get('message', 'Tạo thanh toán thành công'),
            }
        else:
            logger.warning(f"[MoMo] Lỗi từ API | resultCode={result.get('resultCode')} | message={result.get('message')}")
            return {
                'success': False,
                'pay_url': None,
                'order_id': order_id,
                'message': result.get('message', 'Lỗi từ MoMo API'),
            }

    except requests.exceptions.Timeout:
        logger.error(f"[MoMo] Timeout | order_id={order_id}")
        return {'success': False, 'pay_url': None, 'order_id': order_id, 'message': 'MoMo API timeout'}

    except requests.exceptions.ConnectionError:
        logger.error(f"[MoMo] Không kết nối được | order_id={order_id}")
        return {'success': False, 'pay_url': None, 'order_id': order_id, 'message': 'Không thể kết nối MoMo'}

    except requests.exceptions.HTTPError as e:
        logger.error(f"[MoMo] HTTP Error | order_id={order_id} | {e}")
        return {'success': False, 'pay_url': None, 'order_id': order_id, 'message': f'Lỗi HTTP: {str(e)}'}

    except Exception as e:
        logger.error(f"[MoMo] Lỗi không xác định | order_id={order_id} | {e}")
        return {'success': False, 'pay_url': None, 'order_id': order_id, 'message': 'Lỗi hệ thống'}


# =============================================================================
# XÁC THỰC IPN CALLBACK TỪ MOMO
# =============================================================================

def verify_momo_ipn(data: dict) -> bool:
    """
    Xác thực chữ ký IPN callback từ MoMo gửi về.
    Gọi trong route /payment/result khi MoMo POST về.

    Args:
        data: dict từ request.json() của Flask

    Returns:
        True nếu chữ ký hợp lệ
    """
    raw = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={data.get('amount','')}"
        f"&extraData={data.get('extraData','')}"
        f"&message={data.get('message','')}"
        f"&orderId={data.get('orderId','')}"
        f"&orderInfo={data.get('orderInfo','')}"
        f"&orderType={data.get('orderType','')}"
        f"&partnerCode={data.get('partnerCode','')}"
        f"&payType={data.get('payType','')}"
        f"&requestId={data.get('requestId','')}"
        f"&responseTime={data.get('responseTime','')}"
        f"&resultCode={data.get('resultCode','')}"
        f"&transId={data.get('transId','')}"
    )
    expected = _build_signature(raw)
    return expected == data.get('signature', '')
