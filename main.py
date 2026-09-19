import requests
import time

# 公共请求头
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://advanced.fenqubiao.com",
    "Referer": "https://advanced.fenqubiao.com/Macro/Journal?name=%E5%9C%B0%E7%90%83%E7%A7%91%E5%AD%A6&year=2025",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Cookie 字符串
cookie_str = (
    "Hm_lvt_0dae59e1f85da1153b28fb5a2671647f=1789707297; "
    "HMACCOUNT=9C7E8A4B64FA25A6; "
    "Hm_lvt_7e6e274f8fab6425c743106cbd2e8d99=1789707342; "
    "Hm_lpvt_0dae59e1f85da1153b28fb5a2671647f=1789707677; "
    "auth=27C450E6E235D6E6AADC9B27C6D905CC22EC14E693F38B2CEF770B9B900B6EF9CD1606D160EB55770AC545C117283D27063A8E2B1CAE712167938CFACF48ED9709ACC5211E4E23828638C0D9CD354FDEA50DA317302F78312B683665DFF44F710F6CB50A184CAAB449E43FFBECF5624F6158CA425A2A52E1FBDA3A6F5987E96C2EB0997F3E9D3D12896B2B23B551DD366A510E91593518F980F2587C9F0EAE7F6BBF0E4EAEDA3B855381E153521F49E0AA93C3EC7FCC7B8EE73E734DD65C30DA7C1AFED5F3C548129F2CA345BAF4C065255A6F054C8F08978C840012E9A1281F8DF08F1DF2BB7E2241DE18AF549E011D6970E6BCB69D379FE23BF0ED85C3A2296B59584AD841DEF1EA719284C998218F48C3C1CA8E5B0D1C5A0BA774C00D0463FD998D3E777A1112ED58E0E1896227F59788D27791C47A7111549CB73AD0AFDEAC9211023E40C57DC830AFAB570AC757F1AD3D790EAFCF8177E9DBC85D79F442ECE2ACD7901E8CC89A547ABA19E47E98879D48460B15AB14DBACC9BD084CF9516EF9C36ADA6E141B160B750CB2F32255F452F3B2D117FBFBDA4A87A9B296F8AD5BD1EEBB5B5B8005DDD6820FE90AA8AC3026FE5698FC01497B2D0A6F9B1348FF978C9C3A0CF3EB566638B00A422D4536E767D1D333860A008AB0A358C483DE0E51CC5ADCB8BC75FBA8537431D7E3DB0D; "
    "Hm_lpvt_7e6e274f8fab6425c743106cbd2e8d99=1789707808"
)


# 将 Cookie 字符串解析为字典
def parse_cookie(cookie_str):
    cookies = {}
    for item in cookie_str.split("; "):
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key] = value
    return cookies


cookies = parse_cookie(cookie_str)

# 创建 Session
session = requests.Session()
session.headers.update(headers)
session.cookies.update(cookies)


# ========== 请求 1: PageData draw=3 start=40 ==========
def get_page_data(draw, start):
    url1 = "https://advanced.fenqubiao.com/Macro/PageData"
    data1 = (
        f"draw={draw}&columns%5B0%5D%5Bdata%5D=&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&"
        "columns%5B1%5D%5Bdata%5D=title&columns%5B1%5D%5Bname%5D=title&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&"
        "columns%5B2%5D%5Bdata%5D=issn&columns%5B2%5D%5Bname%5D=issn&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=false&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&"
        "columns%5B3%5D%5Bdata%5D=class&columns%5B3%5D%5Bname%5D=class&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=false&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&"
        f"order%5B0%5D%5Bcolumn%5D=0&order%5B0%5D%5Bdir%5D=asc&start={start}&length=20&search%5Bvalue%5D=&search%5Bregex%5D=false&name=%E5%9C%B0%E7%90%83%E7%A7%91%E5%AD%A6&year=2025"
    )
    resp1 = session.post(url1, data=data1)

    print(f"Response {draw}:", resp1.json())
    with open(f"response{draw}.json", "w", encoding="utf-8") as f:
        f.write(resp1.text)


for i in range(30):
    get_page_data(draw=i+1, start=i * 20)
    time.sleep(2)
