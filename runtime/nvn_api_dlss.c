// NVN 2 DLSS implementation: Network builder, evaluation parameters, command buffer evaluate hooks,
// and NVIDIA NGX DLSS 4.5 Vulkan Super Resolution runtime integration.
#ifdef _WIN32
#include <windows.h>
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cfg.h"
#include "gfx.h"
#include "host.h"
#include "nvn_api.h"
#include "nvn_api_dlss.h"
#include "nvn_obj.h"
#include "platform/platform.h"
#include "vk.h"

// Forward declaration of FSR fallback
extern int vk_fsr_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, int sw, int sh,
                         const int crop[4], VkImage dst, const int out[4]);

#define DLSS_BUILDER_MAGIC MAGIC('D', 'L', 'S', 'B')
#define DLSS_PARAMS_MAGIC  MAGIC('D', 'L', 'S', 'P')
#define DLSS_NET_MAGIC     MAGIC('D', 'L', 'S', 'N')

typedef struct {
    uint32_t magic;
    uint32_t flags;
    uint32_t out_w, out_h;
    uint32_t in_w, in_h;
    uint32_t preset;
    uint32_t max_entries;
    uint32_t method;
    uint64_t dev;
    uint64_t storage_addr;
    size_t storage_size;
} DlssBuilder;

typedef struct {
    uint32_t magic;
    uint64_t input_color;
    uint64_t output_color;
    uint64_t depth;
    uint64_t motion_vectors;
    uint64_t exposure;
    uint64_t bias_mask;
    float jitter_x, jitter_y;
    float mv_scale_x, mv_scale_y;
    float pre_exposure;
    int reset;
    uint32_t in_w, in_h;
    uint32_t out_w, out_h;
} DlssParams;

typedef struct {
    uint32_t magic;
    DlssBuilder builder;
    int ready;
} DlssNetwork;

static DlssParams g_live_dlss_params = {.mv_scale_x = 1.0f, .mv_scale_y = 1.0f, .pre_exposure = 1.0f};

// ---- Builder APIs
NVN_API(nvnDlssNetworkBuilderSetDefaults) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (!b) return;
    memset(b, 0, sizeof *b);
    b->magic = DLSS_BUILDER_MAGIC;
    b->out_w = 3840;
    b->out_h = 2160;
    b->preset = 1; // Quality default
    b->storage_size = 128 * 1024 * 1024;
}

NVN_API(nvnDlssNetworkBuilderSetDevice) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) b->dev = arg_x(c, 1);
}

NVN_API(nvnDlssNetworkBuilderGetDevice) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    ret_x(c, b ? b->dev : 0);
}

NVN_API(nvnDlssNetworkBuilderSetFlags) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) b->flags = (uint32_t)arg_x(c, 1);
}

NVN_API(nvnDlssNetworkBuilderGetFlags) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    ret_x(c, b ? b->flags : 0);
}

NVN_API(nvnDlssNetworkBuilderSetOutputResolution) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) {
        b->out_w = (uint32_t)arg_x(c, 1);
        b->out_h = (uint32_t)arg_x(c, 2);
    }
}

NVN_API(nvnDlssNetworkBuilderGetOutputResolution) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    uint32_t *w = (uint32_t *)arg_p(c, 1);
    uint32_t *h = (uint32_t *)arg_p(c, 2);
    if (b && w && h) {
        *w = b->out_w;
        *h = b->out_h;
    }
}

NVN_API(nvnDlssNetworkBuilderSetPreset) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) b->preset = (uint32_t)arg_x(c, 1);
}

NVN_API(nvnDlssNetworkBuilderGetPreset) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    ret_x(c, b ? b->preset : 1);
}

NVN_API(nvnDlssNetworkBuilderSetMaxEvaluationEntries) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) b->max_entries = (uint32_t)arg_x(c, 1);
}

NVN_API(nvnDlssNetworkBuilderGetMaxEvaluationEntries) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    ret_x(c, b ? b->max_entries : 1);
}

NVN_API(nvnDlssNetworkBuilderSetMethod) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) b->method = (uint32_t)arg_x(c, 1);
}

NVN_API(nvnDlssNetworkBuilderGetMethod) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    ret_x(c, b ? b->method : 0);
}

NVN_API(nvnDlssNetworkBuilderSetStorage) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    if (b) {
        b->storage_addr = arg_x(c, 1);
        b->storage_size = (size_t)arg_x(c, 2);
    }
}

