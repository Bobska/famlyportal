/**
 * Expanse Presence System - WebSocket Client
 * 
 * Handles real-time presence tracking for family members:
 * - WebSocket connection management
 * - Heartbeat pings to keep connection alive
 * - Online/offline status updates
 * - UI updates with faction-themed animations
 * 
 * Version: 001
 * Last Updated: 2025-01-09
 */

(function() {
    'use strict';

    // Presence Manager Class
    class ExpansePresenceManager {
        constructor() {
            this.socket = null;
            this.heartbeatInterval = null;
            this.reconnectTimeout = null;
            this.isConnected = false;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 10;
            this.heartbeatFrequency = 30000; // 30 seconds
            this.reconnectDelay = 5000; // 5 seconds
            this.familyPresence = new Map(); // user_id -> presence data
            
            // Get current faction from localStorage
            this.currentFaction = localStorage.getItem('selectedFaction') || 'un';
            
            console.log('[Presence] Manager initialized');
        }

        /**
         * Initialize WebSocket connection
         */
        init() {
            // Only connect if user is authenticated
            const userElement = document.querySelector('[data-user-id]');
            if (!userElement) {
                console.log('[Presence] User not authenticated, skipping connection');
                return;
            }

            this.connect();
        }

        /**
         * Establish WebSocket connection
         */
        connect() {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                console.log('[Presence] Already connected');
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/presence/`;
            
            console.log('[Presence] Connecting to:', wsUrl);
            
            try {
                this.socket = new WebSocket(wsUrl);
                
                this.socket.onopen = this.onOpen.bind(this);
                this.socket.onmessage = this.onMessage.bind(this);
                this.socket.onerror = this.onError.bind(this);
                this.socket.onclose = this.onClose.bind(this);
            } catch (error) {
                console.error('[Presence] Connection error:', error);
                this.scheduleReconnect();
            }
        }

        /**
         * WebSocket opened successfully
         */
        onOpen(event) {
            console.log('[Presence] Connected to presence server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Play connection sound
            if (window.ExpanseAudio && window.ExpanseAudio.play) {
                window.ExpanseAudio.play('notification');
            }
            
            // Update connection status indicator
            this.updateConnectionStatus(true);
        }

        /**
         * Handle incoming WebSocket messages
         */
        onMessage(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('[Presence] Received:', data.type, data);
                
                switch (data.type) {
                    case 'family_presence':
                        // Initial family presence data
                        this.handleFamilyPresence(data.members);
                        break;
                    
                    case 'presence_update':
                        // User went online/offline
                        this.handlePresenceUpdate(data);
                        break;
                    
                    case 'user_page_change':
                        // User changed page/module
                        this.handlePageChange(data);
                        break;
                    
                    case 'heartbeat_ack':
                        // Heartbeat acknowledged
                        // console.log('[Presence] Heartbeat acknowledged');
                        break;
                    
                    default:
                        console.warn('[Presence] Unknown message type:', data.type);
                }
            } catch (error) {
                console.error('[Presence] Message parsing error:', error);
            }
        }

        /**
         * WebSocket error occurred
         */
        onError(error) {
            console.error('[Presence] WebSocket error:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }

        /**
         * WebSocket connection closed
         */
        onClose(event) {
            console.log('[Presence] Disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.stopHeartbeat();
            this.updateConnectionStatus(false);
            
            // Attempt to reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            } else {
                console.error('[Presence] Max reconnection attempts reached');
            }
        }

        /**
         * Schedule reconnection attempt
         */
        scheduleReconnect() {
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
            }
            
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            
            console.log(`[Presence] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            this.reconnectTimeout = setTimeout(() => {
                this.connect();
            }, delay);
        }

        /**
         * Send message to WebSocket server
         */
        send(data) {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(data));
                return true;
            } else {
                console.warn('[Presence] Cannot send - not connected');
                return false;
            }
        }

        /**
         * Start heartbeat interval
         */
        startHeartbeat() {
            this.stopHeartbeat(); // Clear any existing interval
            
            this.heartbeatInterval = setInterval(() => {
                const currentPage = window.location.pathname;
                this.send({
                    type: 'heartbeat',
                    page: currentPage
                });
            }, this.heartbeatFrequency);
            
            console.log('[Presence] Heartbeat started');
        }

        /**
         * Stop heartbeat interval
         */
        stopHeartbeat() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
        }

        /**
         * Notify server of page change
         */
        notifyPageChange(page) {
            this.send({
                type: 'page_change',
                page: page
            });
        }

        /**
         * Handle initial family presence data
         */
        handleFamilyPresence(members) {
            console.log('[Presence] Family presence data:', members);
            
            // Store presence data
            members.forEach(member => {
                this.familyPresence.set(member.user_id, member);
            });
            
            // Update UI
            this.updateCrewList(members);
        }

        /**
         * Handle presence update (user went online/offline)
         */
        handlePresenceUpdate(data) {
            console.log('[Presence] User status changed:', data.username, data.is_online ? 'online' : 'offline');
            
            // Update stored data
            const existingData = this.familyPresence.get(data.user_id) || {};
            this.familyPresence.set(data.user_id, {
                ...existingData,
                is_online: data.is_online,
                last_seen: data.last_seen
            });
            
            // Update UI
            this.updateCrewMemberStatus(data.user_id, data.is_online, data.last_seen);
            
            // Play sound for status change
            if (window.ExpanseAudio && window.ExpanseAudio.play) {
                window.ExpanseAudio.play(data.is_online ? 'success' : 'click');
            }
        }

        /**
         * Handle user page change
         */
        handlePageChange(data) {
            console.log('[Presence] User page change:', data.username, data.page);
            
            // Update stored data
            const existingData = this.familyPresence.get(data.user_id) || {};
            this.familyPresence.set(data.user_id, {
                ...existingData,
                current_page: data.page
            });
            
            // Could show page change indicator in UI (future feature)
        }

        /**
         * Update connection status indicator
         */
        updateConnectionStatus(isConnected) {
            const statusEl = document.querySelector('.connection-status');
            if (!statusEl) return;
            
            if (isConnected) {
                statusEl.classList.remove('disconnected');
                statusEl.classList.add('connected');
                statusEl.textContent = 'CONNECTED';
            } else {
                statusEl.classList.remove('connected');
                statusEl.classList.add('disconnected');
                statusEl.textContent = 'DISCONNECTED';
            }
        }

        /**
         * Update crew list UI with all family members
         */
        updateCrewList(members) {
            const crewList = document.querySelector('.crew-list');
            if (!crewList) {
                console.warn('[Presence] Crew list element not found');
                return;
            }
            
            // Clear existing list
            crewList.innerHTML = '';
            
            // Add each crew member
            members.forEach(member => {
                const crewItem = this.createCrewItem(member);
                crewList.appendChild(crewItem);
            });
        }

        /**
         * Create crew member list item
         */
        createCrewItem(member) {
            const item = document.createElement('div');
            item.className = 'crew-member';
            item.dataset.userId = member.user_id;
            
            const statusClass = member.is_online ? 'online' : 'offline';
            const statusPulse = member.is_online ? '<span class="status-pulse"></span>' : '';
            
            const roleIcon = this.getRoleIcon(member.role);
            const lastSeen = member.is_online ? 'Online now' : this.formatLastSeen(member.last_seen);
            
            item.innerHTML = `
                <div class="crew-status ${statusClass}">
                    <div class="status-indicator"></div>
                    ${statusPulse}
                </div>
                <div class="crew-info">
                    <div class="crew-name">
                        ${roleIcon} ${member.full_name}
                    </div>
                    <div class="crew-detail">${this.formatRole(member.role)} • ${lastSeen}</div>
                </div>
            `;
            
            return item;
        }

        /**
         * Update specific crew member status
         */
        updateCrewMemberStatus(userId, isOnline, lastSeen) {
            const crewItem = document.querySelector(`[data-user-id="${userId}"]`);
            if (!crewItem) return;
            
            const statusEl = crewItem.querySelector('.crew-status');
            const detailEl = crewItem.querySelector('.crew-detail');
            
            if (statusEl) {
                statusEl.className = `crew-status ${isOnline ? 'online' : 'offline'}`;
                
                // Add/remove pulse animation
                const existingPulse = statusEl.querySelector('.status-pulse');
                if (isOnline && !existingPulse) {
                    const pulse = document.createElement('span');
                    pulse.className = 'status-pulse';
                    statusEl.appendChild(pulse);
                } else if (!isOnline && existingPulse) {
                    existingPulse.remove();
                }
            }
            
            if (detailEl) {
                const role = detailEl.textContent.split('•')[0].trim();
                const lastSeenText = isOnline ? 'Online now' : this.formatLastSeen(lastSeen);
                detailEl.textContent = `${role} • ${lastSeenText}`;
            }
            
            // Add brief glow effect
            crewItem.classList.add('status-changed');
            setTimeout(() => {
                crewItem.classList.remove('status-changed');
            }, 1000);
        }

        /**
         * Get role icon
         */
        getRoleIcon(role) {
            const icons = {
                'admin': '<i class="bi bi-shield-fill-check"></i>',
                'parent': '<i class="bi bi-person-fill"></i>',
                'child': '<i class="bi bi-person"></i>',
                'other': '<i class="bi bi-person-circle"></i>'
            };
            return icons[role] || icons['other'];
        }

        /**
         * Format role for display
         */
        formatRole(role) {
            const roles = {
                'admin': 'ADMIN',
                'parent': 'PARENT',
                'child': 'CHILD',
                'other': 'MEMBER'
            };
            return roles[role] || 'MEMBER';
        }

        /**
         * Format last seen timestamp
         */
        formatLastSeen(timestamp) {
            const now = new Date();
            const lastSeen = new Date(timestamp);
            const delta = Math.floor((now - lastSeen) / 1000); // seconds
            
            if (delta < 60) return 'Just now';
            if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
            if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
            return `${Math.floor(delta / 86400)}d ago`;
        }

        /**
         * Disconnect and cleanup
         */
        disconnect() {
            console.log('[Presence] Disconnecting...');
            
            this.stopHeartbeat();
            
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
                this.reconnectTimeout = null;
            }
            
            if (this.socket) {
                this.socket.close();
                this.socket = null;
            }
            
            this.isConnected = false;
            this.reconnectAttempts = 0;
        }
    }

    // Initialize presence manager
    const presenceManager = new ExpansePresenceManager();
    
    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            presenceManager.init();
        });
    } else {
        presenceManager.init();
    }
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('[Presence] Page hidden');
        } else {
            console.log('[Presence] Page visible');
            // Reconnect if disconnected
            if (!presenceManager.isConnected) {
                presenceManager.connect();
            }
        }
    });
    
    // Notify on page navigation (for SPAs or manual tracking)
    window.addEventListener('popstate', () => {
        if (presenceManager.isConnected) {
            presenceManager.notifyPageChange(window.location.pathname);
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        presenceManager.disconnect();
    });
    
    // Expose to window for manual control
    window.ExpansePresence = presenceManager;
    
    console.log('[Presence] System loaded');
})();
