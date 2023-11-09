#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    CHANNEL_SERVICE = "https://botframework.azure.us"
    #OAUTH_URL_GOV = "https://apiDoD.botframework.azure.us"
    OAUTH_URL_GOV = "https://tokengcch.botframework.azure.us/"
    TO_CHANNEL_FROM_BOT_LOGIN_URL = "https://login.microsoftonline.us/MicrosoftServices.onmicrosoft.us"
    TO_CHANNEL_FROM_BOT_OAUTH_SCOPE = "https://api.botframework.us"
    TO_BOT_FROM_CHANNEL_TOKEN_ISSUER = "https://api.botframework.us"
    TO_BOT_FROM_CHANNEL_OPEN_ID_METADATA_URL = "https://login.botframework.azure.us/v1/.well-known/openidconfiguration"
    TO_BOT_FROM_EMULATOR_OPEN_ID_METADATA_URL = "https://login.microsoftonline.us/cab8a31a-1906-4287-a0d8-4eef66b95f6e/v2.0/.well-known/openid-configuration"
    VALIDATE_AUTHORITY = True