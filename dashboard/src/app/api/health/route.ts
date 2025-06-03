import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'emailbot-dashboard',
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      components: {
        api_connection: 'unknown',
        websocket_connection: 'unknown',
        build_status: 'healthy'
      }
    }

    // Test API connection
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const apiResponse = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      })

      if (apiResponse.ok) {
        healthStatus.components.api_connection = 'healthy'
      } else {
        healthStatus.components.api_connection = 'unhealthy'
        healthStatus.status = 'degraded'
      }
    } catch (error) {
      healthStatus.components.api_connection = `error: ${error instanceof Error ? error.message : 'Unknown error'}`
      healthStatus.status = 'degraded'
    }

    // Test WebSocket connection capability
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
      // We can't actually test WebSocket in a server-side API route,
      // but we can validate the URL format and environment
      if (wsUrl && (wsUrl.startsWith('ws://') || wsUrl.startsWith('wss://'))) {
        healthStatus.components.websocket_connection = 'configured'
      } else {
        healthStatus.components.websocket_connection = 'misconfigured'
        healthStatus.status = 'degraded'
      }
    } catch (error) {
      healthStatus.components.websocket_connection = `error: ${error instanceof Error ? error.message : 'Unknown error'}`
      healthStatus.status = 'degraded'
    }

    // Return appropriate status code
    const statusCode = healthStatus.status === 'healthy' ? 200 : 503

    return NextResponse.json(healthStatus, { status: statusCode })

  } catch (error) {
    const errorResponse = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      service: 'emailbot-dashboard',
      error: error instanceof Error ? error.message : 'Unknown error',
      components: {
        api_connection: 'error',
        websocket_connection: 'error',
        build_status: 'error'
      }
    }

    return NextResponse.json(errorResponse, { status: 503 })
  }
} 