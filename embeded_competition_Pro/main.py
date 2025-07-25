import time
import math
from machine import UART,FPIOA

fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)

uart = UART(UART.UART2, 115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)

#上机向32发送数据
uart.write('$KMS:0,100,70,1000!\n')

run_app_status = 0

uart.write("#openmv reset\n\n!")

'''
    3个变量控制机械臂抓取色块时的偏移量,如果机械臂抓取色块失败则调整变量
    cx: 偏右减小, 偏左增加
    cy: 偏前减小，偏后增加
    cz: 偏高减小，偏低增加
'''
cx=0
cy=0
cz=0

if __name__ == '__main__':
    while True:
        #接收数据
        string = uart.read()
        if string:
            try:
                print(string,isinstance(string.decode(),str))
                if string:
                    string = string.decode()
                    if string.find("#RunStop!") >= 0:
                        run_app_status = 0
                    elif string.find("#ColorSort!") >= 0:#色块分拣
                        run_app_status = 1
                    elif string.find("#ColorStack!") >= 0:#色块码垛
                        run_app_status = 2
                    elif string.find("#ColorTrack!") >= 0:#色块跟踪
                        run_app_status = 4 

            except Exception as e:
                print("Error:", e)
                run_app_status = 0
           