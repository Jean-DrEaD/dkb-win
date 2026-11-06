/* Substitui o zbic.c do BANANAS (faltou third_party/zbic no repo). Usa a libzstd do MSYS2. */
#include <stddef.h>
#include <zstd.h>
size_t rt_zbic_decompress(void *dst, size_t dstCap, const void *src, size_t srcSize) {
    size_t r = ZSTD_decompress(dst, dstCap, src, srcSize);
    return ZSTD_isError(r) ? 0 : r;
}
