# kite_authentication.py
from kiteconnect import KiteConnect
import configparser

def generate_access_token():
    """
    Generates an access token for the Kite Connect API.
    This is a manual, one-time process required each day.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    api_key = config['KITE']['API_KEY']
    api_secret = config['KITE']['API_SECRET']

    kite = KiteConnect(api_key=api_key)

    # 1. Generate the login URL
    login_url = kite.login_url()
    print("="*50)
    print("KITE AUTHENTICATION REQUIRED")
    print("="*50)
    print(f"1. Please open the following URL in your browser:\n{login_url}")
    
    # 2. User logs in and gets a request_token from the redirected URL
    request_token = input("2. After logging in, you will be redirected. Paste the full redirected URL here:\n")
    
    # Extract the actual request_token from the URL
    try:
        request_token = request_token.split('request_token=')[1].split('&')[0]
    except IndexError:
        print("Error: Could not find 'request_token' in the provided URL.")
        return

    print(f"Request Token obtained: {request_token[:5]}...")

    # 3. Exchange the request_token for an access_token
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        print("Access Token generated successfully!")

        # 4. Save the access_token to a file for the main agent to use
        with open("access_token.txt", "w") as f:
            f.write(access_token)
        print("Access Token saved to 'access_token.txt'. The main agent can now run.")
        print("="*50)

    except Exception as e:
        print(f"Authentication failed: {e}")

if __name__ == "__main__":
    generate_access_token()