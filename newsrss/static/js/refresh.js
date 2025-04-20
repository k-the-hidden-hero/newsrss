/**
 * Manages the RSS feeds refresh
 */
document.addEventListener('DOMContentLoaded', function() {
    const refreshAllButton = document.getElementById('refresh-all');
    const refreshButtons = document.querySelectorAll('.refresh-feed');
    const loadingOverlay = document.getElementById('loading-overlay');
    const notification = document.getElementById('notification');

    // Handle click on "Refresh all feeds" button
    if (refreshAllButton) {
        refreshAllButton.addEventListener('click', function() {
            refreshAllButton.classList.add('btn-loading');
            loadingOverlay.style.display = 'flex';

            fetch('/refresh', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                refreshAllButton.classList.remove('btn-loading');
                loadingOverlay.style.display = 'none';

                // Update feed information
                if (data.feeds && data.feeds.length > 0) {
                    data.feeds.forEach(feed => {
                        updateFeedCard(feed);
                    });
                    showNotification('All feeds have been successfully updated!', 'success');
                } else {
                    showNotification('No feeds updated.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                refreshAllButton.classList.remove('btn-loading');
                loadingOverlay.style.display = 'none';
                showNotification('An error occurred while updating the feeds.', 'error');
            });
        });
    }

    // Handle click on individual "Refresh" buttons
    refreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const feedId = this.getAttribute('data-feed-id');
            const feedCard = document.querySelector(`.feed-card[data-feed-id="${feedId}"]`);

            button.classList.add('btn-loading');

            fetch(`/refresh?feed_id=${feedId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                button.classList.remove('btn-loading');

                if (data.status === 'success') {
                    // Find the updated feed from the feeds array
                    const updatedFeed = data.feeds.find(f => f.feed_id == feedId);
                    if (updatedFeed) {
                        updateFeedCard(updatedFeed);
                        showNotification('Feed successfully updated!', 'success');
                    } else {
                        showNotification('Could not find updated feed data.', 'error');
                    }
                } else {
                    showNotification('Error updating feed.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                button.classList.remove('btn-loading');
                showNotification('An error occurred while updating the feed.', 'error');
            });
        });
    });

    // Function to update feed card data
    function updateFeedCard(feed) {
        const feedCard = document.querySelector(`.feed-card[data-feed-id="${feed.feed_id}"]`);
        if (!feedCard) return;

        // Update basic information
        const lastScrapeEl = feedCard.querySelector('.last-scrape');
        if (lastScrapeEl) {
            lastScrapeEl.textContent = feed.last_scrape || '';
        }

        const lastDurationEl = feedCard.querySelector('.last-duration');
        if (lastDurationEl) {
            lastDurationEl.textContent = (feed.last_duration || '0') + 's';
        }

        const statusElement = feedCard.querySelector('.status');
        if (statusElement) {
            statusElement.textContent = feed.success ? '✅ Success' : '❌ Failure';
            statusElement.className = `status ml-1 ${feed.success ? 'text-green-400' : 'text-red-400'}`;
        }

        // Update latest episode information
        const latestEpisode = feedCard.querySelector('.latest-episode');
        if (!latestEpisode) return;

        if (feed.last_episode) {
            latestEpisode.style.display = 'block';

            const episodeTitleEl = feedCard.querySelector('.episode-title');
            if (episodeTitleEl) {
                episodeTitleEl.textContent = feed.last_episode;
            }

            // Update episode duration
            const durationBadge = feedCard.querySelector('.duration-badge');
            if (durationBadge) {
                if (feed.episode_duration) {
                    durationBadge.textContent = feed.episode_duration;
                    durationBadge.style.display = 'inline-block';
                } else {
                    durationBadge.style.display = 'none';
                }
            }

            // Update episode author
            const authorContainer = feedCard.querySelector('.episode-author-container');
            const authorElement = feedCard.querySelector('.episode-author');
            if (authorContainer && authorElement) {
                if (feed.episode_author) {
                    authorContainer.style.display = 'flex';
                    authorElement.textContent = feed.episode_author;
                } else {
                    authorContainer.style.display = 'none';
                }
            }

            // Update episode URL
            const urlContainer = feedCard.querySelector('.episode-url-container');
            const urlElement = feedCard.querySelector('.episode-url');
            if (urlContainer && urlElement) {
                if (feed.episode_url) {
                    urlContainer.style.display = 'flex';
                    urlElement.href = feed.episode_url;
                } else {
                    urlContainer.style.display = 'none';
                }
            }
        } else if (latestEpisode) {
            latestEpisode.style.display = 'none';
        }
    }

    // Function to show notifications
    function showNotification(message, type) {
        if (!notification) return;

        notification.textContent = message;
        notification.className = type === 'success' ? 'notification-success' : 'notification-error';
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
});
