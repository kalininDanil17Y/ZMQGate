#ifndef ZEROGW_MD5_H
#define ZEROGW_MD5_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint32_t state[4];
    uint64_t bitcount;
    uint8_t buffer[64];
    size_t buffer_len;
} MD5_CTX;

#define MD5_DIGEST_LENGTH 16

void MD5_Init(MD5_CTX *ctx);
void MD5_Update(MD5_CTX *ctx, const void *data, size_t len);
void MD5_Final(unsigned char digest[MD5_DIGEST_LENGTH], MD5_CTX *ctx);

#endif /* ZEROGW_MD5_H */