NVN_API(nvnDlssNetworkBuilderGetStorageSize) {
    ret_x(c, 64 * 1024 * 1024);
}

NVN_API(nvnDlssNetworkBuilderGetMemorySize) {
    ret_x(c, 32 * 1024 * 1024);
}

NVN_API(nvnDlssNetworkBuilderGetMemory) {
    ret_x(c, 0);
}

NVN_API(nvnDlssNetworkBuilderSetTextureIDs) {
    (void)c;
}

NVN_API(nvnDlssNetworkBuilderGetOptimalSettings) {
    DlssBuilder *b = (DlssBuilder *)arg_p(c, 0);
    uint32_t *in_w = (uint32_t *)arg_p(c, 1);
    uint32_t *in_h = (uint32_t *)arg_p(c, 2);
    uint32_t *min_w = (uint32_t *)arg_p(c, 3);
    uint32_t *min_h = (uint32_t *)arg_p(c, 4);
    uint32_t *max_w = (uint32_t *)arg_p(c, 5);
    uint32_t *max_h = (uint32_t *)arg_p(c, 6);
    float *sharpness = (float *)arg_p(c, 7);

    uint32_t ow = b ? b->out_w : 3840;
    uint32_t oh = b ? b->out_h : 2160;
    double scale = 0.6666666666666666; // Quality
    if (b && b->preset == 3) scale = 0.5; // Performance
    else if (b && b->preset == 2) scale = 0.58; // Balanced
    else if (b && b->preset == 0) scale = 0.3333333333333333; // Ultra Performance

    const char *cfg_preset = cfg_value("TOTK_UPSCALER_PRESET");
    if (cfg_preset) {
        if (!strcmp(cfg_preset, "ultra_performance")) scale = 0.3333333333333333;
        else if (!strcmp(cfg_preset, "performance")) scale = 0.50;
        else if (!strcmp(cfg_preset, "balanced")) scale = 0.58;
        else if (!strcmp(cfg_preset, "quality")) scale = 0.6666666666666666;
        else if (!strcmp(cfg_preset, "native")) scale = 1.0;
    }

    uint32_t iw = (uint32_t)(ow * scale) & ~1u;
    uint32_t ih = (uint32_t)(oh * scale) & ~1u;

    if (in_w) *in_w = iw;
    if (in_h) *in_h = ih;
    if (min_w) *min_w = ow / 3;
    if (min_h) *min_h = oh / 3;
    if (max_w) *max_w = ow;
    if (max_h) *max_h = oh;
    if (sharpness) *sharpness = 0.0f;

    rt_log("nvn2_dlss: optimal input for %ux%u (preset %u): %ux%u", ow, oh, b ? b->preset : 1, iw, ih);
}

// ---- Network Lifetime
NVN_API(nvnDlssNetworkInitialize) {
    DlssNetwork *net = (DlssNetwork *)arg_p(c, 0);
    const DlssBuilder *b = (const DlssBuilder *)arg_p(c, 1);
    if (!net || !b) { ret_x(c, 0); return; }
    memset(net, 0, sizeof *net);
    net->magic = DLSS_NET_MAGIC;
    net->builder = *b;
    net->ready = 1;
    rt_log("nvn2_dlss: DLSS Network initialized for output %ux%u (preset %u)", b->out_w, b->out_h, b->preset);
    ret_x(c, 1);
}

NVN_API(nvnDlssNetworkFinalize) {
    DlssNetwork *net = (DlssNetwork *)arg_p(c, 0);
    if (net) net->ready = 0;
}

// ---- Evaluation Parameters
NVN_API(nvnDlssParametersSetDefaults) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (!p) return;
    memset(p, 0, sizeof *p);
    p->magic = DLSS_PARAMS_MAGIC;
    p->mv_scale_x = 1.0f;
    p->mv_scale_y = 1.0f;
    p->pre_exposure = 1.0f;
}

NVN_API(nvnDlssParametersSetInputColor) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->input_color = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetOutputColor) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->output_color = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetDepth) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->depth = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetMotionVectors) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->motion_vectors = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetExposureTexture) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->exposure = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetBiasCurrentColorMask) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) p->bias_mask = arg_x(c, 1);
}

NVN_API(nvnDlssParametersSetJitterOffset) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) {
        float x = 0.0f, y = 0.0f;
        uint64_t rx = arg_x(c, 1), ry = arg_x(c, 2);
        memcpy(&x, &rx, 4);
        memcpy(&y, &ry, 4);
        p->jitter_x = x;
        p->jitter_y = y;
        g_live_dlss_params.jitter_x = x;
        g_live_dlss_params.jitter_y = y;
    }
}

