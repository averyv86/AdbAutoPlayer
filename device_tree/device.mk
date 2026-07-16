#
# Copyright (C) 2026 The Android Open Source Project
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := device/samsung/gta9wifi

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from TWRP common
$(call inherit-product, vendor/twrp/config/common.mk)

PRODUCT_DEVICE := gta9wifi
PRODUCT_NAME := twrp_gta9wifi
PRODUCT_BRAND := samsung
PRODUCT_MODEL := SM-X110
PRODUCT_MANUFACTURER := samsung

PRODUCT_GMS_CLIENTID_BASE := android-samsung

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="gta9wifixx-user 12 SP1A.210812.016 X110XXS3BXG4 release-keys"

BUILD_FINGERPRINT := samsung/gta9wifixx/gta9wifi:12/SP1A.210812.016/X110XXS3BXG4:user/release-keys

# TWRP product packages
PRODUCT_PACKAGES += \
    twrp \
    recovery

# Debug ADB
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
    ro.debuggable=1 \
    ro.secure=0 \
    ro.adb.secure=0 \
    persist.service.adb.enable=1 \
    persist.sys.usb.config=mtp,adb

# Samsung recovery-specific
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/recovery/root/system/etc/recovery.fstab:recovery/root/system/etc/recovery.fstab
