# Runs once at power-up: present the Pico to the computer as a USB joystick.
# Changes here only take effect after a hard reset (unplug/replug).
import supervisor
import usb_hid

supervisor.set_usb_identification(manufacturer="DIY", product="DIY Switch Panel")

# 32 buttons, no axes.
JOYSTICK_DESCRIPTOR = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x04,        # Usage (Joystick)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x04,        #   Report ID (4)
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (1)
    0x29, 0x20,        #   Usage Maximum (32)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x20,        #   Report Count (32)
    0x81, 0x02,        #   Input (Data, Var, Abs)
    0xC0,              # End Collection
))

usb_hid.enable((
    usb_hid.Device(
        report_descriptor=JOYSTICK_DESCRIPTOR,
        usage_page=0x01,
        usage=0x04,
        report_ids=(4,),
        in_report_lengths=(4,),
        out_report_lengths=(0,),
    ),
))
