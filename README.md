# Yojana Sarathi

**WhatsApp bot to self select government schemes for people living in rural areas.**

_The code was not run on profuction release hence is not clean._

All of the code comes in `webhook.py` script.
`adhar.py` helps extracting data from scanned qr code of the Aadhaar card.

# Here is the flow of the bot

![alt text](https://github.com/viren-vii/yojana-sarathi/blob/main/demo.png "Flow of the bot")

# How to start with it?

As told above, we have worked on the bot only in development phase. So we had chosen meta developers platform for the bot.

First you have to sign up on [meta developers platform](https://developers.facebook.com) and create new app i.e. for WhatsApp.
Once app is created, register recipient phone number on the dashboard. At [meta developers platform](https://developers.facebook.com/apps) in the Whatsapp section inside products, go in Getting Started to enter recipient phone number.

# Webhooks

Endpoints for the webhook have been already created in `webhooks.py`.
On the developers platform, in the WhatsApp section, inside `Configuration`, you have to enter url of your hosting. Once you install all the packages from `requirements.txt` by `pip install -r /path/to/requirements.txt`, you can host the webhook by using `python webhooks.py`. Once it is live on localhost, you can use `ngrok http <port_number>` to host it. Meta platfom requires https requests in order to respond the requests.

You have to enter the same `verify_token` on developers platform as same as in the code in `webhooks.py`.

# Database

PostgreSQL was used for this project. Follow installation and set up process as mentioned in the documentation and update `app.config['SQLALCHEMY_DATABASE_URI']` with your data.

ERD for the project is:
![alt text](https://github.com/viren-vii/yojana-sarathi/blob/main/erd.png "ERD")

# Ending note

Refer to [abstract](https://github.com/viren-vii/yojana-sarathi/blob/main/PAVVVFECT_ABSTRACT.pdf) and [presentation](https://github.com/viren-vii/yojana-sarathi/blob/main/PAVVVFECT_PPT.pdf) for more details on statistics and impact of the project.
