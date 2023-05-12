import boto3

import botocore


class AWSAPITalker:
    """Communicate with AWS API using boto3."""

    def __init__(self):
        """
        Initialize in order to communicate with the AWS API.

        First, initializes the boto3 clients which communicate with AWS.
        Second, sets the maximum amount of elements to fit on one page of an AWS response.
        """
        self.iam_client = boto3.client("iam")
        self.org_client = boto3.client("organizations")
        self.sts_client = boto3.client("sts")

        self.max_results = 20

    def create_organization(self, feature_set: str) -> dict:
        """
        Create an AWS organization.

        :param feature_set: enabled features in the organization (either 'ALL' or 'CONSOLIDATED BILLING').
        :return: dictionary containing information about the organization.
        """
        return self.org_client.create_organization(FeatureSet=feature_set)

    def create_organizational_unit(self, parent_id: str, ou_name: str, tags: list[dict] = []) -> dict:
        """
        Create an organizational unit.

        :param parent_id: the root/OU below which where the new OU will be created.
        :param ou_name: the name of the new OU.
        :param tags: tags (list of dictionaries containing the keys 'Key' and 'Value') to be attached to the account.
        :return: dictionary containing information about the organizational unit.
        """
        return self.org_client.create_organizational_unit(ParentId=parent_id, Name=ou_name, Tags=tags)

    def attach_policy(self, target_id: str, policy_id: str):
        """
        Attach the specified policy to the specified target.

        :param target_id: ID of the target to which the policy should be attached.
        :param policy_id: ID of the policy to attach.
        """
        self.org_client.attach_policy(TargetId=target_id, PolicyId=policy_id)

    def get_caller_identity(self) -> dict:
        """Get the identity of the caller of the API actions."""
        return self.sts_client.get_caller_identity()

    def simulate_principal_policy(self, policy_source_arn: str, action_names: list[str]) -> dict:
        """
        Determine the effective permissions of the policies of an IAM entity by simulating API actions.

        :param policy_source: ARN of the IAM entity.
        :param action_names: list of AWS API actions to simulate.
        :return: dictionary containing information about the simulation's outcome.
        """
        return self.iam_client.simulate_principal_policy(PolicySourceArn=policy_source_arn, ActionNames=action_names)

    def describe_organization(self) -> dict:
        """Describe the AWS organization."""
        return self.org_client.describe_organization()

    def describe_policy(self, policy_id: str) -> dict:
        """Describe the policy with the specified ID."""
        return self.org_client.describe_policy(PolicyId=policy_id)

    def create_account(self, email: str, account_name: str, tags: list[dict] = []) -> dict:
        """
        Move an AWS account in the organization.

        :param email: email address of the account.
        :param account_name: name of the account.
        :param tags: tags (list of dictionaries containing the keys 'Key' and 'Value') to be attached to the account.
        :return: dictionary containing information about the account creation status.
        """
        return self.org_client.create_account(
            Email=email, AccountName=account_name, IamUserAccessToBilling="DENY", Tags=tags
        )

    def move_account(self, account_id: str, source_parent_id: str, dest_parent_id: str):
        """
        Move an AWS account in the organization.

        :param account_id: ID of the account.
        :param source_parent_id: ID of the root/OU containing the account.
        :param dest_parent_id: ID of the root/OU which the account should be moved to.
        """
        self.org_client.move_account(
            AccountId=account_id, SourceParentId=source_parent_id, DestinationParentId=dest_parent_id
        )

    def combine_pages(self, page_iterator: botocore.paginate.PageIterator, key: str) -> list[dict]:
        """
        Combine the information on each page of an AWS API response into a list.

        This function is only used for AWS API operations which can return multiple pages as a response.

        :param page_iterator: boto3 feature which iterates over all pages.
        :param key: the key corresponding to the list of values to be retrieved from each page.
        :return: a list that combines the values from all pages.
        """
        list = []

        for page in page_iterator:
            list = list + page[key]

        return list

    def list_organizational_units_for_parent(self, parent_id: str) -> list[dict]:
        """
        List all organizational units below the specified parent.

        :param parent_id: ID of the parent.
        :return: list of dictionaries containing organizational unit information.
        """
        paginator = self.org_client.get_paginator("list_organizational_units_for_parent")
        page_iterator = paginator.paginate(ParentId=parent_id, MaxResults=self.max_results)

        return self.combine_pages(page_iterator, "OrganizationalUnits")

    def list_accounts_for_parent(self, parent_id: str) -> list[dict]:
        """
        List all accounts below the specified parent.

        :param parent_id: ID of the parent.
        :return: list of dictionaries containing account information
        """
        paginator = self.org_client.get_paginator("list_accounts_for_parent")
        page_iterator = paginator.paginate(ParentId=parent_id, MaxResults=self.max_results)

        return self.combine_pages(page_iterator, "Accounts")

    def list_tags_for_resource(self, resource_id: str) -> list[dict]:
        """
        List all tags belonging to the specified resource.

        :param resource_id: ID of the resource.
        :return: list of dictionaries containing tag information
        """
        paginator = self.org_client.get_paginator("list_tags_for_resource")
        page_iterator = paginator.paginate(
            ResourceId=resource_id,
        )

        return self.combine_pages(page_iterator, "Tags")

    def list_roots(self) -> list[dict]:
        """
        List all roots in the organization.

        :return: list of dictionaries containing root information.
        """
        paginator = self.org_client.get_paginator("list_roots")
        page_iterator = paginator.paginate()

        return self.combine_pages(page_iterator, "Roots")

    def describe_create_account_status(self, create_account_request_id: str) -> dict:
        """
        Describe the status of the given account creation request.

        :return: dictionary containing account creation status information
        """
        return self.org_client.describe_create_account_status(CreateAccountRequestId=create_account_request_id)
