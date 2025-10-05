# Word Challenge

Open Source Wordle-style game with a leaderboard.

I decided to create this for Netskope's 2025 Cyber Security Awareness Month campaign. In 2024 Erica McMillen wanted to have security-focused words for Wordle, as some friendly competition for Netskopers to become more familiar with basic security terms. The first iteration was manually tracking self-reported results in a Slack channel and then bring them into Excel. It was a pain in the ass, and the idea was nixed after a few days of boring number punching and people randomly archiving the channel. Overall the reception to the challenge was positive, so Erica asked me if I could build a proper solution for 2025.

Word Challenge is that solution.

## How to run locally

If you want to test out your changes, you can run the server locally.

1. Install Python 3

2. Install requirements
```pip3 install -r requirements.txt```

3. Add environment variables by creating a .env file or editing the .env.example file.

4. Run web server locally
```gunicorn --daemon --bind 0.0.0.0:8000 --chdir webapp app:app```
- You can replace port 8000 with whatever port you want.

5. Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Setting Up Google OAuth Client
For our use case it made the most sense to have users authenticate with Google. In order to do this, you will need an OAuth2 credentials.

1. Go to https://console.cloud.google.com/ and sign in with your Google account. 

2. Choose the appropriate project, or create a new project.

3. Using the left pane, go to 'APIs & Services > Credentials'. Alternaitvely, go to https://console.cloud.google.com/apis/credentials .

4. Click on 'Create Credentials > OAuth client ID'. 
    - Application type: Web application
    - Name: Wordle Challenge (or whatever you want it to be)
    - Authorized JavaScript Origins: the domain name that the game will be accessible from (e.g. hxxps://wordle.example.com)
    - Authorized redirect URIs: Add '/login/callback' to the end of what you chose for Authorized JavaScript Origins (e.g. hxxps://wordle.example.com/login/callback)

Note: If using this in a competitive scene, make the app available to 'Internal' users only. If you are not part of a google workspace organization, or if you want to expose the game to user's outside of your org, you may need to use the Verification Center to publish the app.

5. Select 'Branding' on the left pane:
    - Specify which email domains will be allowed to access the game by putting them in the 'Authorized domains' section
    - Fill out the rest of the page as necessary

6. Select 'Data Access' on the left pane:
    - Add the following non-sensitive scopes:
        - /auth/userinfo.email
        - /auth/userinfo.profile
        - /openid

7. (Optional) Use the Verification Center if you want to expose the app to user outside of your organization, or if you want to have more than 

## Credits:
- I have to think Hugo0 since I used his code as a starting point. You can find their version here: https://github.com/Hugo0/wordle. 