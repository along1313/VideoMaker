from moviepy.editor import ImageSequenceClip, AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip
def add_audio_to_video(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)