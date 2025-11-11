#include <getopt.h>
#include <zmq.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>

#include "config.h"

typedef struct zmqgatectl_flags_s {
    char *config;
    char *socket;
} zmqgatectl_flags_t;

void print_usage(FILE *out) {
    fprintf(out, "Usage:\n");
    fprintf(out, "    zmqgatectl [options] command argument\n");
    fprintf(out, "\n");
    fprintf(out, "Description:\n");
    fprintf(out, "    An utility to control zmqgate behavior\n");
    fprintf(out, "\n");
    fprintf(out, "Options:\n");
    fprintf(out, "  -c,--config FILE  Configuration file name\n");
    fprintf(out, "  -s,--socket FILE  Overrides socket file name\n");
    fprintf(out, "\n");
    fprintf(out, "Commands:\n");
    fprintf(out, "  list_commands     Query command list from zmqgate\n");
    fprintf(out, "  get_statictics    Gets zmqgate statistics\n");
    fprintf(out, "  pause_websockets  Pauses forwarding messages from\n");
    fprintf(out, "                    websockets to backends (useful to\n");
    fprintf(out, "                    restart backend)\n");
    fprintf(out, "  resume_websockets Pauses forwarding messages from\n");
    fprintf(out, "                    websockets to backends (useful to\n");
    fprintf(out, "                    restart backend)\n");
    fprintf(out, "  sync_now          Synchonize connected users now\n");
    fprintf(out, "  reopen_logs       Reopens log files\n");
    fprintf(out, "\n");
}

void parse_arguments(zmqgatectl_flags_t *flags, int argc, char **argv) {
    int opt;
    while((opt = getopt(argc, argv, "hc:s:")) != -1) {
        switch(opt) {
        case 'c':
            flags->config = optarg;
            break;
        case 's':
            flags->socket = optarg;
            break;
        case 'h':
            print_usage(stdout);
            exit(0);
        default:
            print_usage(stderr);
            exit(1);
        }
    }
}


int main(int argc, char **argv) {
    zmqgatectl_flags_t flags = {NULL,NULL};
    config_main_t config;
    char *sockaddr;
    char *fakeargs[] = {"zmqgatectl", NULL};
    int rc;

    parse_arguments(&flags, argc, argv);
    coyaml_context_t *ctx = config_context(NULL, &config);
    if(!ctx) {
        fprintf(stderr, "zmqgatectl: failed to initialise configuration context\n");
        return 1;
    }
    if(flags.config) {
        ctx->root_filename = flags.config;
    }
    if(coyaml_readfile(ctx) != 0) {
        fprintf(stderr,
            "zmqgatectl: cannot read configuration (check --config and permissions)\n");
        coyaml_context_free(ctx);
        return 1;
    }
    coyaml_context_free(ctx);

    void *zmq = zmq_ctx_new();
    assert(zmq);
    void *socket = zmq_socket(zmq, ZMQ_REQ);
    if(flags.socket) {
        zmq_connect(socket, flags.socket);
    } else {
        CONFIG_ZMQADDR_LOOP(line, config.Server.control.socket.value) {
            if(line->value.kind == CONFIG_zmq_Connect) {
                zmq_bind(socket, line->value.value);  // We are other party
            } else {
                zmq_connect(socket, line->value.value);
            }
        }
    }
    if(optind >= argc) {
        print_usage(stderr);
        return 1;
    }
    for(int i = optind; i < argc; ++i) {
        zmq_msg_t msg;
        rc = zmq_msg_init_data(&msg, argv[i], strlen(argv[i]), NULL, NULL);
        if(rc != 0) {
            fprintf(stderr, "zmqgatectl: failed to send command part\n");
            zmq_msg_close(&msg);
            rc = 1;
            goto end;
        }
        int flags = (i == argc - 1) ? 0 : ZMQ_SNDMORE;
        rc = zmq_msg_send(&msg, socket, flags);
        if(rc < 0) {
            fprintf(stderr, "zmqgatectl: failed to send command to zmqgate: %s\n",
                strerror(errno));
            zmq_msg_close(&msg);
            rc = 1;
            goto end;
        }
        zmq_msg_close(&msg);
    }
    while(TRUE) {
        zmq_msg_t msg;
        zmq_msg_init(&msg);
        rc = zmq_msg_recv(&msg, socket, 0);
        if(rc < 0) {
            fprintf(stderr, "zmqgatectl: receive failed: %s\n", strerror(errno));
            zmq_msg_close(&msg);
            rc = 1;
            goto end;
        }
        int64_t more = 0;
        size_t more_size = sizeof(more);
        rc = zmq_getsockopt(socket, ZMQ_RCVMORE, &more, &more_size);
        if(rc != 0) {
            fprintf(stderr, "zmqgatectl: failed to read reply flag: %s\n",
                strerror(errno));
            zmq_msg_close(&msg);
            rc = 1;
            goto end;
        }
        printf("%.*s\n", (int)zmq_msg_size(&msg), (char *)zmq_msg_data(&msg));
        zmq_msg_close(&msg);
        if(!more) break;
    }
end:
    zmq_close(socket);
    zmq_ctx_term(zmq);
    config_free(&config);
    return rc;
}
