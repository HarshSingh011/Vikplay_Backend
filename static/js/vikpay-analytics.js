/**
 * Frontend JavaScript for Automatic Data Collection
 * This shows how the automatic tracking would work on the client side
 */

class VikPayAnalytics {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.currentVideoId = null;
        this.watchStartTime = null;
        this.lastProgressUpdate = 0;
        this.searchStartTime = null;
        
        // Initialize session tracking
        this.initializeSession();
        
        // Set up automatic tracking
        this.setupAutomaticTracking();
    }

    // ====== SESSION TRACKING ======
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async initializeSession() {
        const sessionData = {
            session_id: this.sessionId,
            device_type: this.detectDeviceType(),
            browser: this.detectBrowser(),
            os: this.detectOS()
        };

        try {
            await fetch('/api/videos/session/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(sessionData)
            });
            console.log('✅ Session tracking started');
        } catch (error) {
            console.error('Failed to start session tracking:', error);
        }
    }

    // ====== VIDEO VIEWING TRACKING ======
    
    startVideoTracking(videoId) {
        this.currentVideoId = videoId;
        this.watchStartTime = Date.now();
        this.lastProgressUpdate = 0;
        
        console.log(`🎥 Started tracking video ${videoId}`);
    }

    async trackVideoProgress(currentTime, duration) {
        if (!this.currentVideoId || !duration) return;

        const watchDuration = Math.floor((Date.now() - this.watchStartTime) / 1000);
        const completionPercentage = (currentTime / duration) * 100;

        // Only send updates every 10 seconds or significant progress changes
        if (watchDuration - this.lastProgressUpdate >= 10 || 
            completionPercentage - this.lastProgressUpdate >= 5) {
            
            const progressData = {
                video_id: this.currentVideoId,
                watch_duration: watchDuration,
                completion_percentage: completionPercentage,
                device_type: this.detectDeviceType(),
                session_id: this.sessionId
            };

            try {
                await fetch('/api/videos/track/watch-progress', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    },
                    body: JSON.stringify(progressData)
                });
                
                this.lastProgressUpdate = watchDuration;
                console.log(`📊 Progress tracked: ${completionPercentage.toFixed(1)}%`);
            } catch (error) {
                console.error('Failed to track video progress:', error);
            }
        }
    }

    async trackVideoInteraction(interactionType, value = null, timestamp = null) {
        if (!this.currentVideoId) return;

        const interactionData = {
            video_id: this.currentVideoId,
            interaction_type: interactionType,
            interaction_value: value,
            video_timestamp: timestamp,
            session_id: this.sessionId,
            device_type: this.detectDeviceType()
        };

        try {
            await fetch('/api/videos/track/interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(interactionData)
            });
            
            console.log(`🎯 Interaction tracked: ${interactionType}`);
        } catch (error) {
            console.error('Failed to track interaction:', error);
        }
    }

    async trackEngagement(rating = null, liked = null, shared = false, bookmarked = false) {
        if (!this.currentVideoId) return;

        const engagementData = {
            video_id: this.currentVideoId,
            rating: rating,
            liked: liked,
            shared: shared,
            bookmarked: bookmarked
        };

        try {
            await fetch('/api/videos/track/engagement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(engagementData)
            });
            
            console.log('❤️ Engagement tracked');
        } catch (error) {
            console.error('Failed to track engagement:', error);
        }
    }

    // ====== SEARCH TRACKING ======
    
    async trackSearch(searchQuery, filters = null) {
        this.searchStartTime = Date.now();

        const searchData = {
            search_query: searchQuery,
            search_filters: filters,
            device_type: this.detectDeviceType()
        };

        try {
            const response = await fetch('/api/videos/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(searchData)
            });
            
            const result = await response.json();
            console.log(`🔍 Search tracked: "${searchQuery}"`);
            
            // Store search ID for click tracking
            this.currentSearchId = result.search_id;
            
            return result;
        } catch (error) {
            console.error('Failed to track search:', error);
            throw error;
        }
    }

    async trackSearchClick(videoId, position) {
        if (!this.currentSearchId) return;

        const timeToClick = this.searchStartTime ? 
            (Date.now() - this.searchStartTime) / 1000 : null;

        const clickData = {
            search_id: this.currentSearchId,
            clicked_video_id: videoId,
            click_position: position,
            time_to_click: timeToClick
        };

        try {
            await fetch('/api/videos/search/click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(clickData)
            });
            
            console.log(`🎯 Search click tracked: position ${position}`);
        } catch (error) {
            console.error('Failed to track search click:', error);
        }
    }

    // ====== AUTOMATIC SETUP ======
    
    setupAutomaticTracking() {
        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.updateSessionActivity();
            }
        });

        // Track before page unload
        window.addEventListener('beforeunload', () => {
            this.endSession();
        });

        // Periodic session activity updates
        setInterval(() => {
            this.updateSessionActivity();
        }, 30000); // Every 30 seconds
    }

    async updateSessionActivity() {
        const activityData = {
            session_id: this.sessionId,
            videos_watched: this.getVideosWatchedCount(),
            searches_performed: this.getSearchesPerformedCount(),
            videos_liked: this.getVideosLikedCount(),
            videos_shared: this.getVideosSharedCount()
        };

        try {
            await fetch('/api/videos/session/activity', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(activityData)
            });
        } catch (error) {
            console.error('Failed to update session activity:', error);
        }
    }

    async endSession() {
        const sessionDuration = Math.floor((Date.now() - this.sessionStartTime) / 1000);
        
        const endData = {
            session_id: this.sessionId,
            session_duration: sessionDuration
        };

        try {
            // Use sendBeacon for reliable delivery during page unload
            if (navigator.sendBeacon) {
                navigator.sendBeacon(
                    '/api/videos/session/end',
                    JSON.stringify(endData)
                );
            } else {
                await fetch('/api/videos/session/end', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    },
                    body: JSON.stringify(endData)
                });
            }
            
            console.log('🏁 Session ended');
        } catch (error) {
            console.error('Failed to end session:', error);
        }
    }

    // ====== UTILITY METHODS ======
    
    detectDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
            return 'mobile';
        } else if (/tablet|ipad/i.test(userAgent)) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }

    detectBrowser() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (userAgent.includes('chrome')) return 'chrome';
        if (userAgent.includes('firefox')) return 'firefox';
        if (userAgent.includes('safari')) return 'safari';
        if (userAgent.includes('edge')) return 'edge';
        return 'unknown';
    }

    detectOS() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (userAgent.includes('windows')) return 'windows';
        if (userAgent.includes('mac')) return 'macos';
        if (userAgent.includes('linux')) return 'linux';
        if (userAgent.includes('android')) return 'android';
        if (userAgent.includes('ios')) return 'ios';
        return 'unknown';
    }

    getAuthToken() {
        // Get JWT token from localStorage or cookies
        return localStorage.getItem('auth_token') || '';
    }

    // Session counters (implement based on your app's state management)
    getVideosWatchedCount() { return this.videosWatchedCount || 0; }
    getSearchesPerformedCount() { return this.searchesPerformedCount || 0; }
    getVideosLikedCount() { return this.videosLikedCount || 0; }
    getVideosSharedCount() { return this.videosSharedCount || 0; }
}

