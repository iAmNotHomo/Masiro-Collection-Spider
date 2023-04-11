import requests
import asyncio, aiohttp, aiofiles
from lxml import etree
import random, os

FILE_DIR = 'D:\\books\\'
START_PAGE = 1
END_PAGE = 1

TIME_OUT = 16
SLEEP_TIME = 3
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

MASIRO_URL = 'https://masiro.me'
XPATH_BOOKS_URL_IN_PAGE = '//div[@class=\'layui-card\']/a[1]/@href' # 在“收藏页/排行榜页”的html中，指向“小说详情页url”的路径
XPATH_BOOK_NAME_IN_BOOK = '//title/text()'
XPATH_SECTIONS_NAME_IN_BOOK = '//div[@class="chapter-content"]//li[@id][%d]/@id'
XPATH_CHAPTERS_NAME_IN_BOOK = '//div[@class="chapter-content"]//li[not(@class)][%d]//a//span[@style="overflow: hidden; text-overflow: ellipsis; margin: 0;"]/text()'
XPATH_CHAPTERS_URL_IN_BOOK = '//div[@class="chapter-content"]//li[not(@class)][%d]//a/@href'

'''
同步：获取小说详情页url
异步：获取章节url、下载章节
'''
'''
async def aio_try_get(url, headers, params):
    session = aiohttp.ClientSession()
    for i in range(3):
        try:
            data = await session.get(url=url, headers=headers, params=params)
        except Exception as e:
            print('time', i+1, 'error')
            print(e)
            if i < 2:
                print('retrying...')
            else:
                print('failed to get.')
                session.close()
            continue
        else:
            session.close()
            return data
'''
def try_get(url, headers, params):
    for i in range(3):
        try:
            data = requests.get(url=url, headers=headers, params=params, timeout=TIME_OUT)
        except Exception as e:
            print(e)
            if i < 2:
                print('retrying...')
            else:
                print('failed to get.')
            continue
        else:
            return data

def my_make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def format_text(str):
    str1 = str.replace('/', '-').replace('\\', '-').replace('<', '-')
    str1 = str1.replace('>', '-').replace('|', '-').replace('\"', '-')
    str1 = str1.replace('?', '-').replace('*', '-').replace(':', '-')
    str1 = str1.replace('\xa0','').replace('\n','').replace('\r', '')
    str1 = str1.replace('\t', '').replace('\u3000', '').replace('\u002F', '-')
    return str1

def from_page_to_books(start_page, end_page): # 从收藏页/排行榜页中，获取小说详情页的url
    page_url = 'https://masiro.me/admin/loadMoreNovels'
    book_url = []

    for i in range(start_page, end_page+1):
        page_params = {
            'page': i,
            'collection': 1
        }
        print('')
        print('extracting page', i, '...')
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
        
        # 通过xpath从html提取信息
        html_encoding = etree.HTMLParser(encoding='utf-8')
        html_tree = etree.HTML(html_in_data, parser=html_encoding)
        url_in_html = html_tree.xpath(XPATH_BOOKS_URL_IN_PAGE)
        # print('url_in_html:')
        # print(url_in_html)
        # print('')

        book_url += url_in_html

    # 有可能爬取的时候恰好小说更新，去重
    book_url = list(set(book_url))

    return(book_url)

async def download_book(book_url):
    book_full_url = MASIRO_URL + book_url
    chapter_url = []
    chapter_name = []

    await asyncio.sleep(random.random() * SLEEP_TIME)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=book_full_url,headers=HEADERS) as response:
            book_info_page = await response.text() # 小说详情页的html
    
    # 通过xpath从html提取信息
    html_encoding = etree.HTMLParser(encoding='utf-8')
    html_tree = etree.HTML(book_info_page, parser=html_encoding)
    
    book_name = html_tree.xpath(XPATH_BOOK_NAME_IN_BOOK)
    book_name_str = format_text(book_name[0][7:])
    book_dir = FILE_DIR + book_name_str + '\\'
    my_make_dir(book_dir)

    section_NO = 1
    #xpath_sections_in_book = (XPATH_SECTIONS_NAME_IN_BOOK % section_NO).rsplit('/',1)[0] # 从右侧切，切1次，返回[0]位置
    section_name = html_tree.xpath(XPATH_SECTIONS_NAME_IN_BOOK % section_NO)
    while section_name:
        section_name_str = format_text(section_name[0])
        section_dir = book_dir + str(section_NO) + '. ' + section_name_str + '\\'
        my_make_dir(section_dir)

        chapter_url = html_tree.xpath(XPATH_CHAPTERS_URL_IN_BOOK % section_NO)
        chapter_name = html_tree.xpath(XPATH_CHAPTERS_NAME_IN_BOOK % section_NO)
        editted_chapter_name = []
        for name in chapter_name:
            editted_chapter_name.append(format_text(name))

        section_download_tasks = []
        for i in range(len(chapter_url)):
            section_download_tasks.append(download_section(section_dir, section_name_str, editted_chapter_name[i], chapter_url[i]))
        await asyncio.wait(section_download_tasks)
    
        section_NO += 1
        section_name = html_tree.xpath(XPATH_SECTIONS_NAME_IN_BOOK % section_NO)

    # print(book_name_str)
    # print(book_full_url)
    # print(section_name_str)
    # print(editted_chapter_name)
    # print(chapter_url)
    

async def download_section(file_path, section_name, chapter_name, chapter_url):
    # print(chapter_name)
    pass

async def download_chapter(file_path, chapter_name, chapter_url):
    pass

async def base():
    my_make_dir(format_text(FILE_DIR))
    book_list = from_page_to_books(START_PAGE, END_PAGE)
    # print(book_list)

    book_download_tasks = [] # 异步任务列表
    for book_url in book_list:
        book_download_tasks.append(download_book(book_url))
    await asyncio.wait(book_download_tasks)

if __name__ == '__main__':
    asyncio.run(base())