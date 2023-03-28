from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RecaptchaChallengeForm,
    ReloginAttemptExceeded,
    SelectContactPointRecoveryForm,
)


def handle_exception(client, e):
    if isinstance(e, BadPassword):
        client.logger.exception(e)
        client.set_proxy(self.next_proxy().href)
        if client.relogin_attempt > 0:
            self.freeze(str(e), days=7)
            raise ReloginAttemptExceeded(e)
        client.settings = self.rebuild_client_settings()
        return self.update_client_settings(client.get_settings())
    elif isinstance(e, LoginRequired):
        client.logger.exception(e)
        client.relogin()
        return self.update_client_settings(client.get_settings())
    elif isinstance(e, ChallengeRequired):
        api_path = json_value(client.last_json, "challenge", "api_path")
        if api_path == "/challenge/":
            client.set_proxy(self.next_proxy().href)
            client.settings = self.rebuild_client_settings()
        else:
            try:
                client.challenge_resolve(client.last_json)
            except ChallengeRequired as e:
                self.freeze('Manual Challenge Required', days=2)
                raise e
            except (ChallengeRequired, SelectContactPointRecoveryForm, RecaptchaChallengeForm) as e:
                self.freeze(str(e), days=4)
                raise e
            self.update_client_settings(client.get_settings())
        return True
    elif isinstance(e, FeedbackRequired):
        message = client.last_json["feedback_message"]
        if "This action was blocked. Please try again later" in message:
            self.freeze(message, hours=12)
            # client.settings = self.rebuild_client_settings()
            # return self.update_client_settings(client.get_settings())
        elif "We restrict certain activity to protect our community" in message:
            # 6 hours is not enough
            self.freeze(message, hours=12)
        elif "Your account has been temporarily blocked" in message:
            """
            Based on previous use of this feature, your account has been temporarily
            blocked from taking this action.
            This block will expire on 2020-03-27.
            """
            self.freeze(message)
    elif isinstance(e, PleaseWaitFewMinutes):
        self.freeze(str(e), hours=1)
    raise e


client = Client()

with open("credentials.txt", "r") as f:
    username, password = f.read().splitlines()

client.login(username, password)

my_user_id = client.user_id_from_username(username)

followers = client.user_followers(my_user_id)

following = client.user_following(my_user_id)

user_doesnt_follow_back = ""

# prints the follower list
# for user in followers:
#     print(client.username_from_user_id(user))

# prints the following list
# for user in following:
#     print(client.username_from_user_id(user))

for user in following:
    if user not in followers:
        user_doesnt_follow_back = client.username_from_user_id(user)
        print(f"{user_doesnt_follow_back} doesn't follow you back.")
        user_info = client.user_info(user)
        follower_count = user_info.follower_count
        if follower_count >= 3000:
            while True:
                print(
                    f"Do you want to unfollow {user_doesnt_follow_back}? y/n")
                choice = input()
                if choice.lower() == "y":
                    client.user_unfollow(user)
                    print(f"Unfollowed {user_doesnt_follow_back}")
                    break
                elif choice.lower() == "n":
                    print(f"You still follow {user_doesnt_follow_back}")
                    break
                else:
                    print("Invalid input. Try again.")
                    continue
        else:
            client.user_unfollow(user)
            print(f"Unfollowed {user_doesnt_follow_back}")
client.handle_exception = handle_exception
