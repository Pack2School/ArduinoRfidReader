import utime
import machine
from machine import UART
import binascii
import time
import uos
import ujson
import sys

pin = machine.Pin(2, machine.Pin.OUT)

def toggle_pin():
    t_end = time.time() + 5
    while time.time() > t_end:
        pin.value(not pin.value())
        time.sleep_ms(300)
        pin.on()


def scan_rfids():
    uart = UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1, timeout=4, rxbuf=100)

    raw = [0xBB, 0x00, 0x22, 0x00, 0x00, 0x22, 0x7E]
    data = ''
    attempts = 0
    error = False

    uos.dupterm(None, 1)

    while data[:1] != b'\xbb' or data[-1:] != b'~' or data == b'\xbb\x01\xff\x00\x01\x15\x16\x7e':
        toggle_pin()
        time.sleep(0.5)
        written = uart.write(bytearray(raw))
        time.sleep(2)
        data = uart.read()
        time.sleep(1)
        attempts += 1
        if attempts > 10:
            error = True
            break

    uos.dupterm(uart, 1)

    if data != None and data != b'':
        if error:
            print('couldn`t read tags, try to move the reader or books a little bit')
            return "{'stickers': [], 'error': 'couldn`t read tags, try to move the reader or books a little bit'}"
        else:
            response = binascii.hexlify(bytearray(data)).decode("utf-8")
            print ("full reader response:", response)
            tags = list(map(lambda x : x[14:38], list(filter(None, response.split('bb')))))
            output = {'stickers': tags}
            print ("tags:", tags)
            return ujson.dumps(output)


def azure_connect():
    from util import create_mqtt_client, get_telemetry_topic, get_c2d_topic, parse_connection
    
    HOST_NAME = "HostName"
    SHARED_ACCESS_KEY_NAME = "SharedAccessKeyName"
    SHARED_ACCESS_KEY = "SharedAccessKey"
    SHARED_ACCESS_SIGNATURE = "SharedAccessSignature"
    DEVICE_ID = "DeviceId"
    MODULE_ID = "ModuleId"
    GATEWAY_HOST_NAME = "GatewayHostName"
    
    
    ## Parse the connection string into constituent parts
    dict_keys = parse_connection("HostName=Pack2SchoolIoThub.azure-devices.net;DeviceId=222;SharedAccessKey=iG1TkmqOglbez3Hf7W93RiwSqPiNYngMWSETYjcbWHA=")
    shared_access_key = dict_keys.get(SHARED_ACCESS_KEY)
    shared_access_key_name =  dict_keys.get(SHARED_ACCESS_KEY_NAME)
    gateway_hostname = dict_keys.get(GATEWAY_HOST_NAME)
    hostname = dict_keys.get(HOST_NAME)
    device_id = dict_keys.get(DEVICE_ID)
    module_id = dict_keys.get(MODULE_ID)
    message_to_send = ''
    
    ## Create you own shared access signature from the connection string that you have
    ## Azure IoT Explorer can be used for this purpose.
    sas_token_str = "SharedAccessSignature sr=Pack2SchoolIoThub.azure-devices.net&sig=%2FEYAobgGjvt%2FYfwE58Z4BrNGbJAUm%2BoDTlTPHrEBpvI%3D&skn=iothubowner&se=1600478289"
    
    ## Create username following the below format '<HOSTNAME>/<DEVICE_ID>'
    username = hostname + '/' + device_id
    
    
    ## Create UMQTT ROBUST or UMQTT SIMPLE CLIENT
    mqtt_client = create_mqtt_client(client_id=device_id, hostname=hostname, username=username, password=sas_token_str, port=   8883, keepalive=120, ssl=True)
    
    print("Connecting to Azure...")
    mqtt_client.reconnect()


    def publish(d2c_message):
        print("Sending Data...")
        print("Message:", d2c_message)
        topic = get_telemetry_topic(device_id)
        
        ## Send telemetry
        reader_details = get_reader_details()
        print(reader_details)


        mqtt_client.publish(topic=topic, msg=d2c_message)
        utime.sleep(1)
    
    def callback_handler(topic, message_receive):
        print("Received plain message: \n", message_receive, "\n")
        message_json = ujson.loads(message_receive)
        print("Received message: \n", message_json, "\n")
        print("Command is: ", message_json['command'])
        if message_json['command'] == "Scan":
            message_to_send = scan_rfids()
            publish(message_to_send)
        if message_json['command'] == "Exit":
            sys.exit(0)

    subscribe_topic = get_c2d_topic(device_id)
    mqtt_client.set_callback(callback_handler)
    mqtt_client.subscribe(topic=subscribe_topic)

    t_end = time.time() + 60 * 60
    while True:
        if time.time() > t_end:
            sys.exit(1)
        ## Send a C2D message and wait for it to arrive at the device
        print("Waiting for command")
        mqtt_client.wait_msg()


def get_reader_details():

    uart = UART(0, 115200)
    uart.init(115200, bits=8, parity=None, stop=1, timeout=4, rxbuf=100)

    data = [0xBB, 0x00, 0x03, 0x00, 0x01, 0x00, 0x04, 0x7E]

    time.sleep(2)
    toggle_pin()
    written = uart.write(bytearray(data))


    uos.dupterm(None, 1)

    data = uart.read()

    uart = machine.UART(0, 115200)
    uos.dupterm(uart, 1)

    if data != None:
        print ("response:", binascii.hexlify(bytearray(data)))
    return data


azure_connect()