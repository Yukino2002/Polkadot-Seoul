//! [`PostmanClient`](struct.PostmanClient.html) is the main entry point for this library.
//!
//! Library created with [`libninja`](https://www.libninja.com).
#![allow(non_camel_case_types)]
#![allow(unused)]
pub mod model;
pub mod request;
use crate::model::*;

pub struct PostmanClient {
    pub(crate) client: httpclient::Client,
    authentication: PostmanAuthentication,
}
impl PostmanClient {
    pub fn from_env() -> Self {
        let url = "https://api.getpostman.com".to_string();
        Self {
            client: httpclient::Client::new(Some(url)),
            authentication: PostmanAuthentication::from_env(),
        }
    }
}
impl PostmanClient {
    pub fn new(url: &str, authentication: PostmanAuthentication) -> Self {
        let client = httpclient::Client::new(Some(url.to_string()));
        Self { client, authentication }
    }
    pub fn with_authentication(mut self, authentication: PostmanAuthentication) -> Self {
        self.authentication = authentication;
        self
    }
    pub fn authenticate<'a>(
        &self,
        mut r: httpclient::RequestBuilder<'a>,
    ) -> httpclient::RequestBuilder<'a> {
        match &self.authentication {
            PostmanAuthentication::PostmanApiKey { postman_api_key } => {
                r = r.header("x-api-key", postman_api_key);
            }
        }
        r
    }
    pub fn with_middleware<M: httpclient::Middleware + 'static>(
        mut self,
        middleware: M,
    ) -> Self {
        self.client = self.client.with_middleware(middleware);
        self
    }
    /**Get all APIs

Gets information about all APIs.*/
    pub fn get_all_apis(&self) -> request::GetAllApisRequest {
        request::GetAllApisRequest {
            http_client: &self,
            workspace: None,
            since: None,
            until: None,
            created_by: None,
            updated_by: None,
            is_public: None,
            name: None,
            summary: None,
            description: None,
            sort: None,
            direction: None,
        }
    }
    /**Create an API

Creates an API.*/
    pub fn create_api(&self) -> request::CreateApiRequest {
        request::CreateApiRequest {
            http_client: &self,
            workspace_id: None,
            api: None,
        }
    }
    /**Get an API

Gets information about an API.*/
    pub fn single_api(&self, api_id: &str) -> request::SingleApiRequest {
        request::SingleApiRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
        }
    }
    /**Update an API

Updates an API.*/
    pub fn update_an_api(&self, api_id: &str) -> request::UpdateAnApiRequest {
        request::UpdateAnApiRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api: None,
        }
    }
    /**Delete an API

Deletes an API.*/
    pub fn delete_an_api(&self, api_id: &str) -> request::DeleteAnApiRequest {
        request::DeleteAnApiRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
        }
    }
    /**Get all API versions

Gets information about an API's versions.*/
    pub fn get_all_api_versions(
        &self,
        api_id: &str,
    ) -> request::GetAllApiVersionsRequest {
        request::GetAllApiVersionsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
        }
    }
    /**Create an API version

Creates a new API version.*/
    pub fn create_api_version(&self, api_id: &str) -> request::CreateApiVersionRequest {
        request::CreateApiVersionRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            version: None,
        }
    }
    /**Get an API version

Gets information about an API version.*/
    pub fn get_an_api_version(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetAnApiVersionRequest {
        request::GetAnApiVersionRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Update an API version

Updates an API version.*/
    pub fn update_an_api_version(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::UpdateAnApiVersionRequest {
        request::UpdateAnApiVersionRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
            version: None,
        }
    }
    /**Delete an API version

Deletes an API version.*/
    pub fn delete_an_api_version(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::DeleteAnApiVersionRequest {
        request::DeleteAnApiVersionRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get contract test relations

This endpoint is **deprecated**. Use the `/apis/{apiId}/versions/{apiVersionId}/test` endpoint.*/
    pub fn get_contract_test_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetContractTestRelationsRequest {
        request::GetContractTestRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get documentation relations

Gets an API version's documentation relations.*/
    pub fn get_documentation_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetDocumentationRelationsRequest {
        request::GetDocumentationRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get environment relations

Gets an API version's environment relations.*/
    pub fn get_environment_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetEnvironmentRelationsRequest {
        request::GetEnvironmentRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get integration test relations

This endpoint is **deprecated**. Use the `/apis/{apiId}/versions/{apiVersionId}/test` endpoint.*/
    pub fn get_integration_test_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetIntegrationTestRelationsRequest {
        request::GetIntegrationTestRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get mock server relations

Gets an API version's mock server relations.*/
    pub fn get_mock_server_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetMockServerRelationsRequest {
        request::GetMockServerRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get monitor relations

Gets an API version's monitor relations.*/
    pub fn get_monitor_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetMonitorRelationsRequest {
        request::GetMonitorRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get all linked relations

Gets all of an API version's relations.*/
    pub fn get_linked_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetLinkedRelationsRequest {
        request::GetLinkedRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Create relations

Creates a new relation for an API version. This endpoint accepts multiple relation arrays in a single call.*/
    pub fn create_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::CreateRelationsRequest {
        request::CreateRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
            documentation: None,
            environment: None,
            mock: None,
            monitor: None,
            test: None,
            contracttest: None,
            testsuite: None,
        }
    }
    /**Create a schema

Creates an API definition.*/
    pub fn create_schema(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::CreateSchemaRequest {
        request::CreateSchemaRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
            schema: None,
        }
    }
    /**Get a schema

Gets information about an API's definition.*/
    pub fn get_schema(
        &self,
        api_id: &str,
        api_version_id: &str,
        schema_id: &str,
    ) -> request::GetSchemaRequest {
        request::GetSchemaRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
            schema_id: schema_id.to_owned(),
        }
    }
    /**Update a schema

Updates an API definition.*/
    pub fn update_schema(
        &self,
        api_id: &str,
        api_version_id: &str,
        schema_id: &str,
    ) -> request::UpdateSchemaRequest {
        request::UpdateSchemaRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
            schema_id: schema_id.to_owned(),
            schema: None,
        }
    }
    /**Create collection from a schema

Creates a collection and links it to an API as one or multiple relations.*/
    pub fn create_collection_from_schema(
        &self,
        args: request::CreateCollectionFromSchemaRequired,
    ) -> request::CreateCollectionFromSchemaRequest {
        request::CreateCollectionFromSchemaRequest {
            http_client: &self,
            api_id: args.api_id.to_owned(),
            api_version_id: args.api_version_id.to_owned(),
            schema_id: args.schema_id.to_owned(),
            workspace_id: None,
            name: args.name.to_owned(),
            relations: args.relations,
        }
    }
    /**Get all test relations

Gets all of an API version's test relations.*/
    pub fn get_test_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetTestRelationsRequest {
        request::GetTestRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Get test suite relations

This endpoint is **deprecated**. Use the `/apis/{apiId}/versions/{apiVersionId}/test` endpoint.*/
    pub fn get_test_suite_relations(
        &self,
        api_id: &str,
        api_version_id: &str,
    ) -> request::GetTestSuiteRelationsRequest {
        request::GetTestSuiteRelationsRequest {
            http_client: &self,
            api_id: api_id.to_owned(),
            api_version_id: api_version_id.to_owned(),
        }
    }
    /**Sync API relations with definition

Syncs an API version's relation with the API's definition.*/
    pub fn sync_relations_with_schema(
        &self,
        args: request::SyncRelationsWithSchemaRequired,
    ) -> request::SyncRelationsWithSchemaRequest {
        request::SyncRelationsWithSchemaRequest {
            http_client: &self,
            api_id: args.api_id.to_owned(),
            api_version_id: args.api_version_id.to_owned(),
            relation_type: args.relation_type.to_owned(),
            entity_id: args.entity_id.to_owned(),
        }
    }
    /**Get all collections

Gets all of your [collections](https://www.getpostman.com/docs/collections). The response includes all of your subscribed collections.*/
    pub fn all_collections(&self) -> request::AllCollectionsRequest {
        request::AllCollectionsRequest {
            http_client: &self,
            workspace_id: None,
        }
    }
    /**Create a collection

Creates a collection using the [Postman Collection v2 schema format](https://schema.postman.com/json/collection/v2.1.0/docs/index.html).

**Note:**

- For a complete list of available property values for this endpoint, use the following references available in the [collection.json schema file](https://schema.postman.com/json/collection/v2.1.0/collection.json):
  - `info` object — Use the `definitions.info` entry.
  - `item` object — Use the `definitions.items` entry.
- For all other possible values, refer to the [collection.json schema file](https://schema.postman.com/json/collection/v2.1.0/collection.json).
*/
    pub fn create_collection(&self) -> request::CreateCollectionRequest {
        request::CreateCollectionRequest {
            http_client: &self,
            workspace_id: None,
            collection: None,
        }
    }
    /**Create a fork

Creates a [fork](https://learning.postman.com/docs/collaborating-in-postman/version-control/#creating-a-fork) from an existing collection into a workspace.*/
    pub fn create_a_fork(
        &self,
        workspace: &str,
        collection_uid: &str,
    ) -> request::CreateAForkRequest {
        request::CreateAForkRequest {
            http_client: &self,
            workspace: workspace.to_owned(),
            collection_uid: collection_uid.to_owned(),
            label: None,
        }
    }
    /**Merge a fork

Merges a forked collection back into its destination collection.*/
    pub fn merge_a_fork(&self) -> request::MergeAForkRequest {
        request::MergeAForkRequest {
            http_client: &self,
            destination: None,
            source: None,
            strategy: None,
        }
    }
    /**Get a collection

Gets information about a collection. For a complete list of this endpoint's possible values, use the [collection.json schema file](https://schema.postman.com/json/collection/v2.1.0/collection.json).*/
    pub fn single_collection(
        &self,
        collection_uid: &str,
    ) -> request::SingleCollectionRequest {
        request::SingleCollectionRequest {
            http_client: &self,
            collection_uid: collection_uid.to_owned(),
        }
    }
    /**Update a collection

Updates a collection using the [Postman Collection v2 schema format](https://schema.postman.com/json/collection/v2.1.0/docs/index.html).

> Use caution when using this endpoint. The system will **replace** the existing collection with the values passed in the request body.

**Note:**

- For a complete list of available property values for this endpoint, use the following references available in the [collection.json schema file](https://schema.postman.com/json/collection/v2.1.0/collection.json):
  - `info` object — Use the `definitions.info` entry.
  - `item` object — Use the `definitions.items` entry.
- For all other possible values, refer to the [collection.json schema file](https://schema.postman.com/json/collection/v2.1.0/collection.json).
*/
    pub fn update_collection(
        &self,
        collection_uid: &str,
    ) -> request::UpdateCollectionRequest {
        request::UpdateCollectionRequest {
            http_client: &self,
            collection_uid: collection_uid.to_owned(),
            collection: None,
        }
    }
    /**Delete a collection

Deletes a collection.*/
    pub fn delete_collection(
        &self,
        collection_uid: &str,
    ) -> request::DeleteCollectionRequest {
        request::DeleteCollectionRequest {
            http_client: &self,
            collection_uid: collection_uid.to_owned(),
        }
    }
    /**Get all environments

Gets information about all of your [environments](https://learning.postman.com/docs/sending-requests/managing-environments/).*/
    pub fn all_environments(&self) -> request::AllEnvironmentsRequest {
        request::AllEnvironmentsRequest {
            http_client: &self,
            workspace_id: None,
        }
    }
    /**Create an environment

Creates an environment.*/
    pub fn create_environment(&self) -> request::CreateEnvironmentRequest {
        request::CreateEnvironmentRequest {
            http_client: &self,
            workspace_id: None,
            environment: None,
        }
    }
    /**Get an environment

Gets information about an environment.*/
    pub fn single_environment(
        &self,
        environment_uid: &str,
    ) -> request::SingleEnvironmentRequest {
        request::SingleEnvironmentRequest {
            http_client: &self,
            environment_uid: environment_uid.to_owned(),
        }
    }
    /**Update an environment

Updates an environment.*/
    pub fn update_environment(
        &self,
        environment_uid: &str,
    ) -> request::UpdateEnvironmentRequest {
        request::UpdateEnvironmentRequest {
            http_client: &self,
            environment_uid: environment_uid.to_owned(),
            environment: None,
        }
    }
    /**Delete an environment

Deletes an environment.*/
    pub fn delete_environment(
        &self,
        environment_uid: &str,
    ) -> request::DeleteEnvironmentRequest {
        request::DeleteEnvironmentRequest {
            http_client: &self,
            environment_uid: environment_uid.to_owned(),
        }
    }
    /**Import an exported Postman data dump file

**This endpoint is deprecated.**

Imports exported Postman data. This endpoint only accepts [export data dump files](https://postman.postman.co/me/export).

For more information, read our [Exporting data dumps](https://learning.postman.com/docs/getting-started/importing-and-exporting-data/#exporting-data-dumps) documentation.
*/
    pub fn import_exported_data(&self) -> request::ImportExportedDataRequest {
        request::ImportExportedDataRequest {
            http_client: &self,
        }
    }
    /**Import an OpenAPI definition

Imports an OpenAPI definition into Postman as a new [Postman Collection](https://learning.postman.com/docs/getting-started/creating-the-first-collection/).*/
    pub fn import_external_api_specification(
        &self,
        body: serde_json::Value,
    ) -> request::ImportExternalApiSpecificationRequest {
        request::ImportExternalApiSpecificationRequest {
            http_client: &self,
            workspace_id: None,
            body,
        }
    }
    /**Get authenticated user

Gets information about the authenticated user.*/
    pub fn api_key_owner(&self) -> request::ApiKeyOwnerRequest {
        request::ApiKeyOwnerRequest {
            http_client: &self,
        }
    }
    /**Get all mock servers

Gets all mock servers.*/
    pub fn all_mocks(&self) -> request::AllMocksRequest {
        request::AllMocksRequest {
            http_client: &self,
        }
    }
    /**Create a mock server

Creates a mock server in a collection.*/
    pub fn create_mock(&self) -> request::CreateMockRequest {
        request::CreateMockRequest {
            http_client: &self,
            workspace_id: None,
            mock: None,
        }
    }
    /**Get a mock server

Gets information about a mock server.*/
    pub fn single_mock(&self, mock_uid: &str) -> request::SingleMockRequest {
        request::SingleMockRequest {
            http_client: &self,
            mock_uid: mock_uid.to_owned(),
        }
    }
    /**Update a mock server

Updates a mock server.*/
    pub fn update_mock(&self, mock_uid: &str) -> request::UpdateMockRequest {
        request::UpdateMockRequest {
            http_client: &self,
            mock_uid: mock_uid.to_owned(),
            mock: None,
        }
    }
    /**Delete a mock server

Deletes a mock server.*/
    pub fn delete_mock(&self, mock_uid: &str) -> request::DeleteMockRequest {
        request::DeleteMockRequest {
            http_client: &self,
            mock_uid: mock_uid.to_owned(),
        }
    }
    /**Publish a mock server

Publishes a mock server. Publishing a mock server sets its **Access Control** configuration setting to public.*/
    pub fn publish_mock(&self, mock_uid: &str) -> request::PublishMockRequest {
        request::PublishMockRequest {
            http_client: &self,
            mock_uid: mock_uid.to_owned(),
        }
    }
    /**Unpublish a mock server

Unpublishes a mock server. Unpublishing a mock server sets its **Access Control** configuration setting to private.*/
    pub fn unpublish_mock(&self, mock_uid: &str) -> request::UnpublishMockRequest {
        request::UnpublishMockRequest {
            http_client: &self,
            mock_uid: mock_uid.to_owned(),
        }
    }
    /**Get all monitors

Gets all monitors.*/
    pub fn all_monitors(&self) -> request::AllMonitorsRequest {
        request::AllMonitorsRequest {
            http_client: &self,
        }
    }
    /**Create a monitor

Creates a monitor.*/
    pub fn create_monitor(&self) -> request::CreateMonitorRequest {
        request::CreateMonitorRequest {
            http_client: &self,
            workspace_id: None,
            monitor: None,
        }
    }
    /**Get a monitor

Gets information about a monitor.*/
    pub fn single_monitor(&self, monitor_uid: &str) -> request::SingleMonitorRequest {
        request::SingleMonitorRequest {
            http_client: &self,
            monitor_uid: monitor_uid.to_owned(),
        }
    }
    /**Update a monitor

Updates a monitor.*/
    pub fn update_monitor(&self, monitor_uid: &str) -> request::UpdateMonitorRequest {
        request::UpdateMonitorRequest {
            http_client: &self,
            monitor_uid: monitor_uid.to_owned(),
            monitor: None,
        }
    }
    /**Delete a monitor

Deletes a monitor.*/
    pub fn delete_monitor(&self, monitor_uid: &str) -> request::DeleteMonitorRequest {
        request::DeleteMonitorRequest {
            http_client: &self,
            monitor_uid: monitor_uid.to_owned(),
        }
    }
    /**Run a monitor

Runs a monitor and returns its run results.*/
    pub fn run_a_monitor(&self, monitor_uid: &str) -> request::RunAMonitorRequest {
        request::RunAMonitorRequest {
            http_client: &self,
            monitor_uid: monitor_uid.to_owned(),
        }
    }
    /**Get resource types

Gets all the resource types supported by Postman's SCIM API.*/
    pub fn get_resource_types(&self) -> request::GetResourceTypesRequest {
        request::GetResourceTypesRequest {
            http_client: &self,
        }
    }
    /**Get service provider configuration

Gets the Postman SCIM API configuration information. This includes a list of supported operations.*/
    pub fn service_provider_config(&self) -> request::ServiceProviderConfigRequest {
        request::ServiceProviderConfigRequest {
            http_client: &self,
        }
    }
    /**Get all user resources

Gets information about all Postman team members.*/
    pub fn fetch_all_user_resource(&self) -> request::FetchAllUserResourceRequest {
        request::FetchAllUserResourceRequest {
            http_client: &self,
            start_index: None,
            count: None,
            filter: None,
        }
    }
    /**Create a user

Creates a new user account in Postman and adds the user to your organization's Postman team. If the account does not already exist, this also activates the user so they can authenticate in to your Postman team.

If the account already exists, the system sends the user an [email invite](https://learning.postman.com/docs/administration/managing-your-team/managing-your-team/#inviting-users) to join the Postman team. The user joins the team once they accept the invite.

By default, the system assigns new users the developer role. You can [update user roles in Postman](https://learning.postman.com/docs/administration/managing-your-team/managing-your-team/#managing-team-roles).
*/
    pub fn create_user(&self) -> request::CreateUserRequest {
        request::CreateUserRequest {
            http_client: &self,
            schemas: None,
            user_name: None,
            active: None,
            external_id: None,
            groups: None,
            locale: None,
            name: None,
        }
    }
    /**Get user resource

Gets information about a Postman team member.*/
    pub fn fetch_user_resource(
        &self,
        user_id: &str,
    ) -> request::FetchUserResourceRequest {
        request::FetchUserResourceRequest {
            http_client: &self,
            user_id: user_id.to_owned(),
        }
    }
    /**Update a user

Updates a user's first and last name in Postman.

**Note:**

You can only use the SCIM API to update a user's first and last name. You cannot update any other user attributes with the API.
*/
    pub fn update_user_information(
        &self,
        user_id: &str,
    ) -> request::UpdateUserInformationRequest {
        request::UpdateUserInformationRequest {
            http_client: &self,
            user_id: user_id.to_owned(),
            schemas: None,
            name: None,
        }
    }
    /**Update a user's state

Updates a user's active state in Postman.

### Reactivating users

By setting the `active` property from `false` to `true`, this reactivates an account. This allows the account to authenticate in to Postman and adds the account back on to your Postman team.
*/
    pub fn update_user_state(&self, user_id: &str) -> request::UpdateUserStateRequest {
        request::UpdateUserStateRequest {
            http_client: &self,
            user_id: user_id.to_owned(),
            schemas: None,
            operations: None,
        }
    }
    /**Schema security validation

Performs a security analysis on the given definition and returns any issues. This can help you understand their impact and provides solutions to help you resolve the errors. You can include this endpoint to your CI/CD process to automate schema validation.

For more information, read our [API definition warnings](https://learning.postman-beta.com/docs/api-governance/api-definition/api-definition-warnings/) documentation.

**Note:**

The maximum allowed size of the definition is 10 MB.
*/
    pub fn schema_security_validation(
        &self,
    ) -> request::SchemaSecurityValidationRequest {
        request::SchemaSecurityValidationRequest {
            http_client: &self,
            schema: None,
        }
    }
    /**Create a webhook

Creates a webhook that triggers a collection with a custom payload. You can get the webhook's URL from the `webhookUrl` property in the endpoint's response.*/
    pub fn create_webhook(&self) -> request::CreateWebhookRequest {
        request::CreateWebhookRequest {
            http_client: &self,
            workspace_id: None,
            webhook: None,
        }
    }
    /**Get all workspaces

Gets all [workspaces](https://learning.postman.com/docs/collaborating-in-postman/using-workspaces/creating-workspaces/). The response includes your workspaces and any workspaces that you have access to.

**Note:**

This endpoint's response contains the visibility field. Visibility determines who can access the workspace:

- `only-me` — Applies to the **My Workspace** workspace.
- `personal` — Only you can access the workspace.
- `team` — All team members can access the workspace.
- `private-team` — Only invited team members can access the workspace.
- `public` — Everyone can access the workspace.
*/
    pub fn all_workspaces(&self) -> request::AllWorkspacesRequest {
        request::AllWorkspacesRequest {
            http_client: &self,
            type_: None,
        }
    }
    /**Create a workspace

Creates a new [workspace](https://learning.postman.com/docs/collaborating-in-postman/using-workspaces/creating-workspaces/).

### Important:

We **deprecated** linking collections or environments between workspaces. We do **not** recommend that you do this.

If you have a linked collection or environment, note the following:

- The endpoint does **not** create a clone of a collection or environment.
- Any changes you make to a linked collection or environment changes them in **all** workspaces.
- If you delete a collection or environment linked between workspaces, the system deletes it in **all** the workspaces.
*/
    pub fn create_workspace(&self) -> request::CreateWorkspaceRequest {
        request::CreateWorkspaceRequest {
            http_client: &self,
            workspace: None,
        }
    }
    /**Get a workspace

Gets information about a workspace.

**Note:**

This endpoint's response contains the `visibility` field. [Visibility](https://learning.postman.com/docs/collaborating-in-postman/using-workspaces/managing-workspaces/#changing-workspace-visibility) determines who can access the workspace:

- `only-me` — Applies to the **My Workspace** workspace.
- `personal` — Only you can access the workspace.
- `team` — All team members can access the workspace.
- `private-team` — Only invited team members can access the workspace.
- `public` — Everyone can access the workspace.
*/
    pub fn single_workspace(
        &self,
        workspace_id: &str,
    ) -> request::SingleWorkspaceRequest {
        request::SingleWorkspaceRequest {
            http_client: &self,
            workspace_id: workspace_id.to_owned(),
        }
    }
    /**Update a workspace

Updates a workspace.

**Note:**

You can change a workspace's type from `personal` to `team`, but you **cannot** change a workspace from `team` to `personal`.

### Important:

We **deprecated** linking collections or environments between workspaces. We do **not** recommend that you do this.

If you have a linked collection or environment, note the following:

- The endpoint does **not** create a clone of a collection or environment.
- Any changes you make to a linked collection or environment changes them in **all** workspaces.
- If you delete a collection or environment linked between workspaces, the system deletes it in **all** the workspaces.
*/
    pub fn update_workspace(
        &self,
        workspace_id: &str,
    ) -> request::UpdateWorkspaceRequest {
        request::UpdateWorkspaceRequest {
            http_client: &self,
            workspace_id: workspace_id.to_owned(),
            workspace: None,
        }
    }
    /**Delete a workspace

Deletes an existing workspace.

### Important:

If you delete a workspace that has a linked collection or environment with another workspace, this will delete the collection and environment in **all** workspaces.
*/
    pub fn delete_workspace(
        &self,
        workspace_id: &str,
    ) -> request::DeleteWorkspaceRequest {
        request::DeleteWorkspaceRequest {
            http_client: &self,
            workspace_id: workspace_id.to_owned(),
        }
    }
}
pub enum PostmanAuthentication {
    PostmanApiKey { postman_api_key: String },
}
impl PostmanAuthentication {
    pub fn from_env() -> Self {
        Self::PostmanApiKey {
            postman_api_key: std::env::var("POSTMAN_API_KEY")
                .expect("Environment variable POSTMAN_API_KEY is not set."),
        }
    }
}
