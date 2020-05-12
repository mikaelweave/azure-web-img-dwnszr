import os, pytest, random
from subprocess import Popen, PIPE
from dotenv import find_dotenv, load_dotenv

from src.Settings import Settings


def execute_process_report_error(command, ignore_error=False):
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print('ERROR in execute_process_report_error')
        print(f'Command: {command}')
        print(f'Output: {stdout.decode("utf-8").rstrip()}')
        print(f'Error: {stderr.decode("utf-8").rstrip()}')
        if ignore_error:
            print('Ignoring error encountered while executing')
        else:
            raise 'Error executing command. Exiting.'

    return stdout.decode("utf-8").rstrip()


@pytest.fixture(scope='session')
def settings():
    '''Create azure resources and deploy function for e2e test'''
    print('Starting creation of infra for E2E testing...')

    # Load settingr from environment
    load_dotenv(find_dotenv())
    rand = random.randint(1, 999999)

    resource_group_name = os.getenv('RESOURCE_GROUP_NAME', f'AzureImageSizerE2E{rand}')
    location = os.getenv('LOCATION', 'westus2')
    storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME', f'aise2e{rand}')
    function_app_name = os.getenv('FUNCTION_APP_NAME', f'aise2e{rand}')

    print(f'Executing e2e test on resource group {resource_group_name} at location {location} with storage account {storage_account_name} and function app {function_app_name}')

    # Create resource group if it doesn't exist
    execute_process_report_error(f'az group create --name {resource_group_name} --location {location}')

    # Create storage account if it doesn't exist
    execute_process_report_error(f'az storage account create --resource-group {resource_group_name} --name {storage_account_name} --location {location}')
    storage_connection_string = execute_process_report_error(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource_group_name} --output tsv')

    # Creating settings object
    settings = Settings({
        'StorageAccountConnectionString': storage_connection_string,
        'ImageSizes': '480,768,1200,1400,1700,2000,2436',
        'ImageContainerName': f'image{rand}',
        'MetadataContainerName': f'metadata{rand}'
    })

    # Create storage containers
    execute_process_report_error(f'az storage container create --account-name {storage_account_name} --name {settings.image_container_name}')
    execute_process_report_error(f'az storage container create --account-name {storage_account_name} --name {settings.metadata_container_name}')

    # Create Azure function
    execute_process_report_error(f'az functionapp create --resource-group {resource_group_name} --consumption-plan-location {location} --runtime python --runtime-version 3.8 --functions-version 3 --name {function_app_name} --storage-account {storage_account_name} --os-type linux --disable-app-insights true')

    # Deployment slots currently do not support Linux functions
    # Switch to slots once this is supported https://feedback.azure.com/forums/355860-azure-functions/suggestions/38891209-slots-for-linux-consumption-plan
    # execute_process_report_error(f'az functionapp deployment slot create --name {function_app_name} --slot {data.function_app_slot}')

    # Build package to test
    execute_process_report_error(f'mkdir -p .tmp/azure-web-img-dwnszr{rand};cp -r host.json local.settings.json .tmp/;pip install  --target=".tmp/.python_packages/lib/site-packages"  -r requirements.txt;cp -r src/* .tmp/azure-web-img-dwnszr{rand}/;cd .tmp; zip -r ../azure-web-img-dwnszr{rand}.zip .*; cd ..;rm -rf .tmp/azure-web-img-dwnszr{rand};')

    # Create function app deployment from local zip
    execute_process_report_error(f'az functionapp deployment source config-zip --name {function_app_name} --resource-group {resource_group_name} --src azure-web-img-dwnszr{rand}.zip', True)

    # Set function settings
    execute_process_report_error(f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group_name} --settings "ImageSizes={",".join(map(str, settings.image_sizes))}"')
    execute_process_report_error(f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group_name} --settings "StorageAccountConnectionString={settings.storage_connection_string}"')
    execute_process_report_error(f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group_name} --settings "ImageContainerName={settings.image_container_name}"')
    execute_process_report_error(f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group_name} --settings "MetadataContainerName={settings.metadata_container_name}"')

    # Create event trigger on image blob
    function_app_id = execute_process_report_error(f'az functionapp show --name {function_app_name} --resource-group {resource_group_name} --output tsv --query "id"')
    function_id = f'{function_app_id}/functions/azure-web-img-dwnszr'
    storage_account_id = execute_process_report_error(f'az storage account show --name {storage_account_name} --resource-group {resource_group_name} --output tsv --query "id"')
    execute_process_report_error(f'az eventgrid event-subscription create --name e2etest{rand} --source-resource-id {storage_account_id} --endpoint-type azurefunction --endpoint {function_id} --included-event-types "Microsoft.Storage.BlobCreated" --advanced-filter subject StringContains "{settings.image_container_name}"')

    # Tests will run here, passing settings to test cases (data)
    print("E2E testing infra created!")
    yield settings
    print("Starting destruction of infra for E2E testing...")

    # Delete event trigger
    execute_process_report_error(f'az eventgrid event-subscription delete --name e2etest{rand} --source-resource-id {storage_account_id}')

    # Delete function app (if not provided by env)
    if 'FUNCTION_APP_NAME' not in os.environ:
        execute_process_report_error(f'az functionapp delete --resource-group {resource_group_name} --name {function_app_name}')

    # Delete containers
    execute_process_report_error(f'az storage container delete --account-name {storage_account_name} --name {settings.image_container_name}')
    execute_process_report_error(f'az storage container delete --account-name {storage_account_name} --name {settings.metadata_container_name}')

    # Delete storage account (if not provided by env)
    if 'STORAGE_ACCOUNT_NAME' not in os.environ:
        execute_process_report_error(f'az storage account delete --resource-group {resource_group_name} --name {storage_account_name} --yes')

    # Delete the resource group (if not provided by env)
    if 'RESOURCE_GROUP_NAME' not in os.environ:
        execute_process_report_error(f'az group delete --name {resource_group_name}')

    print("E2E testing infra destroyed!")
