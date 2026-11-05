/* Native process CWD lookup; no procfs mount and no root privileges. */
#include <sys/types.h>
#include <sys/queue.h>
#include <sys/sysctl.h>
#include <sys/user.h>
#include <libprocstat.h>
#include <stdio.h>

static char *
nostromo_cwd(pid_t pid)
{
	struct procstat *ps;
	struct kinfo_proc *proc;
	struct filestat_list *files;
	struct filestat *file;
	unsigned int count = 0;
	char *path = NULL;

	if (pid <= 0 || !(ps = procstat_open_sysctl()))
		return NULL;
	proc = procstat_getprocs(ps, KERN_PROC_PID, pid, &count);
	if (proc && count == 1) {
		files = procstat_getfiles(ps, proc, 0);
		if (files) {
			STAILQ_FOREACH(file, files, next) {
				if ((file->fs_uflags & PS_FST_UFLAG_CDIR) &&
				    file->fs_path && file->fs_path[0] == '/') {
					path = strdup(file->fs_path);
					break;
				}
			}
			procstat_freefiles(ps, files);
		}
	}
	if (proc)
		procstat_freeprocs(ps, proc);
	procstat_close(ps);
	return path;
}

static void
nostromo_emit_cwd(const char *path)
{
	const unsigned char *p;
	if (!path || *path != '/')
		return;
	fputs("\033]2;NOSTROMO_CWD:file:///", stdout);
	for (p = (const unsigned char *)path + 1; *p; p++)
		printf("%%%02X", *p);
	fputc('\007', stdout);
	fputs("\033]7;file:///", stdout);
	for (p = (const unsigned char *)path + 1; *p; p++)
		printf("%%%02X", *p);
	fputc('\007', stdout);
	fflush(stdout);
}
