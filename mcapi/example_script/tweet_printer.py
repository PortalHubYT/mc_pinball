import time

import tweepy

import mcapi as mc

auth = tweepy.OAuthHandler(
    "tR6HE0QvWhu7t1uhJxmiQuNMi", "dRACvMmj4Qgf7sc1vYhdVpzdwt2t4g4EFSoktdvK6EImF8kFXY"
)

# TODO: REGENERATE THIS VALUE ABOVE !!!!!!!!!! I PUSHED IT ON THE PRIVATE REPO

api = tweepy.API(auth)
username = "FurryEboyVEVO"

sleep_time = 60

while True:

    rcon = mc.connect("localhost", "test", port=25575, mute=False)

    user = api.get_user(screen_name=username)

    url = "https://cdn.discordapp.com/attachments/414084871120617472/849851275372920873/unknown.png"
    url = user.profile_image_url_https.replace("_normal", "")

    mc.post(
        f"say {sleep_time} seconds have passed, it's time to print {user.name}'s latest tweet!!"
    )

    tweet = api.user_timeline(
        screen_name=username,
        count=1,
        include_rts=False,
        exclude_replies=True,
        tweet_mode="extended",
    )

    tweet = tweet[0].full_text

    split_tweet = []
    buff = ""
    count = 0
    for char in tweet:

        if char.isspace() and count > 30:
            split_tweet.append(buff)
            buff = ""
            count = 0
        else:
            buff += char

        count += 1
    else:
        split_tweet.append(buff)
        split_tweet.reverse()

    scale = 0
    y = 4
    zones = []
    for index, line in enumerate(split_tweet):
        coords = mc.BlockCoordinates(-40, y * (scale + 1), -70)
        zone = mc.set_text(
            line,
            coords,
            style="mixed",
            palette="blackstone",
            scale=scale,
        )
        zones.append(zone)

        y += 6
    else:
        coords = mc.BlockCoordinates(-40, y * (scale + 1), -70)
        zone = mc.set_text(
            f"@{username}:",
            coords,
            style="mixed",
            palette="quartz",
            scale=scale,
        )
        zones.append(zone)

    time.sleep(sleep_time)

    for zone in zones:
        mc.set_zone(zone, mc.Block("air"))
