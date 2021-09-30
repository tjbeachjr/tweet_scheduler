# Tweet Scheduler

---
Automated bot for sending tweets 

# Deploying

---
Requires an active AWS account, Python3 and the Chalice framework installed.  See https://github.com/aws/chalice for installation steps.

## Setup Configuration

1. Add Credentials to SecretsManger

Requires Twitter and Google API credentials:

```json
{
    "twitter": "{\"consumer_key\": \"\",     \"consumer_secret\": \"\",     \"access_token\": \"\",     \"access_token_secret\": \"\"}",
    "google": "{ \"type\": \"service_account\",     \"project_id\": \"\",     \"private_key_id\": \"\",     \"private_key\": \"\",     \"client_email\": \"\",     \"client_id\": \"\",     \"auth_uri\": \"https://accounts.google.com/o/oauth2/auth\",     \"token_uri\": \"https://accounts.google.com/o/oauth2/token\",     \"auth_provider_x509_cert_url\": \"https://www.googleapis.com/oauth2/v1/certs\",     \"client_x509_cert_url\": \"\"}"
}

```

2. Update the the `.chalice/config.json` file.  Add the key for the Google sheet containing the Tweets to send and the name of the secret in SecretsManager

## Deploy to AWS

For development:
```
chalice deploy --stage dev
```

For production:
```
chalice deploy --stage prod
```