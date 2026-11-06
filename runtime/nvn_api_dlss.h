#pragma once
#include <stdint.h>
#include "vk.h"

#ifdef __cplusplus
extern "C" {
#endif

void vk_dlss_instance_exts(const char **ext, uint32_t *n, uint32_t max);
void vk_dlss_device_exts(const VkExtensionProperties *have, uint32_t nhave, const char **ext, uint32_t *n, uint32_t max);
void vk_dlss_init(void);
int vk_dlss_available(void);
int vk_dlss_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, int sw, int sh,
                   const int crop[4], VkImage dst, const int out[4]);

#ifdef __cplusplus
}
#endif
