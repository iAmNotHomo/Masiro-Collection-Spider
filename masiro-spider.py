import asyncio, aiohttp, aiofiles
from lxml import html
import random, os

FILE_DIR = 'E:\\books\\'
ERROR_LOG_DIR = FILE_DIR + 'failed.log'
SKIP_LOG_DIR = FILE_DIR + 'skipped.log'

USER_NAME = 'dyzer@qq.com'
PASSWORD = 'D142857ing'

# 爬取收藏页的起始页数
# 一页30本
START_PAGE = 1
END_PAGE = 2

# 单个请求连接超时的阈值时间
TIME_OUT = 16

# 连接尝试的次数
TRY_TIMES = 4

# 请求延迟时间 = random() * SLEEP_TIME
SLEEP_TIME = 4

# 是否购买付费章节
# if PURCHASE and (价格 <= MAX_COST): 购买该章节
PURCHASE = False
MAX_COST = 0

MAX_THREAD = 8

# UPDATE_COVER = False
UPDATE_TEXT = False
UPDATE_PIC = False

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
ACCEPT = '*/*'
ACCEPT_ENCODING = 'gzip, deflate, br'
ACCEPT_LANGUAGE = 'zh-CN,zh;q=0.9'
HEADERS = {
    'Accept': ACCEPT,
    'Accept-Encoding': ACCEPT_ENCODING,
    'Accept-Language': ACCEPT_LANGUAGE,
    'user-agent': USER_AGENT
}

MASIRO = 'https://masiro.me'
MASIRO_COLLECTION = MASIRO + '/admin/loadMoreNovels'
MASIRO_LOGIN = MASIRO + '/admin/auth/login'
XPATH_LOGIN = '//input[@class=\'csrf\']/@value'
XPATH_BOOKS_URL_IN_PAGE = '//div[@class=\'layui-card\']/a[1]/@href' # 在“收藏页/排行榜页”的html中，指向“小说详情页url”的路径
XPATH_BOOK_NAME_IN_BOOK = '//title/text()'
XPATH_SECTIONS_NAME_IN_BOOK = '//div[@class="chapter-content"]//li[@id][%d]/@id'
XPATH_CHAPTERS_IN_BOOK = '//div[@class="chapter-content"]//li[not(@class)][%d]//a'
XPATH_CHAPTERS_NAME_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '//span[@style="overflow: hidden; text-overflow: ellipsis; margin: 0;"]/text()'
XPATH_CHAPTERS_URL_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@href'
XPATH_CHAPTERS_COST_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@data-cost'
XPATH_CHAPTERS_PAYED_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@data-payed'
XPATH_TEXT_IN_CHAPTER = '//div[@class="box-body nvl-content"]//text()'
XPATH_PIC_IN_CHAPTER = '//div[@class="box-body nvl-content"]//img/@src'


async def session_try_get(session, url, headers, params={}):
    for i in range(TRY_TIMES):
        try:
            data = await session.get(url=url, headers=headers, params=params, timeout=TIME_OUT)
        except Exception as e:
            print(e)
            if i < TRY_TIMES - 1:
                print('retrying url:' + url)
            else:
                with open(ERROR_LOG_DIR, mode='a', encoding='utf-8') as log:
                    log.write(url + '\n')
                print('failed to get url:', url)
            continue
        else:
            return data


def use_xpath(html_page, data_xpath):
    page_html = html.fromstring(html_page)
    data = page_html.xpath(data_xpath)
    return data


def my_make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def format_text(str0):
    str1 = str0.replace('/', '-').replace('\\', '-').replace('<', '-')
    str1 = str1.replace('>', '-').replace('|', '-').replace('\"', '-')
    str1 = str1.replace('?', '-').replace('*', '-').replace(':', '-')
    str1 = str1.replace('\xa0','').replace('\n','').replace('\r', '')
    str1 = str1.replace('\t', '').replace('\u3000', '')
    str1 = str1.replace('&nbsp;','').replace('\u002F', '-')
    return str1


def remove_useless_spaces(str0):
    str1 = str0
    while str1[0] == ' ':
        str1 = str1[1:]
    while str1[-1] == ' ':
        str1 = str1[:-1]
    return str1


def chapter_skiped(url):
    with open(SKIP_LOG_DIR, mode='a', encoding='utf-8') as log:
        log.write(url + '\n')
    print('url skipped:', url)


async def save_chapter_text(file_path, chapter_text):
    full_file_path = file_path + '.txt'
    if os.path.exists(full_file_path) and not UPDATE_TEXT:
        return
    async with aiofiles.open(full_file_path, mode='w', encoding='utf-8') as file:
        for paragraph in chapter_text:
            await file.write(paragraph)
    print(full_file_path + ' downloaded.')


async def save_chapter_pic(session, file_path, chapter_pic):
    for i in range(len(chapter_pic)):
        full_file_path = file_path + '-' + str(i) + '.jpeg'
        if os.path.exists(full_file_path) and not UPDATE_PIC:
            continue
        async with aiofiles.open(full_file_path, mode='wb') as file:
            response = await session_try_get(session, chapter_pic[i], HEADERS)
            if not response:
                return
            pic_data = await response.read()
            await file.write(pic_data)
        print(full_file_path + ' downloaded.')


