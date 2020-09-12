## connect to wifi at boot time.
import machine
import time
pin = machine.Pin(2, machine.Pin.OUT)


def toggle_pin(sec):
    t_end = time.time() + sec * 60
    while time.time() > t_end:
        pin.value(not pin.value())
        time.sleep_ms(300)
        pin.on()


def connect_multiple():
    import network
    pin.on()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    credentials = [('SSID1', 'password1'),('SSID2', 'password2')]
    tried = 0
    if not wlan.isconnected():
        print('connecting to network...', credentials[0][0])
        wlan.connect(credentials[0][0], credentials[0][1])
        while not wlan.isconnected():
            tried+=1
            toggle_pin(10)
            time.sleep(1)
            if (tried > 10):
                break
    
    wlan.disconnect()
    wlan = network.WLAN(network.STA_IF)
    tried = 0
    if not wlan.isconnected():
        print('connecting to network...', credentials[1][0])
        wlan.connect(credentials[1][0], credentials[1][1])
        while not wlan.isconnected():
            tried+=1
            toggle_pin(10)
            time.sleep(1)
            if (tried > 10):
                wlan.disconnect()
                break

    if wlan.isconnected():
        print('network config:', wlan.ifconfig())
    else:
        print('not connected')

def no_debug():
    import esp
    # you can run this from the REPL as well
    esp.osdebug(None)

no_debug()
connect_multiple()