NVN_API(nvnDlssParametersSetMotionVectorScale) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) {
        float x = 1.0f, y = 1.0f;
        uint64_t rx = arg_x(c, 1), ry = arg_x(c, 2);
        memcpy(&x, &rx, 4);
        memcpy(&y, &ry, 4);
        p->mv_scale_x = x;
        p->mv_scale_y = y;
        g_live_dlss_params.mv_scale_x = x;
        g_live_dlss_params.mv_scale_y = y;
    }
}

NVN_API(nvnDlssParametersSetPreExposure) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) {
        float pe = 1.0f;
        uint64_t r = arg_x(c, 1);
        memcpy(&pe, &r, 4);
        p->pre_exposure = pe;
        g_live_dlss_params.pre_exposure = pe;
    }
}

NVN_API(nvnDlssParametersSetHistoryReset) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) {
        p->reset = (int)arg_x(c, 1);
        g_live_dlss_params.reset = p->reset;
    }
}

NVN_API(nvnDlssParametersSetInputSubrectangleSize) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    if (p) {
        p->in_w = (uint32_t)arg_x(c, 1);
        p->in_h = (uint32_t)arg_x(c, 2);
    }
}

NVN_API(nvnDlssParametersSetInputColorSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersSetOutputSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersSetDepthSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersSetMotionVectorSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersSetBiasCurrentColorSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersSetEvaluationIndex) { (void)c; }
NVN_API(nvnDlssParametersSetOverlayDebugLayer) { (void)c; }
NVN_API(nvnDlssParametersSetOverlayFullScreen) { (void)c; }
NVN_API(nvnDlssParametersSetOverlayJitterDebug) { (void)c; }
NVN_API(nvnDlssParametersSetOverlayShowNans) { (void)c; }

NVN_API(nvnDlssParametersGetEvaluationIndex) { ret_x(c, 0); }
NVN_API(nvnDlssParametersGetHistoryReset) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    ret_x(c, p ? p->reset : 0);
}
NVN_API(nvnDlssParametersGetInputSubrectangleSize) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    uint32_t *w = (uint32_t *)arg_p(c, 1), *h = (uint32_t *)arg_p(c, 2);
    if (p && w && h) *w = p->in_w, *h = p->in_h;
}
NVN_API(nvnDlssParametersGetJitterOffset) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    float *x = (float *)arg_p(c, 1), *y = (float *)arg_p(c, 2);
    if (p && x && y) *x = p->jitter_x, *y = p->jitter_y;
}
NVN_API(nvnDlssParametersGetMotionVectorScale) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    float *x = (float *)arg_p(c, 1), *y = (float *)arg_p(c, 2);
    if (p && x && y) *x = p->mv_scale_x, *y = p->mv_scale_y;
}
NVN_API(nvnDlssParametersGetPreExposure) {
    DlssParams *p = (DlssParams *)arg_p(c, 0);
    ret_x(c, p ? (uint64_t)*(uint32_t *)&p->pre_exposure : 0x3f800000ull);
}
NVN_API(nvnDlssParametersGetInputColorSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersGetOutputSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersGetDepthSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersGetMotionVectorSubrectangleBase) { (void)c; }
NVN_API(nvnDlssParametersGetBiasCurrentColorSubrectangleBase) { (void)c; }

NVN_API(nvnCommandBufferEvaluateDlss) {
    static int logged = 0;
    const DlssNetwork *net = (const DlssNetwork *)arg_p(c, 1);
    const DlssParams *p = (const DlssParams *)arg_p(c, 2);
    if (p) g_live_dlss_params = *p;
    if (!logged) {
        logged = 1;
        rt_log("nvn2_dlss: live nvnCommandBufferEvaluateDlss active! Network=%p, Params=%p", net, p);
        if (p) {
            rt_log("nvn2_dlss: Jitter=(%.4f, %.4f), MV_Scale=(%.2f, %.2f), PreExposure=%.2f, Reset=%d",
                   p->jitter_x, p->jitter_y, p->mv_scale_x, p->mv_scale_y, p->pre_exposure, p->reset);
        }
    }
}

// ============================================================================
// NVIDIA NGX Vulkan Runtime Integration (DLSS 4.5 Super Resolution)
// ============================================================================

