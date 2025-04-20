from datetime import datetime

from ..models.schemas import Episode, M3UPlaylist


class PlaylistService:
    @staticmethod
    def generate_m3u(episodes: list[Episode]) -> str:
        """Genera una playlist m3u."""
        playlist = "#EXTM3U\n"
        total_duration = 0

        for episode in episodes:
            duration = episode.duration
            total_duration += duration
            playlist += f"#EXTINF:{duration},{episode.title}\n"
            playlist += f"{episode.url}\n"

        return playlist

    @staticmethod
    def generate_m3u8(episodes: list[Episode]) -> str:
        """Genera una playlist m3u8 (HLS)."""
        playlist = "#EXTM3U\n"
        playlist += "#EXT-X-VERSION:3\n"
        playlist += f"#EXT-X-TARGETDURATION:{max(ep.duration for ep in episodes)}\n"
        playlist += "#EXT-X-MEDIA-SEQUENCE:0\n"

        for episode in episodes:
            playlist += f"#EXTINF:{episode.duration},\n"
            playlist += f"{episode.url}\n"

        playlist += "#EXT-X-ENDLIST\n"
        return playlist

    @staticmethod
    def create_playlist(episodes: list[Episode], format: str = "m3u") -> M3UPlaylist:
        """Crea un oggetto playlist con metadati."""
        total_duration = sum(ep.duration for ep in episodes)
        return M3UPlaylist(
            episodes=episodes,
            total_duration=total_duration,
            generated_at=datetime.now(),
        )
