import requests
from lxml import etree

#SLEEP_TIME = 2
#UPDATE_COVER = False
#UPDATE_CHAPTER = False

COOKIE = 'remember_admin_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6Im9lR2U2VWxqRjM1UVMzNmhVRldIMGc9PSIsInZhbHVlIjoiYzMzc3VUWDhJY2lUekFRQnEwMmpRTnRIN05RYWdETE5JZW5oTGkwWlpsbk5DVGM1WHBMOVM1REdiR0RNZVJSTGw4Skhwc2piMytQV2JFbHVmT09xRkFJVzlUa3pzTXhxNkQyelRvXC9wS0g0ZjVpZEV0YkluZ1wvTFJFWWZhWG44cXR6U0FEOWZtWXlWQzBYQUJ6NWFHQ0JOOG8xY1JDdlFNbXF0WFBlQ0xIMitHMFluaHBncUpBNUJvVUlydDArWUkiLCJtYWMiOiJmMDU0N2RmYzJmZTBmZWFhZGMzZDQ5YjY3M2EwZWZmNWY2ZjgzYTRmZTUxYWFiNzI3YmM1NTk1OGRiZWMyMmVlIn0=; __cf_bm=DeYSCNkFs4bYBBVF3zQ_eOCF2iVIAF7acl_DbrlriZg-1681089794-0-AYftAAYf4Wjxa2VDwFSJ7MlG5NcD+cKhaNspBJqtsktlFq3l361+3DjJdziqcAtEAi9eopzPbGlgIXjc6n5/pKE0aqy+tXRylL2KvgMp1K78XFWrgaiqviszticS6IHF3w==; last_signin=1681089794922; XSRF-TOKEN=eyJpdiI6IlNrRjdYaVhlXC94d0lFMzlabWN4dFVRPT0iLCJ2YWx1ZSI6InZkK2JwNDVQUnNROFVWclJ3OFpjbnV3SE5yenR6QnliWDltYWdleW9SNHVuTk5tNFVUdGxQajlkVHdPRGJpXC9paVgyRXI4dk9wcUxTU25NRjRMdkZpUT09IiwibWFjIjoiMmY2Yjk1YWE3Y2JiNGQwOWM3ODNlNTEyNmNmODU3MjZhOTAzZjUxYjc5MDRkNDU1ZWIzZmY2NmE4ZjkzY2VjMiJ9; laravel_session=eyJpdiI6IlN6Q0N2SUtPemZaVm45TGYzVWFiNWc9PSIsInZhbHVlIjoiM3hxVTNzRVR3aUpaSDNleUdoS2VHWUhDb1RrR3pQVTVXRzZEMU1PdmZcL3dRWmpYcXhJTkd5aSs5Nk0yRHg0SVB3VXpCT0FJbWZ4K1BlQzV3alJGWE5RPT0iLCJtYWMiOiIzNzAwMWVlYjkwNzJlYjI3MTJjNDQyZWE0MTdlN2UxOGUzNzY2OGU5YWQzYWE5NDdmYzMyZmQxYjYwMzFhMjJmIn0='
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
ACCEPT = '*/*'
ACCEPT_ENCODING = 'gzip, deflate, br'
ACCEPT_LANGUAGE = 'zh-CN,zh;q=0.9'
HEADERS = {
    'cookie': COOKIE,
    'Accept': ACCEPT,
    'Accept-Encoding': ACCEPT_ENCODING,
    'Accept-Language': ACCEPT_LANGUAGE,
    'user-agent': USER_AGENT
}

XPATH_BOOKS_IN_PAGE = '//div[@class=\'layui-card\']/a[1]/@href' # 在“收藏页/排行榜页”的html中，指向“小说详情页url”的路径


def try_get(url, headers, params):
    for _ in range(3):
        try:
            data = requests.get(url=url, headers=headers, params=params)
        except Exception as e:
            print(e)
            print('retry...')
            continue
        else:
            return data

def from_page_to_books(start_page, end_page): # 从收藏页/排行榜页中，获取小说详情页的url
    page_url = 'https://masiro.me/admin/loadMoreNovels'
    book_url = []

    for i in range(start_page, end_page+1):
        page_params = {
            'page': i,
            'collection': 1
        }
        print('')
        print('page', i, 'downloading...')
        # print('')

        page_data = try_get(page_url, HEADERS, page_params).json()
        # print('page_data:')
        # print(page_data)
        # print('')

        html_in_data = page_data['html']
        # print('html_in_data:')
        # print(html_in_data)
        # print('')

        if not html_in_data: # 尾页判断
            print('page', i, 'is empty.')
            print('')
            break

        html_encoding = etree.HTMLParser(encoding='utf-8') # 为下一行做准备
        html_tree = etree.HTML(html_in_data, parser=html_encoding) # 为下一行做准备
        url_in_html = html_tree.xpath(XPATH_BOOKS_IN_PAGE)
        # print('url_in_html:')
        # print(url_in_html)
        # print('')
        book_url += url_in_html

    # 有可能爬取的时候恰好小说更新，去重
    book_url = list(set(book_url))

    return(book_url)


if __name__ == '__main__':
    pass