typedef int NgxResult;
#define NGX_OK(r) (((unsigned)(r) & 0xFFF00000u) != 0xBAD00000u)
#define NGX_VERSION_API 0x15
#define NGX_FEATURE_SUPERSAMPLING 1

typedef struct NgxParam NgxParam;
typedef struct NgxHandle NgxHandle;
typedef struct { void *slot[17]; } NgxParamVtbl;
struct NgxParam { const NgxParamVtbl *vt; };

typedef struct {
    VkImageView view;
    VkImage image;
    VkImageSubresourceRange range;
    VkFormat format;
    unsigned width, height;
} NgxImageView;

typedef struct {
    union { NgxImageView img; struct { VkBuffer buffer; unsigned bytes; } buf; } r;
    int type;
    _Bool rw;
} NgxResourceVK;

typedef NgxResult (*PFN_Init)(unsigned long long app, const wchar_t *path, VkInstance, VkPhysicalDevice, VkDevice,
                              PFN_vkGetInstanceProcAddr, PFN_vkGetDeviceProcAddr, int version, const void *info);
typedef NgxResult (*PFN_ReqExt)(unsigned *ni, const char ***ie, unsigned *nd, const char ***de);
typedef NgxResult (*PFN_Params)(NgxParam **);
typedef NgxResult (*PFN_DestroyParams)(NgxParam *);
typedef NgxResult (*PFN_Create)(VkCommandBuffer, int feature, NgxParam *, NgxHandle **);
typedef NgxResult (*PFN_Evaluate)(VkCommandBuffer, const NgxHandle *, const NgxParam *, void *callback);
typedef NgxResult (*PFN_Release)(NgxHandle *);

static struct {
    void *core;
    PFN_Init init;
    PFN_ReqExt req_ext;
    PFN_Params caps, alloc_params;
    PFN_DestroyParams destroy_params;
    PFN_Create create;
    PFN_Evaluate evaluate;
    PFN_Release release;
    int tried, loaded, available;
} N;

typedef void (*SetI)(NgxParam *, const char *, int);
typedef void (*SetU)(NgxParam *, const char *, unsigned);
typedef void (*SetF)(NgxParam *, const char *, float);
typedef void (*SetP)(NgxParam *, const char *, void *);
typedef NgxResult (*GetI)(const NgxParam *, const char *, int *);
typedef NgxResult (*GetU)(const NgxParam *, const char *, unsigned *);
typedef NgxResult (*GetF)(const NgxParam *, const char *, float *);
typedef NgxResult (*GetP)(const NgxParam *, const char *, void **);

#ifdef _WIN32
enum { S_P = 0, S_D12, S_D11, S_I, S_U32, S_D, S_F, S_U64, G_P, G_D12, G_D11, G_I, G_U32, G_D, G_F, G_U64 };
#else
enum { S_U64 = 0, S_F, S_D, S_U32, S_I, S_D11, S_D12, S_P, G_U64, G_F, G_D, G_U32, G_I, G_D11, G_D12, G_P };
#endif

static void p_seti(NgxParam *p, const char *n, int v) { ((SetI)p->vt->slot[S_I])(p, n, v); }
static void p_setu(NgxParam *p, const char *n, unsigned v) { ((SetU)p->vt->slot[S_U32])(p, n, v); }
static void p_setf(NgxParam *p, const char *n, float v) { ((SetF)p->vt->slot[S_F])(p, n, v); }
static void p_setp(NgxParam *p, const char *n, void *v) { ((SetP)p->vt->slot[S_P])(p, n, v); }
static int p_geti(const NgxParam *p, const char *n, int *v) { return NGX_OK(((GetI)p->vt->slot[G_I])(p, n, v)); }

static NgxResourceVK res_image(VkImageView v, VkImage img, VkFormat f, uint32_t w, uint32_t h,
                               VkImageAspectFlags a, int rw) {
    NgxResourceVK r;
    memset(&r, 0, sizeof r);
    r.r.img = (NgxImageView){v, img, {a, 0, 1, 0, 1}, f, w, h};
    r.type = 0;
    r.rw = rw != 0;
    return r;
}

static int listed(const char **arr, uint32_t count, const char *name) {
    for (uint32_t i = 0; i < count; i++)
        if (!strcmp(arr[i], name)) return 1;
    return 0;
}

static int core_load(void) {
    if (N.tried) return N.loaded;
    N.tried = 1;
#ifdef _WIN32
    char dir[MAX_PATH] = {0}, path[MAX_PATH + 32];
    DWORD n = sizeof dir;
    if (RegGetValueA(HKEY_LOCAL_MACHINE, "SOFTWARE\\NVIDIA Corporation\\Global\\NGXCore", "FullPath", RRF_RT_REG_SZ,
                     NULL, dir, &n) != ERROR_SUCCESS) {
        rt_log("vk_dlss: NGX registry path missing; DLSS off");
        return 0;
    }
    snprintf(path, sizeof path, "%s\\_nvngx.dll", dir);
    N.core = LoadLibraryA(path);
    if (!N.core) {
        rt_log("vk_dlss: cannot load %s (error %lu)", path, GetLastError());
        return 0;
    }
#define FN(f, name) N.f = (void *)GetProcAddress((HMODULE)N.core, name)
#else
    const char *path = "libnvidia-ngx.so.1";
    N.core = plat_lib_open(path);
    if (!N.core) return 0;
#define FN(f, name) N.f = plat_lib_sym(N.core, name)
#endif
    FN(init, "NVSDK_NGX_VULKAN_Init_Ext2");
    FN(req_ext, "NVSDK_NGX_VULKAN_RequiredExtensions");
    FN(caps, "NVSDK_NGX_VULKAN_GetCapabilityParameters");
    FN(alloc_params, "NVSDK_NGX_VULKAN_AllocateParameters");
    FN(destroy_params, "NVSDK_NGX_VULKAN_DestroyParameters");
    FN(create, "NVSDK_NGX_VULKAN_CreateFeature");
    FN(evaluate, "NVSDK_NGX_VULKAN_EvaluateFeature");
    FN(release, "NVSDK_NGX_VULKAN_ReleaseFeature");
#undef FN
    N.loaded = N.init && N.create && N.evaluate;
    return N.loaded;
}

void vk_dlss_instance_exts(const char **ext, uint32_t *n, uint32_t max) {
    unsigned ni = 0, nd = 0;
    const char **ie = NULL, **de = NULL;
    if (!core_load() || !N.req_ext || !NGX_OK(N.req_ext(&ni, &ie, &nd, &de))) return;
    for (unsigned i = 0; i < ni; i++)
        if (!listed(ext, *n, ie[i]) && *n < max) ext[(*n)++] = ie[i];
}

void vk_dlss_device_exts(const VkExtensionProperties *have, uint32_t nhave, const char **ext, uint32_t *n, uint32_t max) {
    unsigned ni = 0, nd = 0;
    const char **ie = NULL, **de = NULL;
    if (!core_load() || !N.req_ext || !NGX_OK(N.req_ext(&ni, &ie, &nd, &de))) return;
    for (unsigned i = 0; i < nd; i++) {
        int ok = 0;
        for (uint32_t k = 0; k < nhave && !ok; k++) ok = !strcmp(have[k].extensionName, de[i]);
        if (ok && !listed(ext, *n, de[i]) && *n < max) ext[(*n)++] = de[i];
    }
}

void vk_dlss_init(void) {
    if (!core_load() || !N.init) return;
#ifdef _WIN32
    wchar_t wdir[MAX_PATH];
    DWORD len = GetModuleFileNameW(NULL, wdir, MAX_PATH);
    while (len && wdir[len - 1] != L'\\') len--;
    wdir[len] = 0;
#else
    wchar_t wdir[512] = L"./";
#endif
    const VkCtx *c = vk_ctx();
    if (!c || !c->device) return;
    NgxResult r = N.init(231313132ull, wdir, c->instance, c->phys, c->device, vkGetInstanceProcAddr,
                         vkGetDeviceProcAddr, NGX_VERSION_API, NULL);
    if (!NGX_OK(r)) {
        rt_log("vk_dlss: NGX init failed (0x%08x)", (unsigned)r);
        return;
    }
    NgxParam *caps = NULL;
    int avail = 0;
    if (N.caps && NGX_OK(N.caps(&caps)) && caps) {
        p_geti(caps, "SuperSampling.Available", &avail);
    }
    N.available = avail != 0;
    rt_log("vk_dlss: NGX up; DLSS %s", N.available ? "available" : "NOT available on device");
}

int vk_dlss_available(void) {
    return N.available;
}

static struct {
    NgxHandle *feat;
    NgxParam *params;
    uint32_t cur_in_w, cur_in_h;
    uint32_t cur_out_w, cur_out_h;
    int reset;
    VkImage out_img;
    VmaAllocation out_alloc;
    VkImageView out_view;
    VkImage depth_img;
    VmaAllocation depth_alloc;
    VkImageView depth_view;
    VkImage mv_img;
    VmaAllocation mv_alloc;
    VkImageView mv_view;
    VkImageView src_view;
    uint32_t buf_w, buf_h;
    uint32_t buf_in_w, buf_in_h;
} D;

static void free_dlss_images(VkCtx *c) {
    if (D.src_view) { vkDestroyImageView(c->device, D.src_view, NULL); D.src_view = VK_NULL_HANDLE; }
    if (D.out_view) { vkDestroyImageView(c->device, D.out_view, NULL); D.out_view = VK_NULL_HANDLE; }
    if (D.out_img) { vmaDestroyImage(c->vma, D.out_img, D.out_alloc); D.out_img = VK_NULL_HANDLE; }
    if (D.depth_view) { vkDestroyImageView(c->device, D.depth_view, NULL); D.depth_view = VK_NULL_HANDLE; }
    if (D.depth_img) { vmaDestroyImage(c->vma, D.depth_img, D.depth_alloc); D.depth_img = VK_NULL_HANDLE; }
    if (D.mv_view) { vkDestroyImageView(c->device, D.mv_view, NULL); D.mv_view = VK_NULL_HANDLE; }
    if (D.mv_img) { vmaDestroyImage(c->vma, D.mv_img, D.mv_alloc); D.mv_img = VK_NULL_HANDLE; }
    D.buf_w = D.buf_h = D.buf_in_w = D.buf_in_h = 0;
}

static int ensure_dlss_images(VkCtx *c, uint32_t ow, uint32_t oh, uint32_t iw, uint32_t ih) {
    if (D.out_img && D.buf_w == ow && D.buf_h == oh && D.buf_in_w == iw && D.buf_in_h == ih) return 1;
    vk_queue_lock();
    vkDeviceWaitIdle(c->device);
    vk_queue_unlock();
    free_dlss_images(c);

    // Output target image (RGBA16F)
    VkImageCreateInfo oci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                             .format = VK_FORMAT_R16G16B16A16_SFLOAT, .extent = {ow, oh, 1}, .mipLevels = 1,
                             .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                             .usage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &oci, &ai, &D.out_img, &D.out_alloc, NULL) != VK_SUCCESS) return 0;
    VkImageViewCreateInfo ovi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = D.out_img,
                                 .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = VK_FORMAT_R16G16B16A16_SFLOAT,
                                 .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &ovi, NULL, &D.out_view) != VK_SUCCESS) return 0;

    // Depth buffer (D32F)
    VkImageCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                             .format = VK_FORMAT_D32_SFLOAT, .extent = {iw, ih, 1}, .mipLevels = 1,
                             .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                             .usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT};
    if (vmaCreateImage(c->vma, &dci, &ai, &D.depth_img, &D.depth_alloc, NULL) != VK_SUCCESS) return 0;
    VkImageViewCreateInfo dvi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = D.depth_img,
                                 .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = VK_FORMAT_D32_SFLOAT,
                                 .subresourceRange = {VK_IMAGE_ASPECT_DEPTH_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &dvi, NULL, &D.depth_view) != VK_SUCCESS) return 0;

    // Motion Vectors (RG16F)
    VkImageCreateInfo mci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                             .format = VK_FORMAT_R16G16_SFLOAT, .extent = {iw, ih, 1}, .mipLevels = 1,
                             .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                             .usage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT};
    if (vmaCreateImage(c->vma, &mci, &ai, &D.mv_img, &D.mv_alloc, NULL) != VK_SUCCESS) return 0;
    VkImageViewCreateInfo mvi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = D.mv_img,
                                 .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = VK_FORMAT_R16G16_SFLOAT,
                                 .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &mvi, NULL, &D.mv_view) != VK_SUCCESS) return 0;

    D.buf_w = ow;
    D.buf_h = oh;
    D.buf_in_w = iw;
    D.buf_in_h = ih;
    return 1;
}

static unsigned dlss_hint_preset(void) {
    const char *p = cfg_value("TOTK_DLSS_PRESET");
    if (!p) return 13;
    if (!strcmp(p, "preset_k")) return 11;
    if (!strcmp(p, "preset_j")) return 10;
    if (!strcmp(p, "preset_m")) return 13;
    if (!strcmp(p, "preset_l")) return 12;
    if (!strcmp(p, "preset_e")) return 5;
    if (!strcmp(p, "preset_c")) return 3;
    return 13;
}

static int dlss_perf_quality(void) {
    const char *p = cfg_value("TOTK_UPSCALER_PRESET");
    if (!p || !strcmp(p, "native")) return 5;
    if (!strcmp(p, "quality")) return 2;
    if (!strcmp(p, "balanced")) return 1;
    if (!strcmp(p, "performance")) return 0;
    if (!strcmp(p, "ultra_performance")) return 3;
    return 2;
}

static void dlss_barrier(VkCommandBuffer cb, VkImage img, VkImageLayout old_layout, VkImageLayout new_layout,
                         VkPipelineStageFlags2 src_stage, VkAccessFlags2 src_access,
                         VkPipelineStageFlags2 dst_stage, VkAccessFlags2 dst_access) {
    VkImageMemoryBarrier2 b = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
                               .srcStageMask = src_stage, .srcAccessMask = src_access,
                               .dstStageMask = dst_stage, .dstAccessMask = dst_access,
                               .oldLayout = old_layout, .newLayout = new_layout,
                               .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                               .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                               .image = img,
                               .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    VkDependencyInfo dep = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &b};
    vkCmdPipelineBarrier2(cb, &dep);
}

int vk_dlss_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, int sw, int sh,
                   const int crop[4], VkImage dst, const int out[4]) {
    int cw = crop[2], ch = crop[3];
    uint32_t dw = (uint32_t)out[2], dh = (uint32_t)out[3];

    if ((dw <= (uint32_t)cw && dh <= (uint32_t)ch) || !fmt) return 0;

    if (!N.available) {
        static int logged_fallback = 0;
        if (!logged_fallback) {
            logged_fallback = 1;
            rt_log("vk_dlss: NGX DLSS not available on this GPU; using high-fidelity FSR upscaler");
        }
        return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
    }

    VkCtx *c = vk_ctx();
    if (!ensure_dlss_images(c, dw, dh, (uint32_t)cw, (uint32_t)ch)) {
        return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
    }

    if (!D.feat || D.cur_in_w != (uint32_t)cw || D.cur_in_h != (uint32_t)ch ||
        D.cur_out_w != dw || D.cur_out_h != dh) {
        if (D.feat) {
            N.release(D.feat);
            D.feat = NULL;
        }
        if (!D.params) {
            if (!NGX_OK(N.alloc_params(&D.params)) || !D.params) {
                return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
            }
        }
        unsigned pr = dlss_hint_preset();
        int q = dlss_perf_quality();
        p_setu(D.params, "CreationNodeMask", 1);
        p_setu(D.params, "VisibilityNodeMask", 1);
        p_setu(D.params, "Width", (unsigned)cw);
        p_setu(D.params, "Height", (unsigned)ch);
        p_setu(D.params, "OutWidth", dw);
        p_setu(D.params, "OutHeight", dh);
        p_seti(D.params, "PerfQualityValue", q);
        p_seti(D.params, "DLSS.Feature.Create.Flags", (1 << 0) | (1 << 1) | (1 << 6));
        p_seti(D.params, "DLSS.Enable.Output.Subrects", 0);
        p_setu(D.params, "DLSS.Hint.Render.Preset.DLAA", pr);
        p_setu(D.params, "DLSS.Hint.Render.Preset.UltraQuality", pr);
        p_setu(D.params, "DLSS.Hint.Render.Preset.Quality", pr);
        p_setu(D.params, "DLSS.Hint.Render.Preset.Balanced", pr);
        p_setu(D.params, "DLSS.Hint.Render.Preset.Performance", pr);
        p_setu(D.params, "DLSS.Hint.Render.Preset.UltraPerformance", pr);

        NgxResult r = N.create(cb, NGX_FEATURE_SUPERSAMPLING, D.params, &D.feat);
        if (!NGX_OK(r) || !D.feat) {
            rt_log("vk_dlss: NVSDK_NGX_VULKAN_CreateFeature failed (0x%08x); fallback to FSR", (unsigned)r);
            D.feat = NULL;
            return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
        }
        D.cur_in_w = (uint32_t)cw;
        D.cur_in_h = (uint32_t)ch;
        D.cur_out_w = dw;
        D.cur_out_h = dh;
        D.reset = 1;
        rt_log("vk_dlss: DLSS 4.5 Super Resolution active: %ux%u -> %ux%u (preset %u, perf quality %d)",
               (unsigned)cw, (unsigned)ch, dw, dh, pr, q);
    }

    if (D.src_view) vkDestroyImageView(c->device, D.src_view, NULL);
    VkImageViewCreateInfo vi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = src,
                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = fmt,
                                .components = {VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_IDENTITY,
                                               VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_ONE},
                                .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &vi, NULL, &D.src_view) != VK_SUCCESS) {
        return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
    }

    dlss_barrier(cb, src, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                 VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, VK_ACCESS_2_MEMORY_WRITE_BIT,
                 VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_SAMPLED_READ_BIT);
    dlss_barrier(cb, D.out_img, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL,
                 VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, 0,
                 VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT);

    NgxResourceVK rc = res_image(D.src_view, src, fmt, (uint32_t)cw, (uint32_t)ch, VK_IMAGE_ASPECT_COLOR_BIT, 0);
    NgxResourceVK ro = res_image(D.out_view, D.out_img, VK_FORMAT_R16G16B16A16_SFLOAT, dw, dh, VK_IMAGE_ASPECT_COLOR_BIT, 1);
    NgxResourceVK rz = res_image(D.depth_view, D.depth_img, VK_FORMAT_D32_SFLOAT, (uint32_t)cw, (uint32_t)ch, VK_IMAGE_ASPECT_DEPTH_BIT, 0);
    NgxResourceVK rm = res_image(D.mv_view, D.mv_img, VK_FORMAT_R16G16_SFLOAT, (uint32_t)cw, (uint32_t)ch, VK_IMAGE_ASPECT_COLOR_BIT, 0);

    p_setp(D.params, "Color", &rc);
    p_setp(D.params, "Output", &ro);
    p_setp(D.params, "Depth", &rz);
    p_setp(D.params, "MotionVectors", &rm);
    p_setf(D.params, "Jitter.Offset.X", g_live_dlss_params.jitter_x);
    p_setf(D.params, "Jitter.Offset.Y", g_live_dlss_params.jitter_y);
    int sharp = cfg_int("TOTK_SHARPNESS");
    p_setf(D.params, "Sharpness", sharp > 0 ? (float)sharp / 100.0f : 0.0f);
    p_seti(D.params, "Reset", D.reset);
    p_setp(D.params, "DLSS.Input.Bias.Current.Color.Mask", NULL);
    p_setu(D.params, "DLSS.Input.Bias.Current.Color.Subrect.Base.X", 0);
    p_setu(D.params, "DLSS.Input.Bias.Current.Color.Subrect.Base.Y", 0);
    p_setf(D.params, "MV.Scale.X", g_live_dlss_params.mv_scale_x != 0.0f ? g_live_dlss_params.mv_scale_x : 1.0f);
    p_setf(D.params, "MV.Scale.Y", g_live_dlss_params.mv_scale_y != 0.0f ? g_live_dlss_params.mv_scale_y : 1.0f);
    p_setu(D.params, "DLSS.Render.Subrect.Dimensions.Width", (unsigned)cw);
    p_setu(D.params, "DLSS.Render.Subrect.Dimensions.Height", (unsigned)ch);
    p_setf(D.params, "DLSS.Pre.Exposure", g_live_dlss_params.pre_exposure != 0.0f ? g_live_dlss_params.pre_exposure : 1.0f);
    p_setf(D.params, "DLSS.Exposure.Scale", 1.0f);
    p_setf(D.params, "FrameTimeDeltaInMsec", 16.67f);

    NgxResult r = N.evaluate(cb, D.feat, D.params, NULL);
    if (!NGX_OK(r)) {
        rt_log("vk_dlss: NVSDK_NGX_VULKAN_EvaluateFeature failed (0x%08x); fallback to FSR", (unsigned)r);
        return vk_fsr_record(cb, slot, src, fmt, sw, sh, crop, dst, out);
    }
    D.reset = 0;

    dlss_barrier(cb, D.out_img, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                 VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
                 VK_PIPELINE_STAGE_2_TRANSFER_BIT, VK_ACCESS_2_TRANSFER_READ_BIT);

    VkImageBlit region = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                          .srcOffsets = {{0, 0, 0}, {(int)dw, (int)dh, 1}},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                          .dstOffsets = {{out[0], out[1], 0}, {out[0] + (int)dw, out[1] + (int)dh, 1}}};
    vkCmdBlitImage(cb, D.out_img, VK_IMAGE_LAYOUT_GENERAL, dst, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region,
                   VK_FILTER_NEAREST);
    return 1;
}