async def download_chapter(session, file_path, chapter_dict):
    # chapter_dict = {'NO','name','url','cost','payed'}

    chapter_cost = int(chapter_dict['cost'])
    chapter_payed = int(chapter_dict['payed'])
    chapter_full_url = MASIRO + chapter_dict['url']

    if not PURCHASE and chapter_cost > 0:
        chapter_skiped(chapter_full_url)
        return
    if PURCHASE and chapter_cost > MAX_COST and not chapter_payed:
    # 保留 PURCHASE 条件, 制造逻辑短路
        chapter_skiped(chapter_full_url)
        return
    
    chapter_file_path = file_path + str(chapter_dict['NO']) + '. ' + chapter_dict['name']

    await asyncio.sleep(random.random() * SLEEP_TIME)

    if PURCHASE and chapter_cost <= MAX_COST:
        return # 打钱不会写捏, 没想到吧
    
    response = await session_try_get(session, chapter_full_url, HEADERS)
    if not response:
        return
    chapter_page = await response.text()

    chapter_text = use_xpath(chapter_page, XPATH_TEXT_IN_CHAPTER)
    await save_chapter_text(chapter_file_path, chapter_text)

    chapter_pic_url = use_xpath(chapter_page, XPATH_PIC_IN_CHAPTER)
    if chapter_pic_url:
        await save_chapter_pic(session, chapter_file_path, chapter_pic_url)


async def download_book(session, book_url, thread_count):
    book_full_url = MASIRO + book_url
    chapter_url = []
    chapter_name = []

    async with thread_count:
        await asyncio.sleep(random.random() * SLEEP_TIME)
        
        response = await session_try_get(session, book_full_url, HEADERS)
        if not response:
            return
        book_info_page = await response.text() # 小说详情页的html

        # 通过xpath从html提取信息
        # 这个html_tree之后被多次使用, 所以没有调用use_xpath()
        html_tree = html.fromstring(book_info_page)
        
        book_name = html_tree.xpath(XPATH_BOOK_NAME_IN_BOOK)
        book_name_str = format_text(book_name[0][7:])
        book_dir = FILE_DIR + book_name_str + '\\'
        my_make_dir(book_dir)

        section_NO = 1 # 分卷序号
        #xpath_sections_in_book = (XPATH_SECTIONS_NAME_IN_BOOK % section_NO).rsplit('/',1)[0] # 从右侧切，切1次，返回[0]位置
        section_name = html_tree.xpath(XPATH_SECTIONS_NAME_IN_BOOK % section_NO)
        while section_name:
            section_name_str = format_text(section_name[0])
            section_dir = book_dir + str(section_NO) + '. ' + section_name_str + '\\'
            my_make_dir(section_dir)

            chapter_name = html_tree.xpath(XPATH_CHAPTERS_NAME_IN_BOOK % section_NO)
            chapter_url = html_tree.xpath(XPATH_CHAPTERS_URL_IN_BOOK % section_NO)
            chapter_cost = html_tree.xpath(XPATH_CHAPTERS_COST_IN_BOOK % section_NO)
            chapter_payed = html_tree.xpath(XPATH_CHAPTERS_PAYED_IN_BOOK % section_NO)

            # 下载分卷中的章节
            chapter_download_tasks = []
            for i in range(len(chapter_url)):
                chapter_dict = {
                    'NO': i+1,
                    'name': remove_useless_spaces(format_text(chapter_name[i])),
                    'url': chapter_url[i],
                    'cost': chapter_cost[i],
                    'payed': chapter_payed[i]
                }
                chapter_download_tasks.append(download_chapter(session, section_dir, chapter_dict))
            _,_ = await asyncio.wait(chapter_download_tasks)

            section_NO += 1
            section_name = html_tree.xpath(XPATH_SECTIONS_NAME_IN_BOOK % section_NO)

        # print(book_name_str)
        # print(book_full_url)
        # print(section_name_str)
        # print(editted_chapter_name)
        # print(chapter_url)


async def download_collection(session): # 从收藏页/排行榜页中，获取小说详情页的url
    book_url = []
    print('')

    for i in range(START_PAGE, END_PAGE+1):
        page_params = {
            'page': i,
            'collection': 1
        }
        print('extracting page', i, '...')
        # print('')

        response = await session_try_get(session, MASIRO_COLLECTION, HEADERS, page_params)
        if not response:
            continue
        print('done.')
        print('')
        page_data = await response.json()
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
        
        url_in_html = use_xpath(html_in_data, XPATH_BOOKS_URL_IN_PAGE)
        # print('url_in_html:')
        # print(url_in_html)
        # print('')

        book_url += url_in_html

    # 有可能爬取的时候恰好小说更新，去重
    book_url = list(set(book_url))

    thread_count = asyncio.Semaphore(MAX_THREAD)

    book_download_tasks = []
    for url in book_url:
        book_download_tasks.append(download_book(session, url, thread_count))
    _,_ = await asyncio.wait(book_download_tasks)


async def login(session):
    print('')
    print('start login...')

    response = await session_try_get(session, MASIRO_LOGIN, HEADERS)
    if not response:
        exit('login failed.')
    page_html = await response.text()
    token = use_xpath(page_html, XPATH_LOGIN)
    
    params = {
        'username': USER_NAME,
        'password': PASSWORD,
        'remember': '1',
        '_token': token[0]
    }

    headers = HEADERS
    headers['x-csrf-token'] = token[0]
    headers['x-requested-with'] = 'XMLHttpRequest'

    for i in range(TRY_TIMES):
        try:
            response = await session.post(url=MASIRO_LOGIN, headers=headers, data=params, timeout=TIME_OUT)
            print('login succeeded.')
        except Exception as e:
            print(e)
            if i < TRY_TIMES - 1:
                print('retrying login...')
            else:
                print('login failed.')
        else:
            break


async def base():
    my_make_dir(format_text(FILE_DIR))

    async with aiohttp.ClientSession() as session:
        await login(session)
        await download_collection(session)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(base())