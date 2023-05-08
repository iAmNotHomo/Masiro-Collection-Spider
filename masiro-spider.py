import asyncio, aiohttp, aiofiles
from lxml import html
import random, os, zhconv, time, functools

FILE_DIR = 'D:\\books\\masiro\\'
USER_NAME = ''
PASSWORD = ''

MODE_USE_LOCAL_BOOK_LIST = 0 # 使用以前保存到本地的书单
MODE_UPDATE_BOOK_LIST = 1 # 更新书单并使用
MODE = MODE_UPDATE_BOOK_LIST # 设置爬虫的运行模式。首次运行时，需要设置为 MODE_UPDATE_BOOK_LIST

# 爬取收藏页的起始页码, 从1开始数
# 一页30本
START_PAGE = 1
END_PAGE = 999 # 如果要爬取所有收藏, 可以填999

# 一次请求等这么久还没收到服务器回复, 就重发请求
TIME_OUT = 16 # 秒

# 试了这么多次还连不上服务器, 就放弃
TRY_TIMES = 4

# 遇到付费章节, if PURCHASE and (价格 <= MAX_COST): 购买该章节
PURCHASE = True # 是否购买付费章节
MAX_COST = 2 # 价格高于这个数, 就不买

# 请求延迟时间 = random() * SLEEP_TIME
SLEEP_TIME = 2 # 秒

# 并发数量
MAX_THREAD = 4

# 为三个文件命名: 下载失败.log, 太贵不买.log, 书单.txt
TIME = time.localtime(time.time())
TIME_STR = '_%d_%d_%d_%d_%d' % (TIME.tm_year, TIME.tm_mon, TIME.tm_mday, TIME.tm_hour, TIME.tm_min)
ERROR_LOG_DIR = FILE_DIR + 'failed' + TIME_STR + '.log'
SKIP_LOG_DIR = FILE_DIR + 'skipped' + TIME_STR + '.log'
BOOK_LIST_DIR = FILE_DIR + 'book_list.txt'

# 是否更新封面图(还没实现, 大概不会实现)/小说文本/小说插图
# 建议都别 True (
UPDATE_COVER = False
UPDATE_TEXT = False
UPDATE_PIC = False


# 下面的都不要改

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
MASIRO_LOGIN = MASIRO + '/admin/auth/login'
MASIRO_COLLECTION = MASIRO + '/admin/loadMoreNovels'
MASIRO_PAY = MASIRO + '/admin/pay'

XPATH_LOGIN = '//input[@class="csrf"]/@value'
XPATH_BOOKS_URL_IN_PAGE = '//div[@class="layui-card"]/a[1]/@href' # 在“收藏页/排行榜页”的html中，指向“小说详情页url”的路径
XPATH_BOOK_NAME_IN_BOOK = '//title/text()'
XPATH_SECTIONS_NAME_IN_BOOK = '//div[@class="chapter-content"]//li[@id][%d]/@id'
XPATH_CHAPTERS_IN_BOOK = '//div[@class="chapter-content"]//li[not(@class)][%d]//a'
XPATH_CHAPTERS_NAME_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '//span[@style="overflow: hidden; text-overflow: ellipsis; margin: 0;"]/text()'
XPATH_CHAPTERS_URL_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@href'
XPATH_CHAPTERS_COST_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@data-cost'
XPATH_CHAPTERS_PAYED_IN_BOOK = XPATH_CHAPTERS_IN_BOOK + '/@data-payed'
XPATH_TEXT_IN_CHAPTER = '//div[@class="box-body nvl-content"]//text()'
XPATH_PIC_IN_CHAPTER = '//div[@class="box-body nvl-content"]//img/@src'


class downloaded_dict: 
    # 因为 download_collection() 内初始化下载任务的时候, 为了最小化网络波动的影响(很容易波动), 把任务列表重复了3遍(tasks = tasks*3), 后2遍用于查缺补漏. 在 UPDATE_TEXT 模式下, 为了在3轮遍历中不重复下载, 需要设置一个 visited 表. 这个类实现的就是 visited 表的功能. 但是转念一想, UPDATE_TEXT 功能屁用没有, 因为如果需要更新某章节/某小说, 直接删除对应文件就可以. 所以这个类就作为历史问题, 遗留在了这里.

    def __init__(self) -> None:
        self.downloaded = {}
    
    def new_chapter(self, book, section, chapter) -> None:
        if not book in self.downloaded:
            self.downloaded[book] = {section: chapter}
        if not section in self.downloaded[book]:
            self.downloaded[book][section] = chapter
        self.downloaded[book][section][chapter] = True
    
    def search_chapter(self, book, section, chapter) -> bool:
        if not book in self.downloaded:
            return False
        if not section in self.downloaded[book]:
            return False
        if not chapter in self.downloaded[book][section]:
            return False
        return True

