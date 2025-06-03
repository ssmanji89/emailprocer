'use client'

import { useState, useEffect, useCallback } from 'react'
import { Toast, ToastContainer } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { wsClient, WebSocketEvent } from '@/lib/websocket-client'
import { apiClient } from '@/lib/api-client'
import { formatTimeAgo, formatRelativeTime, getStatusColor } from '@/lib/utils'
import {
  Bell,
  X,
  AlertTriangle,
  Clock,
  Users,
  CheckCircle,
  AlertCircle,
  Info,
  ExternalLink,
  Trash2,
  Settings
} from 'lucide-react'

interface Notification {
  id: string
  type: 'sla_warning' | 'sla_overdue' | 'assignment' | 'status_change' | 'team_notification' | 'resolution'
  title: string
  message: string
  escalationId?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  acknowledged: boolean
  data?: any
}

interface EscalationNotificationsProps {
  userId?: string
  teamIds?: string[]
  showToasts?: boolean
  showPanel?: boolean
  maxNotifications?: number
}

export function EscalationNotifications({
  userId,
  teamIds = [],
  showToasts = true,
  showPanel = true,
  maxNotifications = 10
}: EscalationNotificationsProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  // Load initial notifications
  useEffect(() => {
    loadInitialNotifications()
  }, [])

  // Set up WebSocket connections
  useEffect(() => {
    const handleConnectionChange = (connected: boolean) => {
      setIsConnected(connected)
    }

    const handleEscalationEvent = (event: WebSocketEvent) => {
      const notification = createNotificationFromEvent(event)
      if (notification) {
        addNotification(notification)
      }
    }

    wsClient.onConnectionChange(handleConnectionChange)
    wsClient.on('escalation_created', handleEscalationEvent)
    wsClient.on('escalation_assigned', handleEscalationEvent)
    wsClient.on('escalation_status_changed', handleEscalationEvent)
    wsClient.on('escalation_resolved', handleEscalationEvent)
    wsClient.on('sla_warning', handleEscalationEvent)
    wsClient.on('sla_overdue', handleEscalationEvent)
    wsClient.on('team_notification', handleEscalationEvent)

    // Subscribe to team notifications if team IDs provided
    if (teamIds.length > 0) {
      wsClient.subscribeToTeamNotifications(teamIds)
    }

    return () => {
      wsClient.offConnectionChange(handleConnectionChange)
      wsClient.off('escalation_created', handleEscalationEvent)
      wsClient.off('escalation_assigned', handleEscalationEvent)
      wsClient.off('escalation_status_changed', handleEscalationEvent)
      wsClient.off('escalation_resolved', handleEscalationEvent)
      wsClient.off('sla_warning', handleEscalationEvent)
      wsClient.off('sla_overdue', handleEscalationEvent)
      wsClient.off('team_notification', handleEscalationEvent)
    }
  }, [teamIds])

  const loadInitialNotifications = async () => {
    try {
      const alerts = await apiClient.getAlerts()
      const mappedNotifications = alerts.map(alert => ({
        id: alert.id,
        type: alert.type as any,
        title: getNotificationTitle(alert.type),
        message: alert.message,
        escalationId: alert.escalation_id,
        priority: 'medium' as const, // Default priority
        timestamp: alert.created_at,
        acknowledged: alert.acknowledged,
        data: {}
      }))
      
      setNotifications(mappedNotifications)
      setUnreadCount(mappedNotifications.filter(n => !n.acknowledged).length)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    }
  }

  const createNotificationFromEvent = (event: WebSocketEvent): Notification | null => {
    const baseNotification = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: event.timestamp,
      acknowledged: false,
      data: event.data
    }

    switch (event.type) {
      case 'escalation_created':
        return {
          ...baseNotification,
          type: 'status_change',
          title: 'New Escalation Created',
          message: `Escalation for "${event.data.escalation.email_subject}" has been created`,
          escalationId: event.data.escalation.escalation_id,
          priority: event.data.escalation.priority
        }

      case 'escalation_assigned':
        return {
          ...baseNotification,
          type: 'assignment',
          title: 'Escalation Assigned',
          message: event.data.message || 'You have been assigned to an escalation',
          escalationId: event.data.escalation.escalation_id,
          priority: event.data.escalation.priority
        }

      case 'escalation_status_changed':
        return {
          ...baseNotification,
          type: 'status_change',
          title: 'Status Updated',
          message: `Escalation status changed to ${event.data.escalation.status}`,
          escalationId: event.data.escalation.escalation_id,
          priority: event.data.escalation.priority
        }

      case 'escalation_resolved':
        return {
          ...baseNotification,
          type: 'resolution',
          title: 'Escalation Resolved',
          message: `Escalation "${event.data.escalation.email_subject}" has been resolved`,
          escalationId: event.data.escalation.escalation_id,
          priority: 'low'
        }

      case 'sla_warning':
        return {
          ...baseNotification,
          type: 'sla_warning',
          title: 'SLA Warning',
          message: event.data.message || 'Escalation SLA deadline approaching',
          escalationId: event.data.escalation_id,
          priority: 'high'
        }

      case 'sla_overdue':
        return {
          ...baseNotification,
          type: 'sla_overdue',
          title: 'SLA Overdue',
          message: event.data.message || 'Escalation is now overdue',
          escalationId: event.data.escalation_id,
          priority: 'critical'
        }

      case 'team_notification':
        return {
          ...baseNotification,
          type: 'team_notification',
          title: 'Team Notification',
          message: event.data.message,
          escalationId: event.data.escalation_id,
          priority: event.data.priority || 'medium'
        }

      default:
        return null
    }
  }

  const addNotification = useCallback((notification: Notification) => {
    setNotifications(prev => {
      const updated = [notification, ...prev].slice(0, maxNotifications)
      return updated
    })
    
    if (!notification.acknowledged) {
      setUnreadCount(prev => prev + 1)
    }

    // Show toast notification if enabled
    if (showToasts) {
      showToastNotification(notification)
    }

    // Play notification sound for high priority
    if (notification.priority === 'critical' || notification.priority === 'high') {
      playNotificationSound()
    }
  }, [maxNotifications, showToasts])

  const acknowledgeNotification = async (notificationId: string) => {
    try {
      await apiClient.acknowledgeAlert(notificationId)
      
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, acknowledged: true } : n
        )
      )
      
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Failed to acknowledge notification:', error)
    }
  }

  const removeNotification = (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId))
    
    const notification = notifications.find(n => n.id === notificationId)
    if (notification && !notification.acknowledged) {
      setUnreadCount(prev => Math.max(0, prev - 1))
    }
  }

  const clearAllNotifications = () => {
    setNotifications([])
    setUnreadCount(0)
  }

  const markAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.acknowledged)
    
    for (const notification of unreadNotifications) {
      try {
        await apiClient.acknowledgeAlert(notification.id)
      } catch (error) {
        console.error('Failed to acknowledge notification:', error)
      }
    }
    
    setNotifications(prev =>
      prev.map(n => ({ ...n, acknowledged: true }))
    )
    setUnreadCount(0)
  }

  const showToastNotification = (notification: Notification) => {
    // This would integrate with a toast system
    console.log('Toast notification:', notification)
  }

  const playNotificationSound = () => {
    // Play browser notification sound
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Audio('/notification-sound.mp3').play().catch(() => {
          // Ignore audio play errors
        })
      } catch (error) {
        // Ignore audio errors
      }
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'sla_warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'sla_overdue':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'assignment':
        return <Users className="h-4 w-4 text-blue-600" />
      case 'status_change':
        return <Info className="h-4 w-4 text-purple-600" />
      case 'resolution':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'team_notification':
        return <Bell className="h-4 w-4 text-orange-600" />
      default:
        return <Info className="h-4 w-4 text-gray-600" />
    }
  }

  const getNotificationTitle = (type: string) => {
    switch (type) {
      case 'sla_warning': return 'SLA Warning'
      case 'sla_overdue': return 'SLA Overdue'
      case 'assignment': return 'Assignment'
      case 'status_change': return 'Status Change'
      case 'resolution': return 'Resolution'
      case 'team_notification': return 'Team Update'
      default: return 'Notification'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'border-l-red-500 bg-red-50'
      case 'high': return 'border-l-orange-500 bg-orange-50'
      case 'medium': return 'border-l-yellow-500 bg-yellow-50'
      case 'low': return 'border-l-green-500 bg-green-50'
      default: return 'border-l-gray-500 bg-gray-50'
    }
  }

  if (!showPanel) {
    return (
      <div className="fixed top-4 right-4 z-50">
        <Button
          variant="outline"
          size="sm"
          className="relative"
          onClick={() => setIsPanelOpen(true)}
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </div>
    )
  }

  return (
    <>
      {/* Notification Bell Icon */}
      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          className="relative"
          onClick={() => setIsPanelOpen(!isPanelOpen)}
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 h-4 w-4 rounded-full p-0 flex items-center justify-center text-xs">
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>

        {/* Connection Status Indicator */}
        <div
          className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
      </div>

      {/* Notification Panel */}
      {isPanelOpen && (
        <div className="absolute top-full right-0 mt-2 w-80 max-h-96 bg-white border rounded-lg shadow-lg z-50 overflow-hidden">
          <Card className="border-0">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Notifications ({unreadCount} unread)
                </CardTitle>
                <div className="flex gap-1">
                  {unreadCount > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={markAllAsRead}
                      className="text-xs px-2 py-1"
                    >
                      Mark all read
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAllNotifications}
                    className="text-xs px-2 py-1"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsPanelOpen(false)}
                    className="text-xs px-2 py-1"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 max-h-64 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No notifications</p>
                </div>
              ) : (
                <div className="space-y-0">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-3 border-l-4 border-b border-gray-100 hover:bg-gray-50 ${
                        getPriorityColor(notification.priority)
                      } ${
                        !notification.acknowledged ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-start gap-2">
                            {getNotificationIcon(notification.type)}
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm truncate">
                                {notification.title}
                              </p>
                              <p className="text-xs text-gray-600 mt-1">
                                {notification.message}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-xs text-gray-500">
                                  {formatTimeAgo(notification.timestamp)}
                                </span>
                                {notification.escalationId && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-xs px-1 py-0 h-auto text-blue-600 hover:text-blue-800"
                                    onClick={() => {
                                      window.open(`/escalations/${notification.escalationId}`, '_blank')
                                    }}
                                  >
                                    <ExternalLink className="h-3 w-3 mr-1" />
                                    View
                                  </Button>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          {!notification.acknowledged && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => acknowledgeNotification(notification.id)}
                              className="text-xs px-2 py-1"
                            >
                              <CheckCircle className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeNotification(notification.id)}
                            className="text-xs px-2 py-1"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
} 