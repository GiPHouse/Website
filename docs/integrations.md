# GitHub App and G Suite setup

Optional integrations for repository and mailing list synchronisation. You do not need these to run the site or to log in locally; see [Development](development.md) for that.

- [Registering a GitHub App for repository synchronisation](#registering-a-github-app-for-repository-synchronisation)
- [Registering a G Suite service account for mailing list synchronisation](#registering-a-g-suite-service-account-for-mailing-list-synchronisation)

## Registering a GitHub App for repository synchronisation
To enable the synchronisation functionality of repositories and project(team)s, a GitHub App must be registered and installed in an organization. This GitHub App needs the following permissions:

- Repository/Metadata: read-only
- Repository/Administration: read and write
- Organization/Members: read and write
- User/Email addresses: read-only

We assume you already have a [GitHub organization](https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/creating-a-new-organization-from-scratch) setup.

- As an organization, you can develop a GitHub app and register this app at GitHub. People can then install that app in their own account or organization, giving your app access to that account or organization.
For this project, you will need to first [create your own GitHub app](https://developer.github.com/apps/building-github-apps/creating-a-github-app/) and then install it in your organization. 
After this, you can find a `DJANGO_GITHUB_SYNC_APP_ID`, and download the RSA, base64 encode it, and set it in `DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64`. These will be used as environment variables in this project and need to be set as GitHub Actions secrets in the repository (see [Secrets](deployment.md#secrets)). 

- After the app is created, it needs to be [installed in your own organization](https://developer.github.com/apps/installing-github-apps/) (although technically speaking, it is also possible to publish the app in the previous step and install the app in a different organization!).
On installation, you can find the `DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID` which we also need to set in this project. This installation id is hidden in the overview of installed GitHub Apps in your organization.
Additionally, you need to set the `DJANGO_GITHUB_SYNC_ORGANIZATION_NAME` to the name of the organization the app is installed in.

## Registering a G Suite service account for mailing list synchronisation
To enable the synchronisation feature of mailing lists to G Suite, a project and service account need to be setup.

- Create a project in the [google cloud console](https://console.cloud.google.com).
- Create a [service account and credentials](https://developers.google.com/admin-sdk/directory/v1/guides/delegation#create_the_service_account_and_credentials).
- Enable [domain wide delegation of authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation#delegate_domain-wide_authority_to_your_service_account), with the scopes:
  - `https://www.googleapis.com/auth/admin.directory.group` (for accessing groups and adding or deleting members)
  - `https://www.googleapis.com/auth/apps.groups.settings` (for changing settings of groups and adding aliases)
- If this is the first time using the Groups Settings API, [enable it for the project](https://developers.google.com/apps-script/guides/services/advanced#enabling_advanced_services).

The credentials and admin user can then be setup in Github secrets. The email of the G Suite user used to manage to the G Suite domain has to be stored in the Github secret `DJANGO_GSUITE_ADMIN_USER`. The credentials json file has to be `base64` encoded and stored in the Github secret `DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64` (you can use the linux command `base64` for encoding the json file).
