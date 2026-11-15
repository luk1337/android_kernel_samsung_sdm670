/* fwatch DIR... : print every file opened/created under the given dirs (one level each) */
#include <stdio.h>
#include <sys/inotify.h>
#include <unistd.h>
#include <time.h>

int main(int argc, char **argv)
{
	char buf[8192] __attribute__((aligned(8)));
	const char *dirs[256];
	int fd = inotify_init(), i;

	for (i = 1; i < argc && i < 256; i++) {
		int wd = inotify_add_watch(fd, argv[i], IN_OPEN | IN_CREATE | IN_MODIFY);
		if (wd >= 0 && wd < 256)
			dirs[wd] = argv[i];
		else
			fprintf(stderr, "watch failed: %s\n", argv[i]);
	}
	setvbuf(stdout, NULL, _IOLBF, 0);
	for (;;) {
		ssize_t n = read(fd, buf, sizeof(buf));
		char *p;
		struct timespec ts;

		if (n <= 0)
			return 1;
		clock_gettime(CLOCK_BOOTTIME, &ts);
		for (p = buf; p < buf + n;) {
			struct inotify_event *e = (struct inotify_event *)p;

			printf("[%5ld.%03ld] %s %s/%s\n", ts.tv_sec, ts.tv_nsec / 1000000,
			       e->mask & IN_CREATE ? "CREATE" : e->mask & IN_MODIFY ? "MODIFY" : "OPEN",
			       e->wd < 256 ? dirs[e->wd] : "?", e->len ? e->name : "");
			p += sizeof(*e) + e->len;
		}
	}
}
