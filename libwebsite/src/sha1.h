#ifndef LIBWEBSITE_SHA1_H
#define LIBWEBSITE_SHA1_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint32_t state[5];
    uint64_t bitcount;
    uint8_t buffer[64];
    size_t buffer_len;
} SHA1_CTX;

void SHA1_Init(SHA1_CTX *ctx);
void SHA1_Update(SHA1_CTX *ctx, const void *data, size_t len);
void SHA1_Final(unsigned char digest[20], SHA1_CTX *ctx);
unsigned char *SHA1(const unsigned char *data, size_t len,
                    unsigned char *digest);

#endif /* LIBWEBSITE_SHA1_H */

