#
# Copyright 2019-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from helpers import read_master_key, CsfleHelper

"""
This app demonstrates CSFLE in action. If you do not already have a data
encryption key and are using the local master key provider, make sure to run
make_data_key.py first.
"""

def main():

    # For local master key
    master_key = read_master_key()
    kms_provider_name = "local"
    kms_provider = {
        "local": {
            "key": master_key,
        },
    }

    """
    For AWS KMS, uncomment this block. See https://docs.mongodb.com/drivers/security/client-side-field-level-encryption-local-key-to-kms
    for more information on storing a master key on a KMS.
    """

    """
    For Azure KMS, uncomment this block. See https://docs.mongodb.com/drivers/security/client-side-field-level-encryption-local-key-to-kms
    for more information on storing a master key on a KMS.

    kms_provider_name = "azure"
    kms_provider = {
        "azure": {
            "tenantId": "<Azure account organization>",
            "clientId": "<Azure client ID>",
            "clientSecret": "<Azure client secret>"
        }
    }

    master_key = {
        "keyName": "<Azure key name>",
        "keyVaultEndpoint": "<Azure key vault endpoint>",
         "keyVersion": "<Azure key version>",
    }
    """

    """
    For GCP KMS, uncomment this block. See https://docs.mongodb.com/drivers/security/client-side-field-level-encryption-local-key-to-kms
    for more information on storing a master key on a KMS.
    """

    keyDb = "encryption"
    keyColl = "__keyVault"
    keyNamespace = f"{keyDb}.{keyColl}"

    dataDb = "records"
    dataColl = "patients"

    example_document = {
        "name": "Jon Doe",
        "ssn": 241014209,
        "bloodType": "AB+",
        "medicalRecords": [
            {
                "weight": 180,
                "bloodPressure": "120/80"
            }
        ],
        "insurance": {
            "provider": "MaestCare",
            "policyNumber": 123142
        },
    }

    csfle_helper = CsfleHelper(kms_provider_name=kms_provider_name,
        kms_provider=kms_provider, master_key=master_key, key_db=keyDb, key_coll=keyColl)

    # Insert your key generated by make_data_key.py here.
    # Or comment this out if you already have a data key for your provider stored.
    data_key = CsfleHelper.key_from_base64("<paste the output make_data_key.py here>")

    # if you already have a data key, uncomment the line below
    #data_key = csfle_helper.find_or_create_data_key()

    # set a JSON schema for automatic encryption
    schema = CsfleHelper.create_json_schema(data_key=data_key, dbName=dataDb, collName=dataColl)

    encrypted_client = csfle_helper.get_csfle_enabled_client(schema)

    # performing the insert operation with the csfle enabled client
    # we're using an update with upsert so that subsequent runs of this script don't
    # add more documents
    encrypted_client.records.patients.update_one(
        {"ssn": example_document["ssn"]},
        {"$set": example_document}, upsert=True)

    # perform a read using the csfle enabled client. We expect all fields to
    # be readable.
    # querying on an encrypted field using strict equality
    csfle_find_result = encrypted_client.records.patients.find_one({"ssn": example_document["ssn"]})
    print(f"Document retreived with csfle enabled client:\n{csfle_find_result}\n")
    encrypted_client.close()

    # perform a read using the regular client. We expect some fields to be
    # encrypted.
    regular_client = csfle_helper.get_regular_client()
    regular_find_result = regular_client.records.patients.find_one({"name": "Jon Doe"})
    print(f"Document found regular_find_result:\n{regular_find_result}")
    regular_client.close()

if __name__ == "__main__":
    main()
