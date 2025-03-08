from machine import Pin, SPI,WDT
import framebuf
import utime
import array

import time
import network
import ntptime
import machine

import requests
import urequests
import json
import gc

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

#自宅Wi-FiのSSIDとパスワードを入力 
ssid = 'xxxx'
password = 'xxxx'
max_wait = 10

openweathermapAppId='xxxx'
openweathermapPosition = 'xxxx'

ntp_server = 'time.cloudflare.com'

class EPD_7in5_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.partFlag=1
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        

        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200) 
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def WaitUntilIdle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 0):   # Wait until the busy_pin goes LOW
            self.delay_ms(20)
        self.delay_ms(20) 
        print("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x12) # DISPLAY REFRESH
        self.delay_ms(100)      #!!!The delay here is necessary, 200uS at least!!!
        self.WaitUntilIdle()
        
    def init(self):
        # EPD hardware init start     
        self.reset()
        
        self.send_command(0x06)     # btst
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x28)        # If an exception is displayed, try using 0x38
        self.send_data(0x17)
        
#         self.send_command(0x01)  # POWER SETTING
#         self.send_data(0x07)
#         self.send_data(0x07)     # VGH=20V,VGL=-20V
#         self.send_data(0x3f)     # VDH=15V
#         self.send_data(0x3f)     # VDL=-15V
        
        self.send_command(0x04)  # POWER ON
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0X00)   # PANNEL SETTING
        self.send_data(0x0F)      # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)     # tres
        self.send_data(0x03)     # source 800
        self.send_data(0x20)
        self.send_data(0x01)     # gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        self.send_command(0X50)     # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x11)
        self.send_data(0x07)

        self.send_command(0X60)     # TCON SETTING
        self.send_data(0x22)

        self.send_command(0x65)     # Resolution setting
        self.send_data(0x00)
        self.send_data(0x00)     # 800*480
        self.send_data(0x00)
        self.send_data(0x00)
        
        return 0;
    
    def init_Fast(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x0F)

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0x06)
        self.send_data(0x27)
        self.send_data(0x27) 
        self.send_data(0x18)
        self.send_data(0x17)

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5A)

        self.send_command(0X50)
        self.send_data(0x11)
        self.send_data(0x07)
        
        return 0
    
    def init_part(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x1F)

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x6E)

        self.send_command(0X50)
        self.send_data(0xA9)
        self.send_data(0x07)

        # EPD hardware init end
        return 0
    
    
    def Clear(self):
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def ClearRed(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.TurnOnDisplay()
        
    def ClearBlack(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def display(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        # send black data
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1(self.buffer_black[(i * high) : ((i+1) * high)])
            
        # send red data
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1(self.buffer_red[(i * high) : ((i+1) * high)])
            
        self.TurnOnDisplay()
        
    def display_Base_color(self, color):
        if(self.width % 8 == 0):
            Width = self.width // 8
        else:
            Width = self.width // 8 +1
        Height = self.height
        self.send_command(0x10)   #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(color)
                
        self.send_command(0x13)  #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(~color)

        # self.send_command(0x12)
        # self.delay_ms(100)
        # self.WaitUntilIdle()
        
        
    def display_Partial(self, Image, Xstart, Ystart, Xend, Yend):
        if((Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8 == 0 | (Xend - Xstart)%8 == 0):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1
                
        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart
        # self.send_command(0x50)
        # self.send_data(0xA9)
        # self.send_data(0x07)

        self.send_command(0x91) #This command makes the display enter partial mode
        self.send_command(0x90) #resolution setting
        self.send_data (Xstart//256)
        self.send_data (Xstart%256)   #x-start    

        self.send_data ((Xend-1)//256)
        self.send_data ((Xend-1)%256)  #x-end

        self.send_data (Ystart//256)  #
        self.send_data (Ystart%256)   #y-start    

        self.send_data ((Yend-1)//256)
        self.send_data ((Yend-1)%256)  #y-end
        self.send_data (0x01)

        if self.partFlag == 1:
            self.partFlag = 0
            self.send_command(0x10)
            for i in range(0, Width):
                self.send_data1([0xFF] * Height)

        self.send_command(0x13)   #Write Black and White image to RAM
        for i in range(0, Width):
            self.send_data1(Image[(i * Height) : ((i+1) * Height)])

        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def sleep(self):
        self.send_command(0x02) # power off
        self.WaitUntilIdle()
        self.send_command(0x07) # deep sleep
        self.send_data(0xa5)
    
        
    def digital_number(self,x,y,z):
        number_paint = [
            [True,False,True,True,True,True,True],
            [False,False,False,True,False,True,False],
            [True,True,True,True,False,False,True],
            [True,True,True,True,False,True,False],
            [False,True,False,True,True,True,False],
            [True,True,True,False,True,True,False],
            [True,True,True,False,True,True,True],
            [True,False,False,True,False,True,False],
            [True,True,True,True,True,True,True],
            [True,True,True,True,True,True,False]
        ]

        #デジタル時計(数字部分)
        if number_paint[z][0] == True:
            self.imageblack.poly(x, y, array.array('h',[4,0, 25,0, 29,4, 25,8, 4,8, 0,4] ),0x00,True)
        
        if number_paint[z][1] == True:
            self.imageblack.poly(x, y+25, array.array('h',[4,0, 25,0, 29,4, 25,8, 4,8, 0,4] ),0x00,True)
        
        if number_paint[z][2] == True:
            self.imageblack.poly(x, y+50, array.array('h',[4,0, 25,0, 29,4, 25,8, 4,8, 0,4] ),0x00,True)
            
        if number_paint[z][3] == True:
            self.imageblack.poly(x, y, array.array('h',[29,4, 33,8, 33,25, 29,29, 25,25, 25,8] ),0x00,True)
            
        if number_paint[z][4] == True:
            self.imageblack.poly(x, y, array.array('h',[0,4, 4,8, 4,25, 0,29, -4,25, -4,8] ),0x00,True)
            
        if number_paint[z][5] == True:
            self.imageblack.poly(x, y+25, array.array('h',[29,4, 33,8, 33,25, 29,29, 25,25, 25,8] ),0x00,True)
        
        if number_paint[z][6] == True:
            self.imageblack.poly(x, y+25, array.array('h',[0,4, 4,8, 4,25, 0,29, -4,25, -4,8] ),0x00,True)
    
    def digital_clock(self,x,y,z):
        #デジタル時計(数字部分)
        self.digital_number(x,y,(z // 1000) % 10)
        self.digital_number(x+40,y,(z // 100) % 10)
        self.digital_number(x+100,y,(z // 10) % 10)
        self.digital_number(x+140,y,(z % 10))
        #デジタル時計(コロン)
        self.imageblack.ellipse(x+85,y+15,3,3,0x00,True)
        self.imageblack.ellipse(x+85,y+40,3,3,0x00,True)
    
    def rectangle(self,x,y):
        self.imageblack.rect(x, y, 70, 50, 0x00)
        
    def digital_date(self,x,y,z):
        #今日の日付
        self.digital_number(x,y,(z // 1000) % 10)
        self.digital_number(x+40,y,(z // 100) % 10)
        self.digital_number(x+100,y,(z // 10) % 10)
        self.digital_number(x+140,y,(z % 10))
        
        self.imageblack.line(x+94,y+2,x+77,y+55,0x00)
        self.imageblack.line(x+93,y+2,x+76,y+55,0x00)
        self.imageblack.line(x+95,y+2,x+78,y+55,0x00)
    
    #メイン天気の絵
    def illust_base(self,x):
        self.imageblack.ellipse(600,200,90,90,0x00,x)
        self.imageblack.ellipse(600,200,89,89,0x00,x)
        self.imageblack.ellipse(600,200,88,88,0x00,x)
    
    def illust_clear_skies(self):
        self.illust_base("")
    
    def illust_cloudy(self):
        self.illust_base("")
        self.imageblack.ellipse(600,200,45,45,0x00)
        self.imageblack.ellipse(600,200,46,46,0x00)
        self.imageblack.ellipse(600,200,47,47,0x00)
    
    def illust_rainy(self):
        self.illust_base("True")
        
    def illust_snow(self):
        self.illust_base("")
        self.imageblack.hline(510,200,180,0x00)
        self.imageblack.hline(510,201,180,0x00)
        self.imageblack.hline(510,199,180,0x00)
        self.imageblack.line(538,140,663,260,0x00)
        self.imageblack.line(539,139,664,259,0x00)
        self.imageblack.line(537,141,662,261,0x00)
        self.imageblack.line(538,260,663,140,0x00)
        self.imageblack.line(539,261,664,141,0x00)
        self.imageblack.line(537,259,662,139,0x00)
    
    #天気予報の絵
    def small_illust_base(self, x, y, size, fill):
        self.imageblack.ellipse(x, y, size, size, 0x00, fill)

    def small_illust_clear_skies(self, x, y, size):
        self.small_illust_base(x, y, size, "")
    
    def small_illust_cloudy(self, x, y, size):
        self.small_illust_base(x, y, size, "")
        self.imageblack.ellipse(x, y, size-15, size-15,0x00)
    
    def small_illust_rainy(self, x, y, size):
        self.small_illust_base(x, y, size, "True")
        
    def small_illust_snow(self, x, y, size):
        self.small_illust_base(x, y, size, "")
        self.imageblack.hline(x-25, y, 50, 0x00)
        self.imageblack.line(x-12, y-21, x+12, y+21, 0x00)
        self.imageblack.line(x+12, y-21, x-12, y+21, 0x00)
        
    def type_display_express(self, x, y):
        self.imageblack.text("semi", x, y, 0x00)
        self.imageblack.text("express", x, y+12, 0x00)
    
machine.Pin(23, machine.Pin.OUT).high()
led=machine.Pin("LED", machine.Pin.OUT)
led.value(1)

# Wi-Fi設定 
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('接続待ち...')
    time.sleep(1)

if wlan.status() != 3:
    print('ネットワーク接続失敗')
    machine.deepsleep(5000)
else:
    print('接続完了')
    status = wlan.ifconfig()
    print( 'IPアドレス = ' + status[0] )
# 
# NTPサーバーとして"time.cloudflare.com"を指定
ntptime.host = ntp_server

# 時間の同期を試みる
try:
    # NTPサーバーから取得した時刻でPico WのRTCを同期
    ntptime.settime()
except:
    print("時間の同期に失敗しました。")
    raise

# 世界標準時に9時間加算し日本時間を算出
tm = time.localtime(time.time() + 9 * 60 * 60)

today_mm = int(tm[1])
today_dd = int(tm[2])
today = (f"{today_mm:02d}") + (f"{today_dd:02d}")

now_hh = int(tm[3])
now_mm = int(tm[4])
now_time = (f"{now_hh:02d}") + (f"{now_mm:02d}")

#今の天気
gc.collect()
print("get now weather")
weather_url = "https://api.openweathermap.org/data/2.5/weather?units=metric&" + openweathermapPosition + "&appid=" + openweathermapAppId
response = requests.get(weather_url)
data = response.json()
main_data = data['main']
weather_data = data['weather'][0]

#天気予報
gc.collect()
print("get forcast weather")
forecast_url = "https://api.openweathermap.org/data/2.5/forecast?units=metric&cnt=8&" + openweathermapPosition + "&appid=" + openweathermapAppId
response = requests.get(forecast_url)
data = response.json()

wlan.disconnect()
wlan.active(False)
machine.Pin(23, machine.Pin.OUT).low()
    
    
epd = EPD_7in5_B()

epd.imageblack.fill(0xff)
epd.imagered.fill(0x00)

epd.imageblack.text("for HASHIMOTO", 100, 10, 0x00)
epd.imageblack.text("for SHINJUKU", 100, 260, 0x00)


epd.imageblack.vline(400, 5, 470, 0x00)
epd.imageblack.vline(399, 5, 470, 0x00)
epd.imageblack.vline(401, 5, 470, 0x00)
epd.imageblack.hline(5, 240, 395, 0x00)
epd.imageblack.hline(5, 239, 395, 0x00)
epd.imageblack.hline(5, 241, 395, 0x00)

epd.rectangle(10,50)
epd.rectangle(10,150)
epd.rectangle(10,290)
epd.rectangle(10,390)

next_train_time_for_hashimono = []
hashimoto_txt = open('for_hashimoto.txt', 'r')

with hashimoto_txt as f:
    while True:
        line = f.readline()
        if not line:
            break
        # 1行ずつ処理を行う
        splited_line = line.split(",")
        splited_line[0] = int(splited_line[0])
        if len(next_train_time_for_hashimono) >= 2 :
            break
        if (splited_line[0] > int(now_time)) :
            next_train_time_for_hashimono.append(splited_line)

hashimoto_txt.close()

print(next_train_time_for_hashimono)

shinjuku_txt = open('for_shinjuku.txt', 'r')
next_train_time_for_shinjuku = []

with shinjuku_txt as f:
    while True:
        line = f.readline()
        if not line:
            break
        # 1行ずつ処理を行う
        splited_line = line.split(",")
        splited_line[0] = int(splited_line[0])
        if len(next_train_time_for_shinjuku) >= 2 :
            break
        if (splited_line[0] > int(now_time)) :
            next_train_time_for_shinjuku.append(splited_line)

shinjuku_txt.close()

print(next_train_time_for_shinjuku)

#電車の種別(橋本方面)
if next_train_time_for_hashimono[0][1] == "semi-express" :
    epd.type_display_express(18,65)
else :
    epd.imageblack.text(next_train_time_for_hashimono[0][1], 25, 70, 0x00)

if next_train_time_for_hashimono[1][1] == "semi-express" :
    epd.type_display_express(18,165)
else :
    epd.imageblack.text(next_train_time_for_hashimono[1][1], 25, 170, 0x00)

#電車の行き先(橋本方面)
epd.imageblack.text(next_train_time_for_hashimono[0][2].replace('\r\n','\n').replace('\r','\n').replace('\n',''), 100, 70, 0x00)
epd.imageblack.text(next_train_time_for_hashimono[1][2].replace('\r\n','\n').replace('\r','\n').replace('\n',''), 100, 170, 0x00)

#電車の時間(橋本方面)
epd.digital_clock(210,45,next_train_time_for_hashimono[0][0])
epd.digital_clock(210,145,next_train_time_for_hashimono[1][0])


#電車の種別(新宿方面)
if next_train_time_for_shinjuku[0][1] == "semi-express" :
    epd.type_display_express(18,305)
else :
    epd.imageblack.text(next_train_time_for_shinjuku[0][1], 25, 310, 0x00)

if next_train_time_for_shinjuku[1][1] == "semi-express" :
    epd.type_display_express(18,405)
else :
    epd.imageblack.text(next_train_time_for_shinjuku[1][1], 25, 410, 0x00)

#電車の行き先(新宿方面)
epd.imageblack.text(next_train_time_for_shinjuku[0][2].replace('\r\n','\n').replace('\r','\n').replace('\n',''), 100, 310, 0x00)
epd.imageblack.text(next_train_time_for_shinjuku[1][2].replace('\r\n','\n').replace('\r','\n').replace('\n',''), 100, 410, 0x00)

#電車の時間(新宿方面)
epd.digital_clock(210,285,next_train_time_for_shinjuku[0][0])
epd.digital_clock(210,385,next_train_time_for_shinjuku[1][0])


#今日の日付
epd.digital_date(420,10,int(today))

#デジタル時計(現在時刻)
epd.digital_clock(620,10,int(now_time))

#今の天気の表示
if weather_data['main'] == "Clear":
    epd.illust_clear_skies()
    wea_info = "Sunny"
    epd.imageblack.text(wea_info, 650, 310, 0x00)
elif weather_data['main'] == "Clouds":
    epd.illust_cloudy()
    wea_info = "Cloudy"
    epd.imageblack.text(wea_info, 650, 310, 0x00)
elif weather_data['main'] == "Rain":
    epd.illust_rainy()
    wea_info = "Rainy"
    epd.imageblack.text(wea_info, 650, 310, 0x00)
elif weather_data['main'] == "Snow":
    epd.illust_snow()
    wea_info = "Snow"
    epd.imageblack.text(wea_info, 650, 310, 0x00)
    
epd.imageblack.ellipse(768,310,2,2,0x00)
epd.imageblack.text(str(main_data['temp'])+"  C", 718, 310, 0x00)

display_weather_info = []
for weather_info in data["list"]:
    hour = utime.localtime(weather_info["dt"] +(9*60*60))[3]
    weather = weather_info["weather"][0]["main"]
    temp = round(weather_info["main"]["temp"],1)
    info = [hour,weather,temp]
    display_weather_info.append(info)
    
print(display_weather_info)

def search_hour(target_hour):
    for i, row in enumerate(display_weather_info):
        for j, element in enumerate(row):
            if element == target_hour:
                return i

#6時の天気
idx = search_hour(6)
epd.imageblack.text("06:00", 440, 350, 0x00)

if display_weather_info[idx][1] == "Clear" :
    weather_name = "Sunny"
    epd.small_illust_clear_skies(460,400,25)

if display_weather_info[idx][1] == "Clouds" :
    weather_name = "Cloudy"
    epd.small_illust_cloudy(460,400,25)

if display_weather_info[idx][1] == "Rain" :
    weather_name = "Rainy"
    epd.small_illust_rainy(460,400,25)

if display_weather_info[idx][1] == "Snow" :
    weather_name = "Snow"
    epd.small_illust_snow(460,400,25)

epd.imageblack.text(weather_name, 440, 430, 0x00)
epd.imageblack.ellipse(475,442,2,2,0x00)
epd.imageblack.text("C", 480, 442, 0x00)
epd.imageblack.text(str(display_weather_info[idx][2]), 430, 442, 0x00)

#12時の天気
idx = search_hour(12)
epd.imageblack.text("12:00", 535, 350, 0x00)

if display_weather_info[idx][1] == "Clear" :
    weather_name = "Sunny"
    epd.small_illust_clear_skies(555,400,25)

if display_weather_info[idx][1] == "Clouds" :
    weather_name = "Cloudy"
    epd.small_illust_cloudy(555,400,25)

if display_weather_info[idx][1] == "Rain" :
    weather_name = "Rainy"
    epd.small_illust_rainy(555,400,25)

if display_weather_info[idx][1] == "Snow" :
    weather_name = "Snow"
    epd.small_illust_snow(555,400,25)

epd.imageblack.text(weather_name, 535, 430, 0x00)
epd.imageblack.ellipse(570,442,2,2,0x00)
epd.imageblack.text("C", 575, 442, 0x00)
epd.imageblack.text(str(display_weather_info[idx][2]), 525, 442, 0x00)

#18時の天気
idx = search_hour(18)
epd.imageblack.text("18:00", 630, 350, 0x00)

if display_weather_info[idx][1] == "Clear" :
    weather_name = "Sunny"
    epd.small_illust_clear_skies(650,400,25)

if display_weather_info[idx][1] == "Clouds" :
    weather_name = "Cloudy"
    epd.small_illust_cloudy(650,400,25)

if display_weather_info[idx][1] == "Rain" :
    weather_name = "Rainy"
    epd.small_illust_rainy(650,400,25)

if display_weather_info[idx][1] == "Snow" :
    weather_name = "Snow"
    epd.small_illust_snow(650,400,25)

epd.imageblack.text(weather_name, 630, 430, 0x00)
epd.imageblack.ellipse(665,442,2,2,0x00)
epd.imageblack.text("C", 670, 442, 0x00)
epd.imageblack.text(str(display_weather_info[idx][2]), 620, 442, 0x00)

#21時の天気
idx = search_hour(21)
epd.imageblack.text("21:00", 725, 350, 0x00)
if display_weather_info[idx][1] == "Clear" :
    weather_name = "Sunny"
    epd.small_illust_clear_skies(745,400,25)
if display_weather_info[idx][1] == "Clouds" :
    weather_name = "Cloudy"
    epd.small_illust_cloudy(745,400,25)
if display_weather_info[idx][1] == "Rain" :
    weather_name = "Rainy"
    epd.small_illust_rainy(745,400,25)
if display_weather_info[idx][1] == "Snow" :
    weather_name = "Snow"
    epd.small_illust_snow(745,400,25)
epd.imageblack.text(weather_name, 725, 430, 0x00)
epd.imageblack.ellipse(760,442,2,2,0x00)
epd.imageblack.text("C", 765, 442, 0x00)
epd.imageblack.text(str(display_weather_info[idx][2]), 715, 442, 0x00)

epd.init()
epd.Clear()
epd.display()
epd.sleep()
led.value(0)
machine.deepsleep(180000)
