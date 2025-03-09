import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useNavigation } from '@/context/NavigationContext'
import { createStudySession } from '@/services/api'

type Group = {
  id: number
  name: string
}

type StudyActivity = {
  id: number
  title: string
  launch_url: string
  preview_url: string
}

type LaunchData = {
  activity: StudyActivity
  groups: Group[]
}

export default function StudyActivityLaunch() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { setCurrentStudyActivity } = useNavigation()
  const [launchData, setLaunchData] = useState<LaunchData | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`http://localhost:5100/api/study-activities/${id}/launch`)
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch launch data')
        return response.json()
      })
      .then(data => {
        setLaunchData(data)
        setCurrentStudyActivity(data.activity)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [id, setCurrentStudyActivity])

  // Clean up when unmounting
  useEffect(() => {
    return () => {
      setCurrentStudyActivity(null)
    }
  }, [setCurrentStudyActivity])

  const handleLaunch = async () => {
    if (!launchData?.activity || !selectedGroup) {
      console.log('Missing data:', { activity: launchData?.activity, selectedGroup });
      return;
    }
    
    try {
      console.log('Creating study session with:', { groupId: selectedGroup, activityId: launchData.activity.id });
      // Create a study session first
      const result = await createStudySession(parseInt(selectedGroup), launchData.activity.id);
      const sessionId = result.session_id;
      console.log('Study session created:', { sessionId });
      if (!sessionId) {
        console.error('No session ID returned from server');
        return;
      }
      
      // Open Gradio app in a new tab - always use localhost
      const gradioUrl = `http://localhost:8000/?session_id=${sessionId}&group_id=${selectedGroup}`;
      console.log('Opening Gradio app with URL:', gradioUrl);
      
      // Add a small delay to ensure session is saved
      await new Promise(resolve => setTimeout(resolve, 500));
      
      window.open(gradioUrl, '_blank');
      
      // Navigate to the session show page in the main app
      const showUrl = `/sessions/${sessionId}`;
      console.log('Navigating to:', { url: showUrl });
      navigate(showUrl);
    } catch (error) {
      console.error('Failed to launch activity:', error);
      setError(error instanceof Error ? error.message : 'Failed to launch activity');
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>
  }

  if (!launchData) {
    return <div className="text-red-500">Activity not found</div>
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">{launchData.activity.title}</h1>
      
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Select Word Group</label>
          <Select onValueChange={setSelectedGroup} value={selectedGroup}>
            <SelectTrigger>
              <SelectValue placeholder="Select a word group" />
            </SelectTrigger>
            <SelectContent>
              {launchData.groups.map((group) => (
                <SelectItem key={group.id} value={group.id.toString()}>
                  {group.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button 
          onClick={handleLaunch}
          disabled={!selectedGroup}
          className="w-full"
        >
          Launch Now
        </Button>
      </div>
    </div>
  )
}
