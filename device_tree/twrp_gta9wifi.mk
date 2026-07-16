#
# Copyright (C) 2026 The Android Open Source Project
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),gta9wifi)

# Recovery
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
TARGET_RECOVERY_DEVICE_MODULES += init.recovery.gta9wifi

# Inherit from common TWRP
-include vendor/twrp/config/common.mk

# Device-specific fstab
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/recovery/root/system/etc/recovery.fstab:recovery/root/system/etc/recovery.fstab

# Init scripts
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/recovery/root/init.recovery.mt8781.rc:root/init.recovery.mt8781.rc \
    $(LOCAL_PATH)/recovery/root/init.recovery.samsung.rc:root/init.recovery.samsung.rc \
    $(LOCAL_PATH)/recovery/root/dsms.rc:root/dsms.rc \
    $(LOCAL_PATH)/recovery/root/dsms_common.rc:root/dsms_common.rc \
    $(LOCAL_PATH)/recovery/root/mtk-plpath-utils.rc:root/mtk-plpath-utils.rc

# Vendor binaries required for recovery
PRODUCT_PACKAGES += \
    mtk_plpath_utils \
    SamsungReclaim \
    SamsungTexTocToc \
    libkeyutils \
    libhwbinder \
    libhidlbase \
    libsoftkeymasterdevice \
    android.hardware.keymaster@3.0-impl \
    android.hardware.keymaster@4.0-impl

# Debug
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
    ro.debuggable=1 \
    ro.adb.secure=0 \
    persist.service.adb.enable=1 \
    persist.sys.usb.config=mtp,adb

endif
