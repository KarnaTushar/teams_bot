import re
import time
import sqlite3
from datetime import datetime
from os import path
import os.path
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

#import discord_webhook

opt = Options()
opt.add_argument("--disable-infobars")
opt.add_argument("--disable-extentions")
opt.add_argument("--start-maximized")
opt.add_argument("start-maximized")

# Pass 1 in argument to allow and 0 to decline

opt.add_experimental_option("prefs", { \
    "profile.default_content_setting_values.media_stream_camera": 1,
    "profile.default_content_setting_values.media_stream_mic": 1,
    "profile.default_content_setting_values.notification": 1,
    "profile.default_content_setting_value.geolocation": 1
    })

# driver = webdriver.Chrome(chrome_options=opt,service_log_path='NUL')
driver = None
URL = "https://teams.microsoft.com"

#Enter you credential (Username & Password)
CREDS = {'username' : '' , 'password' : ''}


def login():
    global driver
    #signin is required
    print("sigining in")
    usernameField = driver.find_element_by_xpath('//*[@id="i0116]')
    usernameField.click()
    usernameField.send_keys(CREDS['username'])
    driver.find_element_by_xpath('//*[@id="idSIButton9"]').click() # the Next Button
    time.sleep(6)
    passwordField = driver.find_element_by_xpath('//[@id="i0118"]')
    passwordField.click()
    passwordField.send_keys(CREDS['password'])
    driver.find_element_by_xpath('//[@id="idSIbutton9"]').click() # the SignIn Button
    time.sleep(6)
    driver.find_element_by_xpath('//[@id="idSIButton9"]').click() # the Remember Me Button
    time.sleep(6)
    #return driver


def createDB():
    conn = sqlite3.connect('timetable.db')
    c=conn.cursor()
    # Creating table
    c.execute('''CREATE TABLE timetable(class text, start_time, end_time text, day text)''')
    conn.comit()
    conn.close()
    print("Timetable database created")



def validate_input(regex, inp):
    if not re.match(regex, inp):
        return False
    return True

def validate_day(inp):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Staurday", "Sunday"]

    if inp.lower() in days:
        return True
    else:
        return False


def add_timetable():
    if(not(path.exists("timetable.db"))):
            createDB()
    op = int(input("1. Addclass\n2. Done addinf \nEnter option: "))
    while(op == 1):
        name = input("Enter class name: ")
        start_time = input("Enter time at which class begins in 24 hrs fromat: (HH:MM)")
        while not(validate_input("\d\d:\d\d", start_time)):
            print("Invalid input, try again")
            start_time = input("Enter time at which class begins in 24 hrs fromat: (HH:MM)")

    end_time = input("Enter time at which class ends in 24 hrs format: (HH:MM) ")
    while not(validate_input("\d\d:\d\d",end_time)):
        print("Invalid input, try again")
        end_time = input("Enter time at which class ends in 24 hrs format: (HH:MM) ")

    day = input("Enter day of the week(Monday/Tuesday/...etc): ")
    while not(validate_day(day.strip())):
        print("Invalid input,try again")
        end_time = input("Enter day (Monday/Tuesday/...etc): ")


        conn = sqlite3.connect('timetable.db')
        c = conn.cursor()

        # insert a  row of data
        c.execute("Insert Info timetable VALUES ('%s','%s','%s','%s')"%(name,start_time,end_time,day))

        conn.comit()
        conn.close()

        print("Class added to database\n")

        op = int(input("1. Add class\n2. Done adding\nEnter option: "))


def view_timetable():
	conn = sqlite3.connect('timetable.db')
	c=conn.cursor()
	for row in c.execute('SELECT * FROM timetable'):
		print(row)
	conn.close()



def joinclass(class_name,start_time,end_time):
	global driver

	try_time = int(start_time.split(":")[1]) + 15
	try_time = start_time.split(":")[0] + ":" + str(try_time)

	time.sleep(5)


	classes_available = driver.find_elements_by_class_name("name-channel-type")

	for i in classes_available:
		if class_name.lower() in i.get_attribute('innerHTML').lower():
			print("JOINING CLASS ",class_name)
			i.click()
			break


	time.sleep(4)


	try:
		joinbtn = driver.find_element_by_class_name("ts-calling-join-button")
		joinbtn.click()

	except:
		#join button not found
		#refresh every minute until found
		k = 1
		while(k<=15):
			print("Join button not found, trying again")
			time.sleep(60)
			driver.refresh()
			joinclass(class_name,start_time,end_time)
			# schedule.every(1).minutes.do(joinclass,class_name,start_time,end_time)
			k+=1
		print("Seems like there is no class today.")
		discord_webhook.send_msg(class_name=class_name,status="noclass",start_time=start_time,end_time=end_time)


	time.sleep(4)
	webcam = driver.find_element_by_xpath('//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[2]/toggle-button[1]/div/button/span[1]')
	if(webcam.get_attribute('title')=='Turn camera off'):
		webcam.click()
	time.sleep(1)

	microphone = driver.find_element_by_xpath('//*[@id="preJoinAudioButton"]/div/button/span[1]')
	if(microphone.get_attribute('title')=='Mute microphone'):
		microphone.click()

	time.sleep(1)
	joinnowbtn = driver.find_element_by_xpath('//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[1]/div/div/button')
	joinnowbtn.click()

	discord_webhook.send_msg(class_name=class_name,status="joined",start_time=start_time,end_time=end_time)
	
	#now schedule leaving class
	tmp = "%H:%M"

	class_running_time = datetime.strptime(end_time,tmp) - datetime.strptime(start_time,tmp)

	time.sleep(class_running_time.seconds)

	driver.find_element_by_class_name("ts-calling-screen").click()


	driver.find_element_by_xpath('//*[@id="teams-app-bar"]/ul/li[3]').click() #come back to homepage
	time.sleep(1)

	driver.find_element_by_xpath('//*[@id="hangup-button"]').click()
	print("Class left")
	discord_webhook.send_msg(class_name=class_name,status="left",start_time=start_time,end_time=end_time)





def start_browser():

	global driver
	driver = webdriver.Chrome(chrome_options=opt,service_log_path='NUL')

	driver.get(URL)

	WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.TAG_NAME,'body')))

	if("login.microsoftonline.com" in driver.current_url):
		login()



def sched():
	conn = sqlite3.connect('timetable.db')
	c=conn.cursor()
	for row in c.execute('SELECT * FROM timetable'):
		#schedule all classes
		name = row[0]
		start_time = row[1]
		end_time = row[2]
		day = row[3]

		if day.lower()=="monday":
			schedule.every().monday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="tuesday":
			schedule.every().tuesday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="wednesday":
			schedule.every().wednesday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="thursday":
			schedule.every().thursday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="friday":
			schedule.every().friday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="saturday":
			schedule.every().saturday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))
		if day.lower()=="sunday":
			schedule.every().sunday.at(start_time).do(joinclass,name,start_time,end_time)
			print("Scheduled class '%s' on %s at %s"%(name,day,start_time))


	#Start browser
	start_browser()
	while True:
		# Checks whether a scheduled task
		# is pending to run or not
		schedule.run_pending()
		time.sleep(1)


if __name__=="__main__":
	# joinclass("Maths","15:13","15:15","sunday")
	op = int(input(("1. Modify Timetable\n2. View Timetable\n3. Start Bot\nEnter option : ")))
	
	if(op==1):
		add_timetable()
	if(op==2):
		view_timetable()
	if(op==3):
		sched()
    