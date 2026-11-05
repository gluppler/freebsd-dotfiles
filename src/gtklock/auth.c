/* Native PAM on a worker thread. Passwords never enter argv, files or logs.
 * Replaces upstream's fork/pipe polling and multi-message response indexing. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pwd.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <security/pam_appl.h>
#include "auth.h"

struct nostromo_auth {
	const char *password;
	const char *username;
};

static void
wipe(void *data, size_t size)
{
	volatile unsigned char *p = data;
	while (size--)
		*p++ = 0;
}

static int
conversation(int count, const struct pam_message **messages,
		struct pam_response **response, void *context)
{
	const struct nostromo_auth *auth = context;
	struct pam_response *answers;
	int i;
	if (!response || !messages || count < 1 || count > PAM_MAX_NUM_MSG)
		return PAM_CONV_ERR;
	*response = NULL;
	answers = calloc((size_t)count, sizeof(*answers));
	if (!answers)
		return PAM_BUF_ERR;
	for (i = 0; i < count; i++) {
		if (!messages[i])
			goto failed;
		switch (messages[i]->msg_style) {
		case PAM_PROMPT_ECHO_OFF:
			answers[i].resp = strdup(auth->password);
			if (!answers[i].resp) goto failed;
			break;
		case PAM_PROMPT_ECHO_ON:
			answers[i].resp = strdup(auth->username);
			if (!answers[i].resp) goto failed;
			break;
		case PAM_ERROR_MSG:
		case PAM_TEXT_INFO:
			/* Never render arbitrary authentication-stack markup/messages. */
			break;
		default:
			goto failed;
		}
	}
	*response = answers;
	return PAM_SUCCESS;
failed:
	for (i = 0; i < count; i++) {
		if (answers[i].resp) {
			wipe(answers[i].resp, strlen(answers[i].resp));
			free(answers[i].resp);
		}
	}
	free(answers);
	return PAM_CONV_ERR;
}

char *auth_get_error(void) { return NULL; }
char *auth_get_message(void) { return NULL; }

enum pwcheck
auth_pw_check(const char *password)
{
	struct passwd entry, *result = NULL;
	char buffer[16384];
	pam_handle_t *handle = NULL;
	int status, ended;
	struct nostromo_auth auth;
	struct pam_conv conv = {conversation, &auth};
	if (!password || strlen(password) > 4096 ||
	    getpwuid_r(getuid(), &entry, buffer, sizeof(buffer), &result) || !result)
		return PW_FAILURE;
	auth.password = password;
	auth.username = result->pw_name;
	status = pam_start("gtklock", auth.username, &conv, &handle);
	if (status != PAM_SUCCESS)
		return PW_FAILURE;
	status = pam_authenticate(handle, 0);
	/* unix-selfauth supplies authentication; system supplies account validity. */
	if (status == PAM_SUCCESS)
		status = pam_acct_mgmt(handle, 0);
	ended = pam_end(handle, status);
	wipe(buffer, sizeof(buffer));
	return status == PAM_SUCCESS && ended == PAM_SUCCESS ? PW_SUCCESS : PW_FAILURE;
}
