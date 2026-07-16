#
# Copyright (C) 2026 The Android Open Source Project
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common Omni stuff.
$(call inherit-product, vendor/omni/config/common.mk)

# Inherit from gta9wifi device
$(call inherit-product, device/samsung/gta9wifi/device.mk)

PRODUCT_DEVICE := gta9wifi
PRODUCT_NAME := omni_gta9wifi
PRODUCT_BRAND := samsung
PRODUCT_MODEL := SM-X110
PRODUCT_MANUFACTURER := samsung

PRODUCT_GMS_CLIENTID_BASE := android-samsung

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="gta9wifixx-user 12 SP1A.210812.016 X110XXS3BXG4 release-keys"

BUILD_FINGERPRINT := samsung/gta9wifixx/gta9wifi:12/SP1A.210812.016/X110XXS3BXG4:user/release-keys
