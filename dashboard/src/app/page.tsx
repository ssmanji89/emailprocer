'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, Mail, BarChart3, FileText } from 'lucide-react'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Auto-redirect to dashboard after 3 seconds
    const timer = setTimeout(() => {
      router.push('/dashboard')
    }, 3000)

    return () => clearTimeout(timer)
  }, [router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">
            EmailBot Dashboard
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            AI-powered email classification and response system with comprehensive analytics and automation insights.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="text-center">
              <Activity className="h-8 w-8 mx-auto text-blue-600" />
              <CardTitle className="text-lg">Real-time Processing</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Monitor email processing pipeline with live analytics
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <BarChart3 className="h-8 w-8 mx-auto text-green-600" />
              <CardTitle className="text-lg">Classification Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Track AI classification accuracy and confidence metrics
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <FileText className="h-8 w-8 mx-auto text-purple-600" />
              <CardTitle className="text-lg">Automation Patterns</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Identify opportunities for process automation
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Mail className="h-8 w-8 mx-auto text-orange-600" />
              <CardTitle className="text-lg">Email Management</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Complete email history and escalation tracking
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Button 
            size="lg" 
            onClick={() => router.push('/dashboard')}
            className="text-lg px-8 py-3"
          >
            Go to Dashboard
          </Button>
          <p className="text-sm text-muted-foreground">
            Redirecting automatically in 3 seconds...
          </p>
        </div>
      </div>
    </div>
  )
}
