from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from PIL import Image
import base64
import io
import time
import pandas as pd
import numpy as np

# 登录
def login(driver,url):
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        try:
            driver.get(url)
            time.sleep(3)
            vcode = driver.find_element(By.ID,'vcodeImg')
            vcode_src = vcode.get_attribute('src')
            
            if vcode_src:
                print("加载成功")
                break
            else:
                print("页面加载成功，验证码显示失败")
                driver.refresh()

        except NoSuchElementException:
            print("页面加载失败")
            driver.refresh()

        except TimeoutException:
            print("页面加载超时")
            driver.refresh()

    vcode_img_src = driver.find_element(By.ID,"vcodeImg").get_attribute('src')
    img_data = vcode_img_src.split(',')[1]
    img_bytes = base64.b64decode(img_data)
    img = Image.open(io.BytesIO(img_bytes))
    # display(img)
    img.show()
    input_captcha = input("请输入验证码：")

    username = driver.find_element(By.ID,'loginNameDiv').find_element(By.CLASS_NAME,'el-input__inner')
    username.send_keys('username') # 填入用户名
    password = driver.find_element(By.ID,'loginPwdDiv').find_element(By.CLASS_NAME,'el-input__inner')
    password.send_keys('password') # 填入密码
    captcha = driver.find_element(By.CLASS_NAME,'cv-verification-code').find_element(By.ID,'verifyCode')
    captcha.send_keys(input_captcha)

    ## 点击“登录”
    button = driver.find_element(By.CLASS_NAME,'longin-button')
    button.click()
    print("点击“登录”")

    ## 等一下，然后刷新，跳过轮次选择
    time.sleep(5)
    driver.refresh()

# 刷新
def refresher(driver,method,path):
    while True:
        try:
            element = driver.find_element(method, path)
            time.sleep(3) 
            if element:
                print("找到了!")
                break  # 如果找到了元素，跳出循环
        except NoSuchElementException:
            # 如果没有找到元素，刷新页面
            print("没找到呃，在刷新了")
            driver.refresh()

# 点击“全校课程查询”
def clickit(driver,method,path):
    try:
        button = driver.find_element(method,path)
        button.click()
        print("已点击")
    except NoSuchElementException:
        print("没找到")

# 解决开课时间地点存在多个\n问题
def replace_newlines(s):
    '''
    只保留前4个\n和最后9个\n,解决开课时间地点存在多个\n的问题
    '''
    # 找到所有的'\n'的位置
    newline_positions = [pos for pos, char in enumerate(s) if char == '\n']

    # 如果'\n'的数量少于13个，不需要替换
    if len(newline_positions) < 13:
        return s

    # 保留前4个和后9个'\n'的位置
    keep_positions = set(newline_positions[:4] + newline_positions[-9:])

    # 构建新的字符串，替换掉不需要保留的'\n'
    new_s = ''.join([char if pos in keep_positions or char != '\n' else ',' for pos, char in enumerate(s)])

    return new_s

# 爬
def scrape(driver,findhead,findelement):
    courses = []
    # 检查是否加载完成
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME,"el-table__row")))
        print("加载成功！")
    except TimeoutException:
        # refresher(driver,By.CLASS_NAME,'el-table__row')
        # clickit(driver,By.XPATH,'//*[@id="xsxkapp"]/div/div[1]/ul/li[8]/span')
        print("超时了")
        breakpoint()
    # 获取title
    header = driver.find_element(By.CLASS_NAME,findhead).text.replace('\n',' ').split(' ')
    # 获取内容
    container = driver.find_elements(By.CLASS_NAME,findelement) # rows

    for i in range(len(container)):
        # 调整开课时间地点的多换行(replace_newlines函数)
        info = replace_newlines(container[i].text).split('\n')
        col = container[i].find_elements(By.TAG_NAME,'td') #为了解决部分研究生课程开课单位为空的问题
        if col[6].text == '':   # 开课单位在第7列
            info.insert(6,'--') # 插入第6、7列之间，成为第7列
        courses.extend(info)
    return header,courses

# 自动翻页
def next_page(driver,next_button_class):
    try:
        next_button = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, next_button_class))
        )
        next_button.click()
    # 若发生错误
    except Exception as e:
        print("翻页发生错误：",e)
        return False

# 获取当前页码
def get_page(driver):
    page = driver.find_element(By.CLASS_NAME,'number.active').text
    return page

# 整理出dataframe
def make_df(header,courses):
    reshaped_courses = np.array(courses).reshape(-1,14)
    df = pd.DataFrame(reshaped_courses,columns=header)
    return df


# 正式开始，使用`navigate()`可以导航到“全校课程查询”界面
driver = webdriver.Chrome()
url = 'http://xk.xmu.edu.cn/'

login(driver,url)

# 有时点“登录”会犯病显示502，需要刷新重来
while True:
    try:
        # 若出现“选课”键说明登录成功
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME,'courseBtn')))
        print("登陆成功")
        break

    except:
        login(driver,url)

# 等它加载
# 当出现“选课”时，点击
enter = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME,'courseBtn')))
enter.click()
print("点击“选课”")

refresher(driver,method=By.CLASS_NAME,path="el-link--inner")

# 等待一秒，点击任意处跳过“选课指导”界面
time.sleep(1)
actions = ActionChains(driver)
actions.move_by_offset(100,100).click().perform()
clickit(driver,By.XPATH,'//*[@id="xsxkapp"]/div/div[1]/ul/li[8]/span')

time.sleep(1)

AllCourses = []

# 开始爬
while True:
    header, courses = scrape(driver,findhead='el-table__header-wrapper',findelement='el-table__row')
    AllCourses.extend(courses)
    page = get_page(driver)
    print(f"爬完第{page}页啦")
    notactive = next_page(driver,'btn-next')
    current_page = get_page(driver)
    if notactive:
        print("已经是最后一页")
        break

df = make_df(header,AllCourses)
df.to_excel('courses.xlsx', engine='openpyxl', index=False)