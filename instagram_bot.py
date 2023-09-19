from pathlib import Path

from instagrapi import Client
from instagrapi.types import StoryMention, UserShort
from utils import read_credentials, save_posted_story, convert_heic_to_jpeg,\
    verify_if_story_is_already_posted


class Instagram_bot:
    def __init__(self):
        self.client = Client()
        username, password = read_credentials()
        self.username = username
        self.login(username, password)

    def login(self, username, password):
        self.client.login(username, password)

    def get_following_accounts(self):
        user_id = self.client.user_info_by_username(self.username).pk
        return self.client.user_following(user_id)

    def get_followers_accounts(self):
        user_id = self.client.user_info_by_username(self.username).pk
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
