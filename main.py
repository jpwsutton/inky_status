# status - wireless statusnmental monitoring and logging
#
# On first run status will go into provisioning mode where it appears
# as a wireless access point called "status <board type> Setup". Connect
# to the access point with your phone, tablet or laptop and follow the
# on screen instructions.
#
# The provisioning process will generate a `config.py` file which 
# contains settings like your wifi username/password, how often you
# want to log data, and where to upload your data once it is collected.
#
# You can use status out of the box with the options that we supply
# or alternatively you can create your own firmware that behaves how
# you want it to - please share your setups with us! :-)
#
# Need help? check out https://pimoroni.com/status-guide
#
# Happy data hoarding folks,
#
#   - the Pimoroni pirate crew

# import status firmware, this will trigger provisioning if needed
import status

# initialise status
status.startup()

# now that we know the device is provisioned import the config
try:
  import config
except:
  status.halt("! failed to load config.py")

# if the clock isn't set...

status.logging.info("> clock not set, synchronise from ntp server")
if not status.sync_clock_from_ntp():
    # failed to talk to ntp server go back to sleep for another cycle
    status.halt("! failed to synchronise clock")
    status.logging.info("  - rtc synched")


status.stop_activity_led()
status.logging.info("Start to connect to MQTT here?")

status.connect_mqtt()

status.loop_mqtt()
