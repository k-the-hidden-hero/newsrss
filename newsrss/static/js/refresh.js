/**
 * Gestisce l'aggiornamento dei feed RSS
 */
document.addEventListener('DOMContentLoaded', function() {
    const refreshAllButton = document.getElementById('refresh-all');
    const refreshButtons = document.querySelectorAll('.refresh-feed');
    const loadingOverlay = document.getElementById('loading-overlay');
    const notification = document.getElementById('notification');

    // Gestione click sul pulsante "Aggiorna tutti i feed"
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

                // Aggiornamento delle informazioni sui feed
                if (data.feeds && data.feeds.length > 0) {
                    data.feeds.forEach(feed => {
                        updateFeedCard(feed);
                    });
                    showNotification('Tutti i feed sono stati aggiornati con successo!', 'success');
                } else {
                    showNotification('Nessun feed aggiornato.', 'error');
                }
            })
            .catch(error => {
                console.error('Errore:', error);
                refreshAllButton.classList.remove('btn-loading');
                loadingOverlay.style.display = 'none';
                showNotification('Si è verificato un errore durante l\'aggiornamento dei feed.', 'error');
            });
        });
    }

    // Gestione click sui pulsanti "Aggiorna" individuali
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
                    // Trova il feed aggiornato dall'array di feed
                    const updatedFeed = data.feeds.find(f => f.feed_id == feedId);
                    if (updatedFeed) {
                        updateFeedCard(updatedFeed);
                        showNotification('Feed aggiornato con successo!', 'success');
                    } else {
                        showNotification('Impossibile trovare i dati aggiornati del feed.', 'error');
                    }
                } else {
                    showNotification('Errore durante l\'aggiornamento del feed.', 'error');
                }
            })
            .catch(error => {
                console.error('Errore:', error);
                button.classList.remove('btn-loading');
                showNotification('Si è verificato un errore durante l\'aggiornamento del feed.', 'error');
            });
        });
    });

    // Funzione per aggiornare i dati di una card feed
    function updateFeedCard(feed) {
        const feedCard = document.querySelector(`.feed-card[data-feed-id="${feed.feed_id}"]`);
        if (!feedCard) return;

        // Aggiorna le informazioni di base
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
            statusElement.textContent = feed.success ? '✅ Successo' : '❌ Fallimento';
            statusElement.className = `status ml-1 ${feed.success ? 'text-green-400' : 'text-red-400'}`;
        }

        // Aggiorna le informazioni sull'ultimo episodio
        const latestEpisode = feedCard.querySelector('.latest-episode');
        if (!latestEpisode) return;

        if (feed.last_episode) {
            latestEpisode.style.display = 'block';

            const episodeTitleEl = feedCard.querySelector('.episode-title');
            if (episodeTitleEl) {
                episodeTitleEl.textContent = feed.last_episode;
            }

            // Aggiorna durata episodio
            const durationBadge = feedCard.querySelector('.duration-badge');
            if (durationBadge) {
                if (feed.episode_duration) {
                    durationBadge.textContent = feed.episode_duration;
                    durationBadge.style.display = 'inline-block';
                } else {
                    durationBadge.style.display = 'none';
                }
            }

            // Aggiorna autore episodio
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

            // Aggiorna URL episodio
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

    // Funzione per mostrare notifiche
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
