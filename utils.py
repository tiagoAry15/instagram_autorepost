from PIL import Image


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
