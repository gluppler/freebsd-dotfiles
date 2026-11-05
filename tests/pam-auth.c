/* No real authentication: mock PAM and exercise multi-prompt/error handling. */
#include <assert.h>
#include <stdio.h>
#include "../src/gtklock/auth.c"

static int auth_result, account_result, end_result, account_calls;
static int fake_handle;
static struct pam_conv saved;

int pam_start(const char *service, const char *user, const struct pam_conv *conv,
    pam_handle_t **handle)
{
	assert(!strcmp(service, "gtklock"));
	assert(user && *user);
	saved = *conv;
	*handle = (pam_handle_t *)&fake_handle;
	return PAM_SUCCESS;
}

int pam_authenticate(pam_handle_t *handle, int flags)
{
	(void)handle; (void)flags;
	struct pam_message one = {PAM_PROMPT_ECHO_OFF, "Password"};
	struct pam_message two = {PAM_PROMPT_ECHO_ON, "User"};
	struct pam_message three = {PAM_TEXT_INFO, "Info"};
	const struct pam_message *messages[] = {&one, &two, &three};
	struct pam_response *response = NULL;
	assert(saved.conv(3, messages, &response, saved.appdata_ptr) == PAM_SUCCESS);
	assert(!strcmp(response[0].resp, "test-secret"));
	assert(response[1].resp && *response[1].resp);
	assert(!response[2].resp);
	for (int i = 0; i < 3; i++) free(response[i].resp);
	free(response);
	assert(saved.conv(0, messages, &response, saved.appdata_ptr) == PAM_CONV_ERR);
	assert(saved.conv(PAM_MAX_NUM_MSG + 1, messages, &response, saved.appdata_ptr) == PAM_CONV_ERR);
	one.msg_style = -1;
	assert(saved.conv(3, messages, &response, saved.appdata_ptr) == PAM_CONV_ERR);
	assert(response == NULL);
	return auth_result;
}

int pam_acct_mgmt(pam_handle_t *handle, int flags)
{
	(void)handle; (void)flags;
	account_calls++;
	return account_result;
}

int pam_end(pam_handle_t *handle, int status)
{
	(void)handle; (void)status;
	return end_result;
}

int main(void)
{
	assert(auth_pw_check(NULL) == PW_FAILURE);
	assert(auth_pw_check("test-secret") == PW_SUCCESS);
	assert(account_calls == 1);
	auth_result = PAM_AUTH_ERR;
	assert(auth_pw_check("test-secret") == PW_FAILURE);
	assert(account_calls == 1); /* failed passwords cannot reach account acceptance */
	auth_result = PAM_SUCCESS;
	account_result = PAM_ACCT_EXPIRED;
	assert(auth_pw_check("test-secret") == PW_FAILURE);
	account_result = PAM_SUCCESS;
	end_result = PAM_SYSTEM_ERR;
	assert(auth_pw_check("test-secret") == PW_FAILURE);
	puts("PAM conversation and failure-path checks passed");
	return 0;
}
