from pathlib import Path
from PIL import Image
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.types import StoryMention, UserShort


def verify_if_story_is_already_posted(story):
    posted_stories = read_posted_stories()
    if str(story.pk) in posted_stories:
        print(f"Story {story} já foi postado.")
        return True
    return False


def reset_posted_stories():
    with open('posted_stories.txt', 'w') as f:
        f.write('')


def read_credentials():
    with open('credentials.txt', 'r') as f:
        return f.read().splitlines()


def read_verification_code():
    with open('2FA_code.txt', 'r') as f:
        return f.read()


def convert_heic_to_jpeg(heic_path, jpeg_path):
    image = Image.open(heic_path)
    image.convert('RGB').save(jpeg_path, 'JPEG')


def read_posted_stories():
    try:
        with open('posted_stories.txt', 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()


def save_posted_story(story_id):
    with open('posted_stories.txt', 'a') as f:
        f.write(f"{story_id}\n")


class Instagram_bot:
    def __init__(self):
        username, password = read_credentials()
        verification_code = read_verification_code()
        self.username = username
        self.login_user(username, password, verification_code)
        self.client.dump_settings("session.json")

    def login_user(self, username, password, verification_code):
        """
        Attempts to login to Instagram using either the provided session information
        or the provided username and password.
        """

        self.client = Client()
        self.client.delay_range = [1, 3]
        session = self.client.load_settings("session.json")

        login_via_session = False
        login_via_pw = False

        if session:
            try:
                self.client.set_settings(session)
                # resume session
                self.client.login(username, password)

                # check if session is valid
                try:
                    self.client.get_timeline_feed()
                except LoginRequired:
                    print("Session is invalid, need to login via username and password")

                    old_session = self.client.get_settings()

                    # use the same device uuids across logins
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])

                    self.client.login(username, password)
                login_via_session = True
            except Exception as e:
                print("Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                print("Attempting to login via username, password and 2FA. username: %s" % username)
                if self.client.login(username, password, verification_code=verification_code):
                    login_via_pw = True
            except Exception as e:
                print("Couldn't login user using username, password and 2FA: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception("Couldn't login user with either password or session")

    def get_following_accounts(self, username=None):
        user_id = self.client.user_info_by_username(username).pk
        return self.client.user_following(user_id)

    def get_followers_accounts(self, username=None):
        if username is None:
            username = self.username
        user_id = self.client.user_info_by_username(username).pk
        return self.client.user_followers(user_id)

    def get_followers_stories_with_self_mentions(self, user_followers):
        stories_with_mentions = []
        for follower in user_followers:
            user_stories = self.client.user_stories(follower)
            for story in user_stories:
                for mentions in story.mentions:
                    if mentions.user.username == self.username:
                        stories_with_mentions.append(story)
        return stories_with_mentions

    def repost_stories_with_self_mentions(self, stories_with_mentions):
        for story in stories_with_mentions:
            if verify_if_story_is_already_posted(story):
                continue
            media_path = self.client.story_download(story.pk, filename=f'{str(story.pk)}', folder=Path('stories'))
            mention = StoryMention(user=UserShort(pk=story.user.pk), x=0.5, y=0.5, width=0.5, height=0.5)

            if story.media_type == 1:
                jpg_path = f'stories/{str(story.pk)}.jpeg'
                convert_heic_to_jpeg(media_path, jpg_path)
                self.post_image_as_story(jpg_path, mentions=[mention])
            elif story.media_type == 2:
                self.post_video_as_story(media_path, mentions=[mention])

            save_posted_story(story.pk)

    def post_video_as_story(self, video_path, mentions):
        self.client.video_upload_to_story(video_path, mentions=[mentions])

    def post_image_as_story(self, image_path, mentions):
        self.client.photo_upload_to_story(image_path, mentions=mentions)


# Exemplo de uso
if __name__ == "__main__":
    bot = Instagram_bot()
    followers = bot.get_followers_accounts()
    stories = bot.get_followers_stories_with_self_mentions(followers)
    bot.repost_stories_with_self_mentions(stories)
