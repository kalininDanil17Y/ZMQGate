#include "sha1.h"

#include <string.h>

#define ROTL32(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

static void sha1_transform(uint32_t state[5], const uint8_t block[64]) {
    uint32_t w[80];
    for(int i = 0; i < 16; ++i) {
        w[i] = ((uint32_t)block[i * 4] << 24)
            | ((uint32_t)block[i * 4 + 1] << 16)
            | ((uint32_t)block[i * 4 + 2] << 8)
            | ((uint32_t)block[i * 4 + 3]);
    }
    for(int i = 16; i < 80; ++i) {
        w[i] = ROTL32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
    }

    uint32_t a = state[0];
    uint32_t b = state[1];
    uint32_t c = state[2];
    uint32_t d = state[3];
    uint32_t e = state[4];

    for(int i = 0; i < 80; ++i) {
        uint32_t f, k;
        if(i < 20) {
            f = (b & c) | ((~b) & d);
            k = 0x5a827999;
        } else if(i < 40) {
            f = b ^ c ^ d;
            k = 0x6ed9eba1;
        } else if(i < 60) {
            f = (b & c) | (b & d) | (c & d);
            k = 0x8f1bbcdc;
        } else {
            f = b ^ c ^ d;
            k = 0xca62c1d6;
        }
        uint32_t temp = ROTL32(a, 5) + f + e + k + w[i];
        e = d;
        d = c;
        c = ROTL32(b, 30);
        b = a;
        a = temp;
    }

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
}

void SHA1_Init(SHA1_CTX *ctx) {
    ctx->state[0] = 0x67452301;
    ctx->state[1] = 0xefcdab89;
    ctx->state[2] = 0x98badcfe;
    ctx->state[3] = 0x10325476;
    ctx->state[4] = 0xc3d2e1f0;
    ctx->bitcount = 0;
    ctx->buffer_len = 0;
}

void SHA1_Update(SHA1_CTX *ctx, const void *data, size_t len) {
    const uint8_t *bytes = (const uint8_t *)data;
    ctx->bitcount += (uint64_t)len * 8;

    if(ctx->buffer_len) {
        size_t copy = 64 - ctx->buffer_len;
        if(copy > len) {
            copy = len;
        }
        memcpy(ctx->buffer + ctx->buffer_len, bytes, copy);
        ctx->buffer_len += copy;
        bytes += copy;
        len -= copy;
        if(ctx->buffer_len == 64) {
            sha1_transform(ctx->state, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
    while(len >= 64) {
        sha1_transform(ctx->state, bytes);
        bytes += 64;
        len -= 64;
    }
    if(len) {
        memcpy(ctx->buffer + ctx->buffer_len, bytes, len);
        ctx->buffer_len += len;
    }
}

void SHA1_Final(unsigned char digest[20], SHA1_CTX *ctx) {
    uint8_t pad[64] = {0x80};
    uint8_t length[8];

    for(int i = 0; i < 8; ++i) {
        length[7 - i] = (ctx->bitcount >> (i * 8)) & 0xff;
    }

    size_t pad_len = (ctx->buffer_len < 56)
        ? (56 - ctx->buffer_len)
        : (120 - ctx->buffer_len);
    SHA1_Update(ctx, pad, pad_len);
    SHA1_Update(ctx, length, 8);

    for(int i = 0; i < 5; ++i) {
        digest[i * 4] = (ctx->state[i] >> 24) & 0xff;
        digest[i * 4 + 1] = (ctx->state[i] >> 16) & 0xff;
        digest[i * 4 + 2] = (ctx->state[i] >> 8) & 0xff;
        digest[i * 4 + 3] = ctx->state[i] & 0xff;
    }
    memset(ctx, 0, sizeof(*ctx));
}

unsigned char *SHA1(const unsigned char *data, size_t len,
                    unsigned char *digest) {
    SHA1_CTX ctx;
    SHA1_Init(&ctx);
    SHA1_Update(&ctx, data, len);
    SHA1_Final(digest, &ctx);
    return digest;
}

