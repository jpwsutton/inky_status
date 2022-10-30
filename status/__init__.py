
from status.constants import *
from machine import Pin
from pimoroni import Button
import time

from status.display import StatusDisplay


hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT, value=True)

button_a = Button(12)
button_b = Button(13)
button_c = Button(14)



## Inky Display Helpers
display = StatusDisplay()
display.draw_boot("Hello World!")


MONTHNAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    

# set up the activity led
# ===========================================================================
from machine import Timer, Pin
import math

activity_led = Pin('LED', Pin.OUT)

  
activity_led_timer = Timer(-1)
activity_led_pulse_speed_hz = 1

led_state = False

def activity_led_callback(t):
    global led_state
    led_state =  not led_state
    activity_led.value(led_state)
    
    
  

# set the activity led into pulsing mode
def pulse_activity_led(speed_hz = 1):
  global activity_led_timer, activity_led_pulse_speed_hz
  activity_led_pulse_speed_hz = speed_hz
  activity_led_timer.deinit()
  activity_led_timer.init(period=1000, mode=Timer.PERIODIC, callback=activity_led_callback)

# turn off the activity led and disable any pulsing animation that's running
def stop_activity_led():
  global activity_led_timer
  activity_led_timer.deinit()
  activity_led.value(False)
  

# check whether device needs provisioning
# ===========================================================================
import time
from phew import logging
#button_pin = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
needs_provisioning = False
#start = time.time()
#while button_pin.value(): # button held for 3 seconds go into provisioning
#  if time.time() - start > 3:
#    needs_provisioning = True
#    break

try:
  import config # fails to import (missing/corrupt) go into provisioning
  if not config.provisioned: # provisioned flag not set go into provisioning
    needs_provisioning = True
except Exception as e:
  logging.error("> missing or corrupt config.py", e)
  needs_provisioning = True

if needs_provisioning:
  logging.info("> entering provisioning mode")
  display.draw_boot("provisioning")
  import status.provisioning
  # control never returns to here, provisioning takes over completely
  
  

# all the other imports, so many shiny modules
import machine, sys, os, json
from machine import RTC, ADC
import phew
import status.helpers as helpers


# jazz up that console! toot toot!
print("      ___                       ___                       ___           ___      ")
print("     /  /\          ___        /  /\          ___        /__/\         /  /\     ")
print("    /  /:/_        /  /\      /  /::\        /  /\       \  \:\       /  /:/_    ")
print("   /  /:/ /\      /  /:/     /  /:/\:\      /  /:/        \  \:\     /  /:/ /\   ")
print("  /  /:/ /::\    /  /:/     /  /:/~/::\    /  /:/     ___  \  \:\   /  /:/ /::\  ")
print(" /__/:/ /:/\:\  /  /::\    /__/:/ /:/\:\  /  /::\    /__/\  \__\:\ /__/:/ /:/\:\ ")
print(" \  \:\/:/~/:/ /__/:/\:\   \  \:\/:/__\/ /__/:/\:\   \  \:\ /  /:/ \  \:\/:/~/:/ ")
print("  \  \::/ /:/  \__\/  \:\   \  \::/      \__\/  \:\   \  \:\  /:/   \  \::/ /:/  ")
print("   \__\/ /:/        \  \:\   \  \:\           \  \:\   \  \:\/:/     \__\/ /:/   ")
print("     /__/:/          \__\/    \  \:\           \__\/    \  \::/        /__/:/    ")
print("     \__\/                     \__\/                     \__\/         \__\/     ")
print("")
print("    -  --  ---- -----=--==--===  hey status, let's go!  ===--==--=----- ----  --  -     ")
print("")

ip = None
def connect_to_wifi():
  global ip
  if phew.is_connected_to_wifi():
    display.draw_boot("wifi connected.")
    logging.info(f"> already connected to wifi")
    return True

  wifi_ssid = config.wifi_ssid
  wifi_password = config.wifi_password
  display.draw_boot(f"connecting to wifi network '{wifi_ssid}'")
  logging.info(f"> connecting to wifi network '{wifi_ssid}'")
  ip = phew.connect_to_wifi(wifi_ssid, wifi_password, timeout_seconds=30)

  if not ip:
    logging.error(f"! failed to connect to wireless network {wifi_ssid}")
    return False

  logging.info("  - ip address: ", ip)

  return True


# log the error, blink the warning led, and go back to sleep
def halt(message):
  logging.error(message)


# returns True if we've used up 90% of the internal filesystem
def low_disk_space():
  if not phew.remote_mount: # os.statvfs doesn't exist on remote mounts
    return (os.statvfs(".")[3] / os.statvfs(".")[2]) < 0.1   
  return False

# connect to wifi and attempt to fetch the current time from an ntp server
def sync_clock_from_ntp():
  from phew import ntp
  if not connect_to_wifi():
    return False
  timestamp = ntp.fetch()
  return True

def startup():
  # write startup banner into log file
  logging.debug("> performing startup")


  # also immediately turn on the LED to indicate that we're doing something
  logging.debug("  - turn on activity led")
  pulse_activity_led(0.5)


from status.mqttsimple import MQTTClient
import ujson
import time

def mqtt_callback(topic, message):
    timelist = list(time.localtime())
    date = timelist[:3]
    timelist.append(MONTHNAMES[timelist[1] - 1])
    logging.info(timelist)
    datestr = "{2} {8} {0:04d}, {3}:{4:02d}".format(*timelist)
    logging.info(f"Incoming message. Topic: {topic}, message: {message}")
    display.draw_status(message, datestr)
    
mqtt_client = None
def connect_mqtt():
  global mqtt_client
  # Connect to MQTT broker
  logging.info(f">Connecting to MQTT Broker")
  
  display.draw_boot("Connecting to MQTT")
  try:
    mqtt_client = MQTTClient("status_pico",
                             config.mqtt_broker_address,
                             user=config.mqtt_broker_username,
                             password=config.mqtt_broker_password)
    mqtt_client.set_callback(mqtt_callback)
    logging.info("MQTT Client Setup")
    mqtt_client.connect()
    logging.info("MQTT Client connected")
    mqtt_client.subscribe("status/status", qos=2)
    logging.info("MQTT Client subscribed")
    current_state = { 'online' : True, 'ip' : ip }
    mqtt_client.publish(f"status/devicestate", ujson.dumps(current_state), retain=False)
    display.draw_boot("MQTT Connected. Ready!")
  except Exception as ex:
      display.draw_boot("Error Connecting to MQTT")
      logging.error("Exception connecting to MQTT broker.")
      logging.error(ex)
    

def loop_mqtt():
  # Loop MQTT connection
  logging.info(f"> Calling MQTT Loop...")
  try:
      while True:
        mqtt_client.check_msg()
        if button_a.read():
            logging.info("Button a Pressed")
        elif button_b.read():
            logging.info("Button b Pressed")
        elif button_c.read():
            logging.info("Button c Pressed")
        time.sleep(1)
  except Exception as ex:
    display.draw_boot("Error Looping")
    logging.error("Exception whilst looping..")
    logging.error(ex)

  