// ====== USAGE EXAMPLES ======

// Initialize analytics
const analytics = new VikPayAnalytics();

// Video player integration example
class VideoPlayer {
    constructor(videoElement, videoId) {
        this.video = videoElement;
        this.videoId = videoId;
        
        // Start tracking when video starts
        analytics.startVideoTracking(videoId);
        
        // Set up event listeners for automatic tracking
        this.setupVideoTracking();
    }
    
    setupVideoTracking() {
        // Track progress automatically
        this.video.addEventListener('timeupdate', () => {
            analytics.trackVideoProgress(this.video.currentTime, this.video.duration);
        });
        
        // Track interactions automatically
        this.video.addEventListener('play', () => {
            analytics.trackVideoInteraction('play', null, this.video.currentTime);
        });
        
        this.video.addEventListener('pause', () => {
            analytics.trackVideoInteraction('pause', null, this.video.currentTime);
        });
        
        this.video.addEventListener('seeked', () => {
            analytics.trackVideoInteraction('seek', this.video.currentTime.toString(), this.video.currentTime);
        });
        
        this.video.addEventListener('volumechange', () => {
            analytics.trackVideoInteraction('volume_change', this.video.volume.toString());
        });
    }
    
    // Manual engagement tracking
    onLike() {
        analytics.trackEngagement(null, true);
    }
    
    onDislike() {
        analytics.trackEngagement(null, false);
    }
    
    onRate(rating) {
        analytics.trackEngagement(rating);
    }
    
    onShare() {
        analytics.trackEngagement(null, null, true);
    }
    
    onBookmark() {
        analytics.trackEngagement(null, null, false, true);
    }
}

// Search integration example
class SearchComponent {
    async performSearch(query, filters = null) {
        try {
            // This automatically tracks the search
            const results = await analytics.trackSearch(query, filters);
            
            // Display results with click tracking
            this.displayResults(results.results);
            
            return results;
        } catch (error) {
            console.error('Search failed:', error);
        }
    }
    
    displayResults(results) {
        results.forEach((video, index) => {
            const element = this.createVideoElement(video);
            
            // Track clicks automatically
            element.addEventListener('click', () => {
                analytics.trackSearchClick(video.id, index + 1);
            });
            
            this.resultsContainer.appendChild(element);
        });
    }
}

console.log('🚀 VikPay Analytics initialized - All user behavior will be automatically tracked for AI recommendations!');