# downloaded_text = downloaded_dict()
# 为了使用这个类, 曾在调用 download_chapter() 以前, 定义 downloaded_params = [book_name_str, section_name_str, chapter_name_str], 意图传参. 现作为注释保留.


async def session_try_get(session, url, headers, params={}):
    for i in range(TRY_TIMES):
        try:
            data = await session.get(url=url, headers=headers, params=params, timeout=TIME_OUT)
        except Exception as e:
            print(e)
            if i < TRY_TIMES - 1:
                print('retrying url:', url)
            else:
                with open(ERROR_LOG_DIR, mode='a', encoding='utf-8') as log:
                    log.write('failed to get: ' + url + '\n')
                print('failed to get: ' + url)
            continue
        else:
            return data


async def session_try_post(session, url, headers, data={}):
    for i in range(TRY_TIMES):
        try:
            data = await session.post(url=url, headers=headers, data=data, timeout=TIME_OUT)
        except Exception as e:
            print(e)
            if i < TRY_TIMES - 1:
                print('retrying url:', url)
            else:
                with open(ERROR_LOG_DIR, mode='a', encoding='utf-8') as log:
                    log.write('failed to post: ' + url + '\n')
                print('failed to post: ' + url)
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
    print('skipped:', url)


async def save_chapter_text(file_path, chapter_text):
    full_file_path = file_path + '.txt'
    if os.path.exists(full_file_path) and not UPDATE_TEXT:
        return
    async with aiofiles.open(full_file_path, mode='w', encoding='utf-8') as file:
        for paragraph in chapter_text:
            simplified_paragraph = zhconv.convert(paragraph, 'zh-hans')
            if simplified_paragraph[-1] != '\n':
                await file.write(simplified_paragraph + '\n')
            else:
                await file.write(simplified_paragraph)
    print(full_file_path + ' downloaded.')


async def save_chapter_pic(session, file_path, chapter_pic):
    for i in range(len(chapter_pic)):
        if chapter_pic[i].startswith('static'):
            continue
        if chapter_pic[i].find('m.qpic.cn/psc') != -1:
            continue

        file_type = ''
        if chapter_pic[i].find('.googleusercontent.com/') != -1:
            file_type = 'png'
        elif chapter_pic[i].find('m.qpic.cn') != -1:
            file_type = 'webp'
        else:
            file_type = chapter_pic[i].split('?',1)[0].rsplit('.',1)[1]

        full_file_path = file_path + '-' + str(i) + '.' + file_type

        if os.path.exists(full_file_path) and not UPDATE_PIC:
            continue

        async with aiofiles.open(full_file_path, mode='wb') as file:
            response = await session_try_get(session, chapter_pic[i], HEADERS)
            if not response:
                return
            pic_data = await response.read()
            await file.write(pic_data)

        print(full_file_path + ' downloaded.')


async def purchase_chapter(session, token, cost, chapter_id):
    params = {
        'type': '2',
        'object_id': chapter_id,
        'cost': cost
    }
    headers = {
        'User-Agent': HEADERS['user-agent'],
        'x-csrf-token': token,
        'x-requested-with': 'XMLHttpRequest'
    }
    response_text = ''
    response = await session_try_post(session, MASIRO_PAY, headers, params)
    response_text = await response.text()
    return response_text


async def download_chapter(session, token, file_path, chapter_dict):
    # chapter_dict = {'NO','name','url','cost','payed'}

    chapter_cost = int(chapter_dict['cost'])
    chapter_payed = int(chapter_dict['payed'])
    chapter_full_url = MASIRO + chapter_dict['url']

    if not chapter_payed:
        if chapter_cost > MAX_COST:
            chapter_skiped(chapter_full_url)
            return
        if not PURCHASE and chapter_cost:
            chapter_skiped(chapter_full_url)
            return
    
    chapter_file_path = file_path + str(chapter_dict['NO']) + '. ' + chapter_dict['name']

    await asyncio.sleep(random.random() * SLEEP_TIME)

    if PURCHASE and chapter_cost and not chapter_payed:
        chapter_id = chapter_full_url.rsplit('=',1)[1]
        pay_response = await purchase_chapter(session, token, chapter_dict['cost'], chapter_id)
        if not pay_response:
            return
        print('chapter %s purchased. cost %dG.' % (chapter_id, chapter_cost))
    
    response = await session_try_get(session, chapter_full_url, HEADERS)
    if not response:
        return
    chapter_page = await response.text()
    if not chapter_page:
        return

    chapter_text = use_xpath(chapter_page, XPATH_TEXT_IN_CHAPTER)
    await save_chapter_text(chapter_file_path, chapter_text)

    chapter_pic_url = use_xpath(chapter_page, XPATH_PIC_IN_CHAPTER)
    if chapter_pic_url:
        await save_chapter_pic(session, chapter_file_path, chapter_pic_url)


async def download_book(session, token, book_url, thread_count):
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
                chapter_name_str = remove_useless_spaces(format_text(chapter_name[i]))
                chapter_dict = {
                    'NO': i+1,
                    'name': chapter_name_str,
                    'url': chapter_url[i],
                    'cost': chapter_cost[i],
                    'payed': chapter_payed[i]
                }
                # downloaded_params = [book_name_str, section_name_str, chapter_name_str]
                chapter_download_tasks.append(asyncio.create_task(download_chapter(session, token, section_dir, chapter_dict)))
            if chapter_download_tasks:
                _,_ = await asyncio.wait(chapter_download_tasks)

            section_NO += 1
            section_name = html_tree.xpath(XPATH_SECTIONS_NAME_IN_BOOK % section_NO)

        # print(book_name_str)
        # print(book_full_url)
        # print(section_name_str)
        # print(editted_chapter_name)
        # print(chapter_url)


async def update_book_list(session):
    book_url = []
    print('start to update book list...')
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
    book_list = list(set(book_url))

    # 保存
    with open(BOOK_LIST_DIR, 'w', encoding='utf-8') as file:
        for url in book_list:
            file.write(url + '\n')

    print('book list has been updated and saved.')
    print('')
    return book_list


def get_local_book_list():
    file = open(BOOK_LIST_DIR, 'r', encoding='utf-8')
    book_list = file.readlines()
    file.close()

    book_list_editted = []
    # 去掉每个元素结尾的\n
    for url in book_list:
        book_list_editted.append(url[:-1])
    return book_list_editted


async def download_collection(session, token): # 从收藏页/排行榜页中，获取小说详情页的url
    if MODE == MODE_USE_LOCAL_BOOK_LIST:
        book_list = get_local_book_list()
    elif MODE == MODE_UPDATE_BOOK_LIST:
        book_list = await update_book_list(session)

    thread_count = asyncio.Semaphore(MAX_THREAD)

    book_download_tasks = [asyncio.create_task(download_book(session, token, url, thread_count)) for url in book_list] * 3
    _,_ = await asyncio.wait(book_download_tasks)


async def login(session):
    print('')
    print('start login...')

    response = await session_try_get(session, MASIRO_LOGIN, HEADERS)
    if not response:
        print('')
        exit('login failed.')
    page_html = await response.text()
    token = use_xpath(page_html, XPATH_LOGIN)[0]
    
    params = {
        'username': USER_NAME,
        'password': PASSWORD,
        'remember': '1',
        '_token': token
    }

    headers = HEADERS
    headers['x-csrf-token'] = token
    headers['x-requested-with'] = 'XMLHttpRequest'

    response = await session_try_post(session, MASIRO_LOGIN, headers, params)
    if response:
        print('login succeeded.')
        print('')
        return token
    else:
        exit('\nlogin failed.\n')


def create_aiohttp_closed_event(session) -> asyncio.Event: # 用于优雅地终止程序
    """Work around aiohttp issuethat doesn't properly close transports on exit.

    See https://github.com/aio-libs/aiohttp/issues/1925#issuecomment-592596034

    Returns:
       An event that will be set once all transports have been properly closed.
    """

    transports = 0
    all_is_lost = asyncio.Event()

    if len(session.connector._conns) == 0:
        all_is_lost.set()
        return all_is_lost

    def connection_lost(exc, orig_lost):
        nonlocal transports

        try:
            orig_lost(exc)
        finally:
            transports -= 1
            if transports == 0:
                all_is_lost.set()

    def eof_received(orig_eof_received):
        try:
            orig_eof_received()
        except AttributeError:
            # It may happen that eof_received() is called after
            # _app_protocol and _transport are set to None.
            pass

    for conn in session.connector._conns.values():
        for handler, _ in conn:
            proto = getattr(handler.transport, "_ssl_protocol", None)
            if proto is None:
                continue

            transports += 1
            orig_lost = proto.connection_lost
            orig_eof_received = proto.eof_received

            proto.connection_lost = functools.partial(connection_lost, orig_lost=orig_lost)
            proto.eof_received = functools.partial(eof_received, orig_eof_received=orig_eof_received)

    return all_is_lost


async def base():
    async with aiohttp.ClientSession() as session:
        token = await login(session)
        await download_collection(session, token)
        closed_event = create_aiohttp_closed_event(session)
    
    await closed_event.wait()


if __name__ == '__main__':
    my_make_dir(FILE_DIR)

    asyncio.run(base())

    print('')
    print('下载任务全部完成')
    print('')
