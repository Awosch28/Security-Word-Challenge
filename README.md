# Wordle Challenge

[wordle.global](https://wordle.global/)

Open Source Wordle with a leaderboard.

I decided to create this for Netskope's 2025 Cyber Security Awareness Month campaign. In 2024 Erica McMillen came up with the original idea of having security-focused words for Wordle for that month, as some friendly competition for Netskopers to become more familiar with basic security terms. The first iteration was manually tracking self-reported results in a Slack channel and then bring them into Excel. It was a pain in the ass, and the idea was nixed after a few days of boring number punching and people randomly archiving the channel. Overall the reception to the challenge was positive, so Erica asked me if I could build a proper solution for 2025.

Wordle Challenge is that solution.

## How to run locally

If you want to test out your changes, you can run the server locally.

1. Install Python 3

2. Install requirements
```pip3 install -r requirements.txt```

3. Run web server locally
```gunicorn --chdir webapp app:app```

4. Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Credits:
- Most of the code was taken Hugo0's version of wordle, which you can find here: https://github.com/Hugo0/wordle. I chose it since it was written in both Python and Java, and gave me an excuse to learn how to build Flask apps. I stripped out most of the multi-language support for simplicity. 