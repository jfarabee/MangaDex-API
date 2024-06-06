# class MDConnection is connection wrapper for Mangadex API
#   maintain access/refresh tokens and base ssl url, httpx3 lib for async

import httpx
import time
import asyncio
# import all for now - we can pare down to necessities eventually


# opening a connection:
#   1 - POST https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token
#  1b - headers:
#       grant_type=password
#       username=<your_username>
#       password=<your_password>
#       client_id=<your_client_id>
#       client_secret=<your_client_secret>
#   2 - receive JSON obj w/ access token and refresh token
#   3 - EVERY 15 MINUTES: access token dies, 
#       POST https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token
#  3b - headers:
#       grant_type=refresh_token
#       refresh_token=<your_refresh_token>
#       client_id=<your_client_id>
#       client_secret=<your_client_secret>

# request lifecycle:
#   1 - 


class MDConnection:
    ssl_url = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"
    report_url = "https://api.mangadex.network/report"
    access_token = 0
    token_alive = False
    refresh_token = 0
    refresh_time = 0

    def __init__(self, username, password, client_id, client_secret, rate_limit = 5):
        #init SSL auth here
        self.client_id = client_id
        self.client_secret = client_secret
        self.rate_limit = rate_limit            # in CALLS PER SECOND, default 5 (mangadex's recommendation)
        
        md_auth_request = httpx.post(self.ssl_url, data={
            "grant_type": "password",
            "username": username,
            "password": password,               #don't need user/pass for re-auth, just pass them the first time
            "client_id": client_id,
            "client_secret": client_secret
            })
        
        if md_auth_request.status_code != 200:
            raise Exception(f'auth request failed with {md_auth_request.status_code}')  # 200 OK. expand on Exceptions later

        md_auth_response_json = md_auth_request.json()
        
        self.access_token = md_auth_response_json["access_token"]
        self.refresh_token = md_auth_response_json["refresh_token"]
        self.refresh_time = time.time() + md_auth_response_json['expires_in']
        self.token_alive = True
    
        
    def refresh(self):
        
        self.token_alive = False

        md_auth_refresh = httpx.post(__class__.ssl_url, data={
            "grant_type": "refresh_token",
            "refresh_token" : self.refresh_token,
            "client_id" : self.client_id,
            "client_secret": self.client_secret
            }).json()
        
        if md_auth_refresh.status_code != 200:
            raise Exception(f'token refresh failed') # 200 OK. expand on Exceptions here

        self.access_token = md_auth_refresh["access_token"]
        self.refresh_token = md_auth_refresh["refresh_token"]
        self.refresh_time = time.time() + md_auth_refresh['expires_in']
        self.token_alive = True
        
        return True


    def download_chapter(self, chapter_id, dest_path, data_saver = False):
        if self.access_token == 0:
            raise Exception('init MDConnection object first.') # expand on Exceptions here
        
        md_chapter_request = httpx.get(f'https://api.mangadex.org/at-home/server/{chapter_id}', headers = {
            'Authorization': f'Bearer {self.access_token}'
            })
                
        if md_chapter_request.status_code != 200:
            raise Exception('chapter request failed')  # 200 OK. expand on Exceptions here
        
        md_chapter_response_json = md_chapter_request.json()
        
        expanded_base_url = md_chapter_response_json['baseUrl']
        quality = 'data'

        if data_saver:
            expanded_base_url += '/data-saver/'
            quality += 'Saver'
        else:
            expanded_base_url += '/data/'
        
        md_chapter_information = md_chapter_response_json['chapter']

        for page in md_chapter_information[quality]:
            # download request, respecting rate limit.
            self.individual_image_download(expanded_base_url, md_chapter_information['hash'], page, dest_path)
            

            time.sleep(1 / self.rate_limit)
       

    # expanded_base_url contains base_url + data_saver string (data/data-saver)
    def individual_image_download(self, expanded_base_url, chapter_hash, page_id, dest_path):
        md_image_request = httpx.get(f'{expanded_base_url}/{chapter_hash}/{page_id}')
        
        #response has the image in it (raw)
        
        # check OK?

        # write out to page_id (<page#>-<hash>.<ext>) for now
        # allow for custom image names later...
        with open(f'{dest_path}/{page_id}', 'wb') as outfile:
            outfile.write(md_image_request.content)
            outfile.close()
       
            
    async def individual_image_download_async(self, async_client, expanded_base_url, chapter_hash, page_id, dest_path, async_rw = False):
        try:
            md_image_request = await async_client.get(f'{expanded_base_url}/{chapter_hash}/{page_id}')
        except Exception as e:
            print(e)
            return
        
        #response has the image in it (raw)
        
        # check OK?

        # write out to page_id (<page#>-<hash>.<ext>) for now
        # allow for custom image names later...
        with open(f'{dest_path}/{page_id}', 'wb') as outfile:
            outfile.write(md_image_request.content)
            outfile.close()


    async def download_chapter_async(self, chapter_id, dest_path, data_saver = False):
        if self.access_token == 0:
            raise Exception('initialize MDConnection object first.') # expand on Exceptions here
        
        # request chapter metadata

        md_chapter_request = httpx.get(f'https://api.mangadex.org/at-home/server/{chapter_id}', headers = {
            'Authorization': f'Bearer {self.access_token}'
            })
                
        if md_chapter_request.status_code != 200:
            raise Exception('chapter request failed')  # 200 OK. expand on Exceptions here
        
        md_chapter_response_json = md_chapter_request.json()
        
        expanded_base_url = md_chapter_response_json['baseUrl']
        quality = 'data'

        if data_saver:
            expanded_base_url = f'{expanded_base_url}/data-saver/'
            quality += 'Saver'
        else:
            expanded_base_url = f'{expanded_base_url}/data/'
        
        md_chapter_information = md_chapter_response_json['chapter']
        
        async_client = httpx.AsyncClient()

        async with asyncio.TaskGroup() as task_group:
            for page in md_chapter_information[quality]:
            # download request, respecting rate limit.
            
                try:
                    task = task_group.create_task(
                    self.individual_image_download_async(async_client, expanded_base_url, md_chapter_information['hash'], page, dest_path))
         
                except Exception as e:
                    print(e)                #expand

                time.sleep(1 / self.rate_limit)
            
        await async_client.aclose()


    def request_proxy(self, request, *request_params):
        # weird stuff for auth-sensitive requests
        # not necessary for chapter querying, etc...
        # refresh token
        
        # not using atm
        if time.time() >= self.refresh_time:
            self.refresh()
        return request(request_params)
    