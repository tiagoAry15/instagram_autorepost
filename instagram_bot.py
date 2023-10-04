from pathlib import Path
from PIL import Image
from instagrapi import Client
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
        self.client = Client()
        username, password = read_credentials()
        self.username = username
        self.login(username, password)

    def login(self, username, password):
        self.client.login(username, password)

